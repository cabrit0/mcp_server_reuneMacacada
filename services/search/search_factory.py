"""
Factory for creating search instances.
"""

from typing import Dict, Any, Optional, List, Tuple

from infrastructure.logging import logger
from infrastructure.config import config
from services.search.search_service import SearchService
from services.search.duckduckgo_search import DuckDuckGoSearch
from services.search.brave_search import BraveSearch
from services.search.fallback_search import FallbackSearch


class SearchFactory:
    """
    Factory for creating search instances.
    """

    # Singleton instances
    _instances: Dict[str, SearchService] = {}

    @classmethod
    def create_search(cls, search_type: str = "default", config_options: Optional[Dict[str, Any]] = None) -> SearchService:
        """
        Create a search instance.

        Args:
            search_type: Type of search to create ("duckduckgo", "brave", "fallback", "default")
            config_options: Configuration options for the search

        Returns:
            Search instance implementing SearchService
        """
        # Use singleton pattern for efficiency
        if search_type in cls._instances:
            return cls._instances[search_type]
            
        # Get configuration
        if config_options is None:
            config_options = {}
            
        # Get cache TTL from config
        search_config = config.get_section("SEARCH")
        cache_ttl = config_options.get("cache_ttl", search_config.get("cache_ttl", 86400))
        
        # Create search instance
        search: SearchService
        
        if search_type == "duckduckgo":
            search = DuckDuckGoSearch(cache_ttl=cache_ttl)
        elif search_type == "brave":
            search = BraveSearch(cache_ttl=cache_ttl)
        elif search_type == "fallback" or search_type == "default":
            # Create fallback search with multiple engines
            engines: List[Tuple[SearchService, float]] = []
            
            # Add DuckDuckGo (primary)
            engines.append((cls.create_search("duckduckgo"), 1.0))
            
            # Add Brave if API key is configured
            if search_config.get("brave_api_key"):
                engines.append((cls.create_search("brave"), 0.8))
                
            search = FallbackSearch(search_engines=engines, cache_ttl=cache_ttl)
        else:
            logger.warning(f"Unknown search type: {search_type}, falling back to default")
            return cls.create_search("default", config_options)
            
        # Store instance for reuse
        cls._instances[search_type] = search
        
        return search
