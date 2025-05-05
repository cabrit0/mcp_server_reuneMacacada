"""
DuckDuckGo implementation of the search service.
"""

import asyncio
from typing import List, Dict, Any

from infrastructure.logging import logger
from infrastructure.cache import cache
from core.content_sourcing.search_service import SearchService
from services.search import search


class DuckDuckGoSearchService(SearchService):
    """
    DuckDuckGo implementation of the search service.
    Uses the search_service from services.search to perform searches.
    """

    def __init__(self):
        """Initialize the DuckDuckGo search service."""
        self.logger = logger.get_logger("content_sourcing.search.duckduckgo")
        self.logger.info("Initialized DuckDuckGoSearchService")

    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "pt",
        skip_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for resources using DuckDuckGo with improved caching and fallback.

        Args:
            query: The search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'pt', 'en', 'es')
            skip_cache: Whether to skip the cache and force a new search

        Returns:
            List of dictionaries with search results (title, url, etc.)
        """
        # Check cache first (unless skip_cache is True)
        cache_key = f"search:{query}_{max_results}_{language}"

        if not skip_cache:
            cached_result = cache.get(cache_key)
            if cached_result:
                # If we have a small number of results, consider refreshing the cache
                if isinstance(cached_result, list) and len(cached_result) < 3:
                    self.logger.info(f"Found only {len(cached_result)} cached results for '{query}', will refresh in background")
                    # Schedule a background refresh but still return cached results
                    asyncio.create_task(self._refresh_cache(query, max_results, language, cache_key))
                else:
                    self.logger.debug(f"Using cached search results for '{query}' ({len(cached_result)} results)")
                return cached_result

        # Use the search service to perform the search
        try:
            # Try with increased max_results to improve chances of getting enough results
            adjusted_max_results = max(max_results * 2, 10)
            self.logger.info(f"Searching for '{query}' with {adjusted_max_results} max results (requested: {max_results})")

            results = await search.search(query, adjusted_max_results, language)

            # Cache the results if successful
            if results:
                # Adjust cache TTL based on result count
                if len(results) < 3:
                    # Very few results - cache for shorter time (1 hour)
                    cache_ttl = 3600
                    self.logger.info(f"Caching {len(results)} results for '{query}' with shorter TTL (1 hour)")
                elif len(results) < max_results:
                    # Fewer results than requested - cache for 12 hours
                    cache_ttl = 43200
                    self.logger.info(f"Caching {len(results)} results for '{query}' with medium TTL (12 hours)")
                else:
                    # Good number of results - cache for 1 day
                    cache_ttl = 86400
                    self.logger.info(f"Caching {len(results)} results for '{query}' with normal TTL (1 day)")

                cache.setex(cache_key, cache_ttl, results)
            else:
                self.logger.warning(f"No search results found for '{query}'")

            return results[:max_results]  # Return only the requested number of results
        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {str(e)}")
            return []

    async def _refresh_cache(self, query: str, max_results: int, language: str, cache_key: str) -> None:
        """
        Refresh the cache for a query in the background.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code
            cache_key: Cache key to update
        """
        try:
            self.logger.debug(f"Background refreshing cache for '{query}'")
            # Perform a new search with increased max_results, skipping the cache
            adjusted_max_results = max(max_results * 2, 10)
            results = await search.search(query, adjusted_max_results, language)

            if results:
                self.logger.info(f"Updated cache for '{query}' with {len(results)} new results")
                # Cache with appropriate TTL based on result count
                if len(results) < 3:
                    cache_ttl = 3600  # 1 hour
                elif len(results) < max_results:
                    cache_ttl = 43200  # 12 hours
                else:
                    cache_ttl = 86400  # 1 day

                cache.setex(cache_key, cache_ttl, results)
            else:
                self.logger.warning(f"Background refresh for '{query}' found no results")
        except Exception as e:
            self.logger.error(f"Error in background cache refresh for '{query}': {str(e)}")
