"""
Task class for the task management system.
"""

import time
from typing import Dict, Any, List, Optional
from enum import Enum


class TaskStatus(str, Enum):
    """Possible statuses for a task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class Task:
    """Represents an asynchronous task with status and progress."""
    
    def __init__(self, task_id: str, description: str):
        """
        Initialize a new task.

        Args:
            task_id: Unique identifier for the task
            description: Description of the task
        """
        self.id = task_id
        self.description = description
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = time.time()
        self.updated_at = time.time()
        self.completed_at = None
        self.messages: List[Dict[str, Any]] = []
    
    def update_progress(self, progress: int, message: Optional[str] = None) -> None:
        """
        Update the progress of the task.

        Args:
            progress: Progress percentage (0-100)
            message: Optional message to add
        """
        self.progress = min(max(progress, 0), 100)  # Ensure it's between 0-100
        self.updated_at = time.time()
        
        if message:
            self.add_message(message)
    
    def add_message(self, message: str) -> None:
        """
        Add a message to the task's history.

        Args:
            message: Message to add
        """
        self.messages.append({
            "time": time.time(),
            "message": message
        })
    
    def mark_as_running(self) -> None:
        """Mark the task as running."""
        self.status = TaskStatus.RUNNING
        self.updated_at = time.time()
        self.add_message("Task started")
    
    def mark_as_completed(self, result: Any = None) -> None:
        """
        Mark the task as completed.

        Args:
            result: Optional result of the task
        """
        self.status = TaskStatus.COMPLETED
        self.progress = 100
        self.result = result
        self.updated_at = time.time()
        self.completed_at = time.time()
        self.add_message("Task completed successfully")
    
    def mark_as_failed(self, error: str) -> None:
        """
        Mark the task as failed.

        Args:
            error: Error message
        """
        self.status = TaskStatus.FAILED
        self.error = error
        self.updated_at = time.time()
        self.completed_at = time.time()
        self.add_message(f"Task failed: {error}")
    
    def mark_as_canceled(self, reason: Optional[str] = None) -> None:
        """
        Mark the task as canceled.

        Args:
            reason: Optional reason for cancellation
        """
        self.status = TaskStatus.CANCELED
        self.updated_at = time.time()
        self.completed_at = time.time()
        message = f"Task canceled: {reason}" if reason else "Task canceled"
        self.add_message(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task to a dictionary.

        Returns:
            Dictionary representation of the task
        """
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "messages": self.messages
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """
        Create a task from a dictionary.

        Args:
            data: Dictionary representation of a task

        Returns:
            Task object
        """
        task = cls(data["id"], data["description"])
        task.status = TaskStatus(data["status"])
        task.progress = data["progress"]
        task.result = data["result"]
        task.error = data["error"]
        task.created_at = data["created_at"]
        task.updated_at = data["updated_at"]
        task.completed_at = data["completed_at"]
        task.messages = data["messages"]
        return task
