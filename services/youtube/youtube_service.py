"""
Abstract interface for the YouTube integration.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from api.models import Resource


class YouTubeService(ABC):
    """
    Abstract interface for YouTube services.
    Defines the methods that all YouTube implementations must provide.
    """

    @abstractmethod
    async def search_videos(self, query: str, max_results: int = 5, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for YouTube videos.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with video information
        """
        pass

    @abstractmethod
    async def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific video.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with video details or None if not found
        """
        pass

    @abstractmethod
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
        pass
