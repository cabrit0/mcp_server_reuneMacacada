"""
Settings-based configuration service implementation.
"""

import os
import json
import importlib
from typing import Any, Dict, List, Optional, Union

from infrastructure.config.config_service import ConfigService


class SettingsConfig(ConfigService):
    """
    Settings-based configuration service implementation.
    Loads configuration from a Python settings module.
    """

    def __init__(self, settings_module: str = "infrastructure.config.settings"):
        """
        Initialize the configuration service.

        Args:
            settings_module: Python module with settings
        """
        self.settings_module = settings_module
        self.config: Dict[str, Any] = {}
        self.load(settings_module)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested values)
            default: Default value if key is not found

        Returns:
            Configuration value or default if not found
        """
        # Handle dot notation
        if "." in key:
            parts = key.split(".")
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        # Simple key
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested values)
            value: Configuration value
        """
        # Handle dot notation
        if "." in key:
            parts = key.split(".")
            config = self.config
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            # Simple key
            self.config[key] = value

    def has(self, key: str) -> bool:
        """
        Check if a configuration key exists.

        Args:
            key: Configuration key (can use dot notation for nested values)

        Returns:
            True if key exists, False otherwise
        """
        # Handle dot notation
        if "." in key:
            parts = key.split(".")
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return False
            return True
        
        # Simple key
        return key in self.config

    def load(self, source: Union[str, Dict[str, Any]]) -> None:
        """
        Load configuration from a source.

        Args:
            source: Configuration source (module name, file path, or dictionary)
        """
        if isinstance(source, dict):
            # Load from dictionary
            self.config.update(source)
        elif isinstance(source, str):
            if source.endswith(".py") or "." in source:
                # Load from Python module
                try:
                    if source.endswith(".py"):
                        # Remove .py extension
                        source = source[:-3]
                        # Convert path to module name
                        source = source.replace("/", ".").replace("\\", ".")
                    
                    module = importlib.import_module(source)
                    
                    # Get all uppercase variables (standard for settings)
                    for key in dir(module):
                        if key.isupper():
                            self.config[key] = getattr(module, key)
                except ImportError as e:
                    raise ValueError(f"Could not import settings module: {source}") from e
            elif os.path.exists(source):
                # Load from JSON file
                try:
                    with open(source, "r") as f:
                        self.config.update(json.load(f))
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON file: {source}") from e
            else:
                raise ValueError(f"Invalid configuration source: {source}")
        else:
            raise ValueError(f"Invalid configuration source type: {type(source)}")

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration values.

        Returns:
            Dictionary with all configuration values
        """
        return self.config.copy()

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get a configuration section.

        Args:
            section: Section name

        Returns:
            Dictionary with section configuration values
        """
        section_value = self.get(section, {})
        if not isinstance(section_value, dict):
            return {}
        return section_value.copy()
