"""
Abstract interface for the scraper service.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ScraperService(ABC):
    """
    Abstract interface for scraper services.
    Defines the methods that all scraper implementations must provide.
    """

    @abstractmethod
    async def scrape(
        self,
        url: str,
        topic: str,
        timeout: int = 10,
        language: str = "pt"
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL.

        Args:
            url: The URL to scrape
            topic: The topic being searched for (for context)
            timeout: Timeout in seconds
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            Dictionary with scraped data (title, description, type, etc.)
        """
        pass

    @abstractmethod
    def determine_content_type(self, url: str, html_content: Optional[str] = None) -> str:
        """
        Determine the type of content based on the URL and content.

        Args:
            url: The URL of the content
            html_content: Optional HTML content (if already scraped)

        Returns:
            Content type (e.g., 'article', 'video', 'documentation', etc.)
        """
        pass

    @abstractmethod
    def estimate_read_time(self, content_length: int) -> int:
        """
        Estimate reading time in minutes based on content length.

        Args:
            content_length: Length of the content in characters

        Returns:
            Estimated reading time in minutes
        """
        pass
