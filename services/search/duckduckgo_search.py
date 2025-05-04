"""
DuckDuckGo search implementation.
"""

import asyncio
from typing import Dict, List, Any, Optional
from duckduckgo_search import DDGS

from services.search.base_search import BaseSearch


class DuckDuckGoSearch(BaseSearch):
    """
    DuckDuckGo search implementation.
    Uses the duckduckgo_search library to search the web.
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

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the DuckDuckGo search service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        super().__init__(name="duckduckgo", cache_ttl=cache_ttl)

    def get_region_for_language(self, language: str) -> str:
        """
        Get the corresponding region for a language code.

        Args:
            language: Language code (e.g., 'en', 'pt')

        Returns:
            DuckDuckGo region code
        """
        return self.LANGUAGE_TO_REGION.get(language, "wt-wt")  # wt-wt is the global default

    async def _search_impl(self, query: str, max_results: int, language: str) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description
        """
        # Get region for language
        region = self.get_region_for_language(language)
        
        # Use a random User Agent
        user_agent = self.get_random_user_agent()
        results = []

        try:
            # Run in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                self._perform_ddg_search,
                query, max_results, region, user_agent
            )
            
            return results
        except Exception as e:
            self.logger.error(f"Error in DuckDuckGo search: {str(e)}")
            raise

    def _perform_ddg_search(self, query: str, max_results: int, region: str, user_agent: str) -> List[Dict[str, Any]]:
        """
        Perform the actual DuckDuckGo search (runs in a separate thread).

        Args:
            query: Search query
            max_results: Maximum number of results to return
            region: DuckDuckGo region code
            user_agent: User Agent string

        Returns:
            List of dictionaries with title, URL, and description
        """
        results = []
        
        try:
            # The DDGS library doesn't accept user_agent as a parameter in the constructor
            # We'll use headers to set the User-Agent
            headers = {'User-Agent': user_agent}
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
            return []
