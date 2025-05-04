"""
Semantic filter service for filtering resources based on relevance to a topic.
"""

from typing import List
import nltk
from nltk.corpus import stopwords

from api.models import Resource
from infrastructure.logging import logger
from infrastructure.cache import cache

# Download NLTK resources if not already downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)


class SemanticFilterService:
    """
    Service for filtering resources based on relevance to a topic.
    Uses keyword matching to prioritize the most relevant resources.
    """

    # Stopwords for different languages
    STOPWORDS = {
        'pt': set(stopwords.words('portuguese')),
        'en': set(stopwords.words('english')),
        'es': set(stopwords.words('spanish')),
        'fr': set(stopwords.words('french')),
        'de': set(stopwords.words('german')),
        'it': set(stopwords.words('italian')),
        # Add more languages as needed
    }

    # Default stopwords (English) for languages not in the list
    DEFAULT_STOPWORDS = set(stopwords.words('english'))

    def __init__(self):
        """Initialize the semantic filter service."""
        self.logger = logger.get_logger("content_sourcing.semantic_filter")
        self.logger.info("Initialized SemanticFilterService")

    def filter_resources_by_similarity(
        self,
        resources: List[Resource],
        topic: str,
        language: str = "pt",
        similarity_threshold: float = 0.15
    ) -> List[Resource]:
        """
        Filter resources based on relevance to the topic.

        Args:
            resources: List of resources to filter
            topic: The topic to compare against
            language: Language code (e.g., 'pt', 'en', 'es')
            similarity_threshold: Minimum relevance score to keep a resource

        Returns:
            Filtered list of resources
        """
        if not resources:
            return []

        # Check cache first
        cache_key = f"semantic_filter:{topic}_{language}_{similarity_threshold}_{self._hash_resources(resources)}"
        cached_result = cache.get(cache_key, resource_type='resource_list')
        if cached_result:
            self.logger.debug(f"Using cached filter results for '{topic}'")
            return cached_result

        try:
            # Calculate relevance scores for each resource
            filtered_resources = []

            for resource in resources:
                # Calculate relevance based on keyword matching
                relevance = self._calculate_simple_similarity(resource, topic)

                # Filter resources based on relevance threshold
                if relevance >= similarity_threshold:
                    filtered_resources.append(resource)
                    self.logger.debug(f"Resource '{resource.title}' has relevance {relevance:.4f} with topic '{topic}'")
                else:
                    self.logger.debug(f"Filtered out resource '{resource.title}' with low relevance {relevance:.4f}")

            # Sort resources by relevance (highest first)
            filtered_resources.sort(key=lambda r: self._calculate_simple_similarity(r, topic), reverse=True)

            # If we filtered out too many resources, include at least 3 resources
            if len(filtered_resources) < 3 and len(resources) >= 3:
                # Sort all resources by relevance
                sorted_resources = sorted(resources, key=lambda r: self._calculate_simple_similarity(r, topic), reverse=True)
                # Take the top 3
                filtered_resources = sorted_resources[:3]

            # Cache the result
            cache.setex(
                cache_key,
                86400,  # Cache for 1 day
                filtered_resources
            )

            self.logger.info(f"Filtered {len(resources)} resources to {len(filtered_resources)} based on relevance to '{topic}'")
            return filtered_resources

        except Exception as e:
            self.logger.error(f"Error filtering resources: {str(e)}")
            # Return original resources if there's an error
            return resources

    def _calculate_simple_similarity(self, resource: Resource, topic: str) -> float:
        """
        Calculate a simple relevance score based on keyword matching.

        Args:
            resource: The resource to compare
            topic: The topic to compare against

        Returns:
            Relevance score (0-1)
        """
        # Start with a base score
        score = 0.1

        # Get the title and description
        title = resource.title.lower() if resource.title else ""
        description = resource.description.lower() if resource.description else ""
        topic_lower = topic.lower()

        # Check if topic is in title
        if topic_lower in title:
            score += 0.5

        # Check if topic is in description
        if description and topic_lower in description:
            score += 0.3

        # Check if title contains any word from topic
        topic_words = topic_lower.split()
        for word in topic_words:
            if word in title and len(word) > 3:  # Only consider words longer than 3 characters
                score += 0.2

        # Check if description contains any word from topic
        if description:
            for word in topic_words:
                if word in description and len(word) > 3:
                    score += 0.1

        # Boost score for resources with matching type
        if resource.type in ["tutorial", "documentation", "article"]:
            score += 0.2

        # Apply a minimum relevance floor for resources with exact topic match in title
        if topic_lower == title:
            score = max(score, 0.8)

        # Cap the score at 1.0
        return min(score, 1.0)

    def calculate_resource_similarity(self, resource: Resource, topic: str) -> float:
        """
        Calculate the relevance score between a resource and a topic.

        Args:
            resource: The resource to compare
            topic: The topic to compare against

        Returns:
            Relevance score (0-1)
        """
        try:
            # Use the simple relevance calculation
            return self._calculate_simple_similarity(resource, topic)
        except Exception as e:
            self.logger.error(f"Error calculating resource relevance: {str(e)}")
            return 0.0

    def _hash_resources(self, resources: List[Resource]) -> str:
        """
        Create a hash of resources for caching.

        Args:
            resources: List of resources

        Returns:
            Hash string
        """
        # Create a simple hash based on resource IDs and titles
        resource_strings = [f"{r.id}:{r.title}" for r in resources]
        return str(hash(''.join(resource_strings)))
