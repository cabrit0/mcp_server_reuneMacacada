"""
Abstract interface for the quiz generator system.
"""

from abc import ABC, abstractmethod
from typing import List

from api.models import Quiz, Resource


class QuizGeneratorService(ABC):
    """
    Abstract interface for quiz generator services.
    Defines the methods that all quiz generator implementations must provide.
    """

    @abstractmethod
    def generate_quiz(self, topic: str, node_title: str, resources: List[Resource]) -> Quiz:
        """
        Generate a quiz for a node based on its resources.

        Args:
            topic: The topic of the learning path
            node_title: The title of the node
            resources: List of resources in the node

        Returns:
            Quiz object with questions
        """
        pass
