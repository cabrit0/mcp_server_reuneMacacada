"""
Adaptive scraper that automatically chooses the most efficient method for each website.
"""

import time
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
        'twitter.com', 'linkedin.com', 'instagram.com',
        'facebook.com', 'medium.com', 'stackoverflow.com'
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
        
        # Load configuration
        scraping_config = config.get_section("SCRAPING")
        self.default_timeout = scraping_config.get("timeout_default", 8)
        
        self.logger.info("Initialized AdaptiveScraper with both requests and puppeteer scrapers")

    async def _scrape_url_impl(self, url: str, timeout: int = None) -> Optional[Dict[str, Any]]:
        """
        Scrape a URL using the most efficient method.

        Args:
            url: URL to scrape
            timeout: Timeout in seconds

        Returns:
            Dictionary with HTML content and metadata or None if failed
        """
        if timeout is None:
            timeout = self.default_timeout
            
        try:
            # Extract domain from URL
            domain = urlparse(url).netloc
            
            # Determine which method to use
            method_to_use = self._get_method_for_domain(domain)
            
            # Try the chosen method
            result = None
            
            if method_to_use == 'requests':
                # Try simple method first
                result = await self.requests_scraper._scrape_url_impl(url, min(timeout, 5))
                
                # If it fails, try Puppeteer
                if not result:
                    self.logger.debug(f"Simple method failed for {url}, trying Puppeteer")
                    result = await self.puppeteer_scraper._scrape_url_impl(url, timeout)
                    
                    # Update cache
                    self._update_domain_cache(domain, 'puppeteer', bool(result))
                else:
                    # Simple method worked
                    self._update_domain_cache(domain, 'requests', True)
            else:
                # Use Puppeteer directly
                result = await self.puppeteer_scraper._scrape_url_impl(url, timeout)
                
                # Update cache
                self._update_domain_cache(domain, 'puppeteer', bool(result))
            
            if not result:
                self.logger.warning(f"Failed to scrape {url} with all available methods")
                return None
                
            return result
        except Exception as e:
            self.logger.error(f"Error in adaptive scraping: {str(e)}")
            return None

    def _get_method_for_domain(self, domain: str) -> str:
        """
        Get the best scraping method for a domain.

        Args:
            domain: Domain name

        Returns:
            Method name ('requests' or 'puppeteer')
        """
        # Check if domain is known to require JavaScript
        if any(js_domain in domain for js_domain in self.JS_REQUIRED_DOMAINS):
            return 'puppeteer'
            
        # Check domain cache
        if domain in self.domain_method_cache:
            cache_entry = self.domain_method_cache[domain]
            # Cache valid for 1 day
            if time.time() - cache_entry['last_updated'] < 86400:
                return cache_entry['method']
                
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
                    'lastUpdated': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(self.domain_method_cache[d]['last_updated']))
                }
                for d in domains
            ]
        }
