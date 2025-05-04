"""
Abstract interface for the search system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SearchService(ABC):
    """
    Abstract interface for search services.
    Defines the methods that all search implementations must provide.
    """

    @abstractmethod
    async def search(self, query: str, max_results: int = 10, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for a query.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with title, URL, and description
        """
        pass

    @abstractmethod
    async def search_with_retry(self, query: str, max_results: int = 10, language: str = "en", 
                               max_retries: int = 3, backoff_factor: float = 1.5) -> List[Dict[str, Any]]:
        """
        Search with retry and exponential backoff.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')
            max_retries: Maximum number of retries
            backoff_factor: Backoff factor for exponential backoff

        Returns:
            List of dictionaries with title, URL, and description
        """
        pass
