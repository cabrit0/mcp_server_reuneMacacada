# This file is part of the MCP Server package.

from infrastructure.logging.logging_factory import LoggingFactory
from infrastructure.logging.logging_service import LoggingService

# Create a global logger instance
logger: LoggingService = LoggingFactory.create_logger("standard", {
    "name": "mcp_server",
    "level": "INFO"
})

__all__ = ["logger", "LoggingService", "LoggingFactory"]
