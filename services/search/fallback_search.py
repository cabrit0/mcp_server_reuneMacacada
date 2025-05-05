"""
Fallback search implementation that combines multiple search engines with circuit breaker support.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple

from infrastructure.logging import logger
from infrastructure.cache import cache
from infrastructure.circuit_breaker import CircuitBreakerOpenError, CircuitBreaker
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
        Handles circuit breaker exceptions to gracefully fail over to the next engine.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description
        """
        # Check if any circuit breakers are open
        circuit_breakers = CircuitBreaker.get_all_statuses()
        open_breakers = [name for name, status in circuit_breakers.items() if status["state"] == "OPEN"]

        if open_breakers:
            self.logger.warning(f"Circuit breakers are open for: {', '.join(open_breakers)}")

            # If DuckDuckGo is open, try to use Brave directly
            if "duckduckgo_search" in open_breakers:
                for engine, weight in self.search_engines:
                    if engine.name == "brave":
                        self.logger.info(f"DuckDuckGo circuit breaker is open, trying Brave Search directly for query: '{query}'")
                        try:
                            results = await engine.search(query, max_results, language)
                            if results:
                                self.logger.info(f"Search successful with Brave ({len(results)} results) for query: '{query}'")
                                return results
                            else:
                                self.logger.warning(f"No results from Brave for query: '{query}'")
                        except Exception as e:
                            self.logger.error(f"Error with Brave Search for query: '{query}': {str(e)}")
                        break

        # Try each search engine in order
        for engine, weight in self.search_engines:
            try:
                self.logger.info(f"Trying search engine: {engine.name} for query: '{query}'")
                results = await engine.search(query, max_results, language)

                if results:
                    self.logger.info(f"Search successful with {engine.name} ({len(results)} results) for query: '{query}'")
                    return results
                else:
                    self.logger.warning(f"No results from {engine.name} for query: '{query}', trying next engine")
            except CircuitBreakerOpenError:
                # Circuit breaker is open for this engine, try the next one
                self.logger.warning(f"Circuit breaker open for {engine.name}, skipping to next engine for query: '{query}'")
                continue
            except Exception as e:
                self.logger.error(f"Error with search engine {engine.name} for query: '{query}': {str(e)}")

        # If all engines fail, return empty list
        self.logger.error(f"All search engines failed for query: {query}")
        return []

    async def search(self, query: str, max_results: int = 10, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search using multiple search engines with fallback.
        Now uses parallel search by default for better results.

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

        # Check if any circuit breakers are open
        circuit_breakers = CircuitBreaker.get_all_statuses()
        open_breakers = [name for name, status in circuit_breakers.items() if status["state"] == "OPEN"]

        # Use parallel search by default for better results
        if open_breakers:
            self.logger.warning(f"Circuit breakers are open for: {', '.join(open_breakers)}")
            self.logger.info(f"Using parallel search for query: '{query}' due to open circuit breakers")
            results = await self.search_parallel_impl(query, max_results, language)
        else:
            # Try parallel search first
            self.logger.info(f"Using parallel search for query: '{query}'")
            results = await self.search_parallel_impl(query, max_results, language)

            # If parallel search fails, fall back to sequential search
            if not results:
                self.logger.warning(f"Parallel search failed for query: '{query}', falling back to sequential search")
                results = await self._search_impl(query, max_results, language)

        # Cache the results
        if results:
            cache.setex(cache_key, self.cache_ttl, results)
            self.logger.debug(f"Cached {len(results)} search results for '{query}'")

        return results

    async def search_parallel_impl(self, query: str, max_results: int = 10, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search using multiple search engines in parallel and combine results.
        Handles circuit breaker exceptions gracefully.

        This improved implementation prioritizes getting results quickly by:
        1. Using a more aggressive timeout strategy
        2. Allocating more results to more reliable engines
        3. Handling partial results better

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

        # Create tasks for each search engine with dynamic allocation
        tasks = []
        engines_used = []

        # Calculate reliability-based allocation
        total_weight = sum(weight for _, weight in self.search_engines)

        for engine, weight in self.search_engines:
            # Allocate more results to engines with higher weights
            # Add at least 1 to ensure each engine gets some allocation
            engine_allocation = max(1, int((weight / total_weight) * max_results * 1.5))

            # Add task with appropriate error handling
            tasks.append(self._safe_search(engine, query, engine_allocation, language))
            engines_used.append((engine, engine_allocation))
            self.logger.debug(f"Allocated {engine_allocation} results to {engine.name} (weight: {weight})")

        # Run all searches in parallel with a timeout
        try:
            # Use a timeout to ensure we don't wait too long
            all_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=10  # 10 second timeout for all parallel searches
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout in parallel search for '{query}', using partial results")
            # Get partial results from completed tasks
            all_results = []
            for i, task in enumerate(tasks):
                if task.done() and not task.cancelled():
                    try:
                        all_results.append(task.result())
                    except Exception as e:
                        all_results.append(e)
                else:
                    # Cancel the task and add an exception placeholder
                    task.cancel()
                    all_results.append(Exception("Timeout"))

        # Combine and deduplicate results with improved weighting
        combined_results = []
        seen_urls = set()

        # Process results from each engine with dynamic weighting
        for i, (engine, weight) in enumerate(self.search_engines):
            if i >= len(all_results):
                continue

            result = all_results[i]

            # Skip exceptions (including CircuitBreakerOpenError)
            if isinstance(result, Exception):
                if isinstance(result, CircuitBreakerOpenError):
                    self.logger.warning(f"Circuit breaker open for {engine.name} in parallel search for query: '{query}'")
                else:
                    self.logger.error(f"Error with {engine.name} in parallel search for query: '{query}': {str(result)}")
                continue

            # Skip empty results
            if not result:
                self.logger.warning(f"No results from {engine.name} in parallel search for query: '{query}'")
                continue

            self.logger.info(f"Got {len(result)} results from {engine.name} in parallel search for query: '{query}'")

            # Add results from this engine with position-based weighting
            for j, item in enumerate(result):
                url = item.get("url")
                if url and url not in seen_urls:
                    seen_urls.add(url)

                    # Calculate position-based weight
                    # Items at the top of each engine's results get higher weight
                    position_factor = 1.0 - (j / max(len(result), 1) * 0.5)  # 1.0 to 0.5 based on position

                    # Apply engine weight and position factor
                    item["_weight"] = weight * position_factor

                    # Add relevance boost for exact title matches
                    if query.lower() in item.get("title", "").lower():
                        item["_weight"] += 0.2

                    combined_results.append(item)

        # Sort by weight (if available) and limit to max_results
        combined_results.sort(key=lambda x: x.get("_weight", 0), reverse=True)
        combined_results = combined_results[:max_results]

        # Remove temporary weight field
        for result in combined_results:
            if "_weight" in result:
                del result["_weight"]

        # If we got no results, log a warning
        if not combined_results:
            self.logger.warning(f"No combined results from any engine for query: '{query}'")
        else:
            self.logger.info(f"Combined {len(combined_results)} unique results from multiple engines for query: '{query}'")

        # Cache the results
        if combined_results:
            cache.setex(cache_key, self.cache_ttl, combined_results)
            self.logger.info(f"Cached {len(combined_results)} combined results for '{query}'")

        return combined_results

    async def _safe_search(self, engine: SearchService, query: str, max_results: int, language: str) -> List[Dict[str, Any]]:
        """
        Safely execute a search with proper error handling.

        Args:
            engine: Search engine to use
            query: Search query
            max_results: Maximum number of results
            language: Language code

        Returns:
            Search results or raises exception
        """
        try:
            return await engine.search(query, max_results, language)
        except CircuitBreakerOpenError:
            # Re-raise circuit breaker errors to be handled by the caller
            raise
        except Exception as e:
            # Log and re-raise other exceptions
            self.logger.error(f"Error in safe search with {engine.name}: {str(e)}")
            raise
