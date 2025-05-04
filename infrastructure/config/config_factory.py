"""
Factory for creating configuration instances.
"""

from typing import Dict, Any, Optional

from infrastructure.config.config_service import ConfigService
from infrastructure.config.settings_config import SettingsConfig


class ConfigFactory:
    """
    Factory for creating configuration instances.
    """

    @staticmethod
    def create_config(config_type: str = "settings", config: Optional[Dict[str, Any]] = None) -> ConfigService:
        """
        Create a configuration instance.

        Args:
            config_type: Type of configuration to create ("settings", etc.)
            config: Configuration options

        Returns:
            Configuration instance implementing ConfigService
        """
        if config_type == "settings":
            settings_module = config.get("settings_module", "infrastructure.config.settings") if config else "infrastructure.config.settings"
            return SettingsConfig(settings_module=settings_module)
        else:
            # Default to settings config
            return SettingsConfig()
