"""
Unit tests for the scraper implementations.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from services.scraping.requests_scraper import RequestsScraper
from services.scraping.puppeteer_scraper import PuppeteerScraper
from services.scraping.adaptive_scraper import AdaptiveScraper
from services.scraping.scraper_factory import ScraperFactory


class TestRequestsScraper:
    """Tests for the RequestsScraper implementation."""

    @pytest.mark.asyncio
    async def test_scrape_url_impl(self):
        """Test the _scrape_url_impl method."""
        # Mock aiohttp.ClientSession
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="<html><head><title>Test</title></head><body><main>Content</main></body></html>")
        mock_session.__aenter__.return_value = mock_session
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch("aiohttp.ClientSession", return_value=mock_session):
            scraper = RequestsScraper()
            result = await scraper._scrape_url_impl("https://example.com")
            
            # Check result
            assert result is not None
            assert "html" in result
            assert "title" in result
            assert result["method"] == "requests"
            
            # Check that session.get was called with the correct arguments
            mock_session.get.assert_called_once()
            args, kwargs = mock_session.get.call_args
            assert args[0] == "https://example.com"
            assert "timeout" in kwargs
            assert "headers" in kwargs


class TestPuppeteerScraper:
    """Tests for the PuppeteerScraper implementation."""

    @pytest.mark.asyncio
    async def test_scrape_url_impl(self):
        """Test the _scrape_url_impl method."""
        # Mock PuppeteerPool
        mock_pool = MagicMock()
        mock_browser = AsyncMock()
        mock_page = AsyncMock()
        
        # Configure mocks
        mock_pool.get_browser = AsyncMock(return_value=mock_browser)
        mock_pool.release_browser = AsyncMock()
        mock_browser.newPage = AsyncMock(return_value=mock_page)
        mock_page.setRequestInterception = AsyncMock()
        mock_page.setDefaultNavigationTimeout = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><head><title>Test</title></head><body>Content</body></html>")
        mock_page.evaluate = AsyncMock(side_effect=["Test Title", "Test Description"])
        mock_page.close = AsyncMock()
        
        # Create scraper with mock pool
        scraper = PuppeteerScraper(pool=mock_pool)
        
        # Call method
        result = await scraper._scrape_url_impl("https://example.com")
        
        # Check result
        assert result is not None
        assert "html" in result
        assert "title" in result
        assert "description" in result
        assert result["method"] == "puppeteer"
        
        # Check that pool methods were called
        mock_pool.get_browser.assert_called_once()
        mock_pool.release_browser.assert_called_once_with(mock_browser)
        
        # Check that browser and page methods were called
        mock_browser.newPage.assert_called_once()
        mock_page.goto.assert_called_once()
        mock_page.content.assert_called_once()
        assert mock_page.evaluate.call_count == 2
        mock_page.close.assert_called_once()


class TestAdaptiveScraper:
    """Tests for the AdaptiveScraper implementation."""

    @pytest.mark.asyncio
    async def test_scrape_url_impl_requests_success(self):
        """Test the _scrape_url_impl method when requests method succeeds."""
        # Create scraper with mock scrapers
        scraper = AdaptiveScraper()
        
        # Mock the scrapers
        scraper.requests_scraper = MagicMock()
        scraper.puppeteer_scraper = MagicMock()
        
        # Configure mocks
        scraper.requests_scraper._scrape_url_impl = AsyncMock(return_value={
            "html": "<html><body>Content</body></html>",
            "title": "Test",
            "description": "Description",
            "method": "requests"
        })
        
        # Call method
        result = await scraper._scrape_url_impl("https://example.com")
        
        # Check result
        assert result is not None
        assert result["method"] == "requests"
        
        # Check that requests scraper was called but puppeteer scraper was not
        scraper.requests_scraper._scrape_url_impl.assert_called_once()
        scraper.puppeteer_scraper._scrape_url_impl.assert_not_called()

    @pytest.mark.asyncio
    async def test_scrape_url_impl_requests_fallback(self):
        """Test the _scrape_url_impl method when requests method fails and falls back to puppeteer."""
        # Create scraper with mock scrapers
        scraper = AdaptiveScraper()
        
        # Mock the scrapers
        scraper.requests_scraper = MagicMock()
        scraper.puppeteer_scraper = MagicMock()
        
        # Configure mocks
        scraper.requests_scraper._scrape_url_impl = AsyncMock(return_value=None)
        scraper.puppeteer_scraper._scrape_url_impl = AsyncMock(return_value={
            "html": "<html><body>Content</body></html>",
            "title": "Test",
            "description": "Description",
            "method": "puppeteer"
        })
        
        # Call method
        result = await scraper._scrape_url_impl("https://example.com")
        
        # Check result
        assert result is not None
        assert result["method"] == "puppeteer"
        
        # Check that both scrapers were called
        scraper.requests_scraper._scrape_url_impl.assert_called_once()
        scraper.puppeteer_scraper._scrape_url_impl.assert_called_once()

    @pytest.mark.asyncio
    async def test_scrape_url_impl_js_required_domain(self):
        """Test the _scrape_url_impl method with a domain that requires JavaScript."""
        # Create scraper with mock scrapers
        scraper = AdaptiveScraper()
        
        # Add test domain to JS_REQUIRED_DOMAINS
        scraper.JS_REQUIRED_DOMAINS.add("twitter.example.com")
        
        # Mock the scrapers
        scraper.requests_scraper = MagicMock()
        scraper.puppeteer_scraper = MagicMock()
        
        # Configure mocks
        scraper.puppeteer_scraper._scrape_url_impl = AsyncMock(return_value={
            "html": "<html><body>Content</body></html>",
            "title": "Test",
            "description": "Description",
            "method": "puppeteer"
        })
        
        # Call method
        result = await scraper._scrape_url_impl("https://twitter.example.com/page")
        
        # Check result
        assert result is not None
        assert result["method"] == "puppeteer"
        
        # Check that only puppeteer scraper was called
        scraper.requests_scraper._scrape_url_impl.assert_not_called()
        scraper.puppeteer_scraper._scrape_url_impl.assert_called_once()


class TestScraperFactory:
    """Tests for the ScraperFactory."""

    def test_create_scraper(self):
        """Test the create_scraper method."""
        # Clear existing instances
        ScraperFactory._instances = {}
        ScraperFactory._puppeteer_pool = None
        
        # Create scrapers
        requests_scraper = ScraperFactory.create_scraper("requests")
        puppeteer_scraper = ScraperFactory.create_scraper("puppeteer")
        adaptive_scraper = ScraperFactory.create_scraper("adaptive")
        
        # Check types
        assert isinstance(requests_scraper, RequestsScraper)
        assert isinstance(puppeteer_scraper, PuppeteerScraper)
        assert isinstance(adaptive_scraper, AdaptiveScraper)
        
        # Check singleton pattern
        assert ScraperFactory.create_scraper("requests") is requests_scraper
        assert ScraperFactory.create_scraper("puppeteer") is puppeteer_scraper
        assert ScraperFactory.create_scraper("adaptive") is adaptive_scraper
        
        # Check puppeteer pool
        assert ScraperFactory._puppeteer_pool is not None
        assert puppeteer_scraper.pool is ScraperFactory._puppeteer_pool
