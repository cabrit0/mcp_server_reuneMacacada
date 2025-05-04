"""
Base router interface for the API.
"""

from abc import ABC, abstractmethod
from fastapi import APIRouter


class BaseRouter(ABC):
    """
    Base router interface for the API.
    Defines the methods that all routers must provide.
    """

    @abstractmethod
    def get_router(self) -> APIRouter:
        """
        Get the FastAPI router.

        Returns:
            FastAPI router
        """
        pass
