"""
YouTube integration using yt-dlp.
"""

import yt_dlp
import asyncio
import uuid
import re
import random
from typing import List, Dict, Any, Optional

from infrastructure.logging import logger
from infrastructure.cache import cache
from infrastructure.config import config
from api.models import Resource
from services.youtube.youtube_service import YouTubeService


class YtDlpService(YouTubeService):
    """
    YouTube integration using yt-dlp.
    Implements the YouTubeService interface.
    """

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

    # Language prefix mapping
    LANGUAGE_PREFIXES = {
        "pt": "português ",
        "en": "english ",
        "es": "español ",
        "fr": "français ",
        "de": "deutsch ",
        "it": "italiano ",
        "ru": "русский ",
        "ja": "日本語 ",
        "zh": "中文 "
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
        Initialize the YouTube service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger("youtube.ytdlp")

        # Get configuration
        youtube_config = config.get_section("YOUTUBE")
        self.max_results_default = youtube_config.get("max_results", 5)
        self.timeout = youtube_config.get("timeout", 15)

        self.logger.info("Initialized YtDlpService")

    async def search_videos(self, query: str, max_results: int = None, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for YouTube videos.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with video information
        """
        if max_results is None:
            max_results = self.max_results_default

        # Check cache first
        cache_key = f"youtube:search:{query}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached YouTube search results for '{query}'")
            return cached_result

        # Configure yt-dlp options
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
            'format': 'best',
        }

        # Add language prefix to query
        lang_prefix = self.LANGUAGE_PREFIXES.get(language, "")
        search_query = f"ytsearch{max_results*2}:{lang_prefix}{query}"

        try:
            # Run search asynchronously
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self._extract_info_with_ytdlp(search_query, ydl_opts)
            )

            # Process results
            videos = []
            for entry in results:
                # Check if it's a valid video
                if entry.get('_type') == 'url' and 'youtube' in entry.get('url', ''):
                    # Extract duration in minutes
                    duration_seconds = entry.get('duration')
                    duration_minutes = int(duration_seconds / 60) if duration_seconds else None

                    # Get thumbnail
                    thumbnail = self._get_best_thumbnail(entry)

                    # Create video info
                    video = {
                        'id': entry.get('id', uuid.uuid4().hex[:8]),
                        'title': entry.get('title', ''),
                        'url': entry.get('url', ''),
                        'description': entry.get('description', '') or f"Channel: {entry.get('uploader', '')}",
                        'duration': duration_minutes,
                        'thumbnail': thumbnail,
                        'channel': entry.get('uploader', ''),
                        'publishedAt': entry.get('upload_date', '')
                    }

                    videos.append(video)

                    if len(videos) >= max_results:
                        break

            # Cache the results
            if videos:
                cache.setex(cache_key, self.cache_ttl, videos)
                self.logger.debug(f"Cached YouTube search results for '{query}' ({len(videos)} videos)")
            else:
                self.logger.warning(f"No YouTube videos found for '{query}'")

            return videos
        except Exception as e:
            self.logger.error(f"Error searching YouTube for '{query}': {str(e)}")
            return []

    async def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific video.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with video details or None if not found
        """
        # Check cache first
        cache_key = f"youtube:video:{video_id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached YouTube video details for '{video_id}'")
            return cached_result

        # Configure yt-dlp options
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'skip_download': True,
            'format': 'best',
        }

        try:
            # Run extraction asynchronously
            loop = asyncio.get_event_loop()
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            result = await loop.run_in_executor(
                None,
                lambda: self._extract_video_info(video_url, ydl_opts)
            )

            if not result:
                self.logger.warning(f"No details found for YouTube video '{video_id}'")
                return None

            # Process result
            duration_seconds = result.get('duration')
            duration_minutes = int(duration_seconds / 60) if duration_seconds else None

            # Get thumbnail
            thumbnail = self._get_best_thumbnail(result)

            # Create video info
            video = {
                'id': result.get('id', video_id),
                'title': result.get('title', ''),
                'url': video_url,
                'description': result.get('description', ''),
                'duration': duration_minutes,
                'thumbnail': thumbnail,
                'channel': result.get('uploader', ''),
                'publishedAt': result.get('upload_date', ''),
                'viewCount': result.get('view_count'),
                'likeCount': result.get('like_count'),
                'tags': result.get('tags', [])
            }

            # Cache the result
            cache.setex(cache_key, self.cache_ttl, video)
            self.logger.debug(f"Cached YouTube video details for '{video_id}'")

            return video
        except Exception as e:
            self.logger.error(f"Error getting YouTube video details for '{video_id}': {str(e)}")
            return None

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

    def _extract_info_with_ytdlp(self, search_query: str, ydl_opts: dict) -> List[dict]:
        """
        Extract information from videos using yt-dlp.

        Args:
            search_query: Search query
            ydl_opts: yt-dlp options

        Returns:
            List of video information
        """
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(search_query, download=False)
                if result and 'entries' in result:
                    return result['entries']
                return []
        except Exception as e:
            self.logger.error(f"Error extracting info with yt-dlp: {str(e)}")
            return []

    def _extract_video_info(self, video_url: str, ydl_opts: dict) -> Optional[dict]:
        """
        Extract information for a specific video using yt-dlp.

        Args:
            video_url: Video URL
            ydl_opts: yt-dlp options

        Returns:
            Video information or None if not found
        """
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(video_url, download=False)
        except Exception as e:
            self.logger.error(f"Error extracting video info with yt-dlp: {str(e)}")
            return None

    def _get_best_thumbnail(self, video_info: Dict[str, Any]) -> Optional[str]:
        """
        Get the best thumbnail available for a video.

        Args:
            video_info: Video information

        Returns:
            URL of the best thumbnail or None if not found
        """
        # Check if thumbnails are available
        thumbnails = video_info.get('thumbnails', [])

        if not thumbnails:
            # Fallback to default YouTube thumbnail
            video_id = video_info.get('id')
            if video_id:
                return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            return None

        # Sort thumbnails by resolution (width x height)
        sorted_thumbnails = sorted(
            thumbnails,
            key=lambda t: (t.get('width', 0) * t.get('height', 0)),
            reverse=True
        )

        # Return the URL of the best thumbnail
        return sorted_thumbnails[0].get('url') if sorted_thumbnails else None

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
