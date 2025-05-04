"""
Persistent implementation of the task service.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, List

from infrastructure.logging import logger
from core.task_manager.task_service import TaskService
from core.task_manager.task import Task
from core.task_manager.default_task_service import DefaultTaskService


class PersistentTaskService(TaskService):
    """
    Persistent implementation of the task service.
    Saves tasks to disk for persistence across server restarts.
    """

    def __init__(
        self,
        storage_dir: str,
        base_service: Optional[TaskService] = None,
        max_tasks: int = 100
    ):
        """
        Initialize the persistent task service.

        Args:
            storage_dir: Directory to store task data
            base_service: Optional base task service to delegate to
            max_tasks: Maximum number of tasks to store
        """
        self.storage_dir = storage_dir
        self.base_service = base_service or DefaultTaskService(max_tasks)
        self.logger = logger.get_logger("task_manager.persistent")
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        
        # Load existing tasks
        self._load_tasks()
        
        self.logger.info(f"Initialized PersistentTaskService with storage_dir={storage_dir}")

    def create_task(self, description: str) -> Task:
        """
        Create a new task.

        Args:
            description: Description of the task

        Returns:
            The created task
        """
        task = self.base_service.create_task(description)
        self._save_task(task)
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: ID of the task

        Returns:
            The task or None if not found
        """
        return self.base_service.get_task(task_id)

    def get_all_tasks(self) -> Dict[str, Task]:
        """
        Get all tasks.

        Returns:
            Dictionary mapping task IDs to tasks
        """
        return self.base_service.get_all_tasks()

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
        # Update task status before running
        task.mark_as_running()
        self._save_task(task)
        
        try:
            # Run the task using the base service
            result = await self.base_service.run_task(task, func, *args, **kwargs)
            
            # Save the completed task
            self._save_task(task)
            
            return result
            
        except Exception as e:
            # Save the failed task
            self._save_task(task)
            raise

    def clean_old_tasks(self, count: Optional[int] = None) -> int:
        """
        Remove old tasks to free up space.

        Args:
            count: Number of tasks to remove (if None, uses default strategy)

        Returns:
            Number of tasks removed
        """
        removed_count = self.base_service.clean_old_tasks(count)
        
        # Clean up task files
        if removed_count > 0:
            self._cleanup_task_files()
            
        return removed_count

    def _save_task(self, task: Task) -> None:
        """
        Save a task to disk.

        Args:
            task: Task to save
        """
        try:
            task_file = os.path.join(self.storage_dir, f"{task.id}.json")
            with open(task_file, 'w') as f:
                json.dump(task.to_dict(), f)
            self.logger.debug(f"Saved task {task.id} to disk")
        except Exception as e:
            self.logger.error(f"Error saving task {task.id} to disk: {str(e)}")

    def _load_tasks(self) -> None:
        """Load tasks from disk."""
        try:
            # Get all task files
            task_files = [f for f in os.listdir(self.storage_dir) if f.endswith('.json')]
            
            loaded_count = 0
            for file_name in task_files:
                try:
                    task_id = file_name.replace('.json', '')
                    task_file = os.path.join(self.storage_dir, file_name)
                    
                    with open(task_file, 'r') as f:
                        task_data = json.load(f)
                        
                    # Create task from data
                    task = Task.from_dict(task_data)
                    
                    # Add to base service
                    self.base_service.tasks[task.id] = task
                    loaded_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error loading task from {file_name}: {str(e)}")
            
            self.logger.info(f"Loaded {loaded_count} tasks from disk")
            
        except Exception as e:
            self.logger.error(f"Error loading tasks from disk: {str(e)}")

    def _cleanup_task_files(self) -> None:
        """Clean up task files that are no longer needed."""
        try:
            # Get all task files
            task_files = [f for f in os.listdir(self.storage_dir) if f.endswith('.json')]
            
            # Get current task IDs
            current_task_ids = set(self.base_service.tasks.keys())
            
            removed_count = 0
            for file_name in task_files:
                task_id = file_name.replace('.json', '')
                
                # If task is no longer in memory, remove the file
                if task_id not in current_task_ids:
                    task_file = os.path.join(self.storage_dir, file_name)
                    os.remove(task_file)
                    removed_count += 1
            
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} task files from disk")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up task files: {str(e)}")
