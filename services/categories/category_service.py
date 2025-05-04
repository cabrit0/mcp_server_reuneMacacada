"""
Abstract interface for the category system.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class CategoryService(ABC):
    """
    Abstract interface for category services.
    Defines the methods that all category implementations must provide.
    """

    @abstractmethod
    def detect_category(self, topic: str) -> str:
        """
        Detect the category of a topic.

        Args:
            topic: Topic to categorize

        Returns:
            Category name (e.g., 'technology', 'health', 'general')
        """
        pass

    @abstractmethod
    def get_subtopics_for_category(self, topic: str, count: int = 10, category: Optional[str] = None) -> List[str]:
        """
        Generate subtopics for a topic based on its category.

        Args:
            topic: Main topic
            count: Number of subtopics to generate
            category: Optional category override (if None, will be detected)

        Returns:
            List of subtopic strings
        """
        pass

    @abstractmethod
    def get_category_specific_queries(self, topic: str, category: Optional[str] = None) -> List[str]:
        """
        Generate category-specific search queries for a topic.

        Args:
            topic: Main topic
            category: Optional category override (if None, will be detected)

        Returns:
            List of search query strings
        """
        pass

    @abstractmethod
    def get_all_categories(self) -> List[str]:
        """
        Get all available categories.

        Returns:
            List of category names
        """
        pass
