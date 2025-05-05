"""
Factory for creating cache instances.
"""

import logging
import os
from typing import Optional, Dict, Any

from infrastructure.cache.cache_service import CacheService
from infrastructure.cache.memory_cache import MemoryCache
from infrastructure.cache.multi_level_cache import MultiLevelCache

# Configure logging
logger = logging.getLogger("mcp_server.cache.factory")


class CacheFactory:
    """
    Factory for creating cache instances.
    """

    @staticmethod
    def create_cache(cache_type: str = "multi_level", config: Optional[Dict[str, Any]] = None) -> CacheService:
        """
        Create a cache instance.

        Args:
            cache_type: Type of cache to create ("memory", "multi_level", "redis", etc.)
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
        elif cache_type == "multi_level":
            memory_max_size = config.get("memory_max_size", 1000)
            disk_max_size = config.get("disk_max_size", 10000)
            disk_path = config.get("disk_path", os.path.join(os.getcwd(), "cache"))
            sync_interval = config.get("sync_interval", 300)

            logger.info(
                f"Creating multi-level cache with memory_max_size={memory_max_size}, "
                f"disk_max_size={disk_max_size}, disk_path={disk_path}"
            )

            return MultiLevelCache(
                memory_max_size=memory_max_size,
                disk_max_size=disk_max_size,
                disk_path=disk_path,
                sync_interval=sync_interval
            )
        elif cache_type == "redis":
            # Redis implementation would go here
            logger.warning("Redis cache not implemented yet, falling back to multi-level cache")
            return CacheFactory.create_cache("multi_level", config)
        else:
            logger.warning(f"Unknown cache type: {cache_type}, falling back to multi-level cache")
            return CacheFactory.create_cache("multi_level", config)
