"""
Abstract interface for the task management system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Awaitable, List

from core.task_manager.task import Task


class TaskService(ABC):
    """
    Abstract interface for task services.
    Defines the methods that all task service implementations must provide.
    """

    @abstractmethod
    def create_task(self, description: str) -> Task:
        """
        Create a new task.

        Args:
            description: Description of the task

        Returns:
            The created task
        """
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: ID of the task

        Returns:
            The task or None if not found
        """
        pass

    @abstractmethod
    def get_all_tasks(self) -> Dict[str, Task]:
        """
        Get all tasks.

        Returns:
            Dictionary mapping task IDs to tasks
        """
        pass

    @abstractmethod
    async def run_task(
        self,
        task: Task,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Any:
        """
        Run an asynchronous function as a task.

        Args:
            task: The task to run
            func: The asynchronous function to run
            *args, **kwargs: Arguments for the function

        Returns:
            The result of the function
        """
        pass

    @abstractmethod
    def clean_old_tasks(self, count: Optional[int] = None) -> int:
        """
        Remove old tasks to free up space.

        Args:
            count: Number of tasks to remove (if None, uses default strategy)

        Returns:
            Number of tasks removed
        """
        pass
