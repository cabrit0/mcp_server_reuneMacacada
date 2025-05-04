"""
Memory-based cache implementation for the MCP Server.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from cachetools import LRUCache
import msgpack

from infrastructure.cache.cache_service import CacheService
from infrastructure.cache.cache_metrics import CacheMetrics

# Configure logging
logger = logging.getLogger("mcp_server.cache.memory")

class MemoryCache(CacheService):
    """
    Memory-based cache implementation for the MCP Server.
    Implements the CacheService interface with LRU eviction policy and TTL support.
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize the cache.

        Args:
            max_size: Maximum cache size
        """
        self.cache: Dict[str, Any] = {}
        self.expiry: Dict[str, float] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.metrics = CacheMetrics()
        logger.info(f"Initializing MemoryCache with maximum size of {max_size} items")

    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Stored value or None if not found or expired
        """
        self.metrics.increment_get_count()

        # Check if key exists
        if key not in self.cache:
            self.metrics.increment_miss_count()
            return None

        # Check if value has expired
        if key in self.expiry and self.expiry[key] < time.time():
            # Remove expired value
            self._remove_key(key)
            self.metrics.increment_miss_count()
            return None

        # Update access time
        self.access_times[key] = time.time()
        self.metrics.increment_hit_count()

        # Return the value (deserialize if needed)
        value = self.cache[key]
        if isinstance(value, bytes):
            try:
                return msgpack.unpackb(value, raw=False)
            except Exception as e:
                logger.error(f"Error deserializing value for key {key}: {str(e)}")
                return value
        return value

    def setex(self, key: str, ttl: int, value: Any) -> bool:
        """
        Set a value in the cache with TTL.

        Args:
            key: Cache key
            ttl: Time to live in seconds
            value: Value to store

        Returns:
            True if successful
        """
        self.metrics.increment_set_count()

        # Check if cache is full
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove least recently accessed item
            self._evict_lru_item()

        # Try to serialize complex objects for more efficient storage
        try:
            if isinstance(value, (dict, list, tuple)) and not isinstance(value, bytes):
                value = msgpack.packb(value, use_bin_type=True)
        except Exception as e:
            logger.warning(f"Could not serialize value for key {key}: {str(e)}")

        # Store the value
        self.cache[key] = value
        self.expiry[key] = time.time() + ttl
        self.access_times[key] = time.time()
        self.metrics.increment_size(1)

        return True

    def delete(self, key: str) -> int:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            1 if deleted, 0 if not found
        """
        if key in self.cache:
            self._remove_key(key)
            self.metrics.increment_size(-1)
            return 1
        return 0

    def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching a pattern.

        Args:
            pattern: Key pattern (supports only prefix*)

        Returns:
            List of matching keys
        """
        if pattern == "*":
            return list(self.cache.keys())

        prefix = pattern.rstrip("*")
        return [k for k in self.cache.keys() if k.startswith(prefix)]

    def clear(self, pattern: str = "*") -> int:
        """
        Clear cache entries matching a pattern.

        Args:
            pattern: Key pattern. Default is "*" which clears the entire cache.
                    Examples: "mcp:*" for all MCPs, "search:*" for all search results.

        Returns:
            Number of items removed
        """
        if pattern == "*":
            # Clear the entire cache
            count = len(self.cache)
            self.cache.clear()
            self.expiry.clear()
            self.access_times.clear()
            self.metrics.reset_size()
            return count
        else:
            # Remove only keys matching the pattern
            prefix = pattern.rstrip("*")
            keys_to_delete = [k for k in list(self.cache.keys()) if k.startswith(prefix)]
            count = len(keys_to_delete)

            for key in keys_to_delete:
                self._remove_key(key)

            self.metrics.increment_size(-count)
            return count

    def size(self) -> int:
        """
        Get the current cache size.

        Returns:
            Number of items in the cache
        """
        return len(self.cache)

    def cleanup_expired(self) -> int:
        """
        Remove expired items from the cache.

        Returns:
            Number of items removed
        """
        now = time.time()
        expired_keys = [k for k, exp in self.expiry.items() if exp < now]

        for key in expired_keys:
            self._remove_key(key)

        self.metrics.increment_size(-len(expired_keys))
        return len(expired_keys)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache metrics.

        Returns:
            Dictionary with cache metrics
        """
        return self.metrics.get_metrics()

    def info(self) -> Dict[str, Any]:
        """
        Get information about the cache.

        Returns:
            Dictionary with cache information
        """
        # Calculate statistics
        total_keys = len(self.cache)
        expired_keys = sum(1 for exp in self.expiry.values() if exp < time.time())
        active_keys = total_keys - expired_keys

        # Get metrics
        metrics = self.get_metrics()

        return {
            "size": total_keys,
            "active_keys": active_keys,
            "expired_keys": expired_keys,
            "max_size": self.max_size,
            "usage_percentage": (total_keys / self.max_size) * 100 if self.max_size > 0 else 0,
            "metrics": metrics
        }

    def _remove_key(self, key: str) -> None:
        """
        Remove a key from all internal dictionaries.

        Args:
            key: Key to remove
        """
        self.cache.pop(key, None)
        self.expiry.pop(key, None)
        self.access_times.pop(key, None)

    def _evict_lru_item(self) -> None:
        """
        Evict the least recently used item from the cache.
        """
        if not self.access_times:
            return

        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        self._remove_key(lru_key)
        self.metrics.increment_eviction_count()
        logger.debug(f"Evicted LRU item with key: {lru_key}")
