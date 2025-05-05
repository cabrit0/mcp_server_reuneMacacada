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
from services.youtube import get_youtube
from core.content_sourcing.content_source_service import ContentSourceService
from core.content_sourcing.search_service import SearchService
from core.content_sourcing.scraper_service import ScraperService
from core.content_sourcing.semantic_filter_service import SemanticFilterService

# Import documentation factory lazily to avoid circular imports


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
        self.semantic_filter = SemanticFilterService()
        self.logger.info("Initialized DefaultContentSourceService")

    async def find_resources(
        self,
        topic: str,
        max_results: int = 15,
        language: str = "pt",
        category: Optional[str] = None,
        similarity_threshold: float = 0.15
    ) -> List[Resource]:
        """
        Find resources about a topic.

        Args:
            topic: The topic to search for
            max_results: Maximum number of resources to return
            language: Language code (e.g., 'pt', 'en', 'es')
            category: Optional category override (if None, will be detected)
            similarity_threshold: Minimum semantic similarity threshold (0-1)

        Returns:
            List of Resource objects
        """
        # Check cache first
        cache_key = f"resources:{topic}_{max_results}_{language}_{category}_{similarity_threshold}"
        cached_results = cache.get(cache_key, resource_type='resource_list')
        if cached_results:
            self.logger.info(f"Using cached resources for '{topic}'")
            return cached_results

        self.logger.info(f"Starting resource search for topic: '{topic}'")

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

        # Create tasks for all resource types and run them in parallel
        # Aumentar o número de recursos buscados para garantir que tenhamos recursos suficientes
        # Usar busca normal para evitar problemas com a busca paralela
        web_task = asyncio.create_task(self._search_with_queries(queries, topic, max_results * 3, language))
        youtube_task = asyncio.create_task(self._search_youtube(topic, max_results, language))
        documentation_task = asyncio.create_task(self._search_documentation(topic, max_results, language))

        # Set a global timeout for all resource gathering
        try:
            # Wait for all tasks with a global timeout
            results = await asyncio.wait_for(
                asyncio.gather(web_task, youtube_task, documentation_task, return_exceptions=True),
                timeout=60  # 1 minute timeout for all resource gathering
            )

            # Process results
            web_resources = results[0] if not isinstance(results[0], Exception) else []
            youtube_resources = results[1] if not isinstance(results[1], Exception) else []
            documentation_resources = results[2] if not isinstance(results[2], Exception) else []

            if isinstance(results[0], Exception):
                self.logger.error(f"Error searching web resources: {str(results[0])}")
            if isinstance(results[1], Exception):
                self.logger.error(f"Error searching YouTube resources: {str(results[1])}")
            if isinstance(results[2], Exception):
                self.logger.error(f"Error searching documentation resources: {str(results[2])}")

            self.logger.debug(f"Found {len(web_resources)} web resources for '{topic}'")
            self.logger.debug(f"Found {len(youtube_resources)} YouTube videos for '{topic}'")
            self.logger.debug(f"Found {len(documentation_resources)} documentation resources for '{topic}'")

        except asyncio.TimeoutError:
            self.logger.warning(f"Global timeout reached while gathering resources for '{topic}'")
            # Try to get partial results from tasks that might have completed
            web_resources = []
            youtube_resources = []
            documentation_resources = []

            if web_task.done() and not web_task.exception():
                web_resources = web_task.result()
            if youtube_task.done() and not youtube_task.exception():
                youtube_resources = youtube_task.result()
            if documentation_task.done() and not documentation_task.exception():
                documentation_resources = documentation_task.result()

        # Combine all resources
        all_resources = web_resources + youtube_resources + documentation_resources

        # Log detailed information about resources found
        self.logger.info(f"Found {len(web_resources)} web resources for '{topic}'")
        self.logger.info(f"Found {len(youtube_resources)} YouTube resources for '{topic}'")
        self.logger.info(f"Found {len(documentation_resources)} documentation resources for '{topic}'")
        self.logger.info(f"Total resources before filtering: {len(all_resources)}")

        # Log the first few resources for debugging
        if web_resources:
            self.logger.info(f"Sample web resource: {web_resources[0].title} - {web_resources[0].url}")
        if youtube_resources:
            self.logger.info(f"Sample YouTube resource: {youtube_resources[0].title} - {youtube_resources[0].url}")
        if documentation_resources:
            self.logger.info(f"Sample documentation resource: {documentation_resources[0].title} - {documentation_resources[0].url}")

        # If we have too few resources, try to use cached resources from previous searches
        if len(all_resources) < 5:
            self.logger.warning(f"Found only {len(all_resources)} resources for '{topic}', checking cache for similar topics")
            # Try to find similar topics in cache
            similar_resources = self._get_similar_cached_resources(topic, language)
            if similar_resources:
                self.logger.info(f"Found {len(similar_resources)} resources from similar topics in cache")
                all_resources.extend(similar_resources)

        # Filter resources
        filtered_resources = self.filter_resources(
            all_resources,
            topic,
            max_results,
            language,
            similarity_threshold
        )
        self.logger.debug(f"Filtered resources: {len(all_resources)} -> {len(filtered_resources)}")

        # Cache the results
        cache.setex(cache_key, 86400, filtered_resources)  # 1 day
        self.logger.info(f"Cached {len(filtered_resources)} resources for '{topic}'")

        return filtered_resources

    def _get_similar_cached_resources(self, topic: str, language: str) -> List[Resource]:
        """
        Get resources from cache for similar topics.

        Args:
            topic: The current topic
            language: Language code

        Returns:
            List of Resource objects from similar topics
        """
        # This is a simple implementation that just checks for topics that contain
        # the same words. A more sophisticated implementation could use embeddings.
        similar_resources = []
        topic_words = set(topic.lower().split())

        # Get all cache keys for resources
        all_keys = cache.keys("resources:*")

        for key in all_keys:
            # Extract topic and language from key
            parts = key.split("_")
            if len(parts) > 2:  # Need at least topic, max_results, and language
                cached_topic = parts[0].replace("resources:", "")
                cached_language = parts[2]

                # Skip exact match (we already checked that)
                if cached_topic == topic:
                    continue

                # Prefer resources in the same language
                if cached_language != language:
                    continue

                # Check if there's word overlap
                cached_words = set(cached_topic.lower().split())
                if topic_words.intersection(cached_words):
                    # Get resources from cache
                    cached_resources = cache.get(key, resource_type='resource_list')
                    if cached_resources:
                        # Take a few resources from this topic
                        similar_resources.extend(cached_resources[:3])

                        # If we have enough, stop
                        if len(similar_resources) >= 5:
                            break

        return similar_resources

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
        cached_results = cache.get(cache_key, resource_type='resource_list')
        if cached_results:
            self.logger.debug(f"Using cached resources for query '{query}'")
            return cached_results

        # Search for resources
        search_results = await self.search_service.search(query, max_results, language)
        self.logger.debug(f"Found {len(search_results)} search results for query '{query}'")

        # Scrape details for each result
        resources = await self._scrape_search_results(search_results, topic, language)
        self.logger.debug(f"Scraped {len(resources)} resources for query '{query}'")

        # Cache the results
        cache.setex(cache_key, 86400, resources)  # 1 day
        self.logger.info(f"Cached {len(resources)} resources for query '{query}'")

        return resources

    def filter_resources(
        self,
        resources: List[Resource],
        topic: str,
        max_results: int = 15,
        language: str = "pt",
        similarity_threshold: float = 0.1  # Reduced from 0.15 to be less restrictive
    ) -> List[Resource]:
        """
        Filter and prioritize resources.

        Args:
            resources: List of resources to filter
            topic: The topic to filter by
            max_results: Maximum number of resources to return
            language: Language code (e.g., 'pt', 'en', 'es')
            similarity_threshold: Minimum semantic similarity threshold (0-1)

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

        # Apply semantic filtering to ensure resources are relevant to the topic
        self.logger.info(f"Applying semantic filtering with threshold {similarity_threshold} to {len(unique_resources)} resources")

        # Log some sample resources before filtering
        if unique_resources:
            for i, resource in enumerate(unique_resources[:3]):
                self.logger.info(f"Resource {i+1} before filtering: {resource.title} - {resource.url} - Type: {resource.type}")

        semantically_filtered = self.semantic_filter.filter_resources_by_similarity(
            unique_resources, topic, language, similarity_threshold
        )
        self.logger.info(f"Semantic filtering: {len(unique_resources)} -> {len(semantically_filtered)} resources")

        # Log some sample resources after filtering
        if semantically_filtered:
            for i, resource in enumerate(semantically_filtered[:3]):
                self.logger.info(f"Resource {i+1} after filtering: {resource.title} - {resource.url} - Type: {resource.type}")
                if hasattr(resource, 'metadata') and resource.metadata:
                    self.logger.info(f"  Metadata: {resource.metadata}")

        # If semantic filtering removed too many resources, fall back to original list
        if len(semantically_filtered) < 5 and len(unique_resources) > 5:
            self.logger.warning(f"Semantic filtering removed too many resources, falling back to original list")
            filtered_resources = unique_resources
        else:
            filtered_resources = semantically_filtered

        # Log warning if we have few resources
        if len(filtered_resources) < 10:
            self.logger.warning(f"Not enough resources found for topic: {topic}. Only {len(filtered_resources)} resources available.")

        # Log the types of resources we have
        resource_types = {}
        for resource in filtered_resources:
            resource_type = resource.type
            resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
        self.logger.info(f"Resource types distribution: {resource_types}")

        # Sort resources by relevance
        sorted_resources = sorted(
            filtered_resources,
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
            'documentation': 1.6,
            'tutorial': 1.4,
            'video': 1.3,
            'article': 1.2,
            'exercise': 1.1,
            'qa': 1.5  # Stack Overflow questions and answers
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

        # Calculate relevance and boost score
        try:
            relevance = self.semantic_filter.calculate_resource_similarity(resource, topic)
            # Apply a multiplier based on relevance (1.0 to 2.0)
            relevance_boost = 1.0 + relevance
            score *= relevance_boost
            self.logger.debug(f"Resource '{resource.title}' has relevance {relevance:.4f}, boosting score by {relevance_boost:.2f}")
        except Exception as e:
            self.logger.warning(f"Error calculating resource relevance for '{resource.title}': {str(e)}")

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

    async def _search_with_queries_parallel(
        self,
        queries: List[str],
        topic: str,
        max_results: int,
        language: str
    ) -> List[Resource]:
        """
        Search for resources using multiple queries with parallel search.
        Uses the FallbackSearch's parallel search method to search with multiple engines simultaneously.

        Args:
            queries: List of search queries
            topic: The topic to search for
            max_results: Maximum number of results per query
            language: Language code

        Returns:
            List of Resource objects
        """
        # Check cache first for this topic
        cache_key = f"search_with_queries_parallel:{topic}_{language}"
        cached_results = cache.get(cache_key, resource_type='resource_list')
        if cached_results:
            self.logger.info(f"Using cached parallel search results for '{topic}'")
            return cached_results

        all_results = []
        seen_urls: Set[str] = set()

        # Limit the number of queries to reduce processing time
        # We'll prioritize the most important queries
        # Aumentar o número de consultas para garantir que tenhamos recursos suficientes
        max_queries = min(8, len(queries))  # Aumentado de 6 para 8
        if len(queries) > max_queries:
            self.logger.info(f"Limiting search from {len(queries)} to {max_queries} queries for efficiency")
            # Prioritize queries with the topic name
            topic_queries = [q for q in queries if topic.lower() in q.lower()]
            other_queries = [q for q in queries if topic.lower() not in q.lower()]

            # Take a mix of topic-specific and general queries
            selected_queries = (topic_queries + other_queries)[:max_queries]
            queries = selected_queries

        # Calculate max results per query
        # Aumentar o número de resultados por consulta para garantir que tenhamos recursos suficientes
        results_per_query = max(5, max_results // len(queries)) if queries else 8  # Aumentado de 3 para 5, e de 5 para 8

        # Get the fallback search service for parallel search
        from services.search.search_factory import SearchFactory
        fallback_search = SearchFactory.create_search("fallback")

        # Process queries in parallel
        for query in queries:
            try:
                # Use parallel search to search with multiple engines simultaneously
                search_results = await fallback_search.search_parallel(query, results_per_query, language)

                if not search_results:
                    continue

                # Filter out duplicates
                unique_results = [r for r in search_results if r['url'] not in seen_urls]
                if not unique_results:
                    continue

                # Update seen URLs
                seen_urls.update([r['url'] for r in unique_results])

                # Scrape details for each result
                resources = await self._scrape_search_results(unique_results, topic, language)
                all_results.extend(resources)

                # Check if we already have enough results
                if len(all_results) >= max_results:
                    self.logger.info(f"Already have {len(all_results)} results, stopping search")
                    break
            except Exception as e:
                self.logger.error(f"Error processing query '{query}': {str(e)}")

        # Cache the results
        if all_results:
            # Limit the number of results to cache
            cache_results = all_results[:max_results]
            cache.setex(cache_key, 86400, cache_results)  # 1 day
            self.logger.info(f"Cached {len(cache_results)} resources for topic '{topic}'")

        return all_results[:max_results]  # Ensure we don't return more than requested

    async def _search_with_queries(
        self,
        queries: List[str],
        topic: str,
        max_results: int,
        language: str
    ) -> List[Resource]:
        """
        Search for resources using multiple queries with improved parallelism.
        Uses a progressive approach to start processing results as they come in.

        Args:
            queries: List of search queries
            topic: The topic to search for
            max_results: Maximum number of results per query
            language: Language code

        Returns:
            List of Resource objects
        """
        # Check cache first for this topic
        cache_key = f"search_with_queries:{topic}_{language}"
        cached_results = cache.get(cache_key, resource_type='resource_list')
        if cached_results:
            self.logger.info(f"Using cached search results for '{topic}'")
            return cached_results

        all_results = []
        seen_urls: Set[str] = set()

        # Limit the number of queries to reduce processing time
        # We'll prioritize the most important queries
        # Aumentar o número de consultas para garantir que tenhamos recursos suficientes
        max_queries = min(8, len(queries))  # Aumentado de 6 para 8
        if len(queries) > max_queries:
            self.logger.info(f"Limiting search from {len(queries)} to {max_queries} queries for efficiency")
            # Prioritize queries with the topic name
            topic_queries = [q for q in queries if topic.lower() in q.lower()]
            other_queries = [q for q in queries if topic.lower() not in q.lower()]

            # Take a mix of topic-specific and general queries
            selected_queries = (topic_queries + other_queries)[:max_queries]
            queries = selected_queries

        # Calculate max results per query
        # Aumentar o número de resultados por consulta para garantir que tenhamos recursos suficientes
        results_per_query = max(5, max_results // len(queries)) if queries else 8  # Aumentado de 3 para 5, e de 5 para 8

        # Process queries in parallel but with controlled concurrency
        # This allows us to start processing results as they come in
        async def process_query(query: str) -> List[Resource]:
            try:
                # Search with timeout
                search_result = await asyncio.wait_for(
                    self.search_service.search(query, max_results=results_per_query, language=language),
                    timeout=8  # Reduced from 10 to 8 seconds
                )

                if not search_result:
                    return []

                # Filter out duplicates
                unique_results = [r for r in search_result if r['url'] not in seen_urls]
                if not unique_results:
                    return []

                # Update seen URLs (with lock to avoid race conditions)
                seen_urls.update([r['url'] for r in unique_results])

                # Scrape details for each result
                resources = await self._scrape_search_results(unique_results, topic, language)
                return resources
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout searching for '{query}'")
                return []
            except Exception as e:
                self.logger.error(f"Error processing query '{query}': {str(e)}")
                return []

        # Process queries in batches for better control
        batch_size = 3  # Aumentado de 2 para 3 para melhorar a eficiência
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i+batch_size]

            # Check if we already have enough results
            if len(all_results) >= max_results:
                self.logger.info(f"Already have {len(all_results)} results, stopping search")
                break

            # Process this batch
            batch_tasks = [process_query(query) for query in batch]
            try:
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*batch_tasks, return_exceptions=True),
                    timeout=12  # Timeout for the entire batch
                )

                # Process results
                for j, result in enumerate(batch_results):
                    if not isinstance(result, Exception) and result:
                        all_results.extend(result)
                    elif isinstance(result, Exception):
                        self.logger.error(f"Error in batch processing: {str(result)}")
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout processing batch of queries, continuing with partial results")

        # Cache the results
        if all_results:
            # Limit the number of results to cache
            cache_results = all_results[:max_results]
            cache.setex(cache_key, 86400, cache_results)  # 1 day
            self.logger.info(f"Cached {len(cache_results)} resources for topic '{topic}'")

        return all_results[:max_results]  # Ensure we don't return more than requested

    async def _scrape_search_results(
        self,
        search_results: List[Dict[str, Any]],
        topic: str,
        language: str,
        min_resources: int = 15  # Número mínimo de recursos desejados (aumentado de 8 para 15)
    ) -> List[Resource]:
        """
        Scrape details for search results progressively.
        Stops scraping once we have enough good resources.

        Args:
            search_results: List of search results
            topic: The topic to search for
            language: Language code
            min_resources: Minimum number of resources desired

        Returns:
            List of Resource objects
        """
        # Check cache first
        urls = [result['url'] for result in search_results]
        cache_key = f"scrape_results:{','.join(urls[:3])}_{topic}_{language}"
        cached_results = cache.get(cache_key, resource_type='resource_list')
        if cached_results:
            self.logger.info(f"Using cached scrape results for {len(urls)} URLs")
            return cached_results

        resources = []

        # Limit the number of URLs to scrape to improve performance
        # Aumentar o número de URLs para garantir que tenhamos recursos suficientes
        max_urls = min(30, len(search_results))  # Aumentado de 20 para 30
        if len(search_results) > max_urls:
            self.logger.info(f"Limiting scraping from {len(search_results)} to {max_urls} URLs for efficiency")
            search_results = search_results[:max_urls]

        # Process URLs in smaller batches with progressive checking
        max_concurrent_tasks = 5  # Aumentado de 4 para 5 para melhorar a eficiência
        for i in range(0, len(search_results), max_concurrent_tasks):
            # Check if we already have enough resources
            if len(resources) >= min_resources:
                self.logger.info(f"Already have {len(resources)} resources, stopping scraping")
                break

            batch = search_results[i:i+max_concurrent_tasks]

            # Prioritize URLs that are likely to be more relevant
            # (e.g., those with the topic in the URL or title)
            batch = sorted(batch, key=lambda r: self._get_url_relevance_score(r, topic), reverse=True)

            # Create tasks for this batch
            scraper_tasks = []
            for result in batch:
                scraper_tasks.append(self.scraper_service.scrape(
                    url=result['url'],
                    topic=topic,
                    timeout=5,  # 5 seconds timeout per URL
                    language=language
                ))

            # Execute tasks concurrently with global timeout
            try:
                # Use wait_for to ensure we don't get stuck
                scraper_results = await asyncio.wait_for(
                    asyncio.gather(*scraper_tasks, return_exceptions=True),
                    timeout=10  # 10 seconds timeout for the batch
                )

                # Process results
                for j, result in enumerate(batch):
                    if j < len(scraper_results):
                        if not isinstance(scraper_results[j], Exception):
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
                                thumbnail=resource_data.get('thumbnail'),
                                metadata=resource_data.get('metadata')
                            )

                            resources.append(resource)
                        else:
                            # Create a minimal resource with just the URL and title from search result
                            self.logger.debug(f"Using fallback for failed scrape of {result['url']}")
                            resource = Resource(
                                id=f"resource_{uuid.uuid4().hex[:8]}",
                                title=result.get('title', f"Resource about {topic}"),
                                url=result['url'],
                                type='article',
                                description=result.get('description', f"A resource about {topic}"),
                                difficulty="intermediate"
                            )
                            resources.append(resource)

            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout processing batch of URLs, continuing with partial results")
                # Create minimal resources for the URLs in this batch
                for result in batch:
                    resource = Resource(
                        id=f"resource_{uuid.uuid4().hex[:8]}",
                        title=result.get('title', f"Resource about {topic}"),
                        url=result['url'],
                        type='article',
                        description=result.get('description', f"A resource about {topic}"),
                        difficulty="intermediate"
                    )
                    resources.append(resource)

        # Cache the results
        if resources:
            cache.setex(cache_key, 86400, resources)  # 1 day

        return resources

    def _get_url_relevance_score(self, result: Dict[str, Any], topic: str) -> float:
        """
        Calculate a relevance score for a URL based on how likely it is to be useful.

        Args:
            result: Search result dictionary
            topic: The search topic

        Returns:
            Relevance score (higher is better)
        """
        score = 1.0  # Base score

        # Check URL
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        description = result.get('description', '').lower()

        topic_words = topic.lower().split()

        # Boost for topic words in URL
        for word in topic_words:
            if word in url:
                score += 0.5

        # Boost for topic words in title
        for word in topic_words:
            if word in title:
                score += 0.3

        # Boost for topic words in description
        for word in topic_words:
            if word in description:
                score += 0.1

        # Boost for educational domains
        if '.edu' in url:
            score += 0.5
        elif 'tutorial' in url or 'learn' in url or 'course' in url:
            score += 0.3

        # Penalize for potentially low-quality content
        if 'forum' in url or 'comment' in url:
            score -= 0.2

        return score

    async def _search_documentation(self, topic: str, max_results: int, language: str) -> List[Resource]:
        """
        Search for documentation resources.

        Args:
            topic: The topic to search for
            max_results: Maximum number of results
            language: Language code

        Returns:
            List of Resource objects
        """
        # Check cache first
        cache_key = f"documentation:{topic}_{max_results}_{language}"
        cached_result = cache.get(cache_key, resource_type='resource_list')
        if cached_result:
            self.logger.info(f"Using cached documentation resources for '{topic}'")
            return cached_result

        try:
            # Import documentation factory lazily to avoid circular imports
            from services.documentation import get_documentation_factory

            # Get documentation factory
            doc_factory = get_documentation_factory()

            # Get services that support this topic
            services = doc_factory.get_services_for_topic(topic)

            # Filter services by language support
            services = [s for s in services if language in s.supported_languages]

            if not services:
                self.logger.debug(f"No documentation services support topic '{topic}' in language '{language}'")
                return []

            # Limit the number of services to use for better performance
            # Aumentar o número de serviços para garantir que tenhamos recursos suficientes
            max_services = min(3, len(services))
            if len(services) > max_services:
                self.logger.info(f"Limiting documentation services from {len(services)} to {max_services} for efficiency")
                services = services[:max_services]

            # Calculate max results per service
            max_per_service = max(1, max_results // len(services))

            # Search concurrently with all services
            search_tasks = []
            for service in services:
                search_tasks.append(service.search_documentation_for_topic(
                    topic=topic,
                    max_results=max_per_service,
                    language=language
                ))

            # Execute searches concurrently with shorter timeout
            try:
                doc_results = await asyncio.wait_for(
                    asyncio.gather(*search_tasks, return_exceptions=True),
                    timeout=8  # Reduced from 15 to 8 seconds
                )

                # Process results
                all_resources = []
                for i, result in enumerate(doc_results):
                    if not isinstance(result, Exception) and result:
                        all_resources.extend(result)
                    elif isinstance(result, Exception):
                        service_name = services[i].name if i < len(services) else "Unknown"
                        self.logger.error(f"Error searching documentation with {service_name}: {str(result)}")

                # Limit to max_results
                resources = all_resources[:max_results]

                # Cache the results even if empty (to avoid repeated failed lookups)
                cache.setex(cache_key, 86400, resources if resources else [])  # 1 day

                return resources
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout searching documentation for '{topic}'")
                # Cache empty result to avoid repeated timeouts
                cache.setex(cache_key, 3600, [])  # 1 hour for failed searches
                return []

        except Exception as e:
            self.logger.error(f"Error searching documentation: {str(e)}")
            return []

    async def _search_youtube(self, topic: str, max_results: int, language: str) -> List[Resource]:
        """
        Search for YouTube videos with multiple queries to increase coverage.

        Args:
            topic: The topic to search for
            max_results: Maximum number of results
            language: Language code

        Returns:
            List of Resource objects
        """
        # Check cache first
        cache_key = f"youtube:{topic}_{max_results}_{language}"
        cached_result = cache.get(cache_key, resource_type='resource_list')
        if cached_result:
            self.logger.info(f"Using cached YouTube results for '{topic}'")
            return cached_result

        try:
            # Gerar consultas específicas para o YouTube para aumentar a cobertura
            youtube_queries = [
                f"{topic} tutorial",
                f"{topic} guide",
                f"{topic} for beginners",
                f"{topic} explained",
                f"{topic} introduction"
            ]

            # Adicionar a consulta original
            if topic not in youtube_queries:
                youtube_queries.insert(0, topic)

            all_resources = []
            seen_urls = set()

            # Processar consultas em paralelo em lotes
            batch_size = 2  # Processar 2 consultas por vez
            for i in range(0, len(youtube_queries), batch_size):
                batch = youtube_queries[i:i+batch_size]

                # Criar tarefas para este lote
                search_tasks = []
                for query in batch:
                    search_tasks.append(
                        get_youtube().search_videos_for_topic(
                            query,
                            topic,
                            max_results=max(3, max_results // len(youtube_queries)),
                            language=language
                        )
                    )

                # Executar tarefas em paralelo com timeout
                try:
                    batch_results = await asyncio.wait_for(
                        asyncio.gather(*search_tasks, return_exceptions=True),
                        timeout=12  # Timeout mais longo para permitir mais resultados
                    )

                    # Processar resultados
                    for j, result in enumerate(batch_results):
                        if not isinstance(result, Exception) and result:
                            # Filtrar URLs duplicadas
                            unique_resources = []
                            for resource in result:
                                if hasattr(resource, 'url') and resource.url not in seen_urls:
                                    seen_urls.add(resource.url)
                                    unique_resources.append(resource)
                                elif isinstance(resource, dict) and 'url' in resource and resource['url'] not in seen_urls:
                                    seen_urls.add(resource['url'])
                                    unique_resources.append(resource)

                            all_resources.extend(unique_resources)
                            self.logger.debug(f"Found {len(unique_resources)} unique YouTube videos for query '{batch[j]}'")
                        elif isinstance(result, Exception):
                            self.logger.error(f"Error searching YouTube for query '{batch[j]}': {str(result)}")

                except asyncio.TimeoutError:
                    self.logger.warning(f"Timeout searching YouTube videos for batch {i//batch_size + 1}")

                # Se já temos recursos suficientes, parar
                if len(all_resources) >= max_results:
                    self.logger.info(f"Already have {len(all_resources)} YouTube resources, stopping search")
                    break

            # Se não encontramos resultados, tentar uma consulta simplificada
            if not all_resources:
                simplified_topic = topic.split()[0] if ' ' in topic else topic
                if simplified_topic != topic:
                    self.logger.debug(f"Trying simplified topic '{simplified_topic}' for YouTube search")
                    youtube_task = asyncio.create_task(
                        get_youtube().search_videos_for_topic(simplified_topic, topic, max_results=max_results, language=language)
                    )
                    youtube_resources = await asyncio.wait_for(youtube_task, timeout=10)

                    if youtube_resources:
                        all_resources.extend(youtube_resources)
                        self.logger.debug(f"Found {len(youtube_resources)} YouTube videos for simplified topic '{simplified_topic}'")

            # Limitar ao número máximo de resultados
            result_resources = all_resources[:max_results]

            # Cache the results
            if result_resources:
                self.logger.info(f"Found total of {len(result_resources)} YouTube videos for '{topic}'")
                cache.setex(cache_key, 86400, result_resources)  # 1 day
                return result_resources

            # If still no results, return empty list
            return []

        except asyncio.TimeoutError:
            self.logger.warning(f"Timeout searching YouTube videos for '{topic}'")
            return []  # Empty list in case of timeout
        except Exception as e:
            self.logger.error(f"Error searching YouTube videos: {str(e)}")
            return []


