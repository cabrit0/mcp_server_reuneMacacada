"""
Fallback YouTube service that combines multiple implementations.
"""

from typing import List, Dict, Any, Optional, Tuple

from infrastructure.logging import logger
from infrastructure.cache import cache
from api.models import Resource
from services.youtube.youtube_service import YouTubeService


class FallbackYouTubeService(YouTubeService):
    """
    Fallback YouTube service that combines multiple implementations.
    Tries each implementation in order until one succeeds.
    """

    def __init__(self, services: List[Tuple[YouTubeService, float]], cache_ttl: int = 86400):
        """
        Initialize the fallback YouTube service.

        Args:
            services: List of (service, weight) tuples
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        self.services = services
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger("youtube.fallback")

        service_names = [service[0].__class__.__name__ for service in services]
        self.logger.info(f"Initialized FallbackYouTubeService with services: {', '.join(service_names)}")

    async def search_videos(self, query: str, max_results: int = 5, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for YouTube videos using multiple implementations with fallback.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with video information
        """
        # Check cache first
        cache_key = f"youtube:fallback:search:{query}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached fallback YouTube search results for '{query}'")
            return cached_result

        # Try each service in order
        for service, _ in self.services:
            try:
                self.logger.debug(f"Trying YouTube service: {service.__class__.__name__}")
                results = await service.search_videos(query, max_results, language)

                if results:
                    self.logger.info(f"YouTube search successful with {service.__class__.__name__} ({len(results)} results)")

                    # Cache the results
                    cache.setex(cache_key, self.cache_ttl, results)

                    return results
                else:
                    self.logger.warning(f"No results from {service.__class__.__name__}, trying next service")
            except Exception as e:
                self.logger.error(f"Error with YouTube service {service.__class__.__name__}: {str(e)}")

        # If all services fail, return empty list
        self.logger.error(f"All YouTube services failed for query: {query}")
        return []

    async def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific video using multiple implementations with fallback.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with video details or None if not found
        """
        # Check cache first
        cache_key = f"youtube:fallback:video:{video_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached fallback YouTube video details for '{video_id}'")
            return cached_result

        # Try each service in order
        for service, _ in self.services:
            try:
                self.logger.debug(f"Trying YouTube service for video details: {service.__class__.__name__}")
                result = await service.get_video_details(video_id)

                if result:
                    self.logger.info(f"YouTube video details successful with {service.__class__.__name__}")

                    # Cache the result
                    cache.setex(cache_key, self.cache_ttl, result)

                    return result
                else:
                    self.logger.warning(f"No video details from {service.__class__.__name__}, trying next service")
            except Exception as e:
                self.logger.error(f"Error with YouTube service {service.__class__.__name__}: {str(e)}")

        # If all services fail, return None
        self.logger.error(f"All YouTube services failed for video: {video_id}")
        return None

    async def search_videos_for_topic(self, topic: str, subtopic: str = None,
                                     max_results: int = 3, language: str = "en") -> List[Resource]:
        """
        Search for videos related to a topic and convert to Resource objects.

        Args:
            topic: Main topic
            subtopic: Optional subtopic for more specific results
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of Resource objects
        """
        # Check cache first
        cache_key = f"youtube:fallback:topic:{topic}_{subtopic}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached fallback YouTube topic results for '{topic}'")
            return cached_result

        # Try each service in order
        for service, _ in self.services:
            try:
                self.logger.debug(f"Trying YouTube service for topic: {service.__class__.__name__}")
                results = await service.search_videos_for_topic(topic, subtopic, max_results, language)

                if results:
                    self.logger.info(f"YouTube topic search successful with {service.__class__.__name__} ({len(results)} results)")

                    # Cache the results
                    cache.setex(cache_key, self.cache_ttl, results)

                    return results
                else:
                    self.logger.warning(f"No topic results from {service.__class__.__name__}, trying next service")
            except Exception as e:
                self.logger.error(f"Error with YouTube service {service.__class__.__name__}: {str(e)}")

        # If all services fail, return empty list
        self.logger.error(f"All YouTube services failed for topic: {topic}")
        return []
