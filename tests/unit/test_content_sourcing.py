"""
Unit tests for the content sourcing implementations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from api.models import Resource
from core.content_sourcing.duckduckgo_search_service import DuckDuckGoSearchService
from core.content_sourcing.optimized_scraper_service import OptimizedScraperService
from core.content_sourcing.default_content_source_service import DefaultContentSourceService
from core.content_sourcing.content_source_factory import ContentSourceFactory


class TestDuckDuckGoSearchService:
    """Tests for the DuckDuckGoSearchService implementation."""

    @pytest.mark.asyncio
    async def test_search(self):
        """Test the search method."""
        # Mock the search_service
        mock_search_service = MagicMock()
        mock_search_service.search = AsyncMock(return_value=[
            {
                "title": "Python Tutorial",
                "url": "https://example.com/python-tutorial",
                "description": "Learn Python programming"
            },
            {
                "title": "Python for Beginners",
                "url": "https://example.com/python-beginners",
                "description": "Python tutorial for beginners"
            }
        ])

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("core.content_sourcing.duckduckgo_search_service.search_service", mock_search_service), \
             patch("core.content_sourcing.duckduckgo_search_service.cache", mock_cache):
            service = DuckDuckGoSearchService()

            # Test search
            results = await service.search("Python tutorial", 5, "en")

            # Check results
            assert len(results) == 2
            assert results[0]["title"] == "Python Tutorial"
            assert results[0]["url"] == "https://example.com/python-tutorial"

            # Check that search_service.search was called with the correct arguments
            mock_search_service.search.assert_called_once_with("Python tutorial", 5, "en")

            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()


class TestOptimizedScraperService:
    """Tests for the OptimizedScraperService implementation."""

    @pytest.mark.asyncio
    async def test_scrape(self):
        """Test the scrape method."""
        # Mock the scraper
        mock_scraper = MagicMock()
        mock_scraper.scrape_url = AsyncMock(return_value="<html><title>Python Tutorial</title><body>Learn Python</body></html>")
        mock_scraper.extract_metadata_from_html = MagicMock(return_value={
            "title": "Python Tutorial",
            "description": "Learn Python programming",
            "type": "article",
            "content": "Learn Python programming with this tutorial."
        })

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("core.content_sourcing.optimized_scraper_service.scraper", mock_scraper), \
             patch("core.content_sourcing.optimized_scraper_service.cache", mock_cache):
            service = OptimizedScraperService()

            # Test scrape
            result = await service.scrape("https://example.com/python-tutorial", "Python", 10, "en")

            # Check results
            assert result["title"] == "Python Tutorial"
            assert result["description"] == "Learn Python programming"
            assert result["type"] == "article"

            # Check that scraper.scrape_url was called with the correct arguments
            mock_scraper.scrape_url.assert_called_once_with("https://example.com/python-tutorial", 10)

            # Check that scraper.extract_metadata_from_html was called with the correct arguments
            mock_scraper.extract_metadata_from_html.assert_called_once()

            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()

    def test_determine_content_type(self):
        """Test the determine_content_type method."""
        service = OptimizedScraperService()

        # Test video platforms
        assert service.determine_content_type("https://youtube.com/watch?v=123") == "video"
        assert service.determine_content_type("https://vimeo.com/123") == "video"

        # Test documentation sites
        assert service.determine_content_type("https://docs.python.org/3/") == "documentation"
        assert service.determine_content_type("https://developer.mozilla.org/") == "documentation"

        # Test exercise sites
        assert service.determine_content_type("https://exercism.io/tracks/python") == "exercise"
        assert service.determine_content_type("https://leetcode.com/problems/") == "exercise"

        # Test default
        assert service.determine_content_type("https://example.com/blog") == "article"

        # Test with HTML content
        html_with_video = "<html><body><video src='video.mp4'></video></body></html>"
        assert service.determine_content_type("https://example.com/page", html_with_video) == "video"

    def test_estimate_read_time(self):
        """Test the estimate_read_time method."""
        service = OptimizedScraperService()

        # Test with different content lengths
        assert service.estimate_read_time(1000) == 1  # Minimum 1 minute
        assert service.estimate_read_time(5000) == 5  # 5000 chars ≈ 1000 words ≈ 5 minutes
        assert service.estimate_read_time(20000) == 20  # 20000 chars ≈ 4000 words ≈ 20 minutes


class TestDefaultContentSourceService:
    """Tests for the DefaultContentSourceService implementation."""

    @pytest.mark.asyncio
    async def test_find_resources(self):
        """Test the find_resources method."""
        # Mock the search service
        mock_search_service = MagicMock()
        mock_search_service.search = AsyncMock(return_value=[
            {
                "title": "Python Tutorial",
                "url": "https://example.com/python-tutorial",
                "description": "Learn Python programming"
            }
        ])

        # Mock the scraper service
        mock_scraper_service = MagicMock()
        mock_scraper_service.scrape = AsyncMock(return_value={
            "title": "Python Tutorial",
            "url": "https://example.com/python-tutorial",
            "description": "Learn Python programming",
            "type": "article",
            "readTime": 10
        })

        # Mock the category service
        mock_category_service = MagicMock()
        mock_category_service.detect_category.return_value = "technology"
        mock_category_service.get_category_specific_queries.return_value = [
            "Python tutorial",
            "Python guide"
        ]

        # Mock the youtube service
        mock_youtube = MagicMock()
        mock_youtube.search_videos_for_topic = AsyncMock(return_value=[
            Resource(
                id="youtube_123",
                title="Python Video Tutorial",
                url="https://youtube.com/watch?v=123",
                type="video",
                description="Learn Python with this video tutorial",
                duration=15,
                readTime=None,
                difficulty="beginner",
                thumbnail="https://example.com/thumbnail.jpg"
            )
        ])

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("core.content_sourcing.default_content_source_service.category_service", mock_category_service), \
             patch("core.content_sourcing.default_content_source_service.youtube", mock_youtube), \
             patch("core.content_sourcing.default_content_source_service.cache", mock_cache):
            service = DefaultContentSourceService(mock_search_service, mock_scraper_service)

            # Test find_resources
            resources = await service.find_resources("Python", 5, "en")

            # Check results
            assert len(resources) > 0
            assert any(r.title == "Python Tutorial" for r in resources)
            assert any(r.title == "Python Video Tutorial" for r in resources)

            # Check that search_service.search was called
            assert mock_search_service.search.call_count > 0

            # Check that scraper_service.scrape was called
            assert mock_scraper_service.scrape.call_count > 0

            # Check that category_service was called
            mock_category_service.detect_category.assert_called_once_with("Python")
            mock_category_service.get_category_specific_queries.assert_called_once()

            # Check that youtube.search_videos_for_topic was called
            mock_youtube.search_videos_for_topic.assert_called_once()

            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_resources_by_query(self):
        """Test the find_resources_by_query method."""
        # Mock the search service
        mock_search_service = MagicMock()
        mock_search_service.search = AsyncMock(return_value=[
            {
                "title": "Python Tutorial",
                "url": "https://example.com/python-tutorial",
                "description": "Learn Python programming"
            }
        ])

        # Mock the scraper service
        mock_scraper_service = MagicMock()
        mock_scraper_service.scrape = AsyncMock(return_value={
            "title": "Python Tutorial",
            "url": "https://example.com/python-tutorial",
            "description": "Learn Python programming",
            "type": "article",
            "readTime": 10
        })

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("core.content_sourcing.default_content_source_service.cache", mock_cache):
            service = DefaultContentSourceService(mock_search_service, mock_scraper_service)

            # Test find_resources_by_query
            resources = await service.find_resources_by_query("Python tutorial", "Python", 5, "en")

            # Check results
            assert len(resources) > 0
            assert resources[0].title == "Python Tutorial"
            assert resources[0].url == "https://example.com/python-tutorial"

            # Check that search_service.search was called with the correct arguments
            mock_search_service.search.assert_called_once_with("Python tutorial", 5, "en")

            # Check that scraper_service.scrape was called
            mock_scraper_service.scrape.assert_called_once()

            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()

    def test_filter_resources(self):
        """Test the filter_resources method."""
        service = DefaultContentSourceService(MagicMock(), MagicMock())

        # Create test resources
        resources = [
            Resource(
                id="r1",
                title="Python Documentation",
                url="https://docs.python.org/",
                type="documentation",
                description="Official Python documentation",
                duration=None,
                readTime=30,
                difficulty="intermediate",
                thumbnail=None
            ),
            Resource(
                id="r2",
                title="Python Tutorial",
                url="https://example.com/python-tutorial",
                type="tutorial",
                description="Learn Python programming",
                duration=None,
                readTime=15,
                difficulty="beginner",
                thumbnail=None
            ),
            Resource(
                id="r3",
                title="Python Video",
                url="https://youtube.com/watch?v=123",
                type="video",
                description="Python video tutorial",
                duration=10,
                readTime=None,
                difficulty="beginner",
                thumbnail="https://example.com/thumbnail.jpg"
            ),
            # Duplicate URL
            Resource(
                id="r4",
                title="Python Tutorial (Duplicate)",
                url="https://example.com/python-tutorial",
                type="article",
                description="Another Python tutorial",
                duration=None,
                readTime=20,
                difficulty="beginner",
                thumbnail=None
            )
        ]

        # Filter resources
        filtered = service.filter_resources(resources, "Python", 5, "en")

        # Check results
        assert len(filtered) == 3  # Should remove the duplicate

        # Check that resources are sorted by priority (documentation > tutorial > video)
        assert filtered[0].type == "documentation"
        assert filtered[1].type == "tutorial"
        assert filtered[2].type == "video"


class TestContentSourceFactory:
    """Tests for the ContentSourceFactory."""

    def test_create_content_source(self):
        """Test the create_content_source method."""
        # Clear existing instances
        ContentSourceFactory._instances = {}

        # Create content source
        source = ContentSourceFactory.create_content_source("default")

        # Check type
        assert isinstance(source, DefaultContentSourceService)

        # Check singleton pattern
        assert ContentSourceFactory.create_content_source("default") is source
