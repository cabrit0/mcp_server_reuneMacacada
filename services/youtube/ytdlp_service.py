"""
YouTube integration using yt-dlp.

This module provides enhanced YouTube integration with improved video quality filtering,
metadata extraction, and support for playlists.
"""

import yt_dlp
import asyncio
import uuid
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from infrastructure.logging import logger
from infrastructure.cache import cache
from infrastructure.config import config
from api.models import Resource
from services.youtube.youtube_service import YouTubeService


class YtDlpService(YouTubeService):
    """
    YouTube integration using yt-dlp.
    Implements the YouTubeService interface with enhanced features:
    - Quality filtering for videos
    - Improved metadata extraction
    - Support for playlists
    - Relevance scoring for better results
    """

    # Quality filter constants - further relaxed for better coverage
    MIN_VIEWS = 200  # Reduced from 500 to 200 minimum views
    MIN_DURATION_SECONDS = 20  # Reduced from 30 to 20 seconds minimum duration
    MAX_DURATION_SECONDS = 7200  # Increased from 5400 to 7200 seconds (2 hours) maximum duration
    MAX_AGE_DAYS = 3650  # Increased from 2555 to 3650 days (10 years) maximum age

    # Relevance scoring weights
    TITLE_MATCH_WEIGHT = 3.0
    DESCRIPTION_MATCH_WEIGHT = 1.5
    VIEWS_WEIGHT = 1.0
    RECENCY_WEIGHT = 1.0
    DURATION_WEIGHT = 1.0
    LIKE_RATIO_WEIGHT = 2.0

    # List of search term templates for subtopics - expanded for better coverage
    SUBTOPIC_SEARCH_TERMS = [
        "{topic} tutorial",
        "{topic} guide",
        "{topic} explained",
        "{topic} how to",
        "{topic} examples",
        "{topic} course",
        "{topic} for beginners",
        "{topic} introduction",
        "{topic} overview",
        "{topic} fundamentals",
        "{topic} basics",
        "{topic} learn",
        "{topic} lecture",
        "{topic} class",
        "{topic} lesson",
        "{topic} concepts",
        "{topic} principles",
        "{topic} techniques",
        "{topic} methods",
        "{topic} tips",
        "{topic} best practices",
        "{topic} in depth",
        "{topic} masterclass",
        "{topic} crash course"
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
        self.timeout = youtube_config.get("timeout", 12)  # Increased from 8 to 12 seconds for better results

        # Configure yt-dlp common options with improved settings for better performance
        self.common_ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'skip_download': True,
            'extract_flat': 'in_playlist',
            'format': 'best',
            'socket_timeout': 10,  # Increased from 8 to 10 seconds for more reliable connections
            'retries': 5,          # Increased from 3 to 5 retries for better reliability
            'fragment_retries': 3, # Increased from 2 to 3 retries
            'skip_unavailable_fragments': True,
            'no_color': True,
            'geo_bypass': True,    # Try to bypass geo-restrictions
            'geo_bypass_country': 'US',  # Use US as default country for geo-bypass
            'sleep_interval': 0.5, # Reduced from 1 to 0.5 seconds for faster processing
            'max_sleep_interval': 3, # Reduced from 5 to 3 seconds for faster processing
            'extractor_retries': 3, # Added extractor retries
            'skip_playlist_after_errors': 3, # Skip playlist after 3 errors
            'postprocessor_args': {
                'ffmpeg': ['-threads', '4']  # Use 4 threads for ffmpeg processing
            },
        }

        # Create a cache for video details to avoid redundant lookups
        self._video_details_cache = {}

        self.logger.info("Initialized YtDlpService with optimized settings")

    async def search_videos(self, query: str, max_results: int = None, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for YouTube videos with enhanced quality filtering and relevance scoring.

        Args:
            query: Search query
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with video information, sorted by relevance
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
        # Request more results than needed to allow for filtering
        search_query = f"ytsearch{max_results*4}:{lang_prefix}{query}"

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
                        'duration_seconds': duration_seconds,
                        'thumbnail': thumbnail,
                        'channel': entry.get('uploader', ''),
                        'publishedAt': entry.get('upload_date', ''),
                        'viewCount': entry.get('view_count', 0),
                        'likeCount': entry.get('like_count', 0),
                        'tags': entry.get('tags', [])
                    }

                    # Get detailed information for better filtering and scoring
                    if video['id']:
                        detailed_info = await self.get_video_details(video['id'])
                        if detailed_info:
                            # Update with more detailed information
                            video.update({
                                'viewCount': detailed_info.get('viewCount', video['viewCount']),
                                'likeCount': detailed_info.get('likeCount', video['likeCount']),
                                'tags': detailed_info.get('tags', video['tags']),
                                'description': detailed_info.get('description', video['description'])
                            })

                    # Calculate relevance score
                    video['relevance_score'] = self._score_video(video, query)

                    # Apply quality filters
                    if self._filter_video_by_quality(video):
                        videos.append(video)

            # Sort videos by relevance score (descending)
            videos.sort(key=lambda v: v.get('relevance_score', 0), reverse=True)

            # Limit to max_results
            videos = videos[:max_results]

            # Remove scoring information before caching
            for video in videos:
                if 'relevance_score' in video:
                    del video['relevance_score']

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

    async def search_playlists(self, query: str, max_results: int = 3, language: str = "en") -> List[Dict[str, Any]]:
        """
        Search for YouTube playlists related to a query.

        Args:
            query: Search query
            max_results: Maximum number of playlists to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with playlist information
        """
        # Check cache first
        cache_key = f"youtube:playlists:{query}_{max_results}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached YouTube playlist results for '{query}'")
            return cached_result

        # Configure yt-dlp options - use minimal options for faster processing
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': True,
            'skip_download': True,
            'format': 'best',
            'socket_timeout': 3,  # Short timeout
            'retries': 1,         # Minimal retries
        }

        # Add language prefix to query
        lang_prefix = self.LANGUAGE_PREFIXES.get(language, "")
        # Request fewer playlists to speed up processing
        search_query = f"ytsearchplaylist{max_results}:{lang_prefix}{query}"

        try:
            # Run search asynchronously with a timeout
            loop = asyncio.get_event_loop()
            extract_task = loop.run_in_executor(
                None,
                lambda: self._extract_info_with_ytdlp(search_query, ydl_opts)
            )

            # Set a timeout for the extraction
            try:
                results = await asyncio.wait_for(extract_task, timeout=4)  # 4 second timeout
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout searching playlists for '{query}'")
                return []

            # Process results - simplified processing
            playlists = []
            for entry in results:
                # Check if it's a valid playlist
                if entry and entry.get('_type') == 'url' and 'youtube.com/playlist' in entry.get('url', ''):
                    # Extract playlist ID from URL
                    url = entry.get('url', '')
                    playlist_id = None
                    if 'list=' in url:
                        playlist_id = url.split('list=')[1].split('&')[0]

                    if not playlist_id:
                        continue

                    # Create playlist info - minimal information for speed
                    playlist = {
                        'id': playlist_id,
                        'title': entry.get('title', ''),
                        'url': url,
                        'description': entry.get('description', '') or f"Playlist by: {entry.get('uploader', '')}",
                        'channel': entry.get('uploader', ''),
                        'thumbnail': entry.get('thumbnail', '')
                    }

                    playlists.append(playlist)

                    # Stop after finding the first valid playlist to save time
                    if len(playlists) >= max_results:
                        break

            # Cache the results
            if playlists:
                cache.setex(cache_key, self.cache_ttl, playlists)
                self.logger.debug(f"Cached YouTube playlist results for '{query}' ({len(playlists)} playlists)")
            else:
                self.logger.warning(f"No YouTube playlists found for '{query}'")

            return playlists
        except Exception as e:
            self.logger.error(f"Error searching YouTube playlists for '{query}': {str(e)}")
            return []

    async def get_playlist_videos(self, playlist_id: str, max_videos: int = 5, language: str = "en") -> List[Dict[str, Any]]:
        """
        Get videos from a YouTube playlist.

        Args:
            playlist_id: YouTube playlist ID
            max_videos: Maximum number of videos to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with video information
        """
        # Check cache first
        cache_key = f"youtube:playlist_videos:{playlist_id}_{max_videos}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached YouTube playlist videos for '{playlist_id}'")
            return cached_result

        # Configure yt-dlp options - use minimal options for faster processing
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'extract_flat': True,
            'skip_download': True,
            'format': 'best',
            'socket_timeout': 3,  # Short timeout
            'retries': 1,         # Minimal retries
            'playlistend': max_videos,  # Limit the number of videos to extract
        }

        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"

        try:
            # Run extraction asynchronously with a timeout
            loop = asyncio.get_event_loop()
            extract_task = loop.run_in_executor(
                None,
                lambda: self._extract_info_with_ytdlp(playlist_url, ydl_opts)
            )

            # Set a timeout for the extraction
            try:
                result = await asyncio.wait_for(extract_task, timeout=4)  # 4 second timeout
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout getting videos from playlist '{playlist_id}'")
                return []

            # Process results - simplified processing
            videos = []
            playlist_title = result.get('title', '')

            if 'entries' in result:
                # Limit the number of entries to process
                entries = result['entries'][:max_videos]

                # Process entries
                for entry in entries:
                    # Skip non-video entries
                    if not entry or entry.get('_type') != 'url' or 'youtube' not in entry.get('url', ''):
                        continue

                    video_id = entry.get('id')
                    if not video_id:
                        continue

                    # Create a minimal video object from the entry data
                    # This avoids the need for additional API calls
                    video = {
                        'id': video_id,
                        'title': entry.get('title', ''),
                        'url': entry.get('url', ''),
                        'description': entry.get('description', '') or f"Video from playlist: {playlist_title}",
                        'duration': entry.get('duration'),
                        'thumbnail': entry.get('thumbnail'),
                        'playlistId': playlist_id,
                        'playlistTitle': playlist_title,
                        'isFromPlaylist': True
                    }

                    videos.append(video)

                    if len(videos) >= max_videos:
                        break

            # Cache the results
            if videos:
                cache.setex(cache_key, self.cache_ttl, videos)
                self.logger.debug(f"Cached YouTube playlist videos for '{playlist_id}' ({len(videos)} videos)")
            else:
                self.logger.warning(f"No videos found in YouTube playlist '{playlist_id}'")

            return videos
        except Exception as e:
            self.logger.error(f"Error getting videos from YouTube playlist '{playlist_id}': {str(e)}")
            return []

    async def search_videos_for_topic(self, topic: str, subtopic: str = None,
                                     max_results: int = 3, language: str = "en") -> List[Resource]:
        """
        Search for videos related to a topic and convert to Resource objects.
        Enhanced implementation with multiple search strategies and fallbacks.
        Optimized for better performance and reliability.

        Args:
            topic: Main topic
            subtopic: Optional subtopic for more specific results
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of Resource objects
        """
        # Check cache first for this specific topic/subtopic combination
        cache_key = f"youtube:topic:{topic}_{subtopic}_{max_results}_{language}"
        cached_result = cache.get(cache_key, resource_type='resource_list')
        if cached_result:
            # If we have a small number of cached results, consider refreshing in the background
            if len(cached_result) < max_results:
                self.logger.info(f"Found only {len(cached_result)} cached results for '{topic}', will refresh in background")
                # Schedule a background refresh but still return cached results
                asyncio.create_task(self._refresh_topic_cache(topic, subtopic, max_results, language, cache_key))
            else:
                self.logger.info(f"Using cached YouTube topic results for '{topic}' ({len(cached_result)} videos)")
            return cached_result

        # Generate multiple search queries for better coverage
        search_queries = self._generate_search_queries(topic, subtopic, language)

        # Track all videos found across all queries
        all_videos = []
        existing_ids = set()

        # Limit the number of queries to try based on topic complexity
        max_queries_to_try = min(5, len(search_queries))
        if ' ' not in topic:  # Simple topics need fewer queries
            max_queries_to_try = min(3, max_queries_to_try)

        # Use a longer timeout for the first query, shorter for subsequent ones
        first_query_timeout = 15  # 15 seconds for first query
        subsequent_query_timeout = 8  # 8 seconds for subsequent queries

        # Try each query until we have enough results or run out of queries
        for i, query_info in enumerate(search_queries[:max_queries_to_try]):
            query = query_info["query"]
            query_type = query_info["type"]

            self.logger.info(f"Trying {query_type} query: '{query}'")

            # Skip if we already have enough videos
            if len(all_videos) >= max_results * 1.5:  # Get 50% more than needed for better filtering
                break

            # Set timeout based on query position
            query_timeout = first_query_timeout if i == 0 else subsequent_query_timeout

            # Try this query with a timeout
            try:
                # Adjust max_results based on how many we still need
                needed_results = max(1, max_results - len(all_videos))

                # For first query, request more results
                if i == 0:
                    request_count = needed_results * 3  # Request 3x for first query
                else:
                    request_count = needed_results * 2  # Request 2x for subsequent queries

                videos_task = asyncio.create_task(self.search_videos(query, request_count, language))
                videos = await asyncio.wait_for(videos_task, timeout=query_timeout)

                # Add new videos to our collection, avoiding duplicates
                for video in videos:
                    video_id = video.get('id')
                    if video_id and video_id not in existing_ids:
                        all_videos.append(video)
                        existing_ids.add(video_id)

                self.logger.info(f"Found {len(videos)} videos for query '{query}', total now: {len(all_videos)}")

                # If we got good results from the first query, we can be more selective with subsequent ones
                if i == 0 and len(videos) >= max_results:
                    max_queries_to_try = min(3, max_queries_to_try)  # Reduce max queries if first query was successful

            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout searching videos for '{query}'")
                continue
            except Exception as e:
                self.logger.error(f"Error searching videos for '{query}': {str(e)}")
                continue

        # If we still don't have enough videos, try searching for playlists
        if len(all_videos) < max_results:
            self.logger.info(f"Only found {len(all_videos)} videos, trying playlists")

            # Use the main topic for playlist search
            playlist_query = topic
            if subtopic:
                # Include subtopic for more specific playlists
                playlist_query = f"{topic} {subtopic}"

            try:
                # Search for playlists with a timeout
                playlists_task = asyncio.create_task(self.search_playlists(playlist_query, 2, language))
                playlists = await asyncio.wait_for(playlists_task, timeout=6)  # Increased timeout

                # Try each playlist until we have enough videos
                for playlist in playlists:
                    # Skip if we already have enough videos
                    if len(all_videos) >= max_results:
                        break

                    playlist_id = playlist.get('id')
                    if not playlist_id:
                        continue

                    self.logger.info(f"Trying playlist: {playlist.get('title', 'Unknown')}")

                    # Get videos from this playlist
                    try:
                        needed_videos = max(1, max_results - len(all_videos))
                        playlist_videos_task = asyncio.create_task(
                            self.get_playlist_videos(playlist_id, max_videos=needed_videos * 2, language=language)
                        )
                        playlist_videos = await asyncio.wait_for(playlist_videos_task, timeout=6)  # Increased timeout

                        # Add playlist videos to results, avoiding duplicates
                        for video in playlist_videos:
                            video_id = video.get('id')
                            if video_id and video_id not in existing_ids:
                                all_videos.append(video)
                                existing_ids.add(video_id)

                        self.logger.info(f"Added {len(playlist_videos)} videos from playlist, total now: {len(all_videos)}")

                    except (asyncio.TimeoutError, Exception) as e:
                        self.logger.warning(f"Error or timeout getting playlist videos: {str(e)}")
                        continue

            except (asyncio.TimeoutError, Exception) as e:
                self.logger.warning(f"Error or timeout searching playlists: {str(e)}")

        # Sort videos by relevance to the topic/subtopic
        if subtopic:
            relevance_query = f"{topic} {subtopic}"
        else:
            relevance_query = topic

        for video in all_videos:
            video['relevance_score'] = self._score_video(video, relevance_query)

        all_videos.sort(key=lambda v: v.get('relevance_score', 0), reverse=True)

        # Limit to max_results
        final_videos = all_videos[:max_results]

        # Convert to Resource objects
        resources = self._convert_videos_to_resources(final_videos, subtopic=subtopic, is_subtopic=bool(subtopic))

        # Cache the results
        if resources:
            # Use appropriate TTL based on result count
            if len(resources) < max_results // 2:
                # Fewer results than half requested - cache for 12 hours
                cache_ttl = min(43200, self.cache_ttl)
                self.logger.info(f"Caching {len(resources)} resources for '{topic}' with shorter TTL (12 hours)")
            else:
                # Good number of results - cache for normal TTL
                cache_ttl = self.cache_ttl
                self.logger.info(f"Caching {len(resources)} resources for '{topic}' with normal TTL")

            cache.setex(cache_key, cache_ttl, resources)
        else:
            self.logger.warning(f"No YouTube videos found for '{topic}'")

        return resources

    def _generate_search_queries(self, topic: str, subtopic: str = None, language: str = "en") -> List[Dict[str, str]]:
        """
        Generate multiple search queries for a topic/subtopic combination.

        Args:
            topic: Main topic
            subtopic: Optional subtopic
            language: Language code

        Returns:
            List of query dictionaries with 'query' and 'type' keys
        """
        queries = []
        lang_prefix = self.LANGUAGE_PREFIXES.get(language, "")

        # If we have a subtopic, create specific queries
        if subtopic:
            # Clean subtopic for better search results
            clean_subtopic = self._clean_subtopic(subtopic)

            # Add direct subtopic query
            queries.append({
                "query": f"{lang_prefix}{clean_subtopic} {topic}",
                "type": "direct_subtopic"
            })

            # Add formatted subtopic queries
            for template in self.SUBTOPIC_SEARCH_TERMS[:8]:  # Use first 8 templates
                search_term = template.format(topic=clean_subtopic)
                queries.append({
                    "query": f"{lang_prefix}{search_term} {topic}",
                    "type": "formatted_subtopic"
                })

            # Add topic-only query as fallback
            queries.append({
                "query": f"{lang_prefix}{topic}",
                "type": "topic_only"
            })
        else:
            # For main topic, start with direct query
            queries.append({
                "query": f"{lang_prefix}{topic}",
                "type": "direct_topic"
            })

            # Add some formatted topic queries
            for template in self.SUBTOPIC_SEARCH_TERMS[:6]:  # Use first 6 templates
                search_term = template.format(topic=topic)
                queries.append({
                    "query": f"{lang_prefix}{search_term}",
                    "type": "formatted_topic"
                })

        # Add simplified query if topic has multiple words
        if ' ' in topic:
            main_word = topic.split()[0]
            queries.append({
                "query": f"{lang_prefix}{main_word}",
                "type": "simplified_topic"
            })

            if subtopic and ' ' in subtopic:
                main_subtopic_word = subtopic.split()[0]
                queries.append({
                    "query": f"{lang_prefix}{main_subtopic_word} {main_word}",
                    "type": "simplified_subtopic"
                })

        return queries

    async def _refresh_topic_cache(self, topic: str, subtopic: str, max_results: int, language: str, cache_key: str) -> None:
        """
        Refresh the cache for a topic in the background.

        Args:
            topic: Main topic
            subtopic: Optional subtopic
            max_results: Maximum number of results to return
            language: Language code
            cache_key: Cache key to update
        """
        try:
            self.logger.debug(f"Background refreshing cache for topic '{topic}'")

            # Get the current cache value to compare later
            current_cached = cache.get(cache_key, resource_type='resource_list')
            current_count = len(current_cached) if current_cached else 0

            # Generate multiple search queries
            search_queries = self._generate_search_queries(topic, subtopic, language)

            # Track all videos
            all_videos = []
            existing_ids = set()

            # Try each query
            for query_info in search_queries[:3]:  # Limit to first 3 queries for background refresh
                query = query_info["query"]

                try:
                    videos = await self.search_videos(query, max_results * 2, language)

                    # Add new videos, avoiding duplicates
                    for video in videos:
                        video_id = video.get('id')
                        if video_id and video_id not in existing_ids:
                            all_videos.append(video)
                            existing_ids.add(video_id)
                except Exception:
                    continue

                if len(all_videos) >= max_results * 1.5:
                    break

            # Sort by relevance
            relevance_query = f"{topic} {subtopic}" if subtopic else topic
            for video in all_videos:
                video['relevance_score'] = self._score_video(video, relevance_query)

            all_videos.sort(key=lambda v: v.get('relevance_score', 0), reverse=True)

            # Limit to max_results
            final_videos = all_videos[:max_results]

            # Convert to Resource objects
            resources = self._convert_videos_to_resources(final_videos, subtopic=subtopic, is_subtopic=bool(subtopic))

            # Only update cache if we found more results than before
            if len(resources) > current_count:
                self.logger.info(f"Background refresh found {len(resources)} resources (was {current_count})")
                cache.setex(cache_key, self.cache_ttl, resources)
            else:
                self.logger.info(f"Background refresh didn't improve results ({len(resources)} ≤ {current_count})")

        except Exception as e:
            self.logger.error(f"Error in background topic cache refresh: {str(e)}")

    def _convert_videos_to_resources(self, videos: List[Dict[str, Any]],
                                    subtopic: str = None, is_subtopic: bool = False) -> List[Resource]:
        """
        Convert video dictionaries to Resource objects.

        Args:
            videos: List of video dictionaries
            subtopic: Optional subtopic
            is_subtopic: Whether this is a subtopic search

        Returns:
            List of Resource objects
        """
        resources = []
        for video in videos:
            # Determine difficulty based on duration and other factors
            difficulty = "intermediate"
            duration_minutes = video.get('duration', 0)
            if duration_minutes:
                if duration_minutes < 5:
                    difficulty = "beginner"
                elif duration_minutes > 30:
                    difficulty = "advanced"

            resource = Resource(
                id=f"youtube_{video.get('id')}",
                title=video.get('title', ''),
                url=video.get('url', ''),
                type="video",
                description=video.get('description', ''),
                duration=video.get('duration'),
                readTime=None,
                difficulty=difficulty,
                thumbnail=video.get('thumbnail')
            )

            # Add subtopic information if applicable
            if is_subtopic and subtopic:
                resource.title = f"{resource.title} - Relevante para: {subtopic}"

            # Add playlist information if applicable
            if video.get('isFromPlaylist'):
                resource.description = f"{resource.description}\n\nParte da playlist: {video.get('playlistTitle', '')}"
                resource.metadata = {
                    "playlistId": video.get('playlistId'),
                    "playlistTitle": video.get('playlistTitle')
                }

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
        # Merge with common options
        merged_opts = {**self.common_ydl_opts, **ydl_opts}

        # Add a timeout to the entire operation
        try:
            with yt_dlp.YoutubeDL(merged_opts) as ydl:
                # Set a timeout for the extraction process
                ydl.params['socket_timeout'] = 5  # 5 seconds timeout

                # Extract info with timeout
                result = ydl.extract_info(search_query, download=False)

                if result and 'entries' in result:
                    # Filter out None entries that might cause issues
                    entries = [entry for entry in result['entries'] if entry is not None]
                    return entries
                return []
        except yt_dlp.utils.DownloadError as e:
            # More specific error handling for common YouTube issues
            if "This video is not available" in str(e):
                self.logger.warning(f"Video not available: {str(e)}")
            elif "Video unavailable" in str(e):
                self.logger.warning(f"Video unavailable: {str(e)}")
            else:
                self.logger.error(f"Error extracting info with yt-dlp: {str(e)}")
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
        # Check in-memory cache first
        video_id = video_url.split('v=')[-1].split('&')[0] if 'v=' in video_url else None
        if video_id and video_id in self._video_details_cache:
            return self._video_details_cache[video_id]

        # Merge with common options
        merged_opts = {**self.common_ydl_opts, **ydl_opts}

        # Use a more minimal set of options for single video extraction
        merged_opts['extract_flat'] = False  # We want full details for a single video
        merged_opts['writesubtitles'] = False
        merged_opts['writeautomaticsub'] = False
        merged_opts['allsubtitles'] = False
        merged_opts['playlist_items'] = '1'  # Only extract the first item if it's a playlist

        try:
            with yt_dlp.YoutubeDL(merged_opts) as ydl:
                # Set a shorter timeout for single video extraction
                ydl.params['socket_timeout'] = 3  # 3 seconds timeout

                # Extract info with timeout
                result = ydl.extract_info(video_url, download=False, process=False)

                # Cache the result in memory
                if result and video_id:
                    self._video_details_cache[video_id] = result

                return result
        except yt_dlp.utils.DownloadError as e:
            # More specific error handling for common YouTube issues
            if "This video is not available" in str(e):
                self.logger.warning(f"Video not available: {str(e)}")
            elif "Video unavailable" in str(e):
                self.logger.warning(f"Video unavailable: {str(e)}")
            else:
                self.logger.error(f"Error extracting video info with yt-dlp: {str(e)}")
            return None
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

    def _score_video(self, video: Dict[str, Any], query: str) -> float:
        """
        Calculate a relevance score for a video based on various factors.

        Args:
            video: Video information dictionary
            query: Original search query

        Returns:
            Relevance score (higher is better)
        """
        score = 0.0

        # Extract video data
        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        view_count = video.get('viewCount', 0) or 0
        duration_seconds = video.get('duration', 0) * 60 if video.get('duration') else 0
        like_count = video.get('likeCount', 0) or 0

        # Parse upload date
        upload_date_str = video.get('publishedAt', '')
        upload_date = None
        if upload_date_str:
            try:
                # YouTube API format: YYYYMMDD
                if len(upload_date_str) == 8:
                    upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
                # ISO format
                elif 'T' in upload_date_str:
                    upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Calculate title match score
        query_terms = query.lower().split()
        title_match_count = sum(1 for term in query_terms if term in title)
        title_match_score = title_match_count / max(1, len(query_terms))
        score += title_match_score * self.TITLE_MATCH_WEIGHT

        # Calculate description match score
        description_match_count = sum(1 for term in query_terms if term in description)
        description_match_score = description_match_count / max(1, len(query_terms))
        score += description_match_score * self.DESCRIPTION_MATCH_WEIGHT

        # Calculate view count score (logarithmic scale)
        if view_count > 0:
            view_score = min(1.0, max(0.0, (min(10000000, view_count) / 10000000)))
            score += view_score * self.VIEWS_WEIGHT

        # Calculate recency score
        if upload_date:
            days_old = (datetime.now() - upload_date).days
            recency_score = max(0.0, 1.0 - (days_old / self.MAX_AGE_DAYS))
            score += recency_score * self.RECENCY_WEIGHT

        # Calculate duration score (prefer videos between 5-30 minutes)
        if duration_seconds:
            if duration_seconds < 300:  # Less than 5 minutes
                duration_score = duration_seconds / 300
            elif duration_seconds <= 1800:  # 5-30 minutes (ideal)
                duration_score = 1.0
            else:  # More than 30 minutes
                duration_score = max(0.0, 1.0 - ((duration_seconds - 1800) / 1800))
            score += duration_score * self.DURATION_WEIGHT

        # Calculate like ratio score
        if view_count > 0 and like_count > 0:
            like_ratio = min(1.0, like_count / max(1, view_count / 10))  # Assuming 10% like rate is good
            score += like_ratio * self.LIKE_RATIO_WEIGHT

        return score

    def _filter_video_by_quality(self, video: Dict[str, Any]) -> bool:
        """
        Check if a video meets the quality criteria.

        Args:
            video: Video information dictionary

        Returns:
            True if the video meets quality criteria, False otherwise
        """
        # Check view count
        view_count = video.get('viewCount', 0) or 0
        if view_count < self.MIN_VIEWS:
            return False

        # Check duration
        duration_seconds = video.get('duration', 0) * 60 if video.get('duration') else 0
        if duration_seconds < self.MIN_DURATION_SECONDS or duration_seconds > self.MAX_DURATION_SECONDS:
            return False

        # Check age
        upload_date_str = video.get('publishedAt', '')
        if upload_date_str:
            try:
                # YouTube API format: YYYYMMDD
                if len(upload_date_str) == 8:
                    upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
                    days_old = (datetime.now() - upload_date).days
                    if days_old > self.MAX_AGE_DAYS:
                        return False
            except ValueError:
                pass

        return True
