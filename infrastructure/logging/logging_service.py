"""
Abstract interface for the logging system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class LoggingService(ABC):
    """
    Abstract interface for logging services.
    Defines the methods that all logging implementations must provide.
    """

    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        """
        Log a debug message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        """
        Log an info message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs) -> None:
        """
        Log a warning message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        """
        Log an error message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs) -> None:
        """
        Log a critical message.

        Args:
            message: Message to log
            **kwargs: Additional context data
        """
        pass

    @abstractmethod
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set context data to include in all log messages.

        Args:
            context: Context data
        """
        pass

    @abstractmethod
    def get_logger(self, name: str) -> 'LoggingService':
        """
        Get a logger with a specific name.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        pass

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the logging service.

        Args:
            config: Configuration options
        """
        pass
