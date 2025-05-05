"""
Multi-level cache implementation for the MCP Server.

This module provides a multi-level cache implementation that combines
in-memory caching with disk-based persistence for improved performance
and reliability.
"""

import os
import time
import json
import logging
import threading
import pickle
from typing import Dict, Any, Optional, List, Tuple
import msgpack
from pathlib import Path

from infrastructure.cache.cache_service import CacheService
from infrastructure.cache.memory_cache import MemoryCache
from infrastructure.cache.cache_metrics import CacheMetrics

# Configure logging
logger = logging.getLogger("mcp_server.cache.multi_level")


class MultiLevelCache(CacheService):
    """
    Multi-level cache implementation for the MCP Server.
    
    Combines in-memory caching (L1) with disk-based persistence (L2)
    for improved performance and reliability.
    """

    def __init__(
        self,
        memory_max_size: int = 1000,
        disk_max_size: int = 10000,
        disk_path: str = "./cache",
        sync_interval: int = 300,  # 5 minutes
    ):
        """
        Initialize the multi-level cache.

        Args:
            memory_max_size: Maximum size of the memory cache (L1)
            disk_max_size: Maximum size of the disk cache (L2)
            disk_path: Path to the disk cache directory
            sync_interval: Interval in seconds for syncing memory to disk
        """
        # Create L1 cache (memory)
        self.memory_cache = MemoryCache(max_size=memory_max_size)
        
        # L2 cache settings (disk)
        self.disk_path = disk_path
        self.disk_max_size = disk_max_size
        self.disk_index: Dict[str, Tuple[float, str]] = {}  # key -> (expiry, filename)
        self.disk_access_times: Dict[str, float] = {}  # key -> last access time
        
        # Metrics
        self.metrics = CacheMetrics()
        self.l1_hit_count = 0
        self.l2_hit_count = 0
        self.promotion_count = 0
        
        # Ensure disk cache directory exists
        os.makedirs(disk_path, exist_ok=True)
        
        # Load disk index
        self._load_disk_index()
        
        # Start background sync thread
        self.sync_interval = sync_interval
        self.sync_thread = threading.Thread(target=self._background_sync, daemon=True)
        self.sync_thread.start()
        
        logger.info(
            f"Initialized MultiLevelCache with L1 size={memory_max_size}, "
            f"L2 size={disk_max_size}, disk_path={disk_path}"
        )

    def get(self, key: str, resource_type: Optional[str] = None) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Tries L1 first, then L2 if not found in L1.
        Promotes items from L2 to L1 when accessed.

        Args:
            key: Cache key
            resource_type: Optional type hint for deserialization ('resource' or 'resource_list')

        Returns:
            Stored value or None if not found or expired
        """
        self.metrics.increment_get_count()
        
        # Try L1 cache first (memory)
        value = self.memory_cache.get(key, resource_type)
        if value is not None:
            # L1 hit
            self.l1_hit_count += 1
            return value
            
        # Try L2 cache (disk)
        if key in self.disk_index:
            expiry, filename = self.disk_index[key]
            
            # Check if expired
            if expiry < time.time():
                # Remove expired value
                self._remove_from_disk(key)
                self.metrics.increment_miss_count()
                return None
                
            # Load from disk
            try:
                value = self._load_from_disk(filename, resource_type)
                if value is not None:
                    # L2 hit
                    self.l2_hit_count += 1
                    self.metrics.increment_hit_count()
                    
                    # Update access time
                    self.disk_access_times[key] = time.time()
                    
                    # Promote to L1
                    ttl = max(1, int(expiry - time.time()))  # Remaining TTL
                    self.memory_cache.setex(key, ttl, value)
                    self.promotion_count += 1
                    
                    return value
            except Exception as e:
                logger.error(f"Error loading from disk cache for key {key}: {str(e)}")
                # Remove corrupted entry
                self._remove_from_disk(key)
        
        # Not found in any cache level
        self.metrics.increment_miss_count()
        return None

    def setex(self, key: str, ttl: int, value: Any) -> bool:
        """
        Set a value in the cache with TTL.
        
        Stores in both L1 and L2 caches.

        Args:
            key: Cache key
            ttl: Time to live in seconds
            value: Value to store

        Returns:
            True if successful
        """
        self.metrics.increment_set_count()
        
        # Store in L1 (memory)
        self.memory_cache.setex(key, ttl, value)
        
        # Store in L2 (disk)
        expiry = time.time() + ttl
        
        # Check if L2 is full
        if len(self.disk_index) >= self.disk_max_size and key not in self.disk_index:
            # Remove least recently accessed item
            self._evict_lru_disk_item()
            
        # Generate filename
        filename = f"{key.replace(':', '_')}_{int(time.time())}.cache"
        filepath = os.path.join(self.disk_path, filename)
        
        # Store value to disk
        try:
            self._save_to_disk(filepath, value)
            
            # Update index
            self.disk_index[key] = (expiry, filename)
            self.disk_access_times[key] = time.time()
            self.metrics.increment_size(1)
            
            return True
        except Exception as e:
            logger.error(f"Error saving to disk cache for key {key}: {str(e)}")
            return False

    def delete(self, key: str) -> int:
        """
        Delete a value from the cache.
        
        Removes from both L1 and L2 caches.

        Args:
            key: Cache key

        Returns:
            1 if deleted, 0 if not found
        """
        result = 0
        
        # Delete from L1
        if self.memory_cache.delete(key) == 1:
            result = 1
            
        # Delete from L2
        if key in self.disk_index:
            self._remove_from_disk(key)
            result = 1
            
        if result == 1:
            self.metrics.increment_size(-1)
            
        return result

    def keys(self, pattern: str = "*") -> List[str]:
        """
        Get keys matching a pattern.
        
        Combines keys from both L1 and L2 caches.

        Args:
            pattern: Key pattern (supports only prefix*)

        Returns:
            List of matching keys
        """
        # Get keys from L1
        l1_keys = set(self.memory_cache.keys(pattern))
        
        # Get keys from L2
        if pattern == "*":
            l2_keys = set(self.disk_index.keys())
        else:
            prefix = pattern.rstrip("*")
            l2_keys = {k for k in self.disk_index.keys() if k.startswith(prefix)}
            
        # Combine and return unique keys
        return list(l1_keys.union(l2_keys))

    def clear(self, pattern: str = "*") -> int:
        """
        Clear cache entries matching a pattern.
        
        Clears from both L1 and L2 caches.

        Args:
            pattern: Key pattern. Default is "*" which clears the entire cache.
                    Examples: "mcp:*" for all MCPs, "search:*" for all search results.

        Returns:
            Number of items removed
        """
        # Clear from L1
        l1_count = self.memory_cache.clear(pattern)
        
        # Clear from L2
        l2_count = 0
        if pattern == "*":
            # Clear all disk cache
            for key in list(self.disk_index.keys()):
                self._remove_from_disk(key)
            l2_count = len(self.disk_index)
            self.disk_index.clear()
            self.disk_access_times.clear()
        else:
            # Clear only matching keys
            prefix = pattern.rstrip("*")
            keys_to_delete = [k for k in list(self.disk_index.keys()) if k.startswith(prefix)]
            for key in keys_to_delete:
                self._remove_from_disk(key)
            l2_count = len(keys_to_delete)
            
        # Calculate total unique keys removed
        if pattern == "*":
            total_count = max(l1_count, l2_count)  # All keys were cleared
        else:
            # We need to account for keys that might be in both levels
            total_count = l1_count + l2_count  # This is an approximation
            
        self.metrics.reset_size()
        return total_count

    def size(self) -> int:
        """
        Get the current cache size.
        
        Returns the total number of unique keys across both cache levels.

        Returns:
            Number of items in the cache
        """
        # Get all unique keys
        l1_keys = set(self.memory_cache.keys())
        l2_keys = set(self.disk_index.keys())
        all_keys = l1_keys.union(l2_keys)
        
        return len(all_keys)

    def cleanup_expired(self) -> int:
        """
        Remove expired items from the cache.
        
        Cleans up both L1 and L2 caches.

        Returns:
            Number of items removed
        """
        # Cleanup L1
        l1_count = self.memory_cache.cleanup_expired()
        
        # Cleanup L2
        now = time.time()
        expired_keys = [k for k, (exp, _) in self.disk_index.items() if exp < now]
        
        for key in expired_keys:
            self._remove_from_disk(key)
            
        l2_count = len(expired_keys)
        
        # Calculate total unique keys removed
        # This is an approximation as some keys might be in both levels
        total_count = l1_count + l2_count
        
        self.metrics.increment_size(-total_count)
        return total_count

    def info(self) -> Dict[str, Any]:
        """
        Get information about the cache.
        
        Includes information about both L1 and L2 caches.

        Returns:
            Dictionary with cache information
        """
        # Get L1 info
        l1_info = self.memory_cache.info()
        
        # Calculate L2 statistics
        l2_total_keys = len(self.disk_index)
        l2_expired_keys = sum(1 for exp, _ in self.disk_index.values() if exp < time.time())
        l2_active_keys = l2_total_keys - l2_expired_keys
        
        # Get metrics
        metrics = self.get_metrics()
        
        # Calculate total unique keys
        l1_keys = set(self.memory_cache.keys())
        l2_keys = set(self.disk_index.keys())
        all_keys = l1_keys.union(l2_keys)
        total_keys = len(all_keys)
        
        return {
            "size": total_keys,
            "l1_cache": {
                "size": l1_info["size"],
                "active_keys": l1_info["active_keys"],
                "expired_keys": l1_info["expired_keys"],
                "max_size": l1_info["max_size"],
                "usage_percentage": l1_info["usage_percentage"]
            },
            "l2_cache": {
                "size": l2_total_keys,
                "active_keys": l2_active_keys,
                "expired_keys": l2_expired_keys,
                "max_size": self.disk_max_size,
                "usage_percentage": (l2_total_keys / self.disk_max_size) * 100 if self.disk_max_size > 0 else 0,
                "disk_path": self.disk_path
            },
            "metrics": metrics,
            "l1_hit_count": self.l1_hit_count,
            "l2_hit_count": self.l2_hit_count,
            "promotion_count": self.promotion_count
        }
        
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache metrics.

        Returns:
            Dictionary with cache metrics
        """
        metrics = self.metrics.get_metrics()
        
        # Add multi-level specific metrics
        metrics.update({
            "l1_hit_count": self.l1_hit_count,
            "l2_hit_count": self.l2_hit_count,
            "promotion_count": self.promotion_count,
            "l1_hit_ratio": self.l1_hit_count / max(1, metrics["hit_count"]) if "hit_count" in metrics else 0,
            "l2_hit_ratio": self.l2_hit_count / max(1, metrics["hit_count"]) if "hit_count" in metrics else 0
        })
        
        return metrics
        
    def _save_to_disk(self, filepath: str, value: Any) -> None:
        """
        Save a value to disk.
        
        Args:
            filepath: Path to save the file
            value: Value to save
        """
        try:
            # Try to serialize complex objects
            if hasattr(value, 'to_dict') and callable(value.to_dict):
                # Convert Resource object to dictionary
                value = value.to_dict()
            elif isinstance(value, list) and all(hasattr(item, 'to_dict') and callable(item.to_dict) for item in value):
                # Convert list of Resource objects to list of dictionaries
                value = [item.to_dict() for item in value]
                
            # Use msgpack for efficient serialization
            if isinstance(value, (dict, list, tuple)) and not isinstance(value, bytes):
                serialized = msgpack.packb(value, use_bin_type=True)
                with open(filepath, 'wb') as f:
                    f.write(serialized)
            else:
                # Fallback to pickle for other types
                with open(filepath, 'wb') as f:
                    pickle.dump(value, f)
        except Exception as e:
            logger.error(f"Error saving to disk: {str(e)}")
            raise
            
    def _load_from_disk(self, filename: str, resource_type: Optional[str] = None) -> Optional[Any]:
        """
        Load a value from disk.
        
        Args:
            filename: Filename to load
            resource_type: Optional type hint for deserialization
            
        Returns:
            Loaded value or None if error
        """
        filepath = os.path.join(self.disk_path, filename)
        
        try:
            if not os.path.exists(filepath):
                return None
                
            with open(filepath, 'rb') as f:
                data = f.read()
                
            try:
                # Try msgpack first
                value = msgpack.unpackb(data, raw=False)
                
                # Convert to Resource object if requested
                if resource_type == 'resource' and isinstance(value, dict):
                    from api.models import Resource
                    try:
                        return Resource(**value)
                    except Exception as e:
                        logger.error(f"Error creating Resource from dict: {str(e)}")
                        return value
                elif resource_type == 'resource_list' and isinstance(value, list):
                    from api.models import Resource
                    try:
                        return [Resource(**item) if isinstance(item, dict) else item for item in value]
                    except Exception as e:
                        logger.error(f"Error creating Resource list from dict list: {str(e)}")
                        return value
                else:
                    return value
            except Exception:
                # Fallback to pickle
                with open(filepath, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading from disk: {str(e)}")
            return None
            
    def _remove_from_disk(self, key: str) -> None:
        """
        Remove a key from the disk cache.
        
        Args:
            key: Key to remove
        """
        if key in self.disk_index:
            _, filename = self.disk_index[key]
            filepath = os.path.join(self.disk_path, filename)
            
            # Remove file
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                logger.error(f"Error removing file {filepath}: {str(e)}")
                
            # Update index
            self.disk_index.pop(key, None)
            self.disk_access_times.pop(key, None)
            
    def _evict_lru_disk_item(self) -> None:
        """
        Evict the least recently used item from the disk cache.
        """
        if not self.disk_access_times:
            return
            
        lru_key = min(self.disk_access_times.items(), key=lambda x: x[1])[0]
        self._remove_from_disk(lru_key)
        self.metrics.increment_eviction_count()
        logger.debug(f"Evicted LRU item from disk cache with key: {lru_key}")
        
    def _load_disk_index(self) -> None:
        """
        Load the disk cache index from disk.
        """
        index_path = os.path.join(self.disk_path, "index.json")
        
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    data = json.load(f)
                    
                self.disk_index = {k: (exp, filename) for k, (exp, filename) in data.get("index", {}).items()}
                self.disk_access_times = {k: access for k, access in data.get("access_times", {}).items()}
                
                # Cleanup any files that don't exist
                for key, (_, filename) in list(self.disk_index.items()):
                    filepath = os.path.join(self.disk_path, filename)
                    if not os.path.exists(filepath):
                        self.disk_index.pop(key, None)
                        self.disk_access_times.pop(key, None)
                        
                logger.info(f"Loaded disk cache index with {len(self.disk_index)} entries")
            except Exception as e:
                logger.error(f"Error loading disk cache index: {str(e)}")
                self.disk_index = {}
                self.disk_access_times = {}
        else:
            logger.info("No disk cache index found, starting with empty index")
            self.disk_index = {}
            self.disk_access_times = {}
            
    def _save_disk_index(self) -> None:
        """
        Save the disk cache index to disk.
        """
        index_path = os.path.join(self.disk_path, "index.json")
        
        try:
            # Convert to serializable format
            serializable_index = {
                "index": {k: [exp, filename] for k, (exp, filename) in self.disk_index.items()},
                "access_times": self.disk_access_times
            }
            
            with open(index_path, 'w') as f:
                json.dump(serializable_index, f)
                
            logger.debug(f"Saved disk cache index with {len(self.disk_index)} entries")
        except Exception as e:
            logger.error(f"Error saving disk cache index: {str(e)}")
            
    def _background_sync(self) -> None:
        """
        Background thread for syncing memory cache to disk and cleaning up expired items.
        """
        while True:
            try:
                # Sleep first to allow initialization to complete
                time.sleep(self.sync_interval)
                
                # Cleanup expired items
                self.cleanup_expired()
                
                # Save disk index
                self._save_disk_index()
                
                logger.debug("Completed background sync")
            except Exception as e:
                logger.error(f"Error in background sync: {str(e)}")
