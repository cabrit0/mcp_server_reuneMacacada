"""
Factory for creating scraper instances.
"""

from typing import Dict, Any, Optional

from infrastructure.logging import logger
from infrastructure.config import config
from services.scraping.scraper_service import ScraperService
from services.scraping.requests_scraper import RequestsScraper
from services.scraping.puppeteer_scraper import PuppeteerScraper
from services.scraping.adaptive_scraper import AdaptiveScraper
from services.scraping.puppeteer_pool import PuppeteerPool


class ScraperFactory:
    """
    Factory for creating scraper instances.
    """

    # Singleton instances
    _instances: Dict[str, ScraperService] = {}
    _puppeteer_pool: Optional[PuppeteerPool] = None

    @classmethod
    def create_scraper(cls, scraper_type: str = "adaptive", config_options: Optional[Dict[str, Any]] = None) -> ScraperService:
        """
        Create a scraper instance.

        Args:
            scraper_type: Type of scraper to create ("requests", "puppeteer", "adaptive")
            config_options: Configuration options for the scraper

        Returns:
            Scraper instance implementing ScraperService
        """
        # Use singleton pattern for efficiency
        if scraper_type in cls._instances:
            return cls._instances[scraper_type]
            
        # Get configuration
        if config_options is None:
            config_options = {}
            
        # Create shared puppeteer pool if needed
        if cls._puppeteer_pool is None and scraper_type in ["puppeteer", "adaptive"]:
            cls._puppeteer_pool = PuppeteerPool()
            
        # Create scraper instance
        scraper: ScraperService
        
        if scraper_type == "requests":
            scraper = RequestsScraper(
                cache_ttl=config_options.get("cache_ttl", config.get("CACHE.ttl.page_content", 604800))
            )
        elif scraper_type == "puppeteer":
            scraper = PuppeteerScraper(
                pool=cls._puppeteer_pool,
                cache_ttl=config_options.get("cache_ttl", config.get("CACHE.ttl.page_content", 604800))
            )
        elif scraper_type == "adaptive":
            scraper = AdaptiveScraper(
                cache_ttl=config_options.get("cache_ttl", config.get("CACHE.ttl.page_content", 604800))
            )
        else:
            logger.warning(f"Unknown scraper type: {scraper_type}, falling back to adaptive scraper")
            scraper = AdaptiveScraper(
                cache_ttl=config_options.get("cache_ttl", config.get("CACHE.ttl.page_content", 604800))
            )
            
        # Store instance for reuse
        cls._instances[scraper_type] = scraper
        
        return scraper

    @classmethod
    def get_puppeteer_pool(cls) -> PuppeteerPool:
        """
        Get the shared puppeteer pool.

        Returns:
            Puppeteer pool instance
        """
        if cls._puppeteer_pool is None:
            cls._puppeteer_pool = PuppeteerPool()
            
        return cls._puppeteer_pool

    @classmethod
    async def close_all(cls) -> None:
        """
        Close all scraper instances and resources.
        Should be called when shutting down the application.
        """
        # Close puppeteer pool if it exists
        if cls._puppeteer_pool is not None:
            await cls._puppeteer_pool.close_all()
            cls._puppeteer_pool = None
            
        # Clear instances
        cls._instances = {}
