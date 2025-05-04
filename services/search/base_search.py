"""
Base implementation for search services.
"""

import random
import asyncio
from abc import abstractmethod
from typing import Dict, List, Any, Optional

from infrastructure.logging import logger
from infrastructure.cache import cache
from infrastructure.config import config
from services.search.search_service import SearchService


class BaseSearch(SearchService):
    """
    Base implementation for search services.
    Provides common functionality for all search implementations.
    """

    # List of User Agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
    ]

    def __init__(self, name: str, cache_ttl: int = 86400):
        """
        Initialize the search service.

        Args:
            name: Search service name
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        self.name = name
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger(f"search.{name}")
        
        # Get configuration
        search_config = config.get_section("SEARCH")
        self.timeout = search_config.get("timeout", 15)
        self.rate_limit = search_config.get("rate_limit", {}).get("requests_per_minute", 10)
        
        self.logger.info(f"Initialized {name} search service")

    def get_random_user_agent(self) -> str:
        """
        Get a random User Agent from the list.

        Returns:
            Random User Agent string
        """
        return random.choice(self.USER_AGENTS)

    @abstractmethod
    async def _search_impl(self, query: str, max_results: int, language: str) -> List[Dict[str, Any]]:
        """
        Implementation-specific search method.
        Must be implemented by subclasses.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with search results
        """
        pass

    async def search(self, query: str, max_results: int = 10, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for a query.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description
        """
        # Check cache first
        cache_key = f"search:{self.name}:{query}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached search results for '{query}'")
            return cached_result

        try:
            # Add language to query for better results
            query_with_lang = query
            if language != "en":
                query_with_lang = f"{query} {language}"

            # Add random delay to avoid request patterns
            await asyncio.sleep(random.uniform(0.2, 0.5))

            # Call implementation-specific search method
            results = await self._search_impl(query_with_lang, max_results, language)

            # Cache the results if successful
            if results:
                cache.setex(cache_key, self.cache_ttl, results)
                self.logger.debug(f"Cached search results for '{query}' ({len(results)} results)")
            else:
                self.logger.warning(f"No search results found for '{query}'")

            return results
        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {str(e)}")
            return []

    async def search_with_retry(self, query: str, max_results: int = 10, language: str = "en", 
                               max_retries: int = 3, backoff_factor: float = 1.5) -> List[Dict[str, Any]]:
        """
        Search with retry and exponential backoff.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for exponential backoff

        Returns:
            List of dictionaries with title, URL, and description
        """
        # Check cache first
        cache_key = f"search:{self.name}:{query}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached search results for '{query}'")
            return cached_result

        # Add language to query for better results
        query_with_lang = query
        if language != "en":
            query_with_lang = f"{query} {language}"

        # Add random delay to avoid request patterns
        await asyncio.sleep(random.uniform(0.5, 2.0))

        # Implement manual retry with exponential backoff
        retries = 0

        while retries < max_retries:
            try:
                # Try to search
                results = await self._search_impl(query_with_lang, max_results, language)

                if results:
                    self.logger.info(f"Search successful for '{query}' ({len(results)} results)")
                    
                    # Cache the results
                    cache.setex(cache_key, self.cache_ttl, results)
                    
                    return results
                else:
                    self.logger.warning(f"No results found for '{query}'")
                    return []

            except Exception as e:
                retries += 1

                if retries < max_retries:
                    # Calculate wait time with exponential backoff and jitter
                    wait_time = (backoff_factor ** retries) * random.uniform(0.5, 1.5)
                    self.logger.warning(f"Attempt {retries}/{max_retries} failed for '{query}'. Waiting {wait_time:.2f}s before next attempt.")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"All {max_retries} search attempts failed for '{query}': {str(e)}")

        # If we get here, all attempts failed
        return []
