"""
Python documentation service.
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


class PythonDocumentationService(DocumentationService):
    """
    Python documentation service.
    Provides access to Python documentation for Python-related topics.
    """

    # Base URLs for Python documentation
    BASE_URL = "https://docs.python.org/3/"
    SEARCH_URL = "https://docs.python.org/3/search.html"
    
    # Topics supported by Python documentation
    SUPPORTED_TOPICS = [
        "python", "py", "python3", "pip", "venv", "virtualenv",
        "django", "flask", "fastapi", "sqlalchemy", "pandas",
        "numpy", "matplotlib", "scipy", "pytorch", "tensorflow",
        "scikit-learn", "sklearn", "asyncio", "aiohttp", "requests",
        "beautifulsoup", "bs4", "selenium", "pytest", "unittest"
    ]
    
    # Languages supported by Python documentation
    SUPPORTED_LANGUAGES = ["en", "fr", "ja", "ko", "pt-br", "zh-cn"]
    
    # Language mapping for Python documentation URLs
    LANGUAGE_MAPPING = {
        "pt": "pt-br",
        "zh": "zh-cn"
    }

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the Python documentation service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger("documentation.python")
        self.logger.info("Initialized PythonDocumentationService")

    @property
    def name(self) -> str:
        """
        Get the name of the documentation service.

        Returns:
            Service name
        """
        return "Python Documentation"

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
        Map a language code to the format used by Python documentation.

        Args:
            language: Language code (e.g., 'pt', 'en')

        Returns:
            Python documentation language code
        """
        return self.LANGUAGE_MAPPING.get(language, language)

    def _is_topic_supported(self, topic: str) -> bool:
        """
        Check if a topic is supported by Python documentation.

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
        mdn_language = self._map_language(language)
        if mdn_language == "en":
            return self.BASE_URL
        return f"https://docs.python.org/3/{mdn_language}/"

    async def search_documentation(
        self,
        topic: str,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Search for documentation related to a topic in Python documentation.

        Args:
            topic: Topic to search for
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with documentation information
        """
        # Check if topic is supported
        if not self._is_topic_supported(topic):
            self.logger.debug(f"Topic '{topic}' not supported by Python documentation")
            return []

        # Map language to Python documentation format
        py_language = self._map_language(language)
        if py_language not in self.SUPPORTED_LANGUAGES:
            self.logger.debug(f"Language '{language}' not supported by Python documentation, using English")
            py_language = "en"

        # Check cache first
        cache_key = f"python:search:{topic}_{max_results}_{py_language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached Python documentation search results for '{topic}'")
            return cached_result

        # Build search URL
        base_url = self._get_base_url_for_language(language)
        search_url = urljoin(base_url, "search.html")
        params = {"q": topic, "check_keywords": "yes", "area": "default"}

        try:
            # Perform search
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params) as response:
                    if response.status != 200:
                        self.logger.warning(f"Python documentation search failed with status {response.status}")
                        return []

                    html = await response.text()

            # Parse search results
            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Find search result items
            result_items = soup.select("#search-results .search li")
            for item in result_items[:max_results]:
                # Extract title and URL
                title_elem = item.select_one("a")
                if not title_elem or not title_elem.get_text().strip():
                    continue

                title = title_elem.get_text().strip()
                url = title_elem.get("href")
                if not url:
                    continue

                # Make URL absolute if it's relative
                if not url.startswith("http"):
                    url = urljoin(base_url, url)

                # Extract excerpt
                excerpt = ""
                for sibling in title_elem.next_siblings:
                    if sibling.name != "a" and sibling.string and sibling.string.strip():
                        excerpt = sibling.string.strip()
                        break

                # Create result item
                result = {
                    "id": f"python_{uuid.uuid4().hex[:8]}",
                    "title": title,
                    "url": url,
                    "description": excerpt or f"Python documentation about {topic}",
                    "source": "Python Documentation",
                    "type": "documentation"
                }

                results.append(result)

            # Cache the results
            if results:
                cache.setex(cache_key, self.cache_ttl, results)
                self.logger.debug(f"Cached Python documentation search results for '{topic}' ({len(results)} items)")
            else:
                self.logger.warning(f"No Python documentation found for '{topic}'")

            return results
        except Exception as e:
            self.logger.error(f"Error searching Python documentation for '{topic}': {str(e)}")
            return []

    async def get_documentation_details(
        self,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific Python documentation item.

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
            cache_key = f"python:doc:{doc_id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                self.logger.debug(f"Using cached Python documentation details for '{doc_id}'")
                return cached_result

            # We can't get details without a URL
            self.logger.warning(f"Cannot get Python documentation details without a URL: {doc_id}")
            return None

        try:
            # Fetch documentation page
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.warning(f"Python documentation fetch failed with status {response.status}")
                        return None

                    html = await response.text()

            # Parse documentation page
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title_elem = soup.select_one("h1")
            title = title_elem.get_text().strip() if title_elem else "Python Documentation"

            # Extract content
            content_elem = soup.select_one(".body")
            content = content_elem.get_text().strip() if content_elem else ""

            # Extract description
            description = ""
            first_p = soup.select_one(".body p")
            if first_p:
                description = first_p.get_text().strip()

            # Limit description length
            if description and len(description) > 300:
                description = description[:297] + "..."

            # Create result
            result = {
                "id": f"python_{uuid.uuid4().hex[:8]}",
                "title": title,
                "url": url,
                "description": description or f"Python documentation: {title}",
                "content": content,
                "source": "Python Documentation",
                "type": "documentation"
            }

            # Cache the result
            if doc_id != url:  # Only cache if we have a proper ID
                cache.setex(f"python:doc:{doc_id}", self.cache_ttl, result)
                self.logger.debug(f"Cached Python documentation details for '{doc_id}'")

            return result
        except Exception as e:
            self.logger.error(f"Error getting Python documentation details for '{doc_id}': {str(e)}")
            return None

    async def search_documentation_for_topic(
        self,
        topic: str,
        subtopic: str = None,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Resource]:
        """
        Search for Python documentation related to a topic and convert to Resource objects.

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
            self.logger.debug(f"Topic '{topic}' not supported by Python documentation")
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
            # Determine difficulty based on title and description
            difficulty = "intermediate"
            title_lower = doc.get("title", "").lower()
            desc_lower = doc.get("description", "").lower()
            
            if any(term in title_lower or term in desc_lower for term in ["basic", "intro", "getting started", "tutorial"]):
                difficulty = "beginner"
            elif any(term in title_lower or term in desc_lower for term in ["advanced", "expert", "internals", "deep"]):
                difficulty = "advanced"

            resource = Resource(
                id=doc.get("id"),
                title=doc.get("title", ""),
                url=doc.get("url", ""),
                type="documentation",
                description=doc.get("description", ""),
                duration=None,
                readTime=15,  # Estimate 15 minutes read time for Python documentation
                difficulty=difficulty,
                thumbnail=None
            )

            # Add subtopic information if applicable
            if subtopic:
                resource.title = f"{resource.title} - Relevante para: {subtopic}"

            resources.append(resource)

        return resources
