"""
Base interface for documentation services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from api.models import Resource


class DocumentationService(ABC):
    """
    Abstract base class for documentation services.
    Defines the interface that all documentation services must implement.
    """

    @abstractmethod
    async def search_documentation(
        self,
        topic: str,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Search for documentation related to a topic.

        Args:
            topic: Topic to search for
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with documentation information
        """
        pass

    @abstractmethod
    async def get_documentation_details(
        self,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific documentation item.

        Args:
            doc_id: Documentation ID

        Returns:
            Dictionary with documentation details or None if not found
        """
        pass

    @abstractmethod
    async def search_documentation_for_topic(
        self,
        topic: str,
        subtopic: str = None,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Resource]:
        """
        Search for documentation related to a topic and convert to Resource objects.

        Args:
            topic: Main topic
            subtopic: Optional subtopic for more specific results
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of Resource objects
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of the documentation service.

        Returns:
            Service name
        """
        pass

    @property
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """
        Get the list of languages supported by this documentation service.

        Returns:
            List of language codes (e.g., ['en', 'pt'])
        """
        pass

    @property
    @abstractmethod
    def supported_topics(self) -> List[str]:
        """
        Get the list of topics supported by this documentation service.

        Returns:
            List of topic names (e.g., ['web', 'python', 'javascript'])
        """
        pass
