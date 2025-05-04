"""
Abstract interface for the configuration system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union


class ConfigService(ABC):
    """
    Abstract interface for configuration services.
    Defines the methods that all configuration implementations must provide.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested values)
            default: Default value if key is not found

        Returns:
            Configuration value or default if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested values)
            value: Configuration value
        """
        pass

    @abstractmethod
    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.

        Args:
            key: Configuration key (can use dot notation for nested values)

        Returns:
            True if key exists, False otherwise
        """
        pass

    @abstractmethod
    def load(self, source: Union[str, Dict[str, Any]]) -> None:
        """
        Load configuration from a source.

        Args:
            source: Configuration source (file path or dictionary)
        """
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary with all configuration values
        """
        pass

    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary with section configuration values
        """
        pass
