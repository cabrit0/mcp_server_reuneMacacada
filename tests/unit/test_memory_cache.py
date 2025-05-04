"""
Unit tests for the MemoryCache implementation.
"""

import time
import pytest
from infrastructure.cache.memory_cache import MemoryCache


class TestMemoryCache:
    """Tests for the MemoryCache implementation."""

    def test_get_set(self):
        """Test basic get and set operations."""
        cache = MemoryCache(max_size=10)
        
        # Set a value
        cache.setex("test_key", 60, "test_value")
        
        # Get the value
        value = cache.get("test_key")
        
        assert value == "test_value"
        
    def test_ttl_expiration(self):
        """Test that values expire after TTL."""
        cache = MemoryCache(max_size=10)
        
        # Set a value with a short TTL
        cache.setex("test_key", 1, "test_value")
        
        # Value should be available immediately
        assert cache.get("test_key") == "test_value"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Value should be expired
        assert cache.get("test_key") is None
        
    def test_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = MemoryCache(max_size=2)
        
        # Set two values
        cache.setex("key1", 60, "value1")
        cache.setex("key2", 60, "value2")
        
        # Both values should be available
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        
        # Access key1 to make it more recently used
        cache.get("key1")
        
        # Set a third value, which should evict key2 (least recently used)
        cache.setex("key3", 60, "value3")
        
        # key1 and key3 should be available, key2 should be evicted
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
        
    def test_delete(self):
        """Test delete operation."""
        cache = MemoryCache(max_size=10)
        
        # Set a value
        cache.setex("test_key", 60, "test_value")
        
        # Delete the value
        result = cache.delete("test_key")
        
        # delete should return 1 for success
        assert result == 1
        
        # Value should be gone
        assert cache.get("test_key") is None
        
        # Deleting a non-existent key should return 0
        assert cache.delete("non_existent_key") == 0
        
    def test_clear(self):
        """Test clear operation."""
        cache = MemoryCache(max_size=10)
        
        # Set multiple values
        cache.setex("key1", 60, "value1")
        cache.setex("key2", 60, "value2")
        cache.setex("prefix:key3", 60, "value3")
        cache.setex("prefix:key4", 60, "value4")
        
        # Clear values with a specific prefix
        count = cache.clear("prefix:*")
        
        # Should have cleared 2 values
        assert count == 2
        
        # prefix:* keys should be gone, others should remain
        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("prefix:key3") is None
        assert cache.get("prefix:key4") is None
        
        # Clear all values
        count = cache.clear()
        
        # Should have cleared 2 values
        assert count == 2
        
        # All keys should be gone
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        
    def test_keys(self):
        """Test keys operation."""
        cache = MemoryCache(max_size=10)
        
        # Set multiple values
        cache.setex("key1", 60, "value1")
        cache.setex("key2", 60, "value2")
        cache.setex("prefix:key3", 60, "value3")
        cache.setex("prefix:key4", 60, "value4")
        
        # Get all keys
        all_keys = cache.keys()
        
        # Should have 4 keys
        assert len(all_keys) == 4
        assert set(all_keys) == {"key1", "key2", "prefix:key3", "prefix:key4"}
        
        # Get keys with a specific prefix
        prefix_keys = cache.keys("prefix:*")
        
        # Should have 2 keys
        assert len(prefix_keys) == 2
        assert set(prefix_keys) == {"prefix:key3", "prefix:key4"}
        
    def test_size(self):
        """Test size operation."""
        cache = MemoryCache(max_size=10)
        
        # Initially empty
        assert cache.size() == 0
        
        # Set multiple values
        cache.setex("key1", 60, "value1")
        cache.setex("key2", 60, "value2")
        
        # Size should be 2
        assert cache.size() == 2
        
        # Delete a value
        cache.delete("key1")
        
        # Size should be 1
        assert cache.size() == 1
        
        # Clear all values
        cache.clear()
        
        # Size should be 0
        assert cache.size() == 0
        
    def test_cleanup_expired(self):
        """Test cleanup_expired operation."""
        cache = MemoryCache(max_size=10)
        
        # Set values with different TTLs
        cache.setex("key1", 1, "value1")  # Short TTL
        cache.setex("key2", 60, "value2")  # Long TTL
        
        # Wait for key1 to expire
        time.sleep(1.1)
        
        # Cleanup expired values
        count = cache.cleanup_expired()
        
        # Should have cleaned up 1 value
        assert count == 1
        
        # key1 should be gone, key2 should remain
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        
    def test_complex_values(self):
        """Test storing and retrieving complex values."""
        cache = MemoryCache(max_size=10)
        
        # Set a complex value (dictionary)
        complex_value = {
            "name": "test",
            "values": [1, 2, 3],
            "nested": {
                "key": "value"
            }
        }
        
        cache.setex("complex_key", 60, complex_value)
        
        # Get the value
        retrieved_value = cache.get("complex_key")
        
        # Should be equal to the original value
        assert retrieved_value == complex_value
        
    def test_metrics(self):
        """Test cache metrics."""
        cache = MemoryCache(max_size=2)
        
        # Set values
        cache.setex("key1", 60, "value1")
        cache.setex("key2", 60, "value2")
        
        # Get existing value (hit)
        cache.get("key1")
        
        # Get non-existent value (miss)
        cache.get("non_existent_key")
        
        # Set a value that causes eviction
        cache.setex("key3", 60, "value3")
        
        # Get metrics
        metrics = cache.get_metrics()
        
        # Check metrics
        assert metrics["hit_count"] == 1
        assert metrics["miss_count"] == 1
        assert metrics["get_count"] == 2
        assert metrics["set_count"] == 3
        assert metrics["eviction_count"] == 1
        assert metrics["current_size"] == 2
        assert metrics["hit_rate"] == 50.0  # 1 hit out of 2 gets
