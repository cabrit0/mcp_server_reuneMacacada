"""
Default implementation of the path generator service.
"""

import uuid
import random
from typing import List, Dict, Optional

from infrastructure.logging import logger
from infrastructure.cache import cache
from api.models import MCP, Resource
from services.categories import category_service
from core.path_generator.path_generator_service import PathGeneratorService
from core.path_generator.subtopic_generator_service import SubtopicGeneratorService
from core.path_generator.node_structure_service import NodeStructureService


class DefaultPathGenerator(PathGeneratorService):
    """
    Default implementation of the path generator service.
    """

    def __init__(
        self,
        subtopic_generator: SubtopicGeneratorService,
        node_structure_service: NodeStructureService
    ):
        """
        Initialize the default path generator.

        Args:
            subtopic_generator: Subtopic generator service
            node_structure_service: Node structure service
        """
        self.logger = logger.get_logger("path_generator.default")
        self.subtopic_generator = subtopic_generator
        self.node_structure_service = node_structure_service
        self.logger.info("Initialized DefaultPathGenerator")

    async def generate_learning_path(
        self,
        topic: str,
        resources: List[Resource],
        min_nodes: int = 15,
        max_nodes: int = 28,
        min_width: int = 3,
        max_width: int = 5,
        min_height: int = 3,
        max_height: int = 7,
        category: Optional[str] = None,
        language: str = "pt"
    ) -> MCP:
        """
        Generate a learning path based on a topic and a list of resources.

        Args:
            topic: The topic of the learning path
            resources: List of resources to include in the path
            min_nodes: Minimum number of nodes in the learning path
            max_nodes: Maximum number of nodes in the learning path
            min_width: Minimum width of the tree (nodes at first level)
            max_width: Maximum width at any level of the tree
            min_height: Minimum height of the tree (depth)
            max_height: Maximum height of the tree (depth)
            category: Category for the topic (if None, will be detected automatically)
            language: Language for resources (e.g., 'pt', 'en', 'es')

        Returns:
            MCP object representing the learning path
        """
        # Check cache first
        cache_key = f"mcp:{topic}_{min_nodes}_{max_nodes}_{min_width}_{max_width}_{min_height}_{max_height}_{category}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached learning path for '{topic}'")
            return cached_result

        # Detect category if not provided
        if category is None:
            category = category_service.detect_category(topic)
            self.logger.debug(f"Detected category for '{topic}': {category}")
        else:
            self.logger.debug(f"Using provided category for '{topic}': {category}")

        # Generate subtopics
        num_subtopics = max(max_nodes, 30)  # Generate more subtopics than needed
        subtopics = self.subtopic_generator.generate_subtopics(topic, num_subtopics, category)
        self.logger.debug(f"Generated {len(subtopics)} subtopics for '{topic}'")

        # Create node structure
        nodes, node_ids = await self.node_structure_service.create_node_structure(
            topic=topic,
            subtopics=subtopics,
            resources=resources,
            min_nodes=min_nodes,
            max_nodes=max_nodes,
            min_width=min_width,
            max_width=max_width,
            min_height=min_height,
            max_height=max_height,
            language=language
        )
        self.logger.debug(f"Created node structure with {len(nodes)} nodes")

        # Distribute quizzes
        nodes = self.node_structure_service.distribute_quizzes(
            nodes=nodes,
            node_ids=node_ids,
            topic=topic,
            resources=resources
        )
        self.logger.debug("Distributed quizzes across nodes")

        # Estimate total hours
        total_hours = self.estimate_total_hours(resources)
        self.logger.debug(f"Estimated total hours: {total_hours}")

        # Generate tags
        tags = self.generate_tags(topic, resources)
        self.logger.debug(f"Generated tags: {tags}")

        # Create MCP object
        mcp = MCP(
            id=f"mcp_{uuid.uuid4().hex[:8]}",
            title=f"Learning Path: {topic}",
            description=f"A comprehensive learning path for {topic}.",
            topic=topic,
            category=category,
            language=language,
            rootNodeId=node_ids[0],  # First node is the root
            nodes=nodes,
            totalHours=total_hours,
            tags=tags
        )

        # Cache the result
        cache.setex(cache_key, 86400, mcp)  # Cache for 1 day
        self.logger.info(f"Generated learning path for '{topic}' with {len(nodes)} nodes")

        return mcp

    def estimate_total_hours(self, resources: List[Resource]) -> int:
        """
        Estimate the total hours needed to complete the learning path.

        Args:
            resources: List of resources in the learning path

        Returns:
            Estimated hours
        """
        total_minutes = 0

        for resource in resources:
            # Add time based on resource type
            if resource.type == "video":
                # Use duration if available, otherwise estimate
                if resource.duration:
                    total_minutes += resource.duration
                else:
                    total_minutes += 10  # Default video length
            elif resource.type == "article":
                # Use readTime if available, otherwise estimate
                if resource.readTime:
                    total_minutes += resource.readTime
                else:
                    total_minutes += 15  # Default article read time
            elif resource.type == "tutorial":
                total_minutes += 30  # Tutorials take longer
            elif resource.type == "documentation":
                total_minutes += 20  # Documentation reading
            elif resource.type == "exercise":
                total_minutes += 45  # Exercises take time to complete
            elif resource.type == "quiz":
                total_minutes += 15  # Quizzes are quick
            else:
                total_minutes += 20  # Default for other types

        # Add time for quizzes and exercises in the learning path
        # Assuming about 15 minutes per quiz/exercise
        total_minutes += 15 * (len(resources) // 4)

        # Convert to hours and round up
        total_hours = (total_minutes + 59) // 60  # Round up

        # Ensure a minimum of 1 hour
        return max(1, total_hours)

    def generate_tags(self, topic: str, resources: List[Resource]) -> List[str]:
        """
        Generate tags for the MCP based on the topic and resources.

        Args:
            topic: The topic of the learning path
            resources: List of resources in the learning path

        Returns:
            List of tags
        """
        tags = [topic.lower()]

        # Add category as a tag
        category = category_service.detect_category(topic)
        tags.append(category.lower())

        # Extract keywords from resources
        keywords = set()
        for resource in resources:
            # Extract words from title
            title_words = resource.title.lower().split()
            for word in title_words:
                if len(word) > 3 and word not in ["with", "from", "that", "this", "what", "when", "where", "which", "who", "why", "para", "como", "sobre"]:
                    keywords.add(word)

        # Add top keywords as tags
        sorted_keywords = sorted(keywords, key=lambda x: len(x), reverse=True)
        tags.extend(sorted_keywords[:5])

        # Add some common tags based on category
        if category == "technology":
            tags.extend(["programming", "coding", "development", "tech"])
        elif category == "finance":
            tags.extend(["money", "investment", "financial", "economy"])
        elif category == "health":
            tags.extend(["wellness", "fitness", "nutrition", "medical"])
        elif category == "education":
            tags.extend(["learning", "teaching", "academic", "school"])
        elif category == "arts":
            tags.extend(["creative", "artistic", "design", "culture"])
        elif category == "science":
            tags.extend(["research", "scientific", "experiment", "theory"])
        elif category == "business":
            tags.extend(["entrepreneurship", "management", "strategy", "marketing"])
        elif category == "lifestyle":
            tags.extend(["personal", "hobby", "leisure", "self-improvement"])

        # Remove duplicates and limit to 10 tags
        unique_tags = []
        for tag in tags:
            if tag not in unique_tags:
                unique_tags.append(tag)

        return unique_tags[:10]
