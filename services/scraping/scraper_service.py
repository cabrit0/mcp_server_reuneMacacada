"""
Abstract interface for the scraping system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ScraperService(ABC):
    """
    Abstract interface for scraper services.
    Defines the methods that all scraper implementations must provide.
    """

    @abstractmethod
    async def scrape_url(self, url: str, timeout: int = 30, cache_enabled: bool = True) -> Optional[str]:
        """
        Scrape content from a URL.

        Args:
            url: URL to scrape
            timeout: Timeout in seconds
            cache_enabled: Whether to use cache

        Returns:
            HTML content as string or None if failed
        """
        pass

    @abstractmethod
    def extract_metadata_from_html(self, html_content: str, url: str, topic: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML content.

        Args:
            html_content: HTML content
            url: URL of the content
            topic: Topic being searched for

        Returns:
            Dictionary with title, description, content type, etc.
        """
        pass

    @abstractmethod
    async def get_page_content(self, url: str, topic: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Get content from a page with metadata.
        This is a high-level method that combines scrape_url and extract_metadata_from_html.

        Args:
            url: URL to scrape
            topic: Topic being searched for
            timeout: Timeout in seconds

        Returns:
            Dictionary with title, description, content type, etc.
        """
        pass
