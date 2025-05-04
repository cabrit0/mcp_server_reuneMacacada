"""
Unit tests for the search implementations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from services.search.duckduckgo_search import DuckDuckGoSearch
from services.search.brave_search import BraveSearch
from services.search.fallback_search import FallbackSearch
from services.search.search_factory import SearchFactory


class TestDuckDuckGoSearch:
    """Tests for the DuckDuckGoSearch implementation."""

    @pytest.mark.asyncio
    async def test_search_impl(self):
        """Test the _search_impl method."""
        # Mock the DDGS class
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__.return_value = mock_ddgs
        mock_ddgs.text.return_value = [
            {"title": "Test Title 1", "href": "https://example.com/1", "body": "Test Description 1"},
            {"title": "Test Title 2", "href": "https://example.com/2", "body": "Test Description 2"}
        ]
        
        with patch("services.search.duckduckgo_search.DDGS", return_value=mock_ddgs):
            search = DuckDuckGoSearch()
            results = await search._search_impl("test query", 2, "en")
            
            # Check results
            assert len(results) == 2
            assert results[0]["title"] == "Test Title 1"
            assert results[0]["url"] == "https://example.com/1"
            assert results[0]["description"] == "Test Description 1"
            
            # Check that DDGS.text was called with the correct arguments
            mock_ddgs.text.assert_called_once()
            args, kwargs = mock_ddgs.text.call_args
            assert args[0] == "test query"
            assert kwargs["max_results"] == 2
            assert kwargs["region"] == "us-en"

    @pytest.mark.asyncio
    async def test_search_with_cache(self):
        """Test that search uses cache."""
        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = [
            {"title": "Cached Title", "url": "https://example.com/cached", "description": "Cached Description"}
        ]
        
        with patch("services.search.base_search.cache", mock_cache):
            search = DuckDuckGoSearch()
            results = await search.search("test query", 2, "en")
            
            # Check that cache was used
            assert len(results) == 1
            assert results[0]["title"] == "Cached Title"
            
            # Check that cache.get was called with the correct key
            mock_cache.get.assert_called_once()
            args, kwargs = mock_cache.get.call_args
            assert "search:duckduckgo:test query_2_en" in args[0]

    @pytest.mark.asyncio
    async def test_search_with_retry(self):
        """Test the search_with_retry method."""
        # Mock the _search_impl method to fail twice then succeed
        search = DuckDuckGoSearch()
        
        # Create a side effect function that fails twice then succeeds
        search_results = [
            {"title": "Test Title", "url": "https://example.com", "description": "Test Description"}
        ]
        
        side_effect_counter = 0
        
        async def search_side_effect(*args, **kwargs):
            nonlocal side_effect_counter
            side_effect_counter += 1
            if side_effect_counter <= 2:
                raise Exception("Test exception")
            return search_results
            
        search._search_impl = AsyncMock(side_effect=search_side_effect)
        
        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        
        with patch("services.search.base_search.cache", mock_cache):
            results = await search.search_with_retry("test query", 2, "en", max_retries=3, backoff_factor=0.1)
            
            # Check that search_impl was called 3 times
            assert search._search_impl.call_count == 3
            
            # Check that results were returned
            assert len(results) == 1
            assert results[0]["title"] == "Test Title"


class TestBraveSearch:
    """Tests for the BraveSearch implementation."""

    @pytest.mark.asyncio
    async def test_search_impl(self):
        """Test the _search_impl method."""
        # Mock the aiohttp.ClientSession
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "web": {
                "results": [
                    {"title": "Test Title 1", "url": "https://example.com/1", "description": "Test Description 1"},
                    {"title": "Test Title 2", "url": "https://example.com/2", "description": "Test Description 2"}
                ]
            }
        })
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        # Mock the config to provide an API key
        mock_config = MagicMock()
        mock_config.get_section.return_value = {"brave_api_key": "test_api_key"}
        
        with patch("services.search.brave_search.aiohttp.ClientSession", return_value=mock_session), \
             patch("services.search.brave_search.config", mock_config):
            search = BraveSearch()
            results = await search._search_impl("test query", 2, "en")
            
            # Check results
            assert len(results) == 2
            assert results[0]["title"] == "Test Title 1"
            assert results[0]["url"] == "https://example.com/1"
            assert results[0]["description"] == "Test Description 1"
            
            # Check that session.get was called with the correct arguments
            mock_session.get.assert_called_once()
            args, kwargs = mock_session.get.call_args
            assert args[0] == "https://api.search.brave.com/res/v1/web/search"
            assert kwargs["params"]["q"] == "test query"
            assert kwargs["params"]["count"] == 2
            assert kwargs["headers"]["X-Subscription-Token"] == "test_api_key"


class TestFallbackSearch:
    """Tests for the FallbackSearch implementation."""

    @pytest.mark.asyncio
    async def test_search_impl_first_engine_succeeds(self):
        """Test the _search_impl method when the first engine succeeds."""
        # Create mock search engines
        mock_engine1 = MagicMock()
        mock_engine1.name = "engine1"
        mock_engine1.search = AsyncMock(return_value=[
            {"title": "Engine 1 Result", "url": "https://example.com/1", "description": "Engine 1 Description"}
        ])
        
        mock_engine2 = MagicMock()
        mock_engine2.name = "engine2"
        mock_engine2.search = AsyncMock()
        
        # Create fallback search with mock engines
        search = FallbackSearch([(mock_engine1, 1.0), (mock_engine2, 0.8)])
        
        # Test search
        results = await search._search_impl("test query", 2, "en")
        
        # Check results
        assert len(results) == 1
        assert results[0]["title"] == "Engine 1 Result"
        
        # Check that only the first engine was called
        mock_engine1.search.assert_called_once()
        mock_engine2.search.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_impl_fallback(self):
        """Test the _search_impl method when the first engine fails and falls back to the second."""
        # Create mock search engines
        mock_engine1 = MagicMock()
        mock_engine1.name = "engine1"
        mock_engine1.search = AsyncMock(return_value=[])  # Empty results
        
        mock_engine2 = MagicMock()
        mock_engine2.name = "engine2"
        mock_engine2.search = AsyncMock(return_value=[
            {"title": "Engine 2 Result", "url": "https://example.com/2", "description": "Engine 2 Description"}
        ])
        
        # Create fallback search with mock engines
        search = FallbackSearch([(mock_engine1, 1.0), (mock_engine2, 0.8)])
        
        # Test search
        results = await search._search_impl("test query", 2, "en")
        
        # Check results
        assert len(results) == 1
        assert results[0]["title"] == "Engine 2 Result"
        
        # Check that both engines were called
        mock_engine1.search.assert_called_once()
        mock_engine2.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_parallel(self):
        """Test the search_parallel method."""
        # Create mock search engines
        mock_engine1 = MagicMock()
        mock_engine1.name = "engine1"
        mock_engine1.search = AsyncMock(return_value=[
            {"title": "Engine 1 Result 1", "url": "https://example.com/1", "description": "Engine 1 Description 1"},
            {"title": "Engine 1 Result 2", "url": "https://example.com/2", "description": "Engine 1 Description 2"}
        ])
        
        mock_engine2 = MagicMock()
        mock_engine2.name = "engine2"
        mock_engine2.search = AsyncMock(return_value=[
            {"title": "Engine 2 Result 1", "url": "https://example.com/3", "description": "Engine 2 Description 1"},
            {"title": "Engine 2 Result 2", "url": "https://example.com/2", "description": "Engine 2 Description 2"}  # Duplicate URL
        ])
        
        # Create fallback search with mock engines
        search = FallbackSearch([(mock_engine1, 1.0), (mock_engine2, 0.8)])
        
        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        
        with patch("services.search.fallback_search.cache", mock_cache):
            # Test search_parallel
            results = await search.search_parallel("test query", 4, "en")
            
            # Check results (should be 3 unique results)
            assert len(results) == 3
            
            # Check that both engines were called
            mock_engine1.search.assert_called_once()
            mock_engine2.search.assert_called_once()
            
            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()


class TestSearchFactory:
    """Tests for the SearchFactory."""

    def test_create_search(self):
        """Test the create_search method."""
        # Clear existing instances
        SearchFactory._instances = {}
        
        # Create search instances
        duckduckgo_search = SearchFactory.create_search("duckduckgo")
        brave_search = SearchFactory.create_search("brave")
        fallback_search = SearchFactory.create_search("fallback")
        default_search = SearchFactory.create_search("default")
        
        # Check types
        assert isinstance(duckduckgo_search, DuckDuckGoSearch)
        assert isinstance(brave_search, BraveSearch)
        assert isinstance(fallback_search, FallbackSearch)
        assert isinstance(default_search, FallbackSearch)
        
        # Check singleton pattern
        assert SearchFactory.create_search("duckduckgo") is duckduckgo_search
        assert SearchFactory.create_search("brave") is brave_search
        assert SearchFactory.create_search("fallback") is fallback_search
        assert SearchFactory.create_search("default") is default_search
