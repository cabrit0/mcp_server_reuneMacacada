"""
Abstract interface for the search service.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SearchService(ABC):
    """
    Abstract interface for search services.
    Defines the methods that all search implementations must provide.
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 5,
        language: str = "pt"
    ) -> List[Dict[str, Any]]:
        """
        Search for resources using a query.

        Args:
            query: The search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            List of dictionaries with search results (title, url, etc.)
        """
        pass
