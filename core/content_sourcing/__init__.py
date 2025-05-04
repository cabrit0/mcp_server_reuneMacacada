# This file is part of the MCP Server package.

from core.content_sourcing.content_source_service import ContentSourceService
from core.content_sourcing.content_source_factory import ContentSourceFactory

# Create a global content source instance
content_source: ContentSourceService = ContentSourceFactory.create_content_source("default")

__all__ = ["content_source", "ContentSourceService", "ContentSourceFactory"]
