"""
Documentation services for the MCP Server.

This module provides integration with various documentation repositories
to enhance the quality of learning resources.
"""

from services.documentation.documentation_service import DocumentationService
from services.documentation.documentation_factory import get_documentation_factory, DocumentationFactory

__all__ = [
    "DocumentationService",
    "DocumentationFactory",
    "get_documentation_factory"
]
