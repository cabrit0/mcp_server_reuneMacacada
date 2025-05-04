# This file is part of the MCP Server package.

from core.path_generator.path_generator_service import PathGeneratorService
from core.path_generator.path_generator_factory import PathGeneratorFactory

# Create a global path generator instance
path_generator: PathGeneratorService = PathGeneratorFactory.create_path_generator("default")

__all__ = ["path_generator", "PathGeneratorService", "PathGeneratorFactory"]
