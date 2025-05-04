"""
Metrics collection for cache implementations.
"""

import time
from typing import Dict, Any


class CacheMetrics:
    """
    Collects and provides metrics for cache implementations.
    """

    def __init__(self):
        """Initialize metrics."""
        self.hit_count = 0
        self.miss_count = 0
        self.get_count = 0
        self.set_count = 0
        self.eviction_count = 0
        self.current_size = 0
        self.start_time = time.time()

    def increment_hit_count(self) -> None:
        """Increment hit count."""
        self.hit_count += 1

    def increment_miss_count(self) -> None:
        """Increment miss count."""
        self.miss_count += 1

    def increment_get_count(self) -> None:
        """Increment get count."""
        self.get_count += 1

    def increment_set_count(self) -> None:
        """Increment set count."""
        self.set_count += 1

    def increment_eviction_count(self) -> None:
        """Increment eviction count."""
        self.eviction_count += 1

    def increment_size(self, delta: int) -> None:
        """
        Increment or decrement the current size.

        Args:
            delta: Amount to change the size by (positive or negative)
        """
        self.current_size += delta
        if self.current_size < 0:
            self.current_size = 0

    def reset_size(self) -> None:
        """Reset the current size to 0."""
        self.current_size = 0

    def get_hit_rate(self) -> float:
        """
        Calculate the cache hit rate.

        Returns:
            Hit rate as a percentage (0-100)
        """
        if self.get_count == 0:
            return 0.0
        return (self.hit_count / self.get_count) * 100.0

    def get_uptime(self) -> float:
        """
        Get cache uptime in seconds.

        Returns:
            Uptime in seconds
        """
        return time.time() - self.start_time

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics as a dictionary.

        Returns:
            Dictionary with all metrics
        """
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "get_count": self.get_count,
            "set_count": self.set_count,
            "eviction_count": self.eviction_count,
            "current_size": self.current_size,
            "hit_rate": self.get_hit_rate(),
            "uptime": self.get_uptime()
        }
