# This file is part of the MCP Server package.

from services.scraping.scraper_service import ScraperService
from services.scraping.scraper_factory import ScraperFactory

# Create a global scraper instance
scraper: ScraperService = ScraperFactory.create_scraper("adaptive")

__all__ = ["scraper", "ScraperService", "ScraperFactory"]
