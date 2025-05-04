"""
Optimized implementation of the scraper service.
"""

import asyncio
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from infrastructure.logging import logger
from infrastructure.cache import cache
from core.content_sourcing.scraper_service import ScraperService
from services.scraping import scraper


class OptimizedScraperService(ScraperService):
    """
    Optimized implementation of the scraper service.
    Uses the optimized scraper from services.scraping to scrape content.
    """

    def __init__(self):
        """Initialize the optimized scraper service."""
        self.logger = logger.get_logger("content_sourcing.scraper.optimized")
        self.logger.info("Initialized OptimizedScraperService")

    async def scrape(
        self,
        url: str,
        topic: str,
        timeout: int = 10,
        language: str = "pt"
    ) -> Dict[str, Any]:
        """
        Scrape content from a URL using the optimized scraper.

        Args:
            url: The URL to scrape
            topic: The topic being searched for (for context)
            timeout: Timeout in seconds
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            Dictionary with scraped data (title, description, type, etc.)
        """
        # Check cache first
        cache_key = f"resource:{url}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached resource for {url}")
            return cached_result

        # Default result in case of failure
        default_result = {
            'title': f"Resource about {topic}",
            'url': url,
            'description': f"A resource about {topic}",
            'type': self.determine_content_type(url),
            'readTime': None,
            'duration': None,
            'thumbnail': None
        }

        # Use a strict timeout to avoid getting stuck
        try:
            # Create a task with timeout
            scraping_task = asyncio.create_task(scraper.scrape_url(url, timeout))

            # Wait for the task with timeout
            try:
                html_content = await asyncio.wait_for(scraping_task, timeout=timeout)
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout scraping {url} after {timeout} seconds")
                return default_result

            # If no content was returned, return default result
            if not html_content:
                self.logger.warning(f"No content returned for {url}")
                return default_result

            # Extract metadata
            result = scraper.extract_metadata_from_html(html_content, url, topic)
            
            # Determine content type if not already set
            if 'type' not in result or not result['type']:
                result['type'] = self.determine_content_type(url, html_content)
                
            # Estimate read time if not already set
            if ('readTime' not in result or not result['readTime']) and 'content' in result:
                content_length = len(result.get('content', ''))
                if content_length > 0:
                    read_time = self.estimate_read_time(content_length)
                    if result['type'] == 'article':
                        result['readTime'] = read_time
                    elif result['type'] == 'video':
                        result['duration'] = read_time

            # Cache the result
            cache.setex(cache_key, 604800, result)  # 1 week
            self.logger.debug(f"Cached scraped content for {url}")

            return result

        except Exception as e:
            self.logger.warning(f"Error scraping {url}: {str(e)}")
            return default_result

    def determine_content_type(self, url: str, html_content: Optional[str] = None) -> str:
        """
        Determine the type of content based on the URL and content.

        Args:
            url: The URL of the content
            html_content: Optional HTML content (if already scraped)

        Returns:
            Content type (e.g., 'article', 'video', 'documentation', etc.)
        """
        domain = urlparse(url).netloc.lower()

        # Check for video platforms
        if any(platform in domain for platform in ['youtube.com', 'vimeo.com', 'dailymotion.com']):
            return 'video'

        # Check for documentation sites
        if any(platform in domain for platform in ['docs.', 'documentation.', '.dev/docs', 'developer.']):
            return 'documentation'

        # Check for exercise/practice sites
        if any(platform in domain for platform in ['exercism.io', 'leetcode.com', 'hackerrank.com', 'codewars.com']):
            return 'exercise'

        # If we have HTML content, check for video elements
        if html_content:
            try:
                soup = BeautifulSoup(html_content, 'lxml')
                if soup.find('video') or soup.find('iframe', src=re.compile(r'(youtube|vimeo)')):
                    return 'video'
            except Exception as e:
                self.logger.warning(f"Error parsing HTML content: {str(e)}")

        # Default to article
        return 'article'

    def estimate_read_time(self, content_length: int) -> int:
        """
        Estimate reading time in minutes based on content length.

        Args:
            content_length: Length of the content in characters

        Returns:
            Estimated reading time in minutes
        """
        # Average reading speed: ~200 words per minute
        # Average word length: ~5 characters
        words = content_length / 5
        minutes = round(words / 200)
        return max(1, minutes)  # Minimum 1 minute
