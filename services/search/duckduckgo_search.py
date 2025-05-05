"""
DuckDuckGo search implementation with rate limit handling and circuit breaker protection.
"""

import asyncio
import random
import time
from typing import Dict, List, Any
from duckduckgo_search import DDGS
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from services.search.base_search import BaseSearch
from infrastructure.circuit_breaker import async_circuit_breaker, CircuitBreakerOpenError, CircuitBreaker


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

    # Extended list of User Agents for better rotation
    EXTENDED_USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 Edg/95.0.1020.53",
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:95.0) Gecko/20100101 Firefox/95.0",
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
        # Firefox on Linux
        "Mozilla/5.0 (X11; Linux x86_64; rv:95.0) Gecko/20100101 Firefox/95.0",
        # Mobile User Agents
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36",
    ]

    # Accept-Language headers for different languages
    ACCEPT_LANGUAGE_HEADERS = {
        "en": "en-US,en;q=0.9",
        "pt": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "es": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
        "fr": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "de": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
        "it": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "nl": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
        "ru": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "ja": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
        "zh": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
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
        self.min_request_interval = 3.5  # Increased from 2.0 to 3.5 seconds between requests

        # Initialize semaphore for rate limiting
        self.semaphore = asyncio.Semaphore(1)  # Allow only 1 concurrent request

        # Track success/failure rate
        self.success_count = 0
        self.failure_count = 0
        self.total_requests = 0

        # Initialize circuit breaker with enhanced settings for DuckDuckGo
        self._init_circuit_breaker()

    def _init_circuit_breaker(self):
        """
        Initialize the circuit breaker with enhanced settings for DuckDuckGo.
        This configures a more aggressive circuit breaker to better handle rate limiting.
        """
        # Get or create the circuit breaker instance
        circuit_breaker = CircuitBreaker.get_instance("duckduckgo_search")

        # Configure with enhanced settings for DuckDuckGo
        circuit_breaker.failure_threshold = 3  # Open after 3 failures (reduced from default 5)
        circuit_breaker.reset_timeout = 120  # 2 minutes initial timeout (increased from default 60s)
        circuit_breaker.consecutive_failures_threshold = 2  # Open after 2 consecutive failures
        circuit_breaker.error_rate_threshold = 0.4  # 40% error rate threshold (reduced from default 50%)
        circuit_breaker.backoff_multiplier = 2.5  # More aggressive backoff (increased from default 2.0)
        circuit_breaker.max_reset_timeout = 3600  # Maximum 1 hour timeout (increased from default 30 minutes)

        self.logger.info(f"Initialized circuit breaker 'duckduckgo_search'")

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
        Generate random headers for the request with enhanced anti-fingerprinting.

        Args:
            language: Language code for Accept-Language header

        Returns:
            Dictionary of HTTP headers
        """
        user_agent = self.get_random_user_agent()
        accept_language = self.ACCEPT_LANGUAGE_HEADERS.get(language, "en-US,en;q=0.9")

        # Add randomness to accept-language with varying q values
        if random.random() > 0.5 and ',' in accept_language:
            parts = accept_language.split(',')
            if len(parts) > 1:
                # Randomize q values slightly
                q_value = round(0.8 + random.random() * 0.1, 1)
                parts[1] = parts[1].split(';')[0] + f";q={q_value}"
                accept_language = ','.join(parts)

        # Base headers that are always included
        headers = {
            'User-Agent': user_agent,
            'Accept-Language': accept_language,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

        # Additional headers with randomized inclusion
        optional_headers = {
            'Referer': ['https://duckduckgo.com/', 'https://www.google.com/', 'https://www.bing.com/'],
            'DNT': ['1'],
            'Sec-Fetch-Dest': ['document', 'empty'],
            'Sec-Fetch-Mode': ['navigate', 'cors'],
            'Sec-Fetch-Site': ['same-origin', 'cross-site', 'none'],
            'Upgrade-Insecure-Requests': ['1'],
            'Cache-Control': ['max-age=0', 'no-cache', 'max-age=300'],
            'Connection': ['keep-alive', 'close'],
            'Pragma': ['no-cache'],
        }

        # Add some optional headers randomly
        for header, values in optional_headers.items():
            if random.random() > 0.3:  # 70% chance to include each optional header
                headers[header] = random.choice(values)

        # Randomize header order to avoid fingerprinting
        header_items = list(headers.items())
        random.shuffle(header_items)
        return dict(header_items)

    @async_circuit_breaker("duckduckgo_search")
    async def _search_impl(self, query: str, max_results: int, language: str) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo with rate limiting, retry logic, and circuit breaker protection.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description

        Raises:
            CircuitBreakerOpenError: If the circuit breaker is open
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

            # Calculate dynamic delay based on success/failure rate
            dynamic_interval = self.min_request_interval
            if self.total_requests > 10:  # Only after we have some data
                failure_rate = self.failure_count / max(1, self.total_requests)
                if failure_rate > 0.3:  # If more than 30% of requests fail
                    # Increase delay up to 2x based on failure rate
                    dynamic_interval = self.min_request_interval * (1 + failure_rate)
                    self.logger.info(f"Increasing delay due to high failure rate ({failure_rate:.2f}): {dynamic_interval:.2f}s")

            if time_since_last_request < dynamic_interval:
                delay = dynamic_interval - time_since_last_request
                # Add more jitter (0.8-1.2) to avoid patterns
                delay_with_jitter = delay * (0.8 + 0.4 * random.random())
                self.logger.debug(f"Rate limiting: waiting {delay_with_jitter:.2f}s before next request")
                await asyncio.sleep(delay_with_jitter)

            # Update last request time
            self.last_request_time = time.time()

            # Increment total requests counter
            self.total_requests += 1

            try:
                # Run in a separate thread to avoid blocking the event loop
                loop = asyncio.get_event_loop()

                # Set a timeout for the entire operation
                search_timeout = 15  # 15 seconds timeout for the entire search operation
                try:
                    search_task = loop.run_in_executor(
                        None,
                        self._perform_ddg_search_with_retry,
                        query, max_results, region, headers
                    )
                    results = await asyncio.wait_for(search_task, timeout=search_timeout)
                except asyncio.TimeoutError:
                    self.logger.error(f"Timeout after {search_timeout}s searching DuckDuckGo for '{query}'")
                    self.failure_count += 1
                    # Treat timeouts as a serious failure that should trigger circuit breaker
                    raise Exception(f"DuckDuckGo search timeout after {search_timeout}s")

                if results:
                    # Check if results are valid (have required fields)
                    valid_results = [r for r in results if r.get('url') and r.get('title')]

                    if valid_results:
                        self.logger.info(f"Search successful with {self.name} ({len(valid_results)} valid results)")
                        # Track success
                        self.success_count += 1
                        return valid_results
                    else:
                        self.logger.warning(f"DuckDuckGo returned {len(results)} results but none were valid for '{query}'")
                        # Track failure - invalid results count as failures
                        self.failure_count += 1
                        return []
                else:
                    self.logger.warning(f"No search results found for '{query}'")
                    # Track failure - empty results count as failures
                    self.failure_count += 1
                    return []
            except CircuitBreakerOpenError:
                # Re-raise circuit breaker errors to be handled by the fallback search service
                self.logger.warning(f"Circuit breaker open for DuckDuckGo search, failing fast")
                # Track failure
                self.failure_count += 1
                raise
            except Exception as e:
                self.logger.error(f"Error in DuckDuckGo search: {str(e)}")
                # Track failure
                self.failure_count += 1

                # Check for rate limit errors specifically
                error_str = str(e).lower()
                if "ratelimit" in error_str or "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
                    self.logger.error(f"DuckDuckGo rate limit detected: {str(e)}")
                    # Increase the min request interval temporarily
                    self.min_request_interval = min(10.0, self.min_request_interval * 1.5)
                    self.logger.info(f"Increased min request interval to {self.min_request_interval}s")

                    # Re-raise to trigger circuit breaker
                    raise

                return []

    @retry(
        stop=stop_after_attempt(4),  # Increased from 3 to 4 attempts
        wait=wait_exponential(multiplier=2, min=3, max=15),  # More aggressive backoff
        retry=retry_if_exception_type((Exception))
    )
    def _perform_ddg_search_with_retry(self, query: str, max_results: int, region: str, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Perform the actual DuckDuckGo search with enhanced retry logic and error handling.

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
            self.logger.info(f"Starting DuckDuckGo search for query: '{query}', max_results: {max_results}, region: {region}")

            # Only log headers in debug mode to avoid exposing sensitive information
            if self.logger.isEnabledFor(10):  # DEBUG level
                # Redact potentially sensitive header values
                safe_headers = headers.copy()
                for k in safe_headers:
                    if k.lower() in ('cookie', 'authorization', 'x-api-key'):
                        safe_headers[k] = '[REDACTED]'
                self.logger.debug(f"Using headers: {safe_headers}")

            # Request more results than needed to account for filtering
            request_max_results = max(15, max_results * 2)

            # Set a timeout for the DDGS operation
            with DDGS(headers=headers, timeout=10) as ddgs:  # 10 second timeout
                try:
                    # Use a list comprehension with a timeout check
                    start_time = time.time()
                    max_time = 8  # 8 seconds max for the actual search

                    # Get raw results with timeout check
                    raw_results = []
                    for result in ddgs.text(query, max_results=request_max_results, region=region):
                        raw_results.append(result)

                        # Check if we've exceeded our time limit
                        if time.time() - start_time > max_time:
                            self.logger.warning(f"Stopping DuckDuckGo search early after {max_time}s with {len(raw_results)} results")
                            break

                    self.logger.info(f"DuckDuckGo raw results count: {len(raw_results)}")

                    # Process results with better error handling
                    for r in raw_results:
                        if not isinstance(r, dict):
                            self.logger.warning(f"Skipping invalid result (not a dict): {type(r)}")
                            continue

                        # Extract and validate fields
                        title = r.get('title')
                        url = r.get('href')
                        body = r.get('body', '')

                        if not title or not url:
                            self.logger.debug(f"Skipping result with missing title or URL: {r}")
                            continue

                        # Truncate description if needed
                        description = body[:200] + '...' if body and len(body) > 200 else body

                        results.append({
                            "title": title,
                            "url": url,
                            "description": description,
                        })

                except Exception as inner_e:
                    self.logger.error(f"Error during DuckDuckGo search execution: {str(inner_e)}")
                    # Check for rate limiting indicators
                    error_str = str(inner_e).lower()
                    if "ratelimit" in error_str or "429" in error_str or "too many requests" in error_str:
                        self.logger.error("DuckDuckGo rate limit detected in inner exception")
                        raise Exception(f"DuckDuckGo rate limit: {str(inner_e)}")
                    raise

            self.logger.info(f"DuckDuckGo search completed with {len(results)} processed results")
            if len(results) == 0:
                self.logger.warning(f"DuckDuckGo returned zero results for query: '{query}'")

            # Limit to requested max_results
            return results[:max_results]

        except Exception as e:
            error_str = str(e).lower()

            # Special handling for common error types
            if "ratelimit" in error_str or "429" in error_str or "too many requests" in error_str:
                self.logger.error(f"DuckDuckGo rate limit detected: {str(e)}")
                # Make this error more identifiable for circuit breaker
                raise Exception(f"DuckDuckGo rate limit: {str(e)}")
            elif "timeout" in error_str:
                self.logger.error(f"DuckDuckGo timeout: {str(e)}")
                raise Exception(f"DuckDuckGo timeout: {str(e)}")
            elif "connection" in error_str or "network" in error_str:
                self.logger.error(f"DuckDuckGo connection error: {str(e)}")
                raise Exception(f"DuckDuckGo connection error: {str(e)}")
            else:
                self.logger.error(f"Error in DuckDuckGo search thread: {str(e)}")
                self.logger.error(f"Query: '{query}', Region: {region}")
                # Re-raise the exception to trigger retry
                raise
