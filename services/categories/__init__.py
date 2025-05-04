# This file is part of the MCP Server package.

from services.categories.category_service import CategoryService
from services.categories.category_factory import CategoryFactory

# Create a global category service instance
category_service: CategoryService = CategoryFactory.create_category_service("default")

__all__ = ["category_service", "CategoryService", "CategoryFactory"]
