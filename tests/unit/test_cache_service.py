"""
Unit tests for the cache service.
"""

import pytest
from infrastructure.cache.cache_service import CacheService


class TestCacheService:
    """Tests for the CacheService interface."""

    def test_cache_service_is_abstract(self):
        """Test that CacheService is an abstract class."""
        with pytest.raises(TypeError):
            CacheService()  # Should raise TypeError because it's an abstract class
