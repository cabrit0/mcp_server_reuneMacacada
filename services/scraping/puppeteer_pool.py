"""
Pool of Puppeteer browser instances for efficient web scraping.
"""

import asyncio
from typing import Dict, List, Optional, Set, Tuple
from pyppeteer import launch
from pyppeteer.browser import Browser
from pyppeteer.page import Page

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
                    self.logger.debug(f"Reusing existing browser from pool (total: {len(self.browsers)})")
                    return browser

            # Create new browser if not exceeding the limit
            if len(self.browsers) < self.max_instances:
                browser = await self._create_browser()
                self.browsers.append(browser)
                self.in_use.add(browser)
                self.last_used[browser] = asyncio.get_event_loop().time()
                self.logger.debug(f"Created new browser (total: {len(self.browsers)})")
                return browser

            # Wait until a browser is available
            self.logger.debug(f"Waiting for a browser to become available (max: {self.max_instances})")
            wait_start = asyncio.get_event_loop().time()

            while True:
                await asyncio.sleep(0.5)

                # Check if any browsers have become available
                for browser in self.browsers:
                    if browser not in self.in_use:
                        self.in_use.add(browser)
                        self.last_used[browser] = asyncio.get_event_loop().time()
                        wait_time = asyncio.get_event_loop().time() - wait_start
                        self.logger.debug(f"Browser became available after {wait_time:.2f}s")
                        return browser

                # Check if we've been waiting too long
                wait_time = asyncio.get_event_loop().time() - wait_start
                if wait_time > 30:  # 30 seconds timeout
                    self.logger.warning(f"Waited {wait_time:.2f}s for a browser, forcing cleanup")
                    # Force cleanup of idle browsers
                    closed_count = await self.cleanup_idle_browsers(force=True)
                    if closed_count > 0:
                        self.logger.info(f"Forcibly closed {closed_count} browsers")

                    # If still at max capacity, create a new browser anyway
                    if len(self.browsers) >= self.max_instances:
                        self.logger.warning(f"Exceeding max_instances ({self.max_instances}) due to timeout")
                        browser = await self._create_browser()
                        self.browsers.append(browser)
                        self.in_use.add(browser)
                        self.last_used[browser] = asyncio.get_event_loop().time()
                        return browser

    async def _create_browser(self) -> Browser:
        """
        Create a new browser instance with optimized settings for performance.

        Returns:
            Puppeteer browser instance
        """
        self.logger.debug("Creating new browser instance with optimized settings")

        # Enhanced launch arguments for better performance and stability
        args = [
            # Security settings
            '--no-sandbox',
            '--disable-setuid-sandbox',

            # Performance optimizations
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-accelerated-2d-canvas',
            '--disable-infobars',
            '--disable-extensions',
            '--disable-component-extensions-with-background-pages',
            '--disable-default-apps',
            '--disable-popup-blocking',
            '--disable-sync',
            '--disable-translate',
            '--disable-background-networking',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-breakpad',
            '--disable-client-side-phishing-detection',
            '--disable-hang-monitor',
            '--disable-prompt-on-repost',

            # Memory optimizations
            '--disable-features=site-per-process,TranslateUI,BlinkGenPropertyTrees',
            '--disable-ipc-flooding-protection',
            '--single-process',  # Use single process to reduce memory usage

            # Network optimizations
            '--disable-features=NetworkService,NetworkServiceInProcess',

            # Window settings
            '--window-size=1366,768',
            '--hide-scrollbars',
            '--mute-audio'
        ]

        # Get Chrome executable path and download settings from config
        scraping_config = config.get_section("SCRAPING")
        puppeteer_config = scraping_config.get("puppeteer", {})
        executable_path = puppeteer_config.get("executable_path")
        download_chromium = puppeteer_config.get("download_chromium", False)

        # Set environment variable to skip Chromium download if needed
        if not download_chromium:
            import os
            os.environ["PYPPETEER_SKIP_CHROMIUM_DOWNLOAD"] = "1"
            self.logger.info("Skipping Chromium download (PYPPETEER_SKIP_CHROMIUM_DOWNLOAD=1)")

        # Enhanced launch options for better performance
        launch_options = {
            "headless": True,
            "args": args,
            "ignoreHTTPSErrors": True,
            "handleSIGINT": False,  # Don't handle SIGINT to avoid browser hanging
            "handleSIGTERM": False,  # Don't handle SIGTERM to avoid browser hanging
            "handleSIGHUP": False,   # Don't handle SIGHUP to avoid browser hanging
            "dumpio": False,         # Don't dump IO to avoid memory leaks
        }

        # Add executable path if specified
        if executable_path:
            self.logger.info(f"Using Chrome executable at: {executable_path}")
            launch_options["executablePath"] = executable_path
        else:
            self.logger.info("Using default Chrome executable path")

        # Launch browser with retry logic
        max_retries = 3
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                browser = await launch(**launch_options)
                self.logger.info(f"Successfully launched browser (attempt {retry_count + 1}/{max_retries})")

                # Apply stealth mode if enabled
                if self.stealth_mode:
                    await self._apply_stealth_mode(browser)

                return browser
            except Exception as e:
                last_error = e
                retry_count += 1
                self.logger.warning(f"Failed to launch browser (attempt {retry_count}/{max_retries}): {str(e)}")

                # Wait before retrying
                await asyncio.sleep(1)

        # If we get here, all retries failed
        self.logger.error(f"All {max_retries} attempts to launch browser failed")

        # Try with system Chrome as fallback
        if not executable_path:
            return await self._try_system_chrome_fallback(args)
        else:
            # Re-raise the last exception if executable_path was specified
            raise last_error

    async def _try_system_chrome_fallback(self, args):
        """
        Try to launch browser using system Chrome installations as fallback.

        Args:
            args: Chrome launch arguments

        Returns:
            Browser instance if successful

        Raises:
            Exception if all fallbacks fail
        """
        # Common Chrome locations
        chrome_paths = [
            # Windows
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            # Linux
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            # macOS
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ]

        for path in chrome_paths:
            try:
                self.logger.info(f"Trying Chrome at: {path}")
                browser = await launch(
                    headless=True,
                    args=args,
                    ignoreHTTPSErrors=True,
                    executablePath=path,
                    handleSIGINT=False,
                    handleSIGTERM=False,
                    handleSIGHUP=False,
                    dumpio=False
                )
                self.logger.info(f"Successfully launched Chrome from: {path}")

                # Apply stealth mode if enabled
                if self.stealth_mode:
                    await self._apply_stealth_mode(browser)

                return browser
            except Exception as inner_e:
                self.logger.warning(f"Failed to launch Chrome from {path}: {str(inner_e)}")

        # If we get here, all fallbacks failed
        raise Exception("Failed to launch browser with all available Chrome installations")

    async def _apply_stealth_mode(self, browser):
        """
        Apply stealth mode to a browser instance.

        Args:
            browser: Browser instance to apply stealth mode to
        """
        try:
            # Check if pyppeteer_stealth is installed
            try:
                # Import here to avoid dependency if not used
                from pyppeteer_stealth import stealth
                stealth_available = True
            except ImportError:
                stealth_available = False
                self.logger.warning("pyppeteer_stealth module not found. Stealth mode will be disabled.")
                self.stealth_mode = False
                return

            if stealth_available:
                # Create a page for stealth setup
                try:
                    page = await browser.newPage()
                    if not page:
                        self.logger.warning("Failed to create page for stealth mode: page is None")
                    else:
                        await stealth(page)
                        await page.close()
                        self.logger.debug("Applied stealth mode to browser")
                except Exception as page_error:
                    self.logger.warning(f"Failed to create or configure page for stealth mode: {str(page_error)}")
        except Exception as e:
            self.logger.warning(f"Failed to apply stealth mode: {str(e)}")
            self.stealth_mode = False  # Disable stealth mode on failure

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

    async def cleanup_idle_browsers(self, force: bool = False) -> int:
        """
        Close idle browsers to free up memory.

        Args:
            force: If True, close browsers even if they haven't reached max_idle_time
                  but have been idle for at least 10 seconds

        Returns:
            Number of browsers closed
        """
        current_time = asyncio.get_event_loop().time()
        closed_count = 0
        min_idle_time = 10  # Minimum idle time in seconds for forced cleanup

        async with self.lock:
            for browser in list(self.browsers):
                idle_time = current_time - self.last_used.get(browser, 0)

                # Close if browser is not in use and either:
                # 1. It has exceeded max_idle_time, or
                # 2. Force is True and it has been idle for at least min_idle_time
                if (browser not in self.in_use and
                    (idle_time > self.max_idle_time or (force and idle_time > min_idle_time))):
                    try:
                        await browser.close()
                        self.browsers.remove(browser)
                        self.last_used.pop(browser, None)
                        closed_count += 1

                        if idle_time > self.max_idle_time:
                            self.logger.info(f"Closed idle browser instance (idle for {idle_time:.1f}s)")
                        else:
                            self.logger.info(f"Force closed browser instance (idle for {idle_time:.1f}s)")
                    except Exception as e:
                        self.logger.error(f"Error closing browser: {str(e)}")
                        # Remove from pool anyway to avoid keeping broken browsers
                        try:
                            self.browsers.remove(browser)
                            self.last_used.pop(browser, None)
                        except:
                            pass

        return closed_count

    async def create_optimized_page(self, browser: Browser) -> Optional[Page]:
        """
        Create and configure an optimized page for web scraping.
        Includes retry logic and better error handling.

        Args:
            browser: Browser instance to create page in

        Returns:
            Configured Page instance or None if failed
        """
        # Retry logic for page creation
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Check if browser is still connected
                if not browser or not hasattr(browser, 'newPage'):
                    self.logger.error("Browser instance is invalid or disconnected")
                    return None

                # Create a new page
                page = await browser.newPage()
                if not page:
                    raise Exception("browser.newPage() returned None")

                # Set a realistic user agent
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
                ]
                import random

                # Apply page configurations with proper error handling
                try:
                    if hasattr(page, 'setUserAgent'):
                        await page.setUserAgent(random.choice(user_agents))
                except Exception as e:
                    self.logger.warning(f"Error setting user agent: {str(e)}")

                # Set viewport
                try:
                    if hasattr(page, 'setViewport'):
                        await page.setViewport({'width': 1366, 'height': 768})
                except Exception as e:
                    self.logger.warning(f"Error setting viewport: {str(e)}")

                # Disable cache for fresh content
                try:
                    if hasattr(page, 'setCacheEnabled'):
                        await page.setCacheEnabled(False)
                except Exception as e:
                    self.logger.warning(f"Error disabling cache: {str(e)}")

                # Set timeouts
                try:
                    if hasattr(page, 'setDefaultNavigationTimeout'):
                        await page.setDefaultNavigationTimeout(30000)  # 30 seconds
                    if hasattr(page, 'setDefaultTimeout'):
                        await page.setDefaultTimeout(30000)  # 30 seconds
                except Exception as e:
                    self.logger.warning(f"Error configuring timeout: {str(e)}")

                # Optimize resource loading
                try:
                    # Intercept requests to block unnecessary resources
                    if hasattr(page, 'setRequestInterception'):
                        await page.setRequestInterception(True)

                        async def intercept_request(request):
                            try:
                                # Block unnecessary resource types to improve performance
                                if hasattr(request, 'resourceType'):
                                    resource_type = request.resourceType.lower()
                                    blocked_types = ['image', 'media', 'font', 'stylesheet', 'other']

                                    if resource_type in blocked_types:
                                        await request.abort()
                                    else:
                                        await request.continue_()
                                else:
                                    await request.continue_()
                            except Exception as req_err:
                                self.logger.warning(f"Error in request interception: {str(req_err)}")
                                try:
                                    await request.continue_()
                                except:
                                    pass

                        page.on('request', lambda req: asyncio.ensure_future(intercept_request(req)))
                except Exception as e:
                    self.logger.warning(f"Error setting up request interception: {str(e)}")
                    # Disable request interception if it fails
                    try:
                        if hasattr(page, 'setRequestInterception'):
                            await page.setRequestInterception(False)
                    except:
                        pass

                # Apply stealth mode if available
                if self.stealth_mode:
                    try:
                        from pyppeteer_stealth import stealth
                        await stealth(page)
                        self.logger.debug("Applied stealth mode to page")
                    except ImportError:
                        self.logger.warning("pyppeteer_stealth not available, skipping stealth mode")
                    except Exception as e:
                        self.logger.warning(f"Error applying stealth mode to page: {str(e)}")

                self.logger.debug("Successfully created and configured optimized page")
                return page

            except Exception as e:
                retry_count += 1
                self.logger.warning(f"Failed to create page (attempt {retry_count}/{max_retries}): {str(e)}")

                if retry_count < max_retries:
                    # Wait before retrying
                    await asyncio.sleep(1)
                else:
                    self.logger.error(f"All {max_retries} attempts to create page failed")
                    return None

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
