"""
Unit tests for the StandardLogger implementation.
"""

import os
import tempfile
import logging
from unittest.mock import patch, MagicMock

import pytest
from infrastructure.logging.standard_logger import StandardLogger


class TestStandardLogger:
    """Tests for the StandardLogger implementation."""

    def test_log_levels(self):
        """Test that log levels work correctly."""
        logger = StandardLogger(name="test_logger", level="INFO")
        
        # Mock the underlying logger
        mock_logger = MagicMock()
        logger.logger = mock_logger
        
        # Test different log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
        
        # Debug should not be logged (level is INFO)
        mock_logger.log.assert_not_called()
        
        # Reset mock
        mock_logger.reset_mock()
        
        # Change level to DEBUG
        logger.set_level("DEBUG")
        
        # Test again
        logger.debug("Debug message")
        logger.info("Info message")
        
        # Both should be logged now
        assert mock_logger.log.call_count == 2
        
    def test_context(self):
        """Test that context is included in log messages."""
        logger = StandardLogger(name="test_logger")
        
        # Mock the underlying logger
        mock_logger = MagicMock()
        logger.logger = mock_logger
        
        # Set context
        logger.set_context({"user_id": "123", "request_id": "abc"})
        
        # Log a message
        logger.info("Test message")
        
        # Check that context was included
        args, kwargs = mock_logger.log.call_args
        level, message = args
        assert level == logging.INFO
        assert "Test message" in message
        assert "user_id=123" in message
        assert "request_id=abc" in message
        
    def test_additional_context(self):
        """Test that additional context can be passed to log methods."""
        logger = StandardLogger(name="test_logger")
        
        # Mock the underlying logger
        mock_logger = MagicMock()
        logger.logger = mock_logger
        
        # Set base context
        logger.set_context({"user_id": "123"})
        
        # Log with additional context
        logger.info("Test message", request_id="abc", action="test")
        
        # Check that all context was included
        args, kwargs = mock_logger.log.call_args
        level, message = args
        assert level == logging.INFO
        assert "Test message" in message
        assert "user_id=123" in message
        assert "request_id=abc" in message
        assert "action=test" in message
        
    def test_get_logger(self):
        """Test that get_logger returns a new logger with the correct name."""
        parent_logger = StandardLogger(name="parent")
        child_logger = parent_logger.get_logger("child")
        
        assert isinstance(child_logger, StandardLogger)
        assert child_logger.name == "parent.child"
        
    def test_file_handler(self):
        """Test that file handler works correctly."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_file = temp_file.name
        
        try:
            # Create logger with file handler
            logger = StandardLogger(name="test_logger")
            logger.configure({
                "log_file": log_file,
                "max_bytes": 1024,
                "backup_count": 3
            })
            
            # Log some messages
            logger.info("Test message 1")
            logger.error("Test message 2")
            
            # Check that messages were written to the file
            with open(log_file, "r") as f:
                content = f.read()
                assert "Test message 1" in content
                assert "Test message 2" in content
                
        finally:
            # Clean up
            if os.path.exists(log_file):
                os.unlink(log_file)
