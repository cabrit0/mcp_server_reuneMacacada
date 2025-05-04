"""
Fallback search implementation that combines multiple search engines.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple

from infrastructure.logging import logger
from infrastructure.cache import cache
from services.search.base_search import BaseSearch
from services.search.search_service import SearchService


class FallbackSearch(BaseSearch):
    """
    Fallback search implementation that combines multiple search engines.
    Tries each search engine in order until one succeeds.
    """

    def __init__(self, search_engines: List[Tuple[SearchService, float]], cache_ttl: int = 86400):
        """
        Initialize the fallback search service.

        Args:
            search_engines: List of (search_engine, weight) tuples
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        super().__init__(name="fallback", cache_ttl=cache_ttl)
        self.search_engines = search_engines
        
        engine_names = [engine[0].name for engine in search_engines]
        self.logger.info(f"Initialized fallback search with engines: {', '.join(engine_names)}")

    async def _search_impl(self, query: str, max_results: int, language: str) -> List[Dict[str, Any]]:
        """
        Search using multiple search engines with fallback.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description
        """
        # Try each search engine in order
        for engine, weight in self.search_engines:
            try:
                self.logger.debug(f"Trying search engine: {engine.name}")
                results = await engine.search(query, max_results, language)
                
                if results:
                    self.logger.info(f"Search successful with {engine.name} ({len(results)} results)")
                    return results
                else:
                    self.logger.warning(f"No results from {engine.name}, trying next engine")
            except Exception as e:
                self.logger.error(f"Error with search engine {engine.name}: {str(e)}")
                
        # If all engines fail, return empty list
        self.logger.error(f"All search engines failed for query: {query}")
        return []

    async def search_parallel(self, query: str, max_results: int = 10, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search using multiple search engines in parallel and combine results.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description
        """
        # Check cache first
        cache_key = f"search:parallel:{query}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached parallel search results for '{query}'")
            return cached_result

        # Create tasks for each search engine
        tasks = []
        for engine, _ in self.search_engines:
            tasks.append(engine.search(query, max_results // len(self.search_engines) + 1, language))
            
        # Run all searches in parallel
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        combined_results = []
        seen_urls = set()
        
        # Process results from each engine, weighted by engine priority
        for i, (engine, weight) in enumerate(self.search_engines):
            if i < len(all_results) and not isinstance(all_results[i], Exception) and all_results[i]:
                # Add results from this engine, weighted by priority
                engine_results = all_results[i]
                for result in engine_results:
                    url = result.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        combined_results.append(result)
        
        # Limit to max_results
        combined_results = combined_results[:max_results]
        
        # Cache the results
        if combined_results:
            cache.setex(cache_key, self.cache_ttl, combined_results)
            
        return combined_results
