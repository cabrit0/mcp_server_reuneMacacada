"""
Unit tests for the YouTube service implementations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from api.models import Resource
from services.youtube.ytdlp_service import YtDlpService
from services.youtube.youtube_api_service import YouTubeApiService
from services.youtube.fallback_youtube_service import FallbackYouTubeService
from services.youtube.youtube_factory import YouTubeFactory


class TestYtDlpService:
    """Tests for the YtDlpService implementation."""

    @pytest.mark.asyncio
    async def test_search_videos(self):
        """Test the search_videos method."""
        # Mock the _extract_info_with_ytdlp method
        mock_results = [
            {
                "_type": "url",
                "url": "https://www.youtube.com/watch?v=test1",
                "id": "test1",
                "title": "Test Video 1",
                "description": "Test Description 1",
                "duration": 180,
                "uploader": "Test Channel"
            },
            {
                "_type": "url",
                "url": "https://www.youtube.com/watch?v=test2",
                "id": "test2",
                "title": "Test Video 2",
                "description": "Test Description 2",
                "duration": 300,
                "uploader": "Test Channel"
            }
        ]

        service = YtDlpService()
        service._extract_info_with_ytdlp = MagicMock(return_value=mock_results)

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("services.youtube.ytdlp_service.cache", mock_cache):
            # Test search_videos
            results = await service.search_videos("test query", 2, "en")

            # Check results
            assert len(results) == 2
            assert results[0]["id"] == "test1"
            assert results[0]["title"] == "Test Video 1"
            assert results[0]["url"] == "https://www.youtube.com/watch?v=test1"
            assert results[0]["duration"] == 3  # 180 seconds = 3 minutes

            # Check that _extract_info_with_ytdlp was called with the correct arguments
            service._extract_info_with_ytdlp.assert_called_once()
            args, kwargs = service._extract_info_with_ytdlp.call_args
            assert "ytsearch" in args[0]
            assert "test query" in args[0]

            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_videos_for_topic(self):
        """Test the search_videos_for_topic method."""
        # Mock the search_videos method
        service = YtDlpService()
        service.search_videos = AsyncMock(return_value=[
            {
                "id": "test1",
                "title": "Test Video 1",
                "url": "https://www.youtube.com/watch?v=test1",
                "description": "Test Description 1",
                "duration": 3,
                "thumbnail": "https://example.com/thumbnail1.jpg"
            },
            {
                "id": "test2",
                "title": "Test Video 2",
                "url": "https://www.youtube.com/watch?v=test2",
                "description": "Test Description 2",
                "duration": 5,
                "thumbnail": "https://example.com/thumbnail2.jpg"
            }
        ])

        # Test search_videos_for_topic
        results = await service.search_videos_for_topic("python", "classes", 2, "en")

        # Check results
        assert len(results) == 2
        assert isinstance(results[0], Resource)
        assert results[0].id == "youtube_test1"
        assert results[0].title.endswith("Relevante para: classes")
        assert results[0].type == "video"

        # Check that search_videos was called with the correct arguments
        service.search_videos.assert_called_once()
        args, kwargs = service.search_videos.call_args
        assert "python" in args[0]
        assert "classes" in args[0]
        assert args[1] == 2
        assert args[2] == "en"


class TestYouTubeApiService:
    """Tests for the YouTubeApiService implementation."""

    @pytest.mark.asyncio
    async def test_search_videos(self):
        """Test the search_videos method."""
        # Mock the aiohttp.ClientSession
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [
                {"id": {"videoId": "test1"}},
                {"id": {"videoId": "test2"}}
            ]
        })
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response

        # Mock the _get_videos_details method
        service = YouTubeApiService()
        service._get_videos_details = AsyncMock(return_value=[
            {
                "id": "test1",
                "title": "Test Video 1",
                "url": "https://www.youtube.com/watch?v=test1",
                "description": "Test Description 1",
                "duration": 3,
                "thumbnail": "https://example.com/thumbnail1.jpg"
            },
            {
                "id": "test2",
                "title": "Test Video 2",
                "url": "https://www.youtube.com/watch?v=test2",
                "description": "Test Description 2",
                "duration": 5,
                "thumbnail": "https://example.com/thumbnail2.jpg"
            }
        ])

        # Mock the config to provide an API key
        mock_config = MagicMock()
        mock_config.get_section.return_value = {"api_key": "test_api_key"}

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("services.youtube.youtube_api_service.aiohttp.ClientSession", return_value=mock_session), \
             patch("services.youtube.youtube_api_service.config", mock_config), \
             patch("services.youtube.youtube_api_service.cache", mock_cache):
            # Test search_videos
            results = await service.search_videos("test query", 2, "en")

            # Check results
            assert len(results) == 2
            assert results[0]["id"] == "test1"
            assert results[0]["title"] == "Test Video 1"
            assert results[0]["url"] == "https://www.youtube.com/watch?v=test1"

            # Check that session.get was called with the correct arguments
            mock_session.get.assert_called_once()
            args, kwargs = mock_session.get.call_args
            assert args[0] == "https://www.googleapis.com/youtube/v3/search"
            assert kwargs["params"]["q"] == "test query"
            assert kwargs["params"]["maxResults"] == 4  # 2 * 2
            assert kwargs["params"]["key"] == "test_api_key"

            # Check that _get_videos_details was called with the correct arguments
            service._get_videos_details.assert_called_once_with(["test1", "test2"])

            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()


class TestFallbackYouTubeService:
    """Tests for the FallbackYouTubeService implementation."""

    @pytest.mark.asyncio
    async def test_search_videos_first_service_succeeds(self):
        """Test the search_videos method when the first service succeeds."""
        # Create mock services
        mock_service1 = MagicMock()
        mock_service1.__class__.__name__ = "MockService1"
        mock_service1.search_videos = AsyncMock(return_value=[
            {
                "id": "test1",
                "title": "Test Video 1",
                "url": "https://www.youtube.com/watch?v=test1"
            }
        ])

        mock_service2 = MagicMock()
        mock_service2.__class__.__name__ = "MockService2"
        mock_service2.search_videos = AsyncMock()

        # Create fallback service with mock services
        service = FallbackYouTubeService([(mock_service1, 1.0), (mock_service2, 0.8)])

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("services.youtube.fallback_youtube_service.cache", mock_cache):
            # Test search_videos
            results = await service.search_videos("test query", 2, "en")

            # Check results
            assert len(results) == 1
            assert results[0]["id"] == "test1"

            # Check that only the first service was called
            mock_service1.search_videos.assert_called_once()
            mock_service2.search_videos.assert_not_called()

            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_videos_fallback(self):
        """Test the search_videos method when the first service fails and falls back to the second."""
        # Create mock services
        mock_service1 = MagicMock()
        mock_service1.__class__.__name__ = "MockService1"
        mock_service1.search_videos = AsyncMock(return_value=[])  # Empty results

        mock_service2 = MagicMock()
        mock_service2.__class__.__name__ = "MockService2"
        mock_service2.search_videos = AsyncMock(return_value=[
            {
                "id": "test2",
                "title": "Test Video 2",
                "url": "https://www.youtube.com/watch?v=test2"
            }
        ])

        # Create fallback service with mock services
        service = FallbackYouTubeService([(mock_service1, 1.0), (mock_service2, 0.8)])

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("services.youtube.fallback_youtube_service.cache", mock_cache):
            # Test search_videos
            results = await service.search_videos("test query", 2, "en")

            # Check results
            assert len(results) == 1
            assert results[0]["id"] == "test2"

            # Check that both services were called
            mock_service1.search_videos.assert_called_once()
            mock_service2.search_videos.assert_called_once()

            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()


class TestYouTubeFactory:
    """Tests for the YouTubeFactory."""

    def test_create_youtube_service(self):
        """Test the create_youtube_service method."""
        # Clear existing instances
        YouTubeFactory._instances = {}

        # Create services
        ytdlp_service = YouTubeFactory.create_youtube_service("ytdlp")
        api_service = YouTubeFactory.create_youtube_service("api")
        fallback_service = YouTubeFactory.create_youtube_service("fallback")
        default_service = YouTubeFactory.create_youtube_service("default")

        # Check types
        assert isinstance(ytdlp_service, YtDlpService)
        assert isinstance(api_service, YouTubeApiService)
        assert isinstance(fallback_service, FallbackYouTubeService)
        assert isinstance(default_service, FallbackYouTubeService)

        # Check singleton pattern
        assert YouTubeFactory.create_youtube_service("ytdlp") is ytdlp_service
        assert YouTubeFactory.create_youtube_service("api") is api_service
        assert YouTubeFactory.create_youtube_service("fallback") is fallback_service
        assert YouTubeFactory.create_youtube_service("default") is default_service
