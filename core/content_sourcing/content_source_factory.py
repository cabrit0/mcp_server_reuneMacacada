"""
Factory for creating content source instances.
"""

from typing import Dict, Any, Optional

from infrastructure.logging import logger
from core.content_sourcing.content_source_service import ContentSourceService
from core.content_sourcing.default_content_source_service import DefaultContentSourceService
from core.content_sourcing.duckduckgo_search_service import DuckDuckGoSearchService
from core.content_sourcing.optimized_scraper_service import OptimizedScraperService


class ContentSourceFactory:
    """
    Factory for creating content source instances.
    """

    # Singleton instances
    _instances: Dict[str, ContentSourceService] = {}

    @classmethod
    def create_content_source(cls, source_type: str = "default", config_options: Optional[Dict[str, Any]] = None) -> ContentSourceService:
        """
        Create a content source instance.

        Args:
            source_type: Type of source to create ("default")
            config_options: Configuration options for the source

        Returns:
            Content source instance implementing ContentSourceService
        """
        # Use singleton pattern for efficiency
        if source_type in cls._instances:
            return cls._instances[source_type]
            
        # Create source instance
        source: ContentSourceService
        
        if source_type == "default":
            # Create dependencies
            search_service = DuckDuckGoSearchService()
            scraper_service = OptimizedScraperService()
            
            # Create content source
            source = DefaultContentSourceService(search_service, scraper_service)
        else:
            logger.warning(f"Unknown content source type: {source_type}, falling back to default")
            return cls.create_content_source("default", config_options)
            
        # Store instance for reuse
        cls._instances[source_type] = source
        
        return source
