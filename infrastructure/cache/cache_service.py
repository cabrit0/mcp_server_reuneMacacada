"""
Abstract interface for the cache system.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List


class CacheService(ABC):
    """
    Abstract interface for cache services.
    Defines the methods that all cache implementations must provide.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.

        Args:
            key: Cache key

        Returns:
            Stored value or None if not found or expired
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def delete(self, key: str) -> int:
        """
        Delete a value from the cache.

        Args:
            key: Cache key

        Returns:
            1 if deleted, 0 if not found
        """
        pass

    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching a pattern.

        Args:
            pattern: Key pattern (supports only prefix*)

        Returns:
            List of matching keys
        """
        pass

    @abstractmethod
    def clear(self, pattern: str = "*") -> int:
        """
        Clear cache entries matching a pattern.

        Args:
            pattern: Key pattern. Default is "*" which clears the entire cache.
                    Examples: "mcp:*" for all MCPs, "search:*" for all search results.

        Returns:
            Number of items removed
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """
        Get the current cache size.

        Returns:
            Number of items in the cache
        """
        pass

    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        Remove expired items from the cache.

        Returns:
            Number of items removed
        """
        pass

    @abstractmethod
    def info(self) -> dict:
        """
        Get information about the cache.

        Returns:
            Dictionary with cache information
        """
        pass
