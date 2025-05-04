"""
Abstract interface for the exercise generator system.
"""

from abc import ABC, abstractmethod
from typing import List

from api.models import ExerciseSet, Resource


class ExerciseGeneratorService(ABC):
    """
    Abstract interface for exercise generator services.
    Defines the methods that all exercise generator implementations must provide.
    """

    @abstractmethod
    def generate_exercise_set(self, topic: str, node_title: str, resources: List[Resource]) -> ExerciseSet:
        """
        Generate an exercise set for a node based on its resources.

        Args:
            topic: The topic of the learning path
            node_title: The title of the node
            resources: List of resources in the node

        Returns:
            ExerciseSet object with exercises
        """
        pass

    @abstractmethod
    def generate_hints(self, topic: str, node_title: str, exercise_description: str) -> List[str]:
        """
        Generate hints for an exercise.

        Args:
            topic: The topic of the learning path
            node_title: The title of the node
            exercise_description: The description of the exercise

        Returns:
            List of hints for the exercise
        """
        pass
