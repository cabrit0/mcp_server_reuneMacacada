"""
Factory for creating cache instances.
"""

import logging
from typing import Optional, Dict, Any

from infrastructure.cache.cache_service import CacheService
from infrastructure.cache.memory_cache import MemoryCache

# Configure logging
logger = logging.getLogger("mcp_server.cache.factory")


class CacheFactory:
    """
    Factory for creating cache instances.
    """

    @staticmethod
    def create_cache(cache_type: str = "memory", config: Optional[Dict[str, Any]] = None) -> CacheService:
        """
        Create a cache instance.

        Args:
            cache_type: Type of cache to create ("memory", "redis", etc.)
            config: Configuration options for the cache

        Returns:
            Cache instance implementing CacheService
        """
        if config is None:
            config = {}

        if cache_type == "memory":
            max_size = config.get("max_size", 1000)
            logger.info(f"Creating memory cache with max_size={max_size}")
            return MemoryCache(max_size=max_size)
        elif cache_type == "redis":
            # Redis implementation would go here
            logger.warning("Redis cache not implemented yet, falling back to memory cache")
            return MemoryCache(max_size=config.get("max_size", 1000))
        else:
            logger.warning(f"Unknown cache type: {cache_type}, falling back to memory cache")
            return MemoryCache(max_size=config.get("max_size", 1000))
