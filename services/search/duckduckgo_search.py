"""
DuckDuckGo search implementation with rate limit handling.
"""

import asyncio
import random
import time
from typing import Dict, List, Any, Optional
from duckduckgo_search import DDGS
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from services.search.base_search import BaseSearch


class DuckDuckGoSearch(BaseSearch):
    """
    DuckDuckGo search implementation with rate limit handling.
    Uses the duckduckgo_search library to search the web with retry logic
    and advanced rate limit avoidance techniques.
    """

    # Mapping of language codes to DuckDuckGo regions
    LANGUAGE_TO_REGION = {
        "en": "us-en",
        "pt": "br-pt",
        "es": "es-es",
        "fr": "fr-fr",
        "de": "de-de",
        "it": "it-it",
        "nl": "nl-nl",
        "ru": "ru-ru",
        "ja": "jp-jp",
        "zh": "cn-zh",
    }

    # Extended list of User-Agents for better rotation
    EXTENDED_USER_AGENTS = [
        # Windows Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
        # Windows Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0",
        # Windows Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36 Edg/92.0.902.55",
        # macOS Safari
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
        # macOS Chrome
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        # Linux Chrome
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        # Mobile User Agents
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 12; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Mobile Safari/537.36"
    ]

    # Accept-Language headers for different languages
    ACCEPT_LANGUAGE_HEADERS = {
        "en": "en-US,en;q=0.9",
        "pt": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "es": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "fr": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "de": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "it": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the DuckDuckGo search service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        super().__init__(name="duckduckgo", cache_ttl=cache_ttl)

        # Initialize rate limiting parameters
        self.last_request_time = 0
        self.min_request_interval = 2.0  # Minimum seconds between requests

        # Initialize semaphore for rate limiting
        self.semaphore = asyncio.Semaphore(1)  # Allow only 1 concurrent request

    def get_region_for_language(self, language: str) -> str:
        """
        Get the corresponding region for a language code.

        Args:
            language: Language code (e.g., 'en', 'pt')

        Returns:
            DuckDuckGo region code
        """
        return self.LANGUAGE_TO_REGION.get(language, "wt-wt")  # wt-wt is the global default

    def get_random_user_agent(self) -> str:
        """
        Get a random User Agent from the extended list.

        Returns:
            Random User Agent string
        """
        return random.choice(self.EXTENDED_USER_AGENTS)

    def get_random_headers(self, language: str) -> Dict[str, str]:
        """
        Generate random headers for the request.

        Args:
            language: Language code for Accept-Language header

        Returns:
            Dictionary of HTTP headers
        """
        user_agent = self.get_random_user_agent()
        accept_language = self.ACCEPT_LANGUAGE_HEADERS.get(language, "en-US,en;q=0.9")

        headers = {
            'User-Agent': user_agent,
            'Accept-Language': accept_language,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://duckduckgo.com/',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }

        # Randomize header order to avoid fingerprinting
        header_items = list(headers.items())
        random.shuffle(header_items)
        return dict(header_items)

    async def _search_impl(self, query: str, max_results: int, language: str) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo with rate limiting and retry logic.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description
        """
        # Get region for language
        region = self.get_region_for_language(language)

        # Generate random headers
        headers = self.get_random_headers(language)

        # Use semaphore for rate limiting
        async with self.semaphore:
            # Ensure minimum time between requests
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time

            if time_since_last_request < self.min_request_interval:
                delay = self.min_request_interval - time_since_last_request
                delay_with_jitter = delay * (0.5 + random.random())  # Add jitter
                self.logger.debug(f"Rate limiting: waiting {delay_with_jitter:.2f}s before next request")
                await asyncio.sleep(delay_with_jitter)

            # Update last request time
            self.last_request_time = time.time()

            try:
                # Run in a separate thread to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                results = await loop.run_in_executor(
                    None,
                    self._perform_ddg_search_with_retry,
                    query, max_results, region, headers
                )

                if results:
                    self.logger.info(f"Search successful with {self.name} ({len(results)} results)")
                else:
                    self.logger.warning(f"No search results found for '{query}'")

                return results
            except Exception as e:
                self.logger.error(f"Error in DuckDuckGo search: {str(e)}")
                return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception))
    )
    def _perform_ddg_search_with_retry(self, query: str, max_results: int, region: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Perform the actual DuckDuckGo search with retry logic.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            region: DuckDuckGo region code
            headers: HTTP headers for the request

        Returns:
            List of dictionaries with title, URL, and description
        """
        results = []

        try:
            with DDGS(headers=headers) as ddgs:
                for r in ddgs.text(query, max_results=max_results, region=region):
                    results.append({
                        "title": r.get('title'),
                        "url": r.get('href'),
                        "description": r.get('body', '')[:200] + '...' if r.get('body', '') and len(r.get('body', '')) > 200 else r.get('body', ''),
                    })
            return results
        except Exception as e:
            self.logger.error(f"Error in DuckDuckGo search thread: {str(e)}")
            # Re-raise the exception to trigger retry
            raise
