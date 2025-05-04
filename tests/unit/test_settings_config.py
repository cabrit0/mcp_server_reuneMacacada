"""
Unit tests for the SettingsConfig implementation.
"""

import os
import tempfile
import json

import pytest
from infrastructure.config.settings_config import SettingsConfig


class TestSettingsConfig:
    """Tests for the SettingsConfig implementation."""

    def test_load_from_module(self):
        """Test loading configuration from a module."""
        config = SettingsConfig("infrastructure.config.settings")
        
        # Check that some settings were loaded
        assert config.has("BASE_URL")
        assert config.has("PORT")
        assert config.has("DEBUG")
        assert config.has("CACHE")
        
    def test_get(self):
        """Test getting configuration values."""
        config = SettingsConfig("infrastructure.config.settings")
        
        # Get simple values
        assert config.get("BASE_URL") is not None
        assert isinstance(config.get("PORT"), int)
        
        # Get nested values with dot notation
        assert config.get("CACHE.type") == "memory"
        assert isinstance(config.get("CACHE.ttl.search_results"), int)
        
        # Get with default value
        assert config.get("NON_EXISTENT_KEY", "default") == "default"
        assert config.get("CACHE.non_existent", "default") == "default"
        
    def test_set(self):
        """Test setting configuration values."""
        config = SettingsConfig("infrastructure.config.settings")
        
        # Set simple value
        config.set("TEST_KEY", "test_value")
        assert config.get("TEST_KEY") == "test_value"
        
        # Set nested value with dot notation
        config.set("TEST_SECTION.nested_key", "nested_value")
        assert config.get("TEST_SECTION.nested_key") == "nested_value"
        
        # Override existing value
        original_port = config.get("PORT")
        config.set("PORT", 9000)
        assert config.get("PORT") == 9000
        
    def test_has(self):
        """Test checking if configuration keys exist."""
        config = SettingsConfig("infrastructure.config.settings")
        
        # Check simple keys
        assert config.has("BASE_URL")
        assert not config.has("NON_EXISTENT_KEY")
        
        # Check nested keys
        assert config.has("CACHE.type")
        assert not config.has("CACHE.non_existent")
        
    def test_get_all(self):
        """Test getting all configuration values."""
        config = SettingsConfig("infrastructure.config.settings")
        
        # Get all values
        all_config = config.get_all()
        
        # Check that it's a dictionary
        assert isinstance(all_config, dict)
        
        # Check that some keys are present
        assert "BASE_URL" in all_config
        assert "PORT" in all_config
        assert "CACHE" in all_config
        
    def test_get_section(self):
        """Test getting a configuration section."""
        config = SettingsConfig("infrastructure.config.settings")
        
        # Get a section
        cache_section = config.get_section("CACHE")
        
        # Check that it's a dictionary
        assert isinstance(cache_section, dict)
        
        # Check that some keys are present
        assert "type" in cache_section
        assert "ttl" in cache_section
        
    def test_load_from_dict(self):
        """Test loading configuration from a dictionary."""
        # Create a config instance
        config = SettingsConfig("infrastructure.config.settings")
        
        # Load from dictionary
        config.load({
            "TEST_KEY": "test_value",
            "TEST_SECTION": {
                "nested_key": "nested_value"
            }
        })
        
        # Check that values were loaded
        assert config.get("TEST_KEY") == "test_value"
        assert config.get("TEST_SECTION.nested_key") == "nested_value"
        
        # Check that original values are still present
        assert config.has("BASE_URL")
        
    def test_load_from_json_file(self):
        """Test loading configuration from a JSON file."""
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
            json.dump({
                "TEST_KEY": "test_value",
                "TEST_SECTION": {
                    "nested_key": "nested_value"
                }
            }, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Create a config instance
            config = SettingsConfig("infrastructure.config.settings")
            
            # Load from JSON file
            config.load(temp_file_path)
            
            # Check that values were loaded
            assert config.get("TEST_KEY") == "test_value"
            assert config.get("TEST_SECTION.nested_key") == "nested_value"
            
            # Check that original values are still present
            assert config.has("BASE_URL")
            
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
