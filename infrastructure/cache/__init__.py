# This file is part of the MCP Server package.

from infrastructure.cache.cache_factory import CacheFactory
from infrastructure.cache.cache_service import CacheService

# Create a global cache instance
cache: CacheService = CacheFactory.create_cache("memory", {"max_size": 1000})

__all__ = ["cache", "CacheService", "CacheFactory"]
