"""
Router for MCP-related endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks

from infrastructure.logging import logger
from infrastructure.cache import cache
from api.models import MCP, TaskCreationResponse
from core.content_sourcing import content_source
from core.path_generator import path_generator
from core.task_manager import task_service, Task
from api.routers.base_router import BaseRouter


class MCPRouter(BaseRouter):
    """
    Router for MCP-related endpoints.
    Handles synchronous and asynchronous MCP generation.
    """

    def __init__(self):
        """Initialize the MCP router."""
        self.router = APIRouter(tags=["MCP"])
        self.logger = logger.get_logger("api.routers.mcp")
        self._setup_routes()
        self.logger.info("Initialized MCPRouter")

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
            "/generate_mcp",
            self.generate_mcp_endpoint,
            methods=["GET"],
            response_model=MCP,
            summary="Generate MCP synchronously",
            description="Generate a Master Content Plan (MCP) for a given topic synchronously."
        )

        self.router.add_api_route(
            "/generate_mcp_async",
            self.generate_mcp_async_endpoint,
            methods=["POST"],
            response_model=TaskCreationResponse,
            summary="Generate MCP asynchronously",
            description="Generate a Master Content Plan (MCP) for a given topic asynchronously."
        )

    async def generate_mcp_endpoint(
        self,
        topic: str = Query(..., min_length=3, description="The topic to generate an MCP for"),
        max_resources: Optional[int] = Query(15, ge=5, le=30, description="Maximum number of resources to include"),
        num_nodes: Optional[int] = Query(15, ge=10, le=30, description="Number of nodes to include in the learning path"),
        min_width: Optional[int] = Query(3, ge=2, le=10, description="Minimum width of the tree (nodes at first level)"),
        max_width: Optional[int] = Query(5, ge=3, le=15, description="Maximum width at any level of the tree"),
        min_height: Optional[int] = Query(3, ge=2, le=8, description="Minimum height of the tree (depth)"),
        max_height: Optional[int] = Query(7, ge=3, le=12, description="Maximum height of the tree (depth)"),
        language: Optional[str] = Query("pt", description="Language for resources (e.g., 'pt', 'en', 'es')"),
        category: Optional[str] = Query(None, description="Category for the topic (e.g., 'technology', 'finance', 'health'). If not provided, it will be detected automatically."),
        similarity_threshold: Optional[float] = Query(0.15, ge=0.0, le=1.0, description="Minimum semantic similarity threshold for filtering resources (0-1)")
    ):
        """
        Generate a Master Content Plan (MCP) for a given topic.

        This endpoint:
        1. Searches for relevant resources on the web
        2. Organizes them into a structured learning path
        3. Returns a complete MCP in JSON format
        """
        try:
            self.logger.info(f"Received request for topic: {topic}")

            # Check cache first
            cache_key = f"mcp:{topic}_{max_resources}_{num_nodes}_{min_width}_{max_width}_{min_height}_{max_height}_{language}_{category}_{similarity_threshold}"
            cached_mcp = cache.get(cache_key)
            if cached_mcp:
                self.logger.info(f"Returning cached MCP for topic: {topic}")
                return MCP(**cached_mcp)

            # Find resources
            self.logger.info(f"Finding resources for topic: {topic} in language: {language}")
            resources = await content_source.find_resources(
                topic,
                max_results=max_resources,
                language=language,
                category=category,
                similarity_threshold=similarity_threshold
            )

            if not resources:
                self.logger.warning(f"No resources found for topic: {topic}")
                raise HTTPException(status_code=404, detail=f"No resources found for topic: {topic}")

            self.logger.info(f"Found {len(resources)} resources for topic: {topic}")

            # Generate learning path
            self.logger.info(f"Generating learning path for topic: {topic} with {num_nodes} nodes")
            try:
                mcp = await path_generator.generate_learning_path(
                    topic, resources,
                    min_nodes=num_nodes, max_nodes=num_nodes+10,
                    min_width=min_width, max_width=max_width,
                    min_height=min_height, max_height=max_height,
                    category=category, language=language
                )

                # Cache the result
                cache.setex(cache_key, 2592000, mcp.model_dump())  # 30 days
            except ValueError as ve:
                self.logger.warning(f"Could not generate enough nodes: {str(ve)}")
                raise HTTPException(status_code=400, detail=str(ve))

            self.logger.info(f"Successfully generated MCP for topic: {topic}")
            return mcp

        except Exception as e:
            self.logger.error(f"Error generating MCP for topic {topic}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating MCP: {str(e)}")

    async def generate_mcp_async_endpoint(
        self,
        background_tasks: BackgroundTasks,
        topic: str = Query(..., min_length=3, description="The topic to generate an MCP for"),
        max_resources: Optional[int] = Query(15, ge=5, le=30, description="Maximum number of resources to include"),
        num_nodes: Optional[int] = Query(15, ge=10, le=30, description="Number of nodes to include in the learning path"),
        min_width: Optional[int] = Query(3, ge=2, le=10, description="Minimum width of the tree (nodes at first level)"),
        max_width: Optional[int] = Query(5, ge=3, le=15, description="Maximum width at any level of the tree"),
        min_height: Optional[int] = Query(3, ge=2, le=8, description="Minimum height of the tree (depth)"),
        max_height: Optional[int] = Query(7, ge=3, le=12, description="Maximum height of the tree (depth)"),
        language: Optional[str] = Query("pt", description="Language for resources (e.g., 'pt', 'en', 'es')"),
        category: Optional[str] = Query(None, description="Category for the topic (e.g., 'technology', 'finance', 'health'). If not provided, it will be detected automatically."),
        similarity_threshold: Optional[float] = Query(0.15, ge=0.0, le=1.0, description="Minimum semantic similarity threshold for filtering resources (0-1)")
    ):
        """
        Generate a Master Content Plan (MCP) for a given topic asynchronously.

        This endpoint:
        1. Creates a background task to generate the MCP
        2. Returns immediately with a task ID
        3. The client can check the task status using the /status/{task_id} endpoint
        """
        self.logger.info(f"Received async request for topic: {topic}")

        # Check cache first
        cache_key = f"mcp:{topic}_{max_resources}_{num_nodes}_{min_width}_{max_width}_{min_height}_{max_height}_{language}_{category}_{similarity_threshold}"
        cached_mcp = cache.get(cache_key)
        if cached_mcp:
            self.logger.info(f"Found cached MCP for topic: {topic}")
            # Create a completed task with the cached result
            task = task_service.create_task(f"Generate MCP for topic: {topic}")
            # Use the cached result directly
            task.mark_as_completed(cached_mcp)
            return TaskCreationResponse(task_id=task.id, message="Task completed immediately (cached result)")

        # Create a new task
        task = task_service.create_task(f"Generate MCP for topic: {topic}")

        # Add the task to background tasks
        background_tasks.add_task(
            self._process_mcp_generation,
            task_id=task.id,
            topic=topic,
            max_resources=max_resources,
            num_nodes=num_nodes,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            language=language,
            category=category,
            similarity_threshold=similarity_threshold
        )

        return TaskCreationResponse(task_id=task.id)

    async def _process_mcp_generation(
        self,
        task_id: str,
        topic: str,
        max_resources: int,
        num_nodes: int,
        min_width: int,
        max_width: int,
        min_height: int,
        max_height: int,
        language: str,
        category: Optional[str] = None,
        similarity_threshold: float = 0.15
    ):
        """
        Process MCP generation in the background.

        Args:
            task_id: The ID of the task
            topic: The topic to generate an MCP for
            max_resources: Maximum number of resources to include
            num_nodes: Number of nodes to include in the learning path
            min_width: Minimum width of the tree
            max_width: Maximum width of the tree
            min_height: Minimum height of the tree
            max_height: Maximum height of the tree
            language: Language for resources
            category: Category for the topic
            similarity_threshold: Minimum semantic similarity threshold for filtering resources
        """
        task = task_service.get_task(task_id)
        if not task:
            self.logger.error(f"Task {task_id} not found")
            return

        try:
            # Update task status
            task.mark_as_running()
            task.update_progress(10, "Starting resource search")

            # Find resources
            task.update_progress(20, "Searching for resources")
            resources = await content_source.find_resources(
                topic,
                max_results=max_resources,
                language=language,
                category=category,
                similarity_threshold=similarity_threshold
            )

            if not resources:
                task.mark_as_failed(f"No resources found for topic: {topic}")
                return

            task.update_progress(40, f"Found and filtered {len(resources)} resources for topic: {topic}")

            # Generate learning path
            task.update_progress(50, "Generating learning tree structure")
            try:
                task.update_progress(60, "Creating nodes and relationships")
                mcp = await path_generator.generate_learning_path(
                    topic, resources,
                    min_nodes=num_nodes, max_nodes=num_nodes+10,
                    min_width=min_width, max_width=max_width,
                    min_height=min_height, max_height=max_height,
                    category=category, language=language
                )

                task.update_progress(80, "Learning tree generated successfully")

                # Cache the result
                cache_key = f"mcp:{topic}_{max_resources}_{num_nodes}_{min_width}_{max_width}_{min_height}_{max_height}_{language}_{category}_{similarity_threshold}"
                cache.setex(cache_key, 2592000, mcp.model_dump())  # 30 days

                task.update_progress(90, "Caching results for future use")

                # Mark task as completed with the MCP as result
                task.update_progress(100, "Learning tree generation complete")
                task.mark_as_completed(mcp.model_dump())
                self.logger.info(f"Task {task_id} completed successfully with {len(mcp.nodes)} nodes")

            except ValueError as ve:
                task.mark_as_failed(f"Could not generate enough nodes: {str(ve)}")
                self.logger.warning(f"Task {task_id} failed: {str(ve)}")

        except Exception as e:
            task.mark_as_failed(f"Error generating MCP: {str(e)}")
            self.logger.error(f"Task {task_id} failed with error: {str(e)}")
