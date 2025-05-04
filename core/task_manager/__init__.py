# This file is part of the MCP Server package.

from core.task_manager.task import Task, TaskStatus
from core.task_manager.task_service import TaskService
from core.task_manager.task_service_factory import TaskServiceFactory

# Create a global task service instance
# Use persistent service by default for better reliability
task_service: TaskService = TaskServiceFactory.create_task_service(
    "persistent",
    {
        "storage_dir": "data/tasks",
        "max_tasks": 100
    }
)

__all__ = ["task_service", "Task", "TaskStatus", "TaskService", "TaskServiceFactory"]
