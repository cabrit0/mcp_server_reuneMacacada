# This file is part of the MCP Server package.

from infrastructure.config.config_factory import ConfigFactory
from infrastructure.config.config_service import ConfigService

# Create a global configuration instance
config: ConfigService = ConfigFactory.create_config("settings")

__all__ = ["config", "ConfigService", "ConfigFactory"]
