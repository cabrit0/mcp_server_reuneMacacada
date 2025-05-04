"""
Router for health check endpoints.
"""

from fastapi import APIRouter

from infrastructure.logging import logger
from api.routers.base_router import BaseRouter


class HealthRouter(BaseRouter):
    """
    Router for health check endpoints.
    Provides endpoints for monitoring the health of the application.
    """

    def __init__(self):
        """Initialize the health router."""
        self.router = APIRouter(tags=["Health"])
        self.logger = logger.get_logger("api.routers.health")
        self._setup_routes()
        self.logger.info("Initialized HealthRouter")

    def get_router(self) -> APIRouter:
        """
        Get the FastAPI router.

        Returns:
            FastAPI router
        """
        return self.router

    def _setup_routes(self):
        """Set up the router routes."""
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="Health check",
            description="Health check endpoint to verify the server is running."
        )

    async def health_check(self):
        """
        Health check endpoint to verify the server is running.

        Returns:
            Dictionary with status
        """
        self.logger.debug("Health check requested")
        return {"status": "ok"}
