"""
Factory for creating YouTube service instances.
"""

from typing import Dict, Any, Optional, List, Tuple

from infrastructure.logging import logger
from infrastructure.config import config
from services.youtube.youtube_service import YouTubeService
from services.youtube.ytdlp_service import YtDlpService
from services.youtube.youtube_api_service import YouTubeApiService
from services.youtube.fallback_youtube_service import FallbackYouTubeService


class YouTubeFactory:
    """
    Factory for creating YouTube service instances.
    """

    # Singleton instances
    _instances: Dict[str, YouTubeService] = {}

    @classmethod
    def create_youtube_service(cls, service_type: str = "default", config_options: Optional[Dict[str, Any]] = None) -> YouTubeService:
        """
        Create a YouTube service instance.

        Args:
            service_type: Type of service to create ("ytdlp", "api", "fallback", "default")
            config_options: Configuration options for the service

        Returns:
            YouTube service instance implementing YouTubeService
        """
        # Use singleton pattern for efficiency
        if service_type in cls._instances:
            return cls._instances[service_type]

        # Get configuration
        if config_options is None:
            config_options = {}

        # Get cache TTL from config
        youtube_config = config.get_section("YOUTUBE")
        cache_ttl = config_options.get("cache_ttl", youtube_config.get("cache_ttl", 86400))

        # Create service instance
        service: YouTubeService

        if service_type == "ytdlp":
            # Use direct instantiation instead of decorator-based lazy loading
            service = YtDlpService(cache_ttl=cache_ttl)
        elif service_type == "api":
            service = YouTubeApiService(cache_ttl=cache_ttl)
        elif service_type == "fallback" or service_type == "default":
            # Create a simple fallback service first to avoid circular dependencies
            if "ytdlp" not in cls._instances:
                # Create YtDlpService first
                cls._instances["ytdlp"] = YtDlpService(cache_ttl=cache_ttl)

            # Create fallback service with YtDlpService only initially
            services: List[Tuple[YouTubeService, float]] = []
            services.append((cls._instances["ytdlp"], 1.0))

            # Add YouTubeApiService if API key is configured
            if youtube_config.get("api_key"):
                if "api" not in cls._instances:
                    cls._instances["api"] = YouTubeApiService(cache_ttl=cache_ttl)
                services.append((cls._instances["api"], 0.8))

            service = FallbackYouTubeService(services=services, cache_ttl=cache_ttl)
        else:
            logger.warning(f"Unknown YouTube service type: {service_type}, falling back to default")
            return cls.create_youtube_service("default", config_options)

        # Store instance for reuse
        cls._instances[service_type] = service

        logger.info(f"Created YouTube service of type: {service_type}")
        return service
