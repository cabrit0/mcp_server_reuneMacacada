# This file is part of the MCP Server package.

from services.youtube.youtube_service import YouTubeService
from services.youtube.youtube_factory import YouTubeFactory

# Create a lazy-loaded YouTube service
def get_youtube_service():
    from services.youtube.youtube_factory import YouTubeFactory
    return YouTubeFactory.create_youtube_service("default")

# Lazy-loaded YouTube service
youtube = None

def get_youtube():
    global youtube
    if youtube is None:
        youtube = get_youtube_service()
    return youtube

__all__ = ["get_youtube", "YouTubeService", "YouTubeFactory"]
