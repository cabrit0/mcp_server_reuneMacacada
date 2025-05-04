"""
Abstract interface for the content sourcing system.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from api.models import Resource


class ContentSourceService(ABC):
    """
    Abstract interface for content source services.
    Defines the methods that all content source implementations must provide.
    """

    @abstractmethod
    async def find_resources(
        self,
        topic: str,
        max_results: int = 15,
        language: str = "pt",
        category: Optional[str] = None
    ) -> List[Resource]:
        """
        Find resources about a topic.

        Args:
            topic: The topic to search for
            max_results: Maximum number of resources to return
            language: Language code (e.g., 'pt', 'en', 'es')
            category: Optional category override (if None, will be detected)

        Returns:
            List of Resource objects
        """
        pass

    @abstractmethod
    async def find_resources_by_query(
        self,
        query: str,
        topic: str,
        max_results: int = 5,
        language: str = "pt"
    ) -> List[Resource]:
        """
        Find resources using a specific search query.

        Args:
            query: The search query
            topic: The main topic (for context)
            max_results: Maximum number of resources to return
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            List of Resource objects
        """
        pass

    @abstractmethod
    def filter_resources(
        self,
        resources: List[Resource],
        topic: str,
        max_results: int = 15,
        language: str = "pt"
    ) -> List[Resource]:
        """
        Filter and prioritize resources.

        Args:
            resources: List of resources to filter
            topic: The topic to filter by
            max_results: Maximum number of resources to return
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            Filtered list of Resource objects
        """
        pass
