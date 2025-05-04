"""
Router for cache-related endpoints.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Query

from infrastructure.logging import logger
from infrastructure.cache import cache
from api.routers.base_router import BaseRouter


class CacheRouter(BaseRouter):
    """
    Router for cache-related endpoints.
    Handles cache statistics and clearing.
    """

    def __init__(self):
        """Initialize the cache router."""
        self.router = APIRouter(tags=["Cache"])
        self.logger = logger.get_logger("api.routers.cache")
        self._setup_routes()
        self.logger.info("Initialized CacheRouter")

    def get_router(self) -> APIRouter:
        """
        Get the FastAPI router.

        Returns:
            FastAPI router
        """
        return self.router

    def _setup_routes(self):
        """Set up the router routes."""
        self.router.add_api_route(
            "/cache_stats",
            self.get_cache_stats,
            methods=["GET"],
            summary="Get cache statistics",
            description="Get statistics about the cache."
        )
        
        self.router.add_api_route(
            "/clear_cache",
            self.clear_cache,
            methods=["POST"],
            summary="Clear cache",
            description="Clear the cache based on a pattern."
        )

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        This endpoint returns statistics about the cache, including the number of items in the cache
        and information about the domain method cache that stores which scraping method works best for each domain.

        Returns:
            Dictionary with cache statistics.
        """
        try:
            # Get statistics from the main cache
            cache_info = cache.info()
            cache_keys = cache.keys("*")

            # Get statistics from the domain method cache
            from services.scraping import scraper
            domain_cache_stats = scraper.get_domain_method_cache_stats()

            self.logger.debug(f"Retrieved cache statistics: {len(cache_keys)} keys")
            return {
                "status": "success",
                "cache": {
                    "total_keys": len(cache_keys),
                    "info": cache_info
                },
                "domain_method_cache": domain_cache_stats
            }
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {str(e)}")
            return {
                "status": "error",
                "message": f"Error getting cache stats: {str(e)}"
            }

    async def clear_cache(
        self,
        pattern: Optional[str] = Query("*", description="Pattern to match cache keys (e.g., 'mcp:*' for all MCPs, 'search:*' for all search results, '*' for all)"),
        clear_domain_cache: bool = Query(False, description="Whether to also clear the domain method cache")
    ) -> Dict[str, Any]:
        """
        Clear the cache.

        This endpoint allows clearing the cache based on a pattern. Use with caution as it will remove cached data.

        Args:
            pattern: Pattern to match cache keys. Default is "*" which clears all cache.
                    Examples: "mcp:*" for all MCPs, "search:*" for all search results.
            clear_domain_cache: Whether to also clear the domain method cache that stores which scraping method works best for each domain.

        Returns:
            Dictionary with count of items cleared and message.
        """
        try:
            # Clear the main cache
            count = cache.clear(pattern)
            self.logger.info(f"Cleared {count} items from cache matching pattern: {pattern}")

            # Clear the domain method cache if requested
            domain_cache_cleared = 0
            if clear_domain_cache:
                from services.scraping import scraper
                domain_cache_cleared = scraper.clear_domain_method_cache()
                self.logger.info(f"Cleared domain method cache")

            return {
                "status": "success",
                "message": f"Cleared {count} items from cache" + (", including domain method cache" if clear_domain_cache else ""),
                "pattern": pattern,
                "count": count,
                "domain_cache_cleared": domain_cache_cleared
            }
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return {
                "status": "error",
                "message": f"Error clearing cache: {str(e)}"
            }
