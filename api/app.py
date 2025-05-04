"""
FastAPI application for the MCP Server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from infrastructure.logging import logger
from api.routers import HealthRouter, MCPRouter, TaskRouter, CacheRouter


class MCPServerApp:
    """
    FastAPI application for the MCP Server.
    Configures the application and includes all routers.
    """

    def __init__(self, title: str = "MCP Server", version: str = "1.1.3"):
        """
        Initialize the MCP Server application.

        Args:
            title: Title of the application
            version: Version of the application
        """
        self.app = FastAPI(
            title=title,
            description="Server that generates Master Content Plans (MCPs) based on topics",
            version=version
        )
        self.logger = logger.get_logger("api.app")
        
        # Configure CORS
        self._configure_cors()
        
        # Include routers
        self._include_routers()
        
        self.logger.info(f"Initialized MCPServerApp v{version}")

    def get_app(self) -> FastAPI:
        """
        Get the FastAPI application.

        Returns:
            FastAPI application
        """
        return self.app

    def _configure_cors(self):
        """Configure CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, replace with specific origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.logger.debug("Configured CORS middleware")

    def _include_routers(self):
        """Include all routers in the application."""
        # Create routers
        health_router = HealthRouter()
        mcp_router = MCPRouter()
        task_router = TaskRouter()
        cache_router = CacheRouter()
        
        # Include routers
        self.app.include_router(health_router.get_router())
        self.app.include_router(mcp_router.get_router())
        self.app.include_router(task_router.get_router())
        self.app.include_router(cache_router.get_router())
        
        self.logger.debug("Included all routers")
