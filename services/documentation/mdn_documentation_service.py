"""
MDN Web Docs documentation service.
"""

import re
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from bs4 import BeautifulSoup
import aiohttp

from infrastructure.logging import logger
from infrastructure.cache import cache
from api.models import Resource
from services.documentation.documentation_service import DocumentationService


class MDNDocumentationService(DocumentationService):
    """
    MDN Web Docs documentation service.
    Provides access to MDN Web Docs for web development topics.
    """

    # Base URLs for MDN Web Docs
    BASE_URL = "https://developer.mozilla.org"
    SEARCH_URL = "https://developer.mozilla.org/{language}/search"

    # Topics supported by MDN
    SUPPORTED_TOPICS = [
        "html", "css", "javascript", "js", "web", "frontend", "front-end",
        "dom", "browser", "api", "http", "svg", "webgl", "canvas",
        "accessibility", "a11y", "performance", "security", "animation",
        "webapi", "web api", "webcomponents", "web components"
    ]

    # Languages supported by MDN
    SUPPORTED_LANGUAGES = ["en", "es", "fr", "ja", "ko", "pt-BR", "zh-CN", "zh-TW"]

    # Language mapping for MDN URLs
    LANGUAGE_MAPPING = {
        "pt": "pt-BR",
        "zh": "zh-CN"
    }

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the MDN documentation service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger("documentation.mdn")
        self.logger.info("Initialized MDNDocumentationService")

    @property
    def name(self) -> str:
        """
        Get the name of the documentation service.

        Returns:
            Service name
        """
        return "MDN Web Docs"

    @property
    def supported_languages(self) -> List[str]:
        """
        Get the list of languages supported by this documentation service.

        Returns:
            List of language codes
        """
        return self.SUPPORTED_LANGUAGES

    @property
    def supported_topics(self) -> List[str]:
        """
        Get the list of topics supported by this documentation service.

        Returns:
            List of topic names
        """
        return self.SUPPORTED_TOPICS

    def _map_language(self, language: str) -> str:
        """
        Map a language code to the format used by MDN.

        Args:
            language: Language code (e.g., 'pt', 'en')

        Returns:
            MDN language code
        """
        return self.LANGUAGE_MAPPING.get(language, language)

    def _is_topic_supported(self, topic: str) -> bool:
        """
        Check if a topic is supported by MDN.

        Args:
            topic: Topic to check

        Returns:
            True if the topic is supported, False otherwise
        """
        topic_lower = topic.lower()
        return any(supported in topic_lower for supported in self.SUPPORTED_TOPICS)

    async def search_documentation(
        self,
        topic: str,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Search for documentation related to a topic on MDN.

        Args:
            topic: Topic to search for
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with documentation information
        """
        # Check if topic is supported
        if not self._is_topic_supported(topic):
            self.logger.debug(f"Topic '{topic}' not supported by MDN")
            return []

        # Map language to MDN format
        mdn_language = self._map_language(language)
        if mdn_language not in self.SUPPORTED_LANGUAGES:
            self.logger.debug(f"Language '{language}' not supported by MDN, using English")
            mdn_language = "en-US"

        # Check cache first
        cache_key = f"mdn:search:{topic}_{max_results}_{mdn_language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached MDN search results for '{topic}'")
            return cached_result

        # Build search URL
        search_url = self.SEARCH_URL.format(language=mdn_language)
        params = {"q": topic, "locale": mdn_language}

        try:
            # Perform search
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params) as response:
                    if response.status != 200:
                        self.logger.warning(f"MDN search failed with status {response.status}")
                        return []

                    html = await response.text()

            # Parse search results
            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Log the HTML for debugging
            self.logger.debug(f"Parsing HTML from MDN search: {len(html)} characters")

            # Try different selectors for search results
            result_items = []

            # Try the main selector
            result_items = soup.select(".search-results-container .result")

            # If no results, try alternative selectors
            if not result_items:
                result_items = soup.select(".result-list .result")

            if not result_items:
                result_items = soup.select("article.result")

            if not result_items:
                # As a fallback, create a simple result with the search URL
                self.logger.warning(f"No search result items found for '{topic}', using fallback")
                results.append({
                    "id": f"mdn_{uuid.uuid4().hex[:8]}",
                    "title": f"MDN Web Docs: {topic}",
                    "url": f"https://developer.mozilla.org/{mdn_language}/search?q={quote(topic)}",
                    "description": f"MDN documentation about {topic}",
                    "source": "MDN Web Docs",
                    "type": "documentation"
                })
                return results

            self.logger.debug(f"Found {len(result_items)} result items")

            for item in result_items[:max_results]:
                # Try different selectors for title and URL
                title = ""
                url = ""

                # Try different title selectors
                title_elem = item.select_one(".result-title, .title, h3")
                if title_elem:
                    title = title_elem.get_text().strip()

                    # Try to get URL from title element
                    url = title_elem.get("href")
                    if not url:
                        url_elem = title_elem.select_one("a")
                        url = url_elem.get("href") if url_elem else None

                # If still no URL, try to find any link
                if not url:
                    url_elem = item.select_one("a")
                    url = url_elem.get("href") if url_elem else None

                if not title or not url:
                    continue

                # Make URL absolute if it's relative
                if url.startswith("/"):
                    url = f"{self.BASE_URL}{url}"

                # Extract excerpt using different selectors
                excerpt = ""
                for selector in [".result-excerpt", ".excerpt", "p"]:
                    excerpt_elem = item.select_one(selector)
                    if excerpt_elem:
                        excerpt = excerpt_elem.get_text().strip()
                        break

                # Create result item
                result = {
                    "id": f"mdn_{uuid.uuid4().hex[:8]}",
                    "title": title,
                    "url": url,
                    "description": excerpt or f"MDN documentation about {topic}",
                    "source": "MDN Web Docs",
                    "type": "documentation"
                }

                results.append(result)

            # Cache the results
            if results:
                cache.setex(cache_key, self.cache_ttl, results)
                self.logger.debug(f"Cached MDN search results for '{topic}' ({len(results)} items)")
            else:
                self.logger.warning(f"No MDN documentation found for '{topic}'")

            return results
        except Exception as e:
            self.logger.error(f"Error searching MDN for '{topic}': {str(e)}")
            return []

    async def get_documentation_details(
        self,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific MDN documentation item.

        Args:
            doc_id: Documentation ID or URL

        Returns:
            Dictionary with documentation details or None if not found
        """
        # Check if doc_id is a URL
        if doc_id.startswith("http"):
            url = doc_id
        else:
            # Check cache first
            cache_key = f"mdn:doc:{doc_id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                self.logger.debug(f"Using cached MDN documentation details for '{doc_id}'")
                return cached_result

            # We can't get details without a URL
            self.logger.warning(f"Cannot get MDN documentation details without a URL: {doc_id}")
            return None

        try:
            # Fetch documentation page
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.warning(f"MDN documentation fetch failed with status {response.status}")
                        return None

                    html = await response.text()

            # Parse documentation page
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title_elem = soup.select_one("h1")
            title = title_elem.get_text().strip() if title_elem else "MDN Documentation"

            # Extract content
            content_elem = soup.select_one("article")
            content = content_elem.get_text().strip() if content_elem else ""

            # Extract description
            meta_desc = soup.find("meta", attrs={"name": "description"})
            description = meta_desc["content"] if meta_desc and "content" in meta_desc.attrs else ""

            if not description:
                # Try to extract the first paragraph
                first_p = soup.select_one("article p")
                description = first_p.get_text().strip() if first_p else ""

            # Limit description length
            if description and len(description) > 300:
                description = description[:297] + "..."

            # Extract tags/keywords
            tags = []
            tags_elem = soup.select(".metadata tags a")
            if tags_elem:
                tags = [tag.get_text().strip() for tag in tags_elem]

            # Create result
            result = {
                "id": f"mdn_{uuid.uuid4().hex[:8]}",
                "title": title,
                "url": url,
                "description": description or f"MDN documentation: {title}",
                "content": content,
                "source": "MDN Web Docs",
                "type": "documentation",
                "tags": tags
            }

            # Cache the result
            if doc_id != url:  # Only cache if we have a proper ID
                cache.setex(f"mdn:doc:{doc_id}", self.cache_ttl, result)
                self.logger.debug(f"Cached MDN documentation details for '{doc_id}'")

            return result
        except Exception as e:
            self.logger.error(f"Error getting MDN documentation details for '{doc_id}': {str(e)}")
            return None

    async def search_documentation_for_topic(
        self,
        topic: str,
        subtopic: str = None,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Resource]:
        """
        Search for MDN documentation related to a topic and convert to Resource objects.

        Args:
            topic: Main topic
            subtopic: Optional subtopic for more specific results
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of Resource objects
        """
        # Check if topic is supported
        if not self._is_topic_supported(topic):
            self.logger.debug(f"Topic '{topic}' not supported by MDN")
            return []

        # Determine search query
        if subtopic:
            query = f"{topic} {subtopic}"
        else:
            query = topic

        # Search for documentation
        docs = await self.search_documentation(query, max_results, language)

        # Convert to Resource objects
        resources = []
        for doc in docs:
            resource = Resource(
                id=doc.get("id"),
                title=doc.get("title", ""),
                url=doc.get("url", ""),
                type="documentation",
                description=doc.get("description", ""),
                duration=None,
                readTime=10,  # Estimate 10 minutes read time for documentation
                difficulty="intermediate",
                thumbnail=None
            )

            # Add subtopic information if applicable
            if subtopic:
                resource.title = f"{resource.title} - Relevante para: {subtopic}"

            resources.append(resource)

        return resources
