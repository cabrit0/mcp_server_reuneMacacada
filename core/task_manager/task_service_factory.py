"""
Factory for creating task service instances.
"""

import os
from typing import Dict, Any, Optional

from infrastructure.logging import logger
from core.task_manager.task_service import TaskService
from core.task_manager.default_task_service import DefaultTaskService
from core.task_manager.persistent_task_service import PersistentTaskService


class TaskServiceFactory:
    """
    Factory for creating task service instances.
    """

    # Singleton instances
    _instances: Dict[str, TaskService] = {}

    @classmethod
    def create_task_service(
        cls,
        service_type: str = "default",
        config_options: Optional[Dict[str, Any]] = None
    ) -> TaskService:
        """
        Create a task service instance.

        Args:
            service_type: Type of service to create ("default", "persistent")
            config_options: Configuration options for the service

        Returns:
            Task service instance implementing TaskService
        """
        # Use singleton pattern for efficiency
        if service_type in cls._instances:
            return cls._instances[service_type]
        
        # Default config options
        if config_options is None:
            config_options = {}
        
        # Create service instance
        service: TaskService
        
        if service_type == "default":
            max_tasks = config_options.get("max_tasks", 100)
            service = DefaultTaskService(max_tasks=max_tasks)
            
        elif service_type == "persistent":
            storage_dir = config_options.get("storage_dir", "data/tasks")
            max_tasks = config_options.get("max_tasks", 100)
            
            # Create base service
            base_service = DefaultTaskService(max_tasks=max_tasks)
            
            # Create persistent service
            service = PersistentTaskService(
                storage_dir=storage_dir,
                base_service=base_service,
                max_tasks=max_tasks
            )
            
        else:
            logger.warning(f"Unknown task service type: {service_type}, falling back to default")
            return cls.create_task_service("default", config_options)
        
        # Store instance for reuse
        cls._instances[service_type] = service
        
        return service
