"""
Standard logging implementation using Python's built-in logging module.
"""

import logging
import os
import sys
import time
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler

from infrastructure.logging.logging_service import LoggingService


class StandardLogger(LoggingService):
    """
    Standard logging implementation using Python's built-in logging module.
    """

    def __init__(self, name: str = "mcp_server", level: str = "INFO"):
        """
        Initialize the logger.

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.context: Dict[str, Any] = {}
        self.logger = logging.getLogger(name)
        
        # Set level
        self.set_level(level)
        
        # Avoid adding handlers multiple times
        if not self.logger.handlers:
            # Add console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(console_handler)

    def debug(self, message: str, **kwargs) -> None:
        """
        Log a debug message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """
        Log an info message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """
        Log a warning message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """
        Log an error message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """
        Log a critical message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        self._log(logging.CRITICAL, message, **kwargs)

    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set context data to include in all log messages.

        Args:
            context: Context data
        """
        self.context = context

    def get_logger(self, name: str) -> 'LoggingService':
        """
        Get a logger with a specific name.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        return StandardLogger(f"{self.name}.{name}")

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the logging service.

        Args:
            config: Configuration options
        """
        # Set level
        if "level" in config:
            self.set_level(config["level"])
        
        # Add file handler if log_file is specified
        if "log_file" in config:
            self._add_file_handler(
                config["log_file"],
                max_bytes=config.get("max_bytes", 10 * 1024 * 1024),  # 10 MB
                backup_count=config.get("backup_count", 5)
            )
        
        # Set context
        if "context" in config:
            self.set_context(config["context"])

    def set_level(self, level: str) -> None:
        """
        Set the logging level.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        numeric_level = level_map.get(level.upper(), logging.INFO)
        self.logger.setLevel(numeric_level)

    def _log(self, level: int, message: str, **kwargs) -> None:
        """
        Log a message with context.

        Args:
            level: Logging level
            message: Message to log
            **kwargs: Additional context data
        """
        # Combine context with kwargs
        context = {**self.context, **kwargs}
        
        # Add context to message if present
        if context:
            context_str = " ".join(f"{k}={v}" for k, v in context.items())
            message = f"{message} [{context_str}]"
        
        self.logger.log(level, message)

    def _get_formatter(self) -> logging.Formatter:
        """
        Get a formatter for log messages.

        Returns:
            Formatter instance
        """
        return logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def _add_file_handler(self, log_file: str, max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5) -> None:
        """
        Add a file handler to the logger.

        Args:
            log_file: Path to log file
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep
        """
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        
        file_handler.setFormatter(self._get_formatter())
        self.logger.addHandler(file_handler)
