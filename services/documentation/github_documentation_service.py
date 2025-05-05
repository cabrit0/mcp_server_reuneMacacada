"""
GitHub documentation service.
"""

import re
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
import aiohttp

from infrastructure.logging import logger
from infrastructure.cache import cache
from api.models import Resource
from services.documentation.documentation_service import DocumentationService


class GitHubDocumentationService(DocumentationService):
    """
    GitHub documentation service.
    Provides access to GitHub documentation for Git and GitHub-related topics.
    """

    # Base URLs for GitHub documentation
    BASE_URL = "https://docs.github.com/en"
    SEARCH_URL = "https://docs.github.com/search"
    
    # Topics supported by GitHub documentation
    SUPPORTED_TOPICS = [
        "git", "github", "actions", "github actions", "workflow", "ci", "cd",
        "continuous integration", "continuous deployment", "repository", "repo",
        "pull request", "pr", "issue", "fork", "branch", "merge", "commit",
        "clone", "push", "pull", "remote", "origin", "upstream", "gh", "gist"
    ]
    
    # Languages supported by GitHub documentation
    SUPPORTED_LANGUAGES = ["en", "es", "ja", "ko", "pt", "zh"]

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the GitHub documentation service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger("documentation.github")
        self.logger.info("Initialized GitHubDocumentationService")

    @property
    def name(self) -> str:
        """
        Get the name of the documentation service.

        Returns:
            Service name
        """
        return "GitHub Documentation"

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

    def _is_topic_supported(self, topic: str) -> bool:
        """
        Check if a topic is supported by GitHub documentation.

        Args:
            topic: Topic to check

        Returns:
            True if the topic is supported, False otherwise
        """
        topic_lower = topic.lower()
        return any(supported in topic_lower for supported in self.SUPPORTED_TOPICS)

    def _get_base_url_for_language(self, language: str) -> str:
        """
        Get the base URL for a specific language.

        Args:
            language: Language code (e.g., 'en', 'pt')

        Returns:
            Base URL for the language
        """
        if language not in self.SUPPORTED_LANGUAGES:
            return self.BASE_URL
        return f"https://docs.github.com/{language}"

    async def search_documentation(
        self,
        topic: str,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Search for documentation related to a topic in GitHub documentation.

        Args:
            topic: Topic to search for
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with documentation information
        """
        # Check if topic is supported
        if not self._is_topic_supported(topic):
            self.logger.debug(f"Topic '{topic}' not supported by GitHub documentation")
            return []

        # Check if language is supported
        if language not in self.SUPPORTED_LANGUAGES:
            self.logger.debug(f"Language '{language}' not supported by GitHub documentation, using English")
            language = "en"

        # Check cache first
        cache_key = f"github:search:{topic}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached GitHub documentation search results for '{topic}'")
            return cached_result

        # Build search URL
        search_url = self.SEARCH_URL
        params = {"query": topic, "language": language}

        try:
            # Perform search
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params) as response:
                    if response.status != 200:
                        self.logger.warning(f"GitHub documentation search failed with status {response.status}")
                        return []

                    html = await response.text()

            # Parse search results
            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Find search result items
            result_items = soup.select(".search-result-item")
            for item in result_items[:max_results]:
                # Extract title and URL
                title_elem = item.select_one(".search-result-title")
                if not title_elem or not title_elem.get_text().strip():
                    continue

                title = title_elem.get_text().strip()
                url_elem = item.select_one("a")
                url = url_elem.get("href") if url_elem else None

                if not url:
                    continue

                # Make URL absolute if it's relative
                if url.startswith("/"):
                    url = f"https://docs.github.com{url}"

                # Extract excerpt
                excerpt_elem = item.select_one(".search-result-content")
                excerpt = excerpt_elem.get_text().strip() if excerpt_elem else ""

                # Create result item
                result = {
                    "id": f"github_{uuid.uuid4().hex[:8]}",
                    "title": title,
                    "url": url,
                    "description": excerpt or f"GitHub documentation about {topic}",
                    "source": "GitHub Documentation",
                    "type": "documentation"
                }

                results.append(result)

            # Cache the results
            if results:
                cache.setex(cache_key, self.cache_ttl, results)
                self.logger.debug(f"Cached GitHub documentation search results for '{topic}' ({len(results)} items)")
            else:
                self.logger.warning(f"No GitHub documentation found for '{topic}'")

            return results
        except Exception as e:
            self.logger.error(f"Error searching GitHub documentation for '{topic}': {str(e)}")
            return []

    async def get_documentation_details(
        self,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific GitHub documentation item.

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
            cache_key = f"github:doc:{doc_id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                self.logger.debug(f"Using cached GitHub documentation details for '{doc_id}'")
                return cached_result

            # We can't get details without a URL
            self.logger.warning(f"Cannot get GitHub documentation details without a URL: {doc_id}")
            return None

        try:
            # Fetch documentation page
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.warning(f"GitHub documentation fetch failed with status {response.status}")
                        return None

                    html = await response.text()

            # Parse documentation page
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title_elem = soup.select_one("h1")
            title = title_elem.get_text().strip() if title_elem else "GitHub Documentation"

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

            # Create result
            result = {
                "id": f"github_{uuid.uuid4().hex[:8]}",
                "title": title,
                "url": url,
                "description": description or f"GitHub documentation: {title}",
                "content": content,
                "source": "GitHub Documentation",
                "type": "documentation"
            }

            # Cache the result
            if doc_id != url:  # Only cache if we have a proper ID
                cache.setex(f"github:doc:{doc_id}", self.cache_ttl, result)
                self.logger.debug(f"Cached GitHub documentation details for '{doc_id}'")

            return result
        except Exception as e:
            self.logger.error(f"Error getting GitHub documentation details for '{doc_id}': {str(e)}")
            return None

    async def search_documentation_for_topic(
        self,
        topic: str,
        subtopic: str = None,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Resource]:
        """
        Search for GitHub documentation related to a topic and convert to Resource objects.

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
            self.logger.debug(f"Topic '{topic}' not supported by GitHub documentation")
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
                readTime=10,  # Estimate 10 minutes read time for GitHub documentation
                difficulty="intermediate",
                thumbnail=None
            )

            # Add subtopic information if applicable
            if subtopic:
                resource.title = f"{resource.title} - Relevante para: {subtopic}"

            resources.append(resource)

        return resources
