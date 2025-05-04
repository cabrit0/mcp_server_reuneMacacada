"""
Abstract interface for the path generator system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional

from api.models import MCP, Resource


class PathGeneratorService(ABC):
    """
    Abstract interface for path generator services.
    Defines the methods that all path generator implementations must provide.
    """

    @abstractmethod
    async def generate_learning_path(
        self,
        topic: str,
        resources: List[Resource],
        min_nodes: int = 15,
        max_nodes: int = 28,
        min_width: int = 3,
        max_width: int = 5,
        min_height: int = 3,
        max_height: int = 7,
        category: Optional[str] = None,
        language: str = "pt"
    ) -> MCP:
        """
        Generate a learning path based on a topic and a list of resources.

        Args:
            topic: The topic of the learning path
            resources: List of resources to include in the path
            min_nodes: Minimum number of nodes in the learning path
            max_nodes: Maximum number of nodes in the learning path
            min_width: Minimum width of the tree (nodes at first level)
            max_width: Maximum width at any level of the tree
            min_height: Minimum height of the tree (depth)
            max_height: Maximum height of the tree (depth)
            category: Category for the topic (if None, will be detected automatically)
            language: Language for resources (e.g., 'pt', 'en', 'es')

        Returns:
            MCP object representing the learning path
        """
        pass

    @abstractmethod
    def estimate_total_hours(self, resources: List[Resource]) -> int:
        """
        Estimate the total hours needed to complete the learning path.

        Args:
            resources: List of resources in the learning path

        Returns:
            Estimated hours
        """
        pass

    @abstractmethod
    def generate_tags(self, topic: str, resources: List[Resource]) -> List[str]:
        """
        Generate tags for the MCP based on the topic and resources.

        Args:
            topic: The topic of the learning path
            resources: List of resources in the learning path

        Returns:
            List of tags
        """
        pass
