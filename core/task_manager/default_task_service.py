"""
Default implementation of the task service.
"""

import uuid
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, List

from infrastructure.logging import logger
from core.task_manager.task_service import TaskService
from core.task_manager.task import Task


class DefaultTaskService(TaskService):
    """
    Default implementation of the task service.
    Manages asynchronous tasks with progress tracking.
    """

    def __init__(self, max_tasks: int = 100):
        """
        Initialize the default task service.

        Args:
            max_tasks: Maximum number of tasks to store
        """
        self.tasks: Dict[str, Task] = {}
        self.max_tasks = max_tasks
        self.logger = logger.get_logger("task_manager.default")
        self.logger.info(f"Initialized DefaultTaskService with max_tasks={max_tasks}")

    def create_task(self, description: str) -> Task:
        """
        Create a new task.

        Args:
            description: Description of the task

        Returns:
            The created task
        """
        task_id = str(uuid.uuid4())
        task = Task(task_id, description)
        
        # Clean up old tasks if necessary
        if len(self.tasks) >= self.max_tasks:
            self.clean_old_tasks()
        
        self.tasks[task_id] = task
        self.logger.info(f"Created task {task_id}: {description}")
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: ID of the task

        Returns:
            The task or None if not found
        """
        task = self.tasks.get(task_id)
        if task:
            self.logger.debug(f"Retrieved task {task_id}")
        else:
            self.logger.warning(f"Task {task_id} not found")
        return task

    def get_all_tasks(self) -> Dict[str, Task]:
        """
        Get all tasks.

        Returns:
            Dictionary mapping task IDs to tasks
        """
        self.logger.debug(f"Retrieved all tasks ({len(self.tasks)} tasks)")
        return self.tasks

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
        task.mark_as_running()
        self.logger.info(f"Running task {task.id}: {task.description}")
        
        try:
            # Run the function
            result = await func(*args, **kwargs)
            
            # Mark as completed
            task.mark_as_completed(result)
            self.logger.info(f"Task {task.id} completed successfully")
            return result
            
        except asyncio.CancelledError:
            # Handle task cancellation
            task.mark_as_canceled("Task was cancelled")
            self.logger.warning(f"Task {task.id} was cancelled")
            raise
            
        except Exception as e:
            # Mark as failed
            error_message = str(e)
            self.logger.error(f"Task {task.id} failed: {error_message}")
            task.mark_as_failed(error_message)
            raise

    def clean_old_tasks(self, count: Optional[int] = None) -> int:
        """
        Remove old tasks to free up space.

        Args:
            count: Number of tasks to remove (if None, removes 10% of tasks)

        Returns:
            Number of tasks removed
        """
        # Sort tasks by creation date (oldest first)
        sorted_tasks = sorted(
            self.tasks.items(),
            key=lambda x: x[1].created_at
        )
        
        # Determine how many tasks to remove
        if count is None:
            tasks_to_remove = max(1, len(self.tasks) // 10)  # Remove at least 1, up to 10%
        else:
            tasks_to_remove = min(count, len(self.tasks))
        
        # Remove the oldest tasks
        removed_count = 0
        for i in range(tasks_to_remove):
            if i < len(sorted_tasks):
                task_id = sorted_tasks[i][0]
                del self.tasks[task_id]
                removed_count += 1
                self.logger.info(f"Removed old task {task_id}")
        
        return removed_count
