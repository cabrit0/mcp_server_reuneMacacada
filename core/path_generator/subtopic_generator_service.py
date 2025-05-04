"""
Abstract interface for the subtopic generator system.
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class SubtopicGeneratorService(ABC):
    """
    Abstract interface for subtopic generator services.
    Defines the methods that all subtopic generator implementations must provide.
    """

    @abstractmethod
    def generate_subtopics(self, topic: str, count: int = 10, category: Optional[str] = None) -> List[str]:
        """
        Generate subtopics based on a main topic.

        Args:
            topic: The main topic
            count: Number of subtopics to generate
            category: Optional category override (if None, will be detected)

        Returns:
            List of subtopic strings
        """
        pass
