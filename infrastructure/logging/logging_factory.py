"""
Factory for creating logger instances.
"""

from typing import Dict, Any, Optional

from infrastructure.logging.logging_service import LoggingService
from infrastructure.logging.standard_logger import StandardLogger


class LoggingFactory:
    """
    Factory for creating logger instances.
    """

    @staticmethod
    def create_logger(logger_type: str = "standard", config: Optional[Dict[str, Any]] = None) -> LoggingService:
        """
        Create a logger instance.

        Args:
            logger_type: Type of logger to create ("standard", etc.)
            config: Configuration options for the logger

        Returns:
            Logger instance implementing LoggingService
        """
        if config is None:
            config = {}
        
        if logger_type == "standard":
            name = config.get("name", "mcp_server")
            level = config.get("level", "INFO")
            logger = StandardLogger(name=name, level=level)
            
            # Apply additional configuration
            if config:
                logger.configure(config)
                
            return logger
        else:
            # Default to standard logger
            return StandardLogger()
