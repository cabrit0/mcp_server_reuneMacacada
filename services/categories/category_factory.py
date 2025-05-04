"""
Factory for creating category service instances.
"""

from typing import Dict, Any, Optional

from infrastructure.logging import logger
from services.categories.category_service import CategoryService
from services.categories.default_category_service import DefaultCategoryService
from services.categories.ai_category_service import AICategoryService


class CategoryFactory:
    """
    Factory for creating category service instances.
    """

    # Singleton instances
    _instances: Dict[str, CategoryService] = {}

    @classmethod
    def create_category_service(cls, service_type: str = "default", config_options: Optional[Dict[str, Any]] = None) -> CategoryService:
        """
        Create a category service instance.

        Args:
            service_type: Type of service to create ("default", "ai")
            config_options: Configuration options for the service

        Returns:
            Category service instance implementing CategoryService
        """
        # Use singleton pattern for efficiency
        if service_type in cls._instances:
            return cls._instances[service_type]
            
        # Create service instance
        service: CategoryService
        
        if service_type == "default":
            service = DefaultCategoryService()
        elif service_type == "ai":
            # Create AI service with default service as fallback
            default_service = cls.create_category_service("default")
            service = AICategoryService(fallback_service=default_service)
        else:
            logger.warning(f"Unknown category service type: {service_type}, falling back to default")
            return cls.create_category_service("default", config_options)
            
        # Store instance for reuse
        cls._instances[service_type] = service
        
        return service
