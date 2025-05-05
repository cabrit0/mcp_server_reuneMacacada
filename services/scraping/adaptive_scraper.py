"""
Adaptive scraper that automatically chooses the most efficient method for each website.
"""

import time
import random
import asyncio
from typing import Dict, Any, Optional, Set
from urllib.parse import urlparse

from infrastructure.logging import logger
from infrastructure.cache import cache
from infrastructure.config import config
from services.scraping.base_scraper import BaseScraper
from services.scraping.requests_scraper import RequestsScraper
from services.scraping.puppeteer_scraper import PuppeteerScraper
from services.scraping.puppeteer_pool import PuppeteerPool


class AdaptiveScraper(BaseScraper):
    """
    Adaptive scraper that automatically chooses the most efficient method for each website.
    """

    # Domains that are known to require JavaScript
    JS_REQUIRED_DOMAINS: Set[str] = {
        # Social media and video platforms
        'youtube.com', 'youtu.be',
        'twitter.com', 'x.com',
        'facebook.com', 'fb.com',
        'instagram.com',
        'linkedin.com',
        'tiktok.com',
        'pinterest.com',

        # Developer platforms
        'github.com',
        'stackoverflow.com',
        'medium.com',
        'dev.to',
        'reddit.com',
        'hashnode.com',

        # Documentation sites
        'docs.microsoft.com', 'learn.microsoft.com',
        'developer.mozilla.org',
        'reactjs.org', 'react.dev',
        'vuejs.org', 'vue.dev',
        'angular.io',
        'flutter.dev',
        'kotlinlang.org',
        'tensorflow.org',
        'pytorch.org',
        'aws.amazon.com',
        'cloud.google.com',
        'azure.microsoft.com',

        # Learning platforms
        'coursera.org',
        'udemy.com',
        'edx.org',
        'khanacademy.org',
        'freecodecamp.org',
        'codecademy.com',
        'pluralsight.com',
        'datacamp.com',

        # News sites
        'nytimes.com',
        'theguardian.com',
        'bbc.com',
        'cnn.com',
        'washingtonpost.com',

        # Other common sites that need JavaScript
        'notion.so',
        'airtable.com',
        'trello.com',
        'figma.com',
        'canva.com',
        'vercel.com',
        'netlify.com',
        'heroku.com',
        'digitalocean.com'
    }

    def __init__(self, cache_ttl: int = 604800):
        """
        Initialize the adaptive scraper.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 week)
        """
        super().__init__(name="adaptive", cache_ttl=cache_ttl)

        # Create puppeteer pool
        self.puppeteer_pool = PuppeteerPool()

        # Create scrapers
        self.requests_scraper = RequestsScraper(cache_ttl=cache_ttl)
        self.puppeteer_scraper = PuppeteerScraper(pool=self.puppeteer_pool, cache_ttl=cache_ttl)

        # Domain method cache
        self.domain_method_cache: Dict[str, Dict[str, Any]] = {}

        # Domain timeout cache - stores adaptive timeouts for each domain
        self.domain_timeout_cache: Dict[str, Dict[str, Any]] = {}

        # Load configuration
        scraping_config = config.get_section("SCRAPING")
        self.default_timeout = scraping_config.get("timeout_default", 12)  # Increased from 8 to 12
        self.min_timeout = scraping_config.get("timeout_min", 5)  # Increased from 3 to 5
        self.max_timeout = scraping_config.get("timeout_max", 20)  # Increased from 15 to 20

        self.logger.info("Initialized AdaptiveScraper with adaptive timeouts and method selection")

    async def _scrape_url_impl(self, url: str, timeout: int = None) -> Optional[Dict[str, Any]]:
        """
        Scrape a URL using the most efficient method with adaptive timeouts.
        Enhanced with better error handling and performance optimizations.

        Args:
            url: URL to scrape
            timeout: Timeout in seconds (if None, uses adaptive timeout)

        Returns:
            Dictionary with HTML content and metadata or None if failed
        """
        # Extract domain from URL
        try:
            domain = urlparse(url).netloc
            if not domain:
                self.logger.warning(f"Invalid URL format: {url}")
                return None

            # Skip known problematic domains
            if any(blocked in domain.lower() for blocked in [
                'facebook.com', 'instagram.com', 'twitter.com', 'x.com',  # Social media with strict scraping policies
                'youtube.com', 'youtu.be',  # Video sites that need special handling
                'linkedin.com',  # Requires login
                'captcha', 'recaptcha'  # Likely to have CAPTCHAs
            ]):
                self.logger.info(f"Skipping known problematic domain: {domain}")
                return None

            # Get adaptive timeout for this domain
            adaptive_timeout = self._get_adaptive_timeout(domain)

            # Use provided timeout if specified, otherwise use adaptive timeout
            effective_timeout = timeout if timeout is not None else adaptive_timeout

            # Ensure minimum timeout
            effective_timeout = max(self.min_timeout, effective_timeout)

            # Record start time for performance tracking
            start_time = time.time()

            # Determine which method to use
            method_to_use = self._get_method_for_domain(domain)

            # Set up a task to track overall timeout
            result = None
            success = False

            try:
                # Try the chosen method with overall timeout protection
                if method_to_use == 'requests':
                    # Try simple method first with shorter timeout
                    requests_timeout = min(effective_timeout, 4)  # Cap at 4 seconds for requests
                    self.logger.debug(f"Trying requests method for {domain} with timeout {requests_timeout}s")

                    # Use asyncio.wait_for to enforce timeout
                    try:
                        requests_task = self.requests_scraper._scrape_url_impl(url, requests_timeout)
                        result = await asyncio.wait_for(requests_task, timeout=requests_timeout + 1)
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Requests method timed out for {domain} after {requests_timeout}s")
                        result = None

                    # If it fails, try Puppeteer
                    if not result:
                        self.logger.debug(f"Simple method failed for {url}, trying Puppeteer")
                        remaining_time = effective_timeout - (time.time() - start_time)
                        puppeteer_timeout = max(self.min_timeout, int(remaining_time))

                        if puppeteer_timeout > 3:  # Only try if we have enough time left
                            try:
                                puppeteer_task = self.puppeteer_scraper._scrape_url_impl(url, puppeteer_timeout)
                                result = await asyncio.wait_for(puppeteer_task, timeout=puppeteer_timeout + 2)

                                # Update cache
                                success = bool(result)
                                self._update_domain_cache(domain, 'puppeteer', success)
                            except asyncio.TimeoutError:
                                self.logger.warning(f"Puppeteer method timed out for {domain} after {puppeteer_timeout}s")
                                result = None
                    else:
                        # Simple method worked
                        success = True
                        self._update_domain_cache(domain, 'requests', True)
                else:
                    # Use Puppeteer directly
                    self.logger.debug(f"Using Puppeteer for {domain} with timeout {effective_timeout}s")
                    try:
                        puppeteer_task = self.puppeteer_scraper._scrape_url_impl(url, effective_timeout)
                        result = await asyncio.wait_for(puppeteer_task, timeout=effective_timeout + 2)

                        # Update cache
                        success = bool(result)
                        self._update_domain_cache(domain, 'puppeteer', success)
                    except asyncio.TimeoutError:
                        self.logger.warning(f"Puppeteer method timed out for {domain} after {effective_timeout}s")
                        result = None
            except Exception as method_error:
                self.logger.error(f"Error using {method_to_use} method for {domain}: {str(method_error)}")
                result = None
                success = False

            # Calculate elapsed time
            elapsed_time = time.time() - start_time

            # Log performance metrics
            if result:
                content_length = len(result.get('content', ''))
                self.logger.debug(
                    f"Scraped {domain} in {elapsed_time:.2f}s using {method_to_use} "
                    f"(content: {content_length} chars)"
                )

            # Update adaptive timeout based on result
            self._update_adaptive_timeout(domain, elapsed_time, success)

            if not result:
                self.logger.warning(f"Failed to scrape {url} with all available methods")
                return None

            return result
        except Exception as e:
            self.logger.error(f"Error in adaptive scraping for {url}: {str(e)}")
            return None

    def _get_adaptive_timeout(self, domain: str) -> int:
        """
        Get the adaptive timeout for a domain based on past performance.

        Args:
            domain: Domain name

        Returns:
            Timeout in seconds
        """
        # Check if we have a cached timeout for this domain
        if domain in self.domain_timeout_cache:
            cache_entry = self.domain_timeout_cache[domain]
            # Cache valid for 1 day
            if time.time() - cache_entry['last_updated'] < 86400:
                return cache_entry['timeout']

        # Default to the configured default timeout
        return self.default_timeout

    def _update_adaptive_timeout(self, domain: str, elapsed_time: float, success: bool) -> None:
        """
        Update the adaptive timeout for a domain based on the result of a scrape.
        Enhanced with better timeout adjustment logic and performance optimizations.

        Args:
            domain: Domain name
            elapsed_time: Time taken for the scrape in seconds
            success: Whether the scrape was successful
        """
        # Ignore extremely short or long times that might be outliers
        if elapsed_time < 0.1 or elapsed_time > 60:
            self.logger.debug(f"Ignoring outlier elapsed time for {domain}: {elapsed_time:.2f}s")
            return

        current_time = time.time()

        if domain not in self.domain_timeout_cache:
            # Initialize cache entry
            initial_timeout = self.default_timeout
            if success:
                if elapsed_time < self.default_timeout:
                    # If successful and fast, use slightly higher than elapsed time
                    # but ensure it's at least the minimum timeout
                    initial_timeout = min(self.default_timeout, max(self.min_timeout, int(elapsed_time * 1.5)))
                else:
                    # If successful but slow, use the elapsed time plus a small buffer
                    initial_timeout = min(self.max_timeout, max(self.min_timeout, int(elapsed_time * 1.2)))

            self.domain_timeout_cache[domain] = {
                'timeout': initial_timeout,
                'success_rate': 1.0 if success else 0.0,
                'avg_time': elapsed_time if success else self.default_timeout,
                'last_updated': current_time,
                'usage_count': 1,
                'last_success_time': current_time if success else 0
            }
            return

        # Update existing cache entry
        cache = self.domain_timeout_cache[domain]
        cache['usage_count'] += 1

        # Weight for moving averages - give more weight to recent results for frequently used domains
        alpha = min(0.3, 2.0 / (cache['usage_count'] + 5))  # Adaptive weight that decreases with more usage

        # Update success rate with exponential moving average
        cache['success_rate'] = cache['success_rate'] * (1 - alpha) + (alpha if success else 0)

        if success:
            # Update last success time
            cache['last_success_time'] = current_time

            # Update average time with exponential moving average
            cache['avg_time'] = cache['avg_time'] * (1 - alpha) + elapsed_time * alpha

            # Adjust timeout based on average time and success rate
            if cache['success_rate'] > 0.8:
                # High success rate, we can optimize for speed
                # Use a smaller multiplier for frequently accessed domains
                multiplier = 1.3 if cache['usage_count'] > 10 else 1.5
                new_timeout = max(self.min_timeout, min(int(cache['avg_time'] * multiplier), self.max_timeout))
            elif cache['success_rate'] > 0.5:
                # Moderate success rate, be somewhat conservative
                new_timeout = max(self.min_timeout, min(int(cache['avg_time'] * 1.7), self.max_timeout))
            else:
                # Lower success rate, be more conservative
                new_timeout = max(self.min_timeout, min(int(cache['avg_time'] * 2.0), self.max_timeout))
        else:
            # Failed scrape, increase timeout based on how long since last success
            time_since_success = current_time - cache.get('last_success_time', 0)

            if time_since_success > 86400:  # No success in over a day
                # Significant increase for long-term problematic domains
                new_timeout = min(int(cache['timeout'] * 1.5), self.max_timeout)
            else:
                # Normal increase for recently successful domains
                new_timeout = min(int(cache['timeout'] * 1.2), self.max_timeout)

        # Update timeout only if significant change to avoid log spam
        if abs(new_timeout - cache['timeout']) > 1:
            self.logger.debug(
                f"Adjusting timeout for {domain} from {cache['timeout']}s to {new_timeout}s "
                f"(success rate: {cache['success_rate']:.2f}, avg time: {cache['avg_time']:.2f}s)"
            )
            cache['timeout'] = new_timeout

        cache['last_updated'] = current_time

    def _get_method_for_domain(self, domain: str) -> str:
        """
        Get the best scraping method for a domain with improved heuristics.
        Enhanced with more efficient pattern matching and better domain analysis.

        Args:
            domain: Domain name

        Returns:
            Method name ('requests' or 'puppeteer')
        """
        # First check domain cache for faster lookups
        if domain in self.domain_method_cache:
            cache_entry = self.domain_method_cache[domain]
            # Cache valid for 1 day
            if time.time() - cache_entry['last_updated'] < 86400:
                # If we have high confidence (used multiple times with good success rate)
                if cache_entry['usage_count'] > 3 and cache_entry['success_rate'] > 0.7:
                    return cache_entry['method']

        # Normalize domain for pattern matching
        domain_lower = domain.lower()

        # Check if domain is known to require JavaScript (exact match for better performance)
        for js_domain in self.JS_REQUIRED_DOMAINS:
            if js_domain in domain_lower:
                return 'puppeteer'

        # Check for common patterns that suggest JavaScript is needed
        js_patterns = [
            'app.', 'dashboard.', 'portal.', 'learn.', 'courses.',
            'interactive.', 'player.', 'viewer.', 'web.', 'cloud.',
            'admin.', 'account.', 'login.', 'auth.', 'secure.',
            'platform.', 'online.', 'live.', 'stream.', 'play.',
            'studio.', 'editor.', 'console.', 'panel.', 'manage.'
        ]

        for pattern in js_patterns:
            if pattern in domain_lower:
                return 'puppeteer'

        # Check for domains that likely use modern web frameworks
        domain_parts = domain_lower.split('.')
        if len(domain_parts) >= 2:
            tld = domain_parts[-1]
            if tld in ['io', 'app', 'dev', 'ai', 'co', 'me', 'so', 'tech']:
                # Domains with these TLDs are more likely to be modern web apps
                return 'puppeteer'

        # Check for specific subdomains that often use JavaScript
        if len(domain_parts) >= 3:
            subdomain = domain_parts[0]
            js_subdomains = ['app', 'dashboard', 'portal', 'admin', 'account', 'my', 'web', 'cloud']
            if subdomain in js_subdomains:
                return 'puppeteer'

        # Check for domains with common JavaScript framework keywords
        js_keywords = ['react', 'vue', 'angular', 'next', 'nuxt', 'svelte', 'ember', 'gatsby']
        for keyword in js_keywords:
            if keyword in domain_lower:
                return 'puppeteer'

        # If we have some cache data but not enough for high confidence
        if domain in self.domain_method_cache:
            cache_entry = self.domain_method_cache[domain]
            # If we've had some success with a method, keep using it
            if cache_entry['success_rate'] > 0.5:
                return cache_entry['method']

        # Use puppeteer more often for unknown domains (20% of the time)
        # This helps discover which domains need puppeteer, but we reduced from 30% to 20%
        # to favor the faster requests method for most cases
        if random.random() < 0.2:
            return 'puppeteer'

        # Default: try simple method first
        return 'requests'

    def _update_domain_cache(self, domain: str, method: str, success: bool) -> None:
        """
        Update the domain method cache.

        Args:
            domain: Domain name
            method: Method used ('requests' or 'puppeteer')
            success: Whether the method was successful
        """
        if domain not in self.domain_method_cache:
            # Initialize cache entry
            self.domain_method_cache[domain] = {
                'method': method,
                'success_rate': 1.0 if success else 0.0,
                'last_updated': time.time(),
                'usage_count': 1
            }
            return

        cache = self.domain_method_cache[domain]
        cache['usage_count'] += 1

        if cache['method'] == method:
            # Update success rate of current method
            cache['success_rate'] = cache['success_rate'] * 0.9 + (0.1 if success else 0)
        elif success:
            # If the new method was successful, consider switching
            cache['success_rate'] = cache['success_rate'] * 0.7  # Penalize current method

            # Switch method if success rate is low
            if cache['success_rate'] < 0.5:
                self.logger.info(f"Switching preferred method for {domain} from {cache['method']} to {method}")
                cache['method'] = method
                cache['success_rate'] = 0.7  # Start with a reasonable rate

        cache['last_updated'] = time.time()

    def clear_domain_method_cache(self) -> int:
        """
        Clear the domain method cache.

        Returns:
            Number of entries removed
        """
        count = len(self.domain_method_cache)
        self.domain_method_cache.clear()
        self.logger.info("Domain method cache cleared")
        return count

    def get_domain_method_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the domain method cache.

        Returns:
            Dictionary with cache statistics
        """
        domains = list(self.domain_method_cache.keys())
        simple_count = sum(1 for d in domains if self.domain_method_cache[d]['method'] == 'requests')
        puppeteer_count = sum(1 for d in domains if self.domain_method_cache[d]['method'] == 'puppeteer')

        return {
            'totalDomains': len(domains),
            'simpleMethodCount': simple_count,
            'puppeteerMethodCount': puppeteer_count,
            'domains': [
                {
                    'domain': d,
                    'method': self.domain_method_cache[d]['method'],
                    'successRate': self.domain_method_cache[d]['success_rate'],
                    'usageCount': self.domain_method_cache[d]['usage_count'],
                    'lastUpdated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.domain_method_cache[d]['last_updated'])),
                    'timeout': self.domain_timeout_cache.get(d, {}).get('timeout', self.default_timeout) if d in self.domain_timeout_cache else self.default_timeout
                }
                for d in domains
            ]
        }

    def get_timeout_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the adaptive timeout cache.

        Returns:
            Dictionary with timeout cache statistics
        """
        domains = list(self.domain_timeout_cache.keys())

        # Calculate average timeout
        avg_timeout = sum(self.domain_timeout_cache[d]['timeout'] for d in domains) / max(1, len(domains))

        # Calculate average success rate
        avg_success_rate = sum(self.domain_timeout_cache[d]['success_rate'] for d in domains) / max(1, len(domains))

        return {
            'totalDomains': len(domains),
            'averageTimeout': round(avg_timeout, 2),
            'averageSuccessRate': round(avg_success_rate, 2),
            'minTimeout': self.min_timeout,
            'maxTimeout': self.max_timeout,
            'defaultTimeout': self.default_timeout,
            'domains': [
                {
                    'domain': d,
                    'timeout': self.domain_timeout_cache[d]['timeout'],
                    'successRate': self.domain_timeout_cache[d]['success_rate'],
                    'avgTime': round(self.domain_timeout_cache[d]['avg_time'], 2),
                    'usageCount': self.domain_timeout_cache[d]['usage_count'],
                    'lastUpdated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.domain_timeout_cache[d]['last_updated']))
                }
                for d in domains
            ]
        }

    def clear_timeout_cache(self) -> int:
        """
        Clear the adaptive timeout cache.

        Returns:
            Number of entries removed
        """
        count = len(self.domain_timeout_cache)
        self.domain_timeout_cache.clear()
        self.logger.info("Adaptive timeout cache cleared")
        return count
