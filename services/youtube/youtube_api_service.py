"""
YouTube integration using the YouTube Data API.
"""

import asyncio
import aiohttp
import random
import re
from typing import List, Dict, Any, Optional

from infrastructure.logging import logger
from infrastructure.cache import cache
from infrastructure.config import config
from api.models import Resource
from services.youtube.youtube_service import YouTubeService


class YouTubeApiService(YouTubeService):
    """
    YouTube integration using the YouTube Data API.
    Implements the YouTubeService interface.
    """

    # YouTube API base URL
    API_BASE_URL = "https://www.googleapis.com/youtube/v3"

    # List of search term templates for subtopics
    SUBTOPIC_SEARCH_TERMS = [
        "{topic} tutorial",
        "{topic} guide",
        "{topic} explained",
        "{topic} how to",
        "{topic} examples",
        "{topic} course",
        "{topic} for beginners",
        "{topic} introduction"
    ]

    # Language to region code mapping
    LANGUAGE_TO_REGION = {
        "en": "US",
        "pt": "BR",
        "es": "ES",
        "fr": "FR",
        "de": "DE",
        "it": "IT",
        "ru": "RU",
        "ja": "JP",
        "zh": "CN"
    }

    # Prefixes to remove from subtopics for better search results
    PREFIXES_TO_REMOVE = [
        "Introduction to", "Getting Started with", "Understanding", "Basics of",
        "Advanced", "Mastering", "Practical", "Exploring", "Deep Dive into",
        "Essential", "Fundamentals of", "Working with", "Building with",
        "Developing with", "Professional", "Modern", "Effective", "Efficient",
        "Introdução a", "Introdução ao", "Conceitos de", "Fundamentos de",
        "Avançado", "Prático", "Explorando", "Essencial", "Trabalhando com",
        "Desenvolvendo com", "Profissional", "Moderno", "Eficiente"
    ]

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the YouTube API service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger("youtube.api")

        # Get configuration
        youtube_config = config.get_section("YOUTUBE")
        self.api_key = youtube_config.get("api_key")
        self.max_results_default = youtube_config.get("max_results", 5)
        self.timeout = youtube_config.get("timeout", 15)

        if not self.api_key:
            self.logger.warning("YouTube API key not configured. YouTube API service will not work.")
        else:
            self.logger.info("Initialized YouTubeApiService")

    async def search_videos(self, query: str, max_results: int = None, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for YouTube videos using the YouTube Data API.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with video information
        """
        if not self.api_key:
            self.logger.error("YouTube API key not configured")
            return []

        if max_results is None:
            max_results = self.max_results_default

        # Check cache first
        cache_key = f"youtube:api:search:{query}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached YouTube API search results for '{query}'")
            return cached_result

        # Get region code for language
        region_code = self.LANGUAGE_TO_REGION.get(language, "US")

        # Prepare request parameters
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": min(max_results * 2, 50),  # API limit is 50
            "regionCode": region_code,
            "relevanceLanguage": language,
            "key": self.api_key
        }

        try:
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.API_BASE_URL}/search", params=params, timeout=self.timeout) as response:
                    if response.status != 200:
                        self.logger.error(f"YouTube API error: {response.status}")
                        return []

                    data = await response.json()

                    # Extract video IDs
                    video_ids = [item["id"]["videoId"] for item in data.get("items", []) if "videoId" in item.get("id", {})]

                    if not video_ids:
                        self.logger.warning(f"No YouTube videos found for '{query}'")
                        return []

                    # Get video details
                    videos = await self._get_videos_details(video_ids)

                    # Limit to max_results
                    videos = videos[:max_results]

                    # Cache the results
                    if videos:
                        cache.setex(cache_key, self.cache_ttl, videos)
                        self.logger.debug(f"Cached YouTube API search results for '{query}' ({len(videos)} videos)")

                    return videos
        except Exception as e:
            self.logger.error(f"Error searching YouTube API for '{query}': {str(e)}")
            return []

    async def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific video using the YouTube Data API.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with video details or None if not found
        """
        if not self.api_key:
            self.logger.error("YouTube API key not configured")
            return None

        # Check cache first
        cache_key = f"youtube:api:video:{video_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached YouTube API video details for '{video_id}'")
            return cached_result

        # Get video details
        videos = await self._get_videos_details([video_id])

        if not videos:
            self.logger.warning(f"No details found for YouTube video '{video_id}'")
            return None

        video = videos[0]

        # Cache the result
        cache.setex(cache_key, self.cache_ttl, video)
        self.logger.debug(f"Cached YouTube API video details for '{video_id}'")

        return video

    async def search_videos_for_topic(self, topic: str, subtopic: str = None,
                                     max_results: int = 3, language: str = "en") -> List[Resource]:
        """
        Search for videos related to a topic and convert to Resource objects.

        Args:
            topic: Main topic
            subtopic: Optional subtopic for more specific results
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of Resource objects
        """
        # Determine search query
        if subtopic:
            # Clean subtopic for better search results
            clean_subtopic = self._clean_subtopic(subtopic)

            # For subtopics, use a more specific query
            search_term = random.choice(self.SUBTOPIC_SEARCH_TERMS).format(topic=clean_subtopic)
            query = f"{search_term} {topic}"
            is_subtopic = True
        else:
            # For main topic, use a general query
            query = topic
            is_subtopic = False

        # Search for videos
        videos = await self.search_videos(query, max_results, language)

        # Convert to Resource objects
        resources = []
        for video in videos:
            resource = Resource(
                id=f"youtube_{video.get('id')}",
                title=video.get('title', ''),
                url=video.get('url', ''),
                type="video",
                description=video.get('description', ''),
                duration=video.get('duration'),
                readTime=None,
                difficulty="intermediate",
                thumbnail=video.get('thumbnail')
            )

            # Add subtopic information if applicable
            if is_subtopic and subtopic:
                resource.title = f"{resource.title} - Relevante para: {subtopic}"

            resources.append(resource)

        return resources

    async def _get_videos_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get details for multiple videos using the YouTube Data API.

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            List of dictionaries with video details
        """
        if not video_ids:
            return []

        # Prepare request parameters
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(video_ids),
            "key": self.api_key
        }

        try:
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.API_BASE_URL}/videos", params=params, timeout=self.timeout) as response:
                    if response.status != 200:
                        self.logger.error(f"YouTube API error: {response.status}")
                        return []

                    data = await response.json()

                    # Process results
                    videos = []
                    for item in data.get("items", []):
                        # Extract video details
                        video_id = item.get("id")
                        snippet = item.get("snippet", {})
                        content_details = item.get("contentDetails", {})
                        statistics = item.get("statistics", {})

                        # Parse duration
                        duration_str = content_details.get("duration")
                        duration_minutes = self._parse_duration(duration_str)

                        # Get thumbnail
                        thumbnails = snippet.get("thumbnails", {})
                        thumbnail = None
                        for quality in ["maxres", "high", "medium", "default"]:
                            if quality in thumbnails:
                                thumbnail = thumbnails[quality].get("url")
                                break

                        if not thumbnail and video_id:
                            thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                        # Create video info
                        video = {
                            'id': video_id,
                            'title': snippet.get('title', ''),
                            'url': f"https://www.youtube.com/watch?v={video_id}",
                            'description': snippet.get('description', ''),
                            'duration': duration_minutes,
                            'thumbnail': thumbnail,
                            'channel': snippet.get('channelTitle', ''),
                            'publishedAt': snippet.get('publishedAt', ''),
                            'viewCount': int(statistics.get('viewCount', 0)),
                            'likeCount': int(statistics.get('likeCount', 0)),
                            'tags': snippet.get('tags', [])
                        }

                        videos.append(video)

                    return videos
        except Exception as e:
            self.logger.error(f"Error getting YouTube video details: {str(e)}")
            return []

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """
        Convert a duration string to minutes.

        Args:
            duration_str: Duration string (e.g., "PT1H30M15S" or "1:30:15")

        Returns:
            Duration in minutes or None if conversion is not possible
        """
        if not duration_str:
            return None

        # ISO 8601 format (PT1H30M15S)
        iso_match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if iso_match:
            hours = int(iso_match.group(1) or 0)
            minutes = int(iso_match.group(2) or 0)
            seconds = int(iso_match.group(3) or 0)
            return hours * 60 + minutes + (1 if seconds > 30 else 0)

        # HH:MM:SS or MM:SS format
        time_match = re.match(r'(?:(\d+):)?(\d+):(\d+)', duration_str)
        if time_match:
            hours = int(time_match.group(1) or 0)
            minutes = int(time_match.group(2) or 0)
            seconds = int(time_match.group(3) or 0)
            return hours * 60 + minutes + (1 if seconds > 30 else 0)

        return None

    def _clean_subtopic(self, subtopic: str) -> str:
        """
        Clean a subtopic for better search results.

        Args:
            subtopic: Subtopic to clean

        Returns:
            Cleaned subtopic
        """
        clean_subtopic = subtopic

        # Remove common prefixes that might interfere with search
        for prefix in self.PREFIXES_TO_REMOVE:
            if clean_subtopic.startswith(prefix):
                clean_subtopic = clean_subtopic[len(prefix):].strip()
                break

        return clean_subtopic
