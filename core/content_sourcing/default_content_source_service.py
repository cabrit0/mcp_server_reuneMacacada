"""
Default implementation of the content source service.
"""

import uuid
import asyncio
from typing import List, Dict, Any, Optional, Set

from infrastructure.logging import logger
from infrastructure.cache import cache
from api.models import Resource
from services.categories import category_service
from services.youtube import youtube
from core.content_sourcing.content_source_service import ContentSourceService
from core.content_sourcing.search_service import SearchService
from core.content_sourcing.scraper_service import ScraperService


class DefaultContentSourceService(ContentSourceService):
    """
    Default implementation of the content source service.
    Combines search, scraping, and filtering to find resources.
    """

    def __init__(
        self,
        search_service: SearchService,
        scraper_service: ScraperService
    ):
        """
        Initialize the default content source service.

        Args:
            search_service: Service for searching resources
            scraper_service: Service for scraping resource details
        """
        self.logger = logger.get_logger("content_sourcing.default")
        self.search_service = search_service
        self.scraper_service = scraper_service
        self.logger.info("Initialized DefaultContentSourceService")

    async def find_resources(
        self,
        topic: str,
        max_results: int = 15,
        language: str = "pt",
        category: Optional[str] = None
    ) -> List[Resource]:
        """
        Find resources about a topic.

        Args:
            topic: The topic to search for
            max_results: Maximum number of resources to return
            language: Language code (e.g., 'pt', 'en', 'es')
            category: Optional category override (if None, will be detected)

        Returns:
            List of Resource objects
        """
        # Check cache first
        cache_key = f"resources:{topic}_{max_results}_{language}_{category}"
        cached_results = cache.get(cache_key)
        if cached_results:
            self.logger.debug(f"Using cached resources for '{topic}'")
            return [Resource(**r) for r in cached_results]

        # Use provided category or detect it automatically
        if category is None:
            category = category_service.detect_category(topic)
            self.logger.debug(f"Detected category for '{topic}': {category}")
        else:
            self.logger.debug(f"Using provided category for '{topic}': {category}")

        # Get category-specific search queries
        category_queries = category_service.get_category_specific_queries(topic, category)

        # Generate language-specific queries
        language_queries = self._generate_language_queries(topic, language)

        # Combine category-specific and language-specific queries
        queries = list(set(category_queries + language_queries))  # Remove duplicates
        self.logger.debug(f"Generated {len(queries)} search queries for '{topic}'")

        # Search for resources using the queries
        web_resources = await self._search_with_queries(queries, topic, max_results, language)
        self.logger.debug(f"Found {len(web_resources)} web resources for '{topic}'")

        # Search for YouTube videos
        youtube_resources = await self._search_youtube(topic, max_results // 3, language)
        self.logger.debug(f"Found {len(youtube_resources)} YouTube videos for '{topic}'")

        # Combine web and YouTube resources
        all_resources = web_resources + youtube_resources

        # Filter resources
        filtered_resources = self.filter_resources(all_resources, topic, max_results, language)
        self.logger.debug(f"Filtered resources: {len(all_resources)} -> {len(filtered_resources)}")

        # Cache the results
        cache.setex(cache_key, 86400, [r.model_dump() for r in filtered_resources])  # 1 day
        self.logger.info(f"Cached {len(filtered_resources)} resources for '{topic}'")

        return filtered_resources

    async def find_resources_by_query(
        self,
        query: str,
        topic: str,
        max_results: int = 5,
        language: str = "pt"
    ) -> List[Resource]:
        """
        Find resources using a specific search query.

        Args:
            query: The search query
            topic: The main topic (for context)
            max_results: Maximum number of resources to return
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            List of Resource objects
        """
        # Check cache first
        cache_key = f"resources_query:{query}_{topic}_{max_results}_{language}"
        cached_results = cache.get(cache_key)
        if cached_results:
            self.logger.debug(f"Using cached resources for query '{query}'")
            return [Resource(**r) for r in cached_results]

        # Search for resources
        search_results = await self.search_service.search(query, max_results, language)
        self.logger.debug(f"Found {len(search_results)} search results for query '{query}'")

        # Scrape details for each result
        resources = await self._scrape_search_results(search_results, topic, language)
        self.logger.debug(f"Scraped {len(resources)} resources for query '{query}'")

        # Cache the results
        cache.setex(cache_key, 86400, [r.model_dump() for r in resources])  # 1 day
        self.logger.info(f"Cached {len(resources)} resources for query '{query}'")

        return resources

    def filter_resources(
        self,
        resources: List[Resource],
        topic: str,
        max_results: int = 15,
        language: str = "pt"
    ) -> List[Resource]:
        """
        Filter and prioritize resources.

        Args:
            resources: List of resources to filter
            topic: The topic to filter by
            max_results: Maximum number of resources to return
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            Filtered list of Resource objects
        """
        # Remove duplicates (by URL)
        unique_resources = []
        seen_urls = set()
        for resource in resources:
            if resource.url not in seen_urls:
                unique_resources.append(resource)
                seen_urls.add(resource.url)

        # Sort resources by relevance (currently just by type)
        # In a future implementation, this could use TF-IDF or embeddings for better relevance scoring
        sorted_resources = sorted(
            unique_resources,
            key=lambda r: self._get_resource_priority(r, topic, language),
            reverse=True
        )

        # Limit the number of resources
        return sorted_resources[:max_results]

    def _get_resource_priority(self, resource: Resource, topic: str, language: str) -> float:
        """
        Get the priority score for a resource.

        Args:
            resource: The resource to score
            topic: The topic to score against
            language: Language code

        Returns:
            Priority score (higher is better)
        """
        # Base score
        score = 1.0

        # Boost score based on resource type
        type_boosts = {
            'documentation': 1.5,
            'tutorial': 1.4,
            'video': 1.3,
            'article': 1.2,
            'exercise': 1.1
        }
        score *= type_boosts.get(resource.type, 1.0)

        # Boost score if topic is in title
        if topic.lower() in resource.title.lower():
            score *= 1.5

        # Boost score if topic is in description
        if resource.description and topic.lower() in resource.description.lower():
            score *= 1.2

        # Boost score based on language match
        if resource.url and language in resource.url:
            score *= 1.3

        return score

    def _generate_language_queries(self, topic: str, language: str) -> List[str]:
        """
        Generate language-specific search queries.

        Args:
            topic: The topic to search for
            language: Language code

        Returns:
            List of search queries
        """
        if language == "pt":
            return [
                f"{topic} tutorial",
                f"{topic} documentação",
                f"{topic} guia",
                f"{topic} exemplos",
                f"{topic} exercícios",
                f"{topic} aula",
                f"{topic} curso",
                f"{topic} como aprender"
            ]
        elif language == "es":
            return [
                f"{topic} tutorial",
                f"{topic} documentación",
                f"{topic} guía",
                f"{topic} ejemplos",
                f"{topic} ejercicios",
                f"{topic} curso",
                f"{topic} cómo aprender"
            ]
        else:  # Default to English
            return [
                f"{topic} tutorial",
                f"{topic} documentation",
                f"{topic} guide",
                f"{topic} examples",
                f"{topic} exercises",
                f"{topic} video tutorial",
                f"{topic} how to learn"
            ]

    async def _search_with_queries(
        self,
        queries: List[str],
        topic: str,
        max_results: int,
        language: str
    ) -> List[Resource]:
        """
        Search for resources using multiple queries.

        Args:
            queries: List of search queries
            topic: The topic to search for
            max_results: Maximum number of results per query
            language: Language code

        Returns:
            List of Resource objects
        """
        all_results = []
        seen_urls: Set[str] = set()

        # Search concurrently with all queries
        search_tasks = []
        for query in queries:
            search_tasks.append(self.search_service.search(query, max_results=3, language=language))

        # Execute searches concurrently
        if search_tasks:
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(search_results):
                if not isinstance(result, Exception) and result:
                    # Filter out duplicates
                    unique_results = [r for r in result if r['url'] not in seen_urls]
                    if unique_results:
                        # Update seen URLs
                        seen_urls.update([r['url'] for r in unique_results])
                        # Scrape details for each result
                        resources = await self._scrape_search_results(unique_results, topic, language)
                        all_results.extend(resources)
                elif isinstance(result, Exception):
                    self.logger.error(f"Error searching for '{queries[i]}': {str(result)}")

        return all_results

    async def _scrape_search_results(
        self,
        search_results: List[Dict[str, Any]],
        topic: str,
        language: str
    ) -> List[Resource]:
        """
        Scrape details for search results.

        Args:
            search_results: List of search results
            topic: The topic to search for
            language: Language code

        Returns:
            List of Resource objects
        """
        resources = []

        # Process URLs in batches to avoid overload
        max_concurrent_tasks = 5  # Limit to 5 concurrent tasks
        for i in range(0, len(search_results), max_concurrent_tasks):
            batch = search_results[i:i+max_concurrent_tasks]

            # Create tasks for this batch
            scraper_tasks = []
            for result in batch:
                scraper_tasks.append(self.scraper_service.scrape(
                    url=result['url'],
                    topic=topic,
                    timeout=8,
                    language=language
                ))

            # Execute tasks concurrently with global timeout
            try:
                # Use wait_for to ensure we don't get stuck
                scraper_results = await asyncio.wait_for(
                    asyncio.gather(*scraper_tasks, return_exceptions=True),
                    timeout=20  # Global timeout of 20 seconds for the entire batch
                )

                # Process results
                for j, result in enumerate(batch):
                    if j < len(scraper_results) and not isinstance(scraper_results[j], Exception):
                        # Merge search result with scraped data
                        resource_data = {**result, **scraper_results[j]}

                        # Generate a unique ID
                        resource_id = f"resource_{uuid.uuid4().hex[:8]}"

                        # Create Resource object
                        resource = Resource(
                            id=resource_id,
                            title=resource_data.get('title', f"Resource about {topic}"),
                            url=resource_data['url'],
                            type=resource_data.get('type', 'article'),
                            description=resource_data.get('description', f"A resource about {topic}"),
                            duration=resource_data.get('duration'),
                            readTime=resource_data.get('readTime'),
                            difficulty="intermediate",  # Default difficulty
                            thumbnail=resource_data.get('thumbnail')
                        )

                        resources.append(resource)

            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout processing batch of URLs starting with {batch[0]['url']}")

            # Add a small delay to avoid overloading the server
            await asyncio.sleep(0.1)

        return resources

    async def _search_youtube(self, topic: str, max_results: int, language: str) -> List[Resource]:
        """
        Search for YouTube videos.

        Args:
            topic: The topic to search for
            max_results: Maximum number of results
            language: Language code

        Returns:
            List of Resource objects
        """
        try:
            # Use wait_for to ensure we don't get stuck
            youtube_task = asyncio.create_task(
                youtube.search_videos_for_topic(topic, topic, max_results=max_results, language=language)
            )
            youtube_resources = await asyncio.wait_for(youtube_task, timeout=15)  # 15 seconds timeout
            self.logger.debug(f"Found {len(youtube_resources)} YouTube videos for '{topic}'")
            return youtube_resources
        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout searching YouTube videos for '{topic}'")
            return []  # Empty list in case of timeout
        except Exception as e:
            self.logger.error(f"Error searching YouTube videos: {str(e)}")
            return []
