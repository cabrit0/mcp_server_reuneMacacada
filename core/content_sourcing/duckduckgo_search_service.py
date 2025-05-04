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
        language: str = "pt"
    ) -> List[Dict[str, Any]]:
        """
        Search for resources using DuckDuckGo.

        Args:
            query: The search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            List of dictionaries with search results (title, url, etc.)
        """
        # Check cache first
        cache_key = f"search:{query}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached search results for '{query}'")
            return cached_result

        # Use the search service to perform the search
        try:
            results = await search.search(query, max_results, language)

            # Cache the results if successful
            if results:
                # Cache for 1 day (86400 seconds)
                cache.setex(cache_key, 86400, results)
                self.logger.debug(f"Cached search results for '{query}' ({len(results)} results)")
            else:
                self.logger.warning(f"No search results found for '{query}'")

            return results
        except Exception as e:
            self.logger.error(f"Error searching for '{query}': {str(e)}")
            return []
