"""
Brave Search implementation.
"""

import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from urllib.parse import quote

from infrastructure.config import config
from services.search.base_search import BaseSearch


class BraveSearch(BaseSearch):
    """
    Brave Search implementation.
    Uses the Brave Search API to search the web.
    """

    # Base URL for Brave Search API
    API_BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the Brave Search service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        super().__init__(name="brave", cache_ttl=cache_ttl)
        
        # Get API key from config
        search_config = config.get_section("SEARCH")
        self.api_key = search_config.get("brave_api_key")
        
        if not self.api_key:
            self.logger.warning("Brave Search API key not configured. Brave Search will not work.")

    async def _search_impl(self, query: str, max_results: int, language: str) -> List[Dict[str, Any]]:
        """
        Search using Brave Search API.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description
        """
        if not self.api_key:
            self.logger.error("Brave Search API key not configured")
            return []
            
        # Prepare request parameters
        params = {
            "q": query,
            "count": min(max_results, 20),  # API limit is 20
            "search_lang": language,
            "ui_lang": language,
            "safesearch": "moderate"
        }
        
        headers = {
            "Accept": "application/json",
            "Accept-Language": language,
            "X-Subscription-Token": self.api_key,
            "User-Agent": self.get_random_user_agent()
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.API_BASE_URL, params=params, headers=headers) as response:
                    if response.status != 200:
                        self.logger.error(f"Brave Search API error: {response.status}")
                        return []
                        
                    data = await response.json()
                    
                    # Extract search results
                    results = []
                    
                    if "web" in data and "results" in data["web"]:
                        for item in data["web"]["results"]:
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "description": item.get("description", "")
                            })
                    
                    return results
        except Exception as e:
            self.logger.error(f"Error in Brave Search: {str(e)}")
            return []
