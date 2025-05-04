"""
Base implementation for scrapers.
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from infrastructure.logging import logger
from infrastructure.cache import cache
from services.scraping.scraper_service import ScraperService


class BaseScraper(ScraperService):
    """
    Base implementation for scrapers.
    Provides common functionality for all scraper implementations.
    """

    def __init__(self, name: str, cache_ttl: int = 604800):
        """
        Initialize the scraper.

        Args:
            name: Scraper name
            cache_ttl: Cache TTL in seconds (default: 1 week)
        """
        self.name = name
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger(f"scraper.{name}")

    @abstractmethod
    async def _scrape_url_impl(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Implementation-specific scraping method.
        Must be implemented by subclasses.

        Args:
            url: URL to scrape
            timeout: Timeout in seconds

        Returns:
            Dictionary with HTML content and metadata or None if failed
        """
        pass

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
        # Check cache first if enabled
        if cache_enabled:
            cache_key = f"page:{url}"
            cached_content = cache.get(cache_key)
            if cached_content:
                self.logger.debug(f"Using cached content for {url}")
                return cached_content

        try:
            # Call implementation-specific scraping method
            result = await self._scrape_url_impl(url, timeout)

            if not result or not result.get('html'):
                self.logger.warning(f"Scraping failed for {url}")
                return None

            content = result['html']

            # Store content in cache if successful and cache is enabled
            if content and cache_enabled:
                cache.setex(cache_key, self.cache_ttl, content)
                self.logger.debug(f"Cached content for {url} (method: {self.name})")

            return content
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None

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
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract title
            title = soup.title.text.strip() if soup.title else f"Resource about {topic}"
            if not title or len(title) < 3:
                title = f"Resource about {topic}"

            # Extract description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc['content'] if meta_desc and 'content' in meta_desc.attrs else ''

            if not description or len(description) < 10:
                # Try to extract the first paragraph
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.text.strip()
                    if len(text) > 50:
                        description = text[:300] + '...' if len(text) > 300 else text
                        break

            if not description or len(description) < 10:
                description = f"A resource about {topic}"

            # Determine content type
            content_type = self._determine_content_type(soup, url)

            return {
                'title': title,
                'url': url,
                'description': description,
                'type': content_type
            }
        except Exception as e:
            self.logger.warning(f"Error extracting metadata from {url}: {str(e)}")
            return {
                'title': f"Resource about {topic}",
                'url': url,
                'description': f"A resource about {topic}",
                'type': 'unknown'
            }

    def _determine_content_type(self, soup: 'BeautifulSoup', url: str) -> str:
        """
        Determine content type based on URL and HTML content.

        Args:
            soup: BeautifulSoup object
            url: URL of the content

        Returns:
            Content type (article, video, documentation, etc.)
        """
        domain = urlparse(url).netloc.lower()

        # Check video platforms
        if any(platform in domain for platform in ['youtube.com', 'vimeo.com', 'dailymotion.com']):
            return 'video'

        # Check documentation sites
        if any(platform in domain for platform in ['docs.', 'documentation.', '.dev/docs', 'developer.']):
            return 'documentation'

        # Check exercise/practice sites
        if any(platform in domain for platform in ['exercism.io', 'leetcode.com', 'hackerrank.com', 'codewars.com']):
            return 'exercise'

        # Check for video elements on the page
        video_elements = soup.select('video, iframe[src*="youtube"], iframe[src*="vimeo"]')
        if video_elements:
            return 'video'

        # Check for code elements or code-like content
        code_elements = soup.select('code, pre, .code, .codehilite, .highlight')
        if code_elements:
            return 'tutorial'

        # Check for quiz or exercise content
        if soup.body:
            text = soup.body.get_text().lower()
            has_quiz = (
                ('quiz' in text or 'exercise' in text or 'practice' in text) and
                ('question' in text or 'answer' in text or 'solution' in text)
            )
            if has_quiz:
                return 'quiz'

        # Default to article
        return 'article'

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
        # Default result in case of failure
        default_result = {
            'title': f"Resource about {topic}",
            'url': url,
            'description': f"A resource about {topic}",
            'type': 'unknown'
        }

        # Check cache first
        cache_key = f"resource:{url}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached resource for {url}")
            return cached_result

        try:
            # Scrape the URL
            html_content = await self.scrape_url(url, timeout)

            # If no content was returned, return default result
            if not html_content:
                self.logger.warning(f"No content returned for {url}")
                return default_result

            # Extract metadata
            result = self.extract_metadata_from_html(html_content, url, topic)

            # Cache the result
            cache.setex(cache_key, self.cache_ttl, result)

            return result
        except Exception as e:
            self.logger.error(f"Error getting page content for {url}: {str(e)}")
            return default_result
