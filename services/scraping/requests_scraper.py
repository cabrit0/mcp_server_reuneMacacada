"""
Requests-based scraper implementation.
"""

import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

from services.scraping.base_scraper import BaseScraper


class RequestsScraper(BaseScraper):
    """
    Requests-based scraper implementation.
    Uses aiohttp for simple websites that don't require JavaScript.
    """

    def __init__(self, cache_ttl: int = 604800):
        """
        Initialize the Requests scraper.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 week)
        """
        super().__init__(name="requests", cache_ttl=cache_ttl)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

    async def _scrape_url_impl(self, url: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Scrape a URL using aiohttp.

        Args:
            url: URL to scrape
            timeout: Timeout in seconds

        Returns:
            Dictionary with HTML content and metadata or None if failed
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout, headers=self.headers) as response:
                    if response.status != 200:
                        self.logger.debug(f"Simple method failed for {url}: Status {response.status}")
                        return None

                    html = await response.text()

                    # Check if main content is present
                    # This helps detect sites that require JavaScript
                    soup = BeautifulSoup(html, 'html.parser')

                    has_main_content = bool(
                        soup.find('main') or
                        soup.find(id='content') or
                        soup.find(class_='content') or
                        soup.find('article') or
                        len(soup.get_text()) > 1000
                    )

                    if not has_main_content:
                        self.logger.debug(f"Simple method didn't find main content in {url}")
                        return None

                    # Extract basic metadata
                    title = soup.title.text.strip() if soup.title else ''
                    description = ''

                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc and meta_desc.get('content'):
                        description = meta_desc['content']
                    else:
                        og_desc = soup.find('meta', attrs={'property': 'og:description'})
                        if og_desc and og_desc.get('content'):
                            description = og_desc['content']

                    return {
                        'html': html,
                        'title': title,
                        'description': description,
                        'method': 'requests'
                    }
        except Exception as e:
            self.logger.debug(f"Simple method failed for {url}: {str(e)}")
            return None
