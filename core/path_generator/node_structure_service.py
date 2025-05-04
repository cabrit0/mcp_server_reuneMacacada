"""
Abstract interface for the node structure system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional

from api.models import Node, Resource


class NodeStructureService(ABC):
    """
    Abstract interface for node structure services.
    Defines the methods that all node structure implementations must provide.
    """

    @abstractmethod
    async def create_node_structure(
        self,
        topic: str,
        subtopics: List[str],
        resources: List[Resource],
        min_nodes: int = 15,
        max_nodes: int = 28,
        min_width: int = 3,
        max_width: int = 5,
        min_height: int = 3,
        max_height: int = 7,
        language: str = "pt"
    ) -> Tuple[Dict[str, Node], List[str]]:
        """
        Create a node structure with the given subtopics.

        Args:
            topic: The main topic
            subtopics: List of subtopics
            resources: List of resources to distribute
            min_nodes: Minimum number of nodes
            max_nodes: Maximum number of nodes
            min_width: Minimum width of the tree (nodes at first level)
            max_width: Maximum width at any level of the tree
            min_height: Minimum height of the tree (depth)
            max_height: Maximum height of the tree (depth)
            language: Language for resources

        Returns:
            Tuple of (nodes dictionary, list of node IDs)
        """
        pass

    @abstractmethod
    def distribute_quizzes(
        self,
        nodes: Dict[str, Node],
        node_ids: List[str],
        topic: str,
        resources: List[Resource],
        target_percentage: float = 0.25
    ) -> Dict[str, Node]:
        """
        Distribute quizzes strategically across the learning tree.

        Args:
            nodes: Dictionary of nodes
            node_ids: List of node IDs
            topic: The main topic
            resources: List of resources
            target_percentage: Target percentage of nodes to have quizzes

        Returns:
            Updated dictionary of nodes
        """
        pass

    def get_nodes(self) -> Dict[str, Node]:
        """
        Get the current nodes dictionary.

        Returns:
            Dictionary of nodes
        """
        return {}
