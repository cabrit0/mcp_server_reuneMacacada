"""
Semantic filter service for filtering resources based on relevance to a topic.
"""

from typing import List, Dict, Set

from api.models import Resource
from infrastructure.logging import logger
from infrastructure.cache import cache

# Try to import NLTK, but don't fail if it's not available
NLTK_AVAILABLE = False
try:
    import nltk
    from nltk.corpus import stopwords

    # Download NLTK resources if not already downloaded
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

    NLTK_AVAILABLE = True
    logger.get_logger("semantic_filter").info("NLTK is available and initialized")
except ImportError:
    logger.get_logger("semantic_filter").warning("NLTK is not available, using fallback stopwords")


class SemanticFilterService:
    """
    Service for filtering resources based on relevance to a topic.
    Uses keyword matching to prioritize the most relevant resources.
    """

    # Stopwords for different languages
    STOPWORDS = {}
    DEFAULT_STOPWORDS = set()

    if NLTK_AVAILABLE:
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
    else:
        # Fallback stopwords for common languages
        STOPWORDS = {
            'en': set(['a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
                      'at', 'from', 'by', 'for', 'with', 'about', 'against', 'between',
                      'into', 'through', 'during', 'before', 'after', 'above', 'below',
                      'to', 'of', 'in', 'on', 'is', 'are', 'was', 'were', 'be', 'been', 'being']),
            'pt': set(['a', 'o', 'e', 'é', 'de', 'da', 'do', 'em', 'no', 'na', 'um', 'uma',
                      'que', 'para', 'com', 'por', 'como', 'mas', 'ou', 'se', 'porque',
                      'quando', 'onde', 'quem', 'qual', 'quais', 'seu', 'sua', 'seus', 'suas']),
            'es': set(['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o',
                      'pero', 'si', 'de', 'del', 'a', 'en', 'por', 'para', 'con', 'sin',
                      'sobre', 'entre', 'como', 'cuando', 'donde', 'quien', 'que', 'cual'])
        }
        DEFAULT_STOPWORDS = STOPWORDS['en']

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
        Uses progressive filtering with adaptive thresholds.

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
            # Pre-calculate all relevance scores to avoid redundant calculations
            resource_scores = []
            for resource in resources:
                score = self._calculate_simple_similarity(resource, topic)
                # Store the score with the resource for later use
                resource_scores.append((resource, score))

            # Sort by relevance (highest first)
            resource_scores.sort(key=lambda x: x[1], reverse=True)

            # Adaptive filtering based on the number of resources
            min_required = min(15, len(resources))  # At least 15 resources or all if fewer (increased from 8)

            # Log the top 5 resources with their scores for debugging
            for i, (resource, score) in enumerate(resource_scores[:5]):
                self.logger.info(f"Top resource {i+1}: {resource.title} - Score: {score:.4f}")

            # Try with a lower threshold to get more resources
            lower_threshold = max(0.05, similarity_threshold * 0.5)  # Lower the threshold by 50%, but not below 0.05
            self.logger.info(f"Using lower threshold {lower_threshold} instead of {similarity_threshold} to get more resources")

            filtered_resources = [r for r, score in resource_scores if score >= lower_threshold]
            self.logger.info(f"Got {len(filtered_resources)} resources with threshold {lower_threshold}")

            # If we don't have enough resources, try with an even lower threshold
            if len(filtered_resources) < min_required:
                # Calculate a dynamic threshold that would give us the minimum required resources
                if len(resource_scores) >= min_required:
                    # Get the score of the min_required-th resource
                    dynamic_threshold = resource_scores[min_required-1][1]
                    # Use the lower of the adjusted threshold or the dynamic one
                    adjusted_threshold = min(lower_threshold, dynamic_threshold)

                    # Apply the adjusted threshold
                    filtered_resources = [r for r, score in resource_scores if score >= adjusted_threshold]

                    self.logger.info(f"Adjusted threshold from {lower_threshold} to {adjusted_threshold} to include at least {min_required} resources")
                else:
                    # If we have fewer resources than min_required, use all of them
                    filtered_resources = [r for r, _ in resource_scores]
                    self.logger.info(f"Using all {len(filtered_resources)} resources because we have fewer than {min_required}")

            # If we still don't have enough resources, just take the top ones
            if len(filtered_resources) < min_required and len(resource_scores) >= min_required:
                filtered_resources = [r for r, _ in resource_scores[:min_required]]
                self.logger.info(f"Taking top {min_required} resources because filtering didn't yield enough")

            # Add relevance scores as metadata for debugging and sorting
            for i, (resource, score) in enumerate(resource_scores):
                if resource in filtered_resources:
                    if not resource.metadata:
                        resource.metadata = {}
                    resource.metadata['relevance_score'] = score
                    resource.metadata['relevance_rank'] = i + 1

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
        Optimized for performance with early returns and caching.

        Args:
            resource: The resource to compare
            topic: The topic to compare against

        Returns:
            Relevance score (0-1)
        """
        # Check if we already calculated this score (in resource metadata)
        if resource.metadata and 'relevance_score' in resource.metadata:
            return resource.metadata['relevance_score']

        # Start with a higher base score to be less restrictive
        score = 0.2  # Increased from 0.1

        # Get the title and description
        title = resource.title.lower() if resource.title else ""
        if not title:  # If no title, still give it a chance
            return 0.15  # Increased from 0.05

        description = resource.description.lower() if resource.description else ""
        topic_lower = topic.lower()

        # Early return for exact matches (high performance optimization)
        if topic_lower == title:
            return 0.95  # Almost perfect match

        # Check if topic is in title (high impact)
        if topic_lower in title:
            score += 0.5
            # If topic is a significant part of the title, boost further
            if len(topic_lower) > len(title) / 3:
                score += 0.2

        # Check if topic is in description
        if description and topic_lower in description:
            score += 0.3

        # If we already have a high score, we can return early
        if score >= 0.7:
            return min(score, 1.0)

        # Prepare topic words once (optimization)
        # Reduced minimum word length from 3 to 2 to catch more matches
        topic_words = [w for w in topic_lower.split() if len(w) > 2]

        # Check if title contains any word from topic
        title_matches = sum(1 for word in topic_words if word in title)
        if title_matches > 0:
            # Proportional boost based on how many words match (increased from 0.2)
            score += 0.25 * (title_matches / max(1, len(topic_words)))

        # Check if description contains any word from topic
        if description:
            desc_matches = sum(1 for word in topic_words if word in description)
            if desc_matches > 0:
                # Proportional boost based on how many words match (increased from 0.1)
                score += 0.15 * (desc_matches / max(1, len(topic_words)))

        # Boost score for resources with matching type (increased boosts)
        if resource.type in ["tutorial", "documentation", "article"]:
            score += 0.25  # Increased from 0.2
        elif resource.type == "video":
            score += 0.2  # Increased from 0.15

        # URL relevance boost (increased from 0.1)
        if resource.url and topic_lower in resource.url.lower():
            score += 0.15

        # Store the score in metadata for future use
        if not resource.metadata:
            resource.metadata = {}
        resource.metadata['relevance_score'] = min(score, 1.0)

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
