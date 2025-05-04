"""
Router for task-related endpoints.
"""

from typing import List
from fastapi import APIRouter, Path, HTTPException

from infrastructure.logging import logger
from api.models import TaskInfo
from core.task_manager import task_service
from api.routers.base_router import BaseRouter


class TaskRouter(BaseRouter):
    """
    Router for task-related endpoints.
    Handles task status and listing.
    """

    def __init__(self):
        """Initialize the task router."""
        self.router = APIRouter(tags=["Tasks"])
        self.logger = logger.get_logger("api.routers.task")
        self._setup_routes()
        self.logger.info("Initialized TaskRouter")

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
            "/status/{task_id}",
            self.get_task_status,
            methods=["GET"],
            response_model=TaskInfo,
            summary="Get task status",
            description="Get the status of a task."
        )

        self.router.add_api_route(
            "/tasks",
            self.list_tasks,
            methods=["GET"],
            response_model=List[TaskInfo],
            summary="List all tasks",
            description="List all tasks."
        )

    async def get_task_status(self, task_id: str = Path(..., description="The ID of the task to check")):
        """
        Get the status of a task.

        Args:
            task_id: The ID of the task to check

        Returns:
            Information about the task
        """
        task = task_service.get_task(task_id)
        if not task:
            self.logger.warning(f"Task with ID {task_id} not found")
            raise HTTPException(status_code=404, detail=f"Task with ID {task_id} not found")

        self.logger.debug(f"Retrieved status for task {task_id}")
        return task.to_dict()

    async def list_tasks(self):
        """
        List all tasks.

        Returns:
            List of all tasks
        """
        tasks = task_service.get_all_tasks()
        self.logger.debug(f"Retrieved {len(tasks)} tasks")
        return [task.to_dict() for task in tasks.values()]
