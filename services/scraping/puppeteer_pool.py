"""
Pool of Puppeteer browser instances for efficient web scraping.
"""

import asyncio
from typing import Dict, List, Optional, Set
from pyppeteer import launch
from pyppeteer.browser import Browser

from infrastructure.logging import logger
from infrastructure.config import config


class PuppeteerPool:
    """
    Pool of Puppeteer browser instances for efficient web scraping.
    """

    def __init__(self, max_instances: int = None, max_idle_time: int = None):
        """
        Initialize the Puppeteer browser pool.

        Args:
            max_instances: Maximum number of browser instances
            max_idle_time: Maximum idle time in seconds
        """
        # Get configuration from settings
        scraping_config = config.get_section("SCRAPING")
        puppeteer_config = scraping_config.get("puppeteer", {})

        self.max_instances = max_instances or puppeteer_config.get("max_instances", 3)
        self.max_idle_time = max_idle_time or puppeteer_config.get("max_idle_time", 300)  # seconds
        self.stealth_mode = puppeteer_config.get("stealth", True)

        self.browsers: List[Browser] = []
        self.in_use: Set[Browser] = set()
        self.lock = asyncio.Lock()
        self.last_used: Dict[Browser, float] = {}
        self.logger = logger.get_logger("scraper.puppeteer_pool")
        
        self.logger.info(f"Initialized PuppeteerPool with max_instances={self.max_instances}, max_idle_time={self.max_idle_time}s")

    async def get_browser(self) -> Browser:
        """
        Get a browser instance from the pool.

        Returns:
            Puppeteer browser instance
        """
        async with self.lock:
            # Try to reuse an existing browser
            for browser in self.browsers:
                if browser not in self.in_use:
                    self.in_use.add(browser)
                    self.last_used[browser] = asyncio.get_event_loop().time()
                    return browser
            
            # Create new browser if not exceeding the limit
            if len(self.browsers) < self.max_instances:
                browser = await self._create_browser()
                self.browsers.append(browser)
                self.in_use.add(browser)
                self.last_used[browser] = asyncio.get_event_loop().time()
                return browser
                
            # Wait until a browser is available
            while True:
                await asyncio.sleep(0.5)
                for browser in self.browsers:
                    if browser not in self.in_use:
                        self.in_use.add(browser)
                        self.last_used[browser] = asyncio.get_event_loop().time()
                        return browser

    async def _create_browser(self) -> Browser:
        """
        Create a new browser instance.

        Returns:
            Puppeteer browser instance
        """
        self.logger.debug("Creating new browser instance")
        
        # Launch arguments
        args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            '--disable-infobars',
            '--window-size=1366,768'
        ]
        
        # Launch browser
        browser = await launch(
            headless=True,
            args=args,
            ignoreHTTPSErrors=True
        )
        
        # Apply stealth mode if enabled
        if self.stealth_mode:
            try:
                # Import here to avoid dependency if not used
                from pyppeteer_stealth import stealth
                
                # Create a page for stealth setup
                page = await browser.newPage()
                await stealth(page)
                await page.close()
                
                self.logger.debug("Applied stealth mode to browser")
            except Exception as e:
                self.logger.warning(f"Failed to apply stealth mode: {str(e)}")
        
        return browser

    async def release_browser(self, browser: Browser) -> None:
        """
        Release a browser back to the pool.

        Args:
            browser: Browser instance to release
        """
        async with self.lock:
            if browser in self.in_use:
                self.in_use.remove(browser)
                self.last_used[browser] = asyncio.get_event_loop().time()
                self.logger.debug("Released browser back to pool")

    async def cleanup_idle_browsers(self) -> int:
        """
        Close idle browsers to free up memory.

        Returns:
            Number of browsers closed
        """
        current_time = asyncio.get_event_loop().time()
        closed_count = 0
        
        async with self.lock:
            for browser in list(self.browsers):
                if (browser not in self.in_use and 
                    current_time - self.last_used.get(browser, 0) > self.max_idle_time):
                    await browser.close()
                    self.browsers.remove(browser)
                    self.last_used.pop(browser, None)
                    closed_count += 1
                    self.logger.info("Closed idle browser instance")
        
        return closed_count

    async def close_all(self) -> None:
        """Close all browsers when shutting down the application."""
        async with self.lock:
            for browser in self.browsers:
                try:
                    await browser.close()
                    self.logger.debug("Closed browser during shutdown")
                except Exception as e:
                    self.logger.error(f"Error closing browser: {str(e)}")
            
            self.browsers = []
            self.in_use = set()
            self.last_used = {}
            self.logger.info("Closed all browser instances")
