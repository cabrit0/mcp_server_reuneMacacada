# This file is part of the MCP Server package.

from services.youtube.youtube_service import YouTubeService
from services.youtube.youtube_factory import YouTubeFactory

# Create a global YouTube service instance
youtube: YouTubeService = YouTubeFactory.create_youtube_service("default")

__all__ = ["youtube", "YouTubeService", "YouTubeFactory"]
