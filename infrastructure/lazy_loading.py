"""
Lazy loading implementation for services.

This module provides a lazy loading mechanism for services to improve
startup time and reduce memory usage by only initializing services
when they are actually needed.
"""

import logging
import threading
from typing import Dict, Any, Type, TypeVar, Callable, Optional, List, Set

# Configure logging
logger = logging.getLogger("mcp_server.lazy_loading")

# Type variable for service classes
T = TypeVar('T')


class LazyServiceLoader:
    """
    Lazy service loader that initializes services only when needed.

    This class provides a way to defer the initialization of services
    until they are actually needed, which can improve startup time
    and reduce memory usage.
    """

    # Class-level storage for singleton instances
    _instances: Dict[str, Any] = {}
    _locks: Dict[str, threading.Lock] = {}
    _dependencies: Dict[str, Set[str]] = {}

    @classmethod
    def get_instance(cls, service_name: str, service_class: Type[T], *args: Any, **kwargs: Any) -> T:
        """
        Get or create a service instance.

        Args:
            service_name: Name of the service
            service_class: Class of the service
            *args: Positional arguments for the service constructor
            **kwargs: Keyword arguments for the service constructor

        Returns:
            Service instance
        """
        # Check if instance already exists
        if service_name in cls._instances:
            return cls._instances[service_name]

        # Create lock if it doesn't exist
        if service_name not in cls._locks:
            cls._locks[service_name] = threading.Lock()

        # Acquire lock to prevent race conditions
        with cls._locks[service_name]:
            # Check again in case another thread created the instance
            if service_name in cls._instances:
                return cls._instances[service_name]

            # Create instance
            logger.info(f"Lazy loading service: {service_name}")
            instance = service_class(*args, **kwargs)
            cls._instances[service_name] = instance

            return instance

    @classmethod
    def register_dependency(cls, service_name: str, depends_on: str) -> None:
        """
        Register a dependency between services.

        Args:
            service_name: Name of the dependent service
            depends_on: Name of the service it depends on
        """
        if service_name not in cls._dependencies:
            cls._dependencies[service_name] = set()

        cls._dependencies[service_name].add(depends_on)

    @classmethod
    def get_dependencies(cls, service_name: str) -> Set[str]:
        """
        Get the dependencies of a service.

        Args:
            service_name: Name of the service

        Returns:
            Set of service names that this service depends on
        """
        return cls._dependencies.get(service_name, set())

    @classmethod
    def get_dependents(cls, service_name: str) -> Set[str]:
        """
        Get the services that depend on this service.

        Args:
            service_name: Name of the service

        Returns:
            Set of service names that depend on this service
        """
        dependents = set()
        for dependent, dependencies in cls._dependencies.items():
            if service_name in dependencies:
                dependents.add(dependent)

        return dependents

    @classmethod
    def is_initialized(cls, service_name: str) -> bool:
        """
        Check if a service is initialized.

        Args:
            service_name: Name of the service

        Returns:
            True if the service is initialized
        """
        return service_name in cls._instances

    @classmethod
    def get_all_initialized(cls) -> List[str]:
        """
        Get all initialized services.

        Returns:
            List of initialized service names
        """
        return list(cls._instances.keys())

    @classmethod
    def clear_instance(cls, service_name: str) -> None:
        """
        Clear a service instance.

        Args:
            service_name: Name of the service
        """
        if service_name in cls._instances:
            # Check for dependents
            dependents = cls.get_dependents(service_name)
            if dependents:
                logger.warning(
                    f"Clearing service {service_name} that has dependents: {dependents}. "
                    f"This may cause issues if those services are still in use."
                )

            # Remove instance
            del cls._instances[service_name]
            logger.info(f"Cleared service instance: {service_name}")

    @classmethod
    def clear_all(cls) -> None:
        """
        Clear all service instances.
        """
        cls._instances.clear()
        logger.info("Cleared all service instances")


def lazy_service(service_name: str, depends_on: Optional[List[str]] = None) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator for lazy loading services.

    Args:
        service_name: Name of the service
        depends_on: List of services this service depends on

    Returns:
        Decorated class
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Store original __init__ method
        original_init = cls.__init__

        # Define new __init__ method
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            # Register dependencies
            if depends_on:
                for dependency in depends_on:
                    LazyServiceLoader.register_dependency(service_name, dependency)

            # Call original __init__
            original_init(self, *args, **kwargs)

            # Register instance
            LazyServiceLoader._instances[service_name] = self

        # Replace __init__ method
        cls.__init__ = __init__

        # Create a factory function
        def get_instance(*args: Any, **kwargs: Any) -> T:
            if service_name in LazyServiceLoader._instances:
                return LazyServiceLoader._instances[service_name]

            # Create new instance
            logger.info(f"Lazy loading service: {service_name}")
            instance = cls(*args, **kwargs)
            return instance

        # Add factory function to class
        cls.get_instance = staticmethod(get_instance)

        return cls

    return decorator
