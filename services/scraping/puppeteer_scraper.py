"""
Puppeteer-based scraper implementation.
"""

import asyncio
from typing import Dict, Any, Optional

from services.scraping.base_scraper import BaseScraper
from services.scraping.puppeteer_pool import PuppeteerPool


class PuppeteerScraper(BaseScraper):
    """
    Puppeteer-based scraper implementation.
    Uses Puppeteer for JavaScript-heavy websites.
    """

    def __init__(self, pool: PuppeteerPool = None, cache_ttl: int = 604800):
        """
        Initialize the Puppeteer scraper.

        Args:
            pool: Puppeteer browser pool
            cache_ttl: Cache TTL in seconds (default: 1 week)
        """
        super().__init__(name="puppeteer", cache_ttl=cache_ttl)
        self.pool = pool or PuppeteerPool()

    async def _scrape_url_impl(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Scrape a URL using Puppeteer.

        Args:
            url: URL to scrape
            timeout: Timeout in seconds

        Returns:
            Dictionary with HTML content and metadata or None if failed
        """
        browser = None

        try:
            # Get browser from pool
            browser = await self.pool.get_browser()

            page = None
            try:
                page = await browser.newPage()

                # Configure request interception to block unnecessary resources
                try:
                    await page.setRequestInterception(True)

                    # Define request handler
                    async def request_handler(req):
                        try:
                            if req.resourceType in ['stylesheet', 'font', 'image']:
                                await req.abort()
                            else:
                                await req.continue_()
                        except Exception as e:
                            self.logger.error(f"Error in request handler: {str(e)}")
                            # Try to continue the request in case of error
                            try:
                                await req.continue_()
                            except:
                                pass

                    page.on('request', lambda req: asyncio.ensure_future(request_handler(req)))
                except Exception as e:
                    self.logger.error(f"Error configuring request interception: {str(e)}")

                # Configure timeout and navigation
                try:
                    await page.setDefaultNavigationTimeout(timeout * 1000)
                except Exception as e:
                    self.logger.error(f"Error configuring timeout: {str(e)}")

                # Navigate to the page
                try:
                    await page.goto(url, {'waitUntil': 'domcontentloaded', 'timeout': timeout * 1000})
                except Exception as e:
                    self.logger.error(f"Error navigating to {url}: {str(e)}")
                    # Try to load a blank page in case of error
                    try:
                        await page.goto('about:blank')
                    except:
                        pass

                # Wait a bit for dynamic content to load
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error initializing page: {str(e)}")
                return None

            # Extract content and metadata
            html = "<html><body>Error</body></html>"
            title = ""
            description = ""

            if page:  # Check if page was successfully initialized
                try:
                    html = await page.content()

                    # Use try/except for each operation that might fail
                    try:
                        title = await page.evaluate('() => document.title || ""')
                    except Exception as e:
                        self.logger.error(f"Error getting title: {str(e)}")
                        title = ""

                    try:
                        description = await page.evaluate('''
                            () => {
                                const metaDesc = document.querySelector('meta[name="description"]');
                                const ogDesc = document.querySelector('meta[property="og:description"]');
                                return (metaDesc && metaDesc.getAttribute('content')) ||
                                       (ogDesc && ogDesc.getAttribute('content')) || '';
                            }
                        ''')
                    except Exception as e:
                        self.logger.error(f"Error getting description: {str(e)}")
                        description = ""
                except Exception as e:
                    self.logger.error(f"Error extracting content: {str(e)}")
                    html = "<html><body>Error</body></html>"
                    title = ""
                    description = ""

            if page:  # Check if page was successfully initialized
                try:
                    await page.close()
                except Exception as e:
                    self.logger.error(f"Error closing page: {str(e)}")

            return {
                'html': html,
                'title': title,
                'description': description,
                'method': 'puppeteer'
            }
        except Exception as e:
            self.logger.error(f"Puppeteer method failed for {url}: {str(e)}")
            return None
        finally:
            # Always return the browser to the pool
            if browser:
                await self.pool.release_browser(browser)
