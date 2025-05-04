"""
Default implementation of the category service.
"""

import random
from typing import Dict, List, Any, Optional

from infrastructure.logging import logger
from services.categories.category_service import CategoryService
from services.categories.category_data import CATEGORIES


class DefaultCategoryService(CategoryService):
    """
    Default implementation of the category service.
    Uses predefined category data to categorize topics and generate subtopics.
    """

    def __init__(self):
        """Initialize the default category service."""
        self.logger = logger.get_logger("categories.default")
        self.categories = CATEGORIES
        self.logger.info(f"Initialized DefaultCategoryService with {len(self.categories)} categories")

    def detect_category(self, topic: str) -> str:
        """
        Detect the category of a topic.

        Args:
            topic: Topic to categorize

        Returns:
            Category name (e.g., 'technology', 'health', 'general')
        """
        topic_lower = topic.lower()
        
        # Score for each category
        scores = {}
        
        for category, data in self.categories.items():
            if category == "general":
                continue  # Skip the general category in scoring
                
            score = 0
            for keyword in data["keywords"]:
                if keyword in topic_lower:
                    score += 1
            scores[category] = score
        
        # If no category has a score, use "general"
        if not scores or all(score == 0 for score in scores.values()):
            self.logger.debug(f"No specific category detected for '{topic}', using 'general'")
            return "general"
        
        # Return the category with the highest score
        best_category = max(scores.items(), key=lambda x: x[1])[0]
        self.logger.debug(f"Detected category '{best_category}' for topic '{topic}'")
        return best_category

    def get_subtopics_for_category(self, topic: str, count: int = 10, category: Optional[str] = None) -> List[str]:
        """
        Generate subtopics for a topic based on its category.

        Args:
            topic: Main topic
            count: Number of subtopics to generate
            category: Optional category override (if None, will be detected)

        Returns:
            List of subtopic strings
        """
        # Detect category if not provided
        if category is None:
            category = self.detect_category(topic)
        
        # Get subtopic templates for the category
        subtopic_templates = self.categories.get(category, self.categories["general"])["subtopics"]
        
        # If there aren't enough templates, repeat some
        while len(subtopic_templates) < count:
            subtopic_templates.extend(subtopic_templates)
        
        # Randomly select and format the templates
        selected_templates = random.sample(subtopic_templates, count)
        subtopics = [template.format(topic=topic) for template in selected_templates]
        
        self.logger.debug(f"Generated {len(subtopics)} subtopics for '{topic}' (category: {category})")
        return subtopics

    def get_category_specific_queries(self, topic: str, category: Optional[str] = None) -> List[str]:
        """
        Generate category-specific search queries for a topic.

        Args:
            topic: Main topic
            category: Optional category override (if None, will be detected)

        Returns:
            List of search query strings
        """
        # Detect category if not provided
        if category is None:
            category = self.detect_category(topic)
        
        # Get query templates for the category
        query_templates = self.categories.get(category, self.categories["general"])["resource_queries"]
        
        # Format the queries
        queries = [template.format(topic=topic) for template in query_templates]
        
        self.logger.debug(f"Generated {len(queries)} search queries for '{topic}' (category: {category})")
        return queries

    def get_all_categories(self) -> List[str]:
        """
        Get all available categories.

        Returns:
            List of category names
        """
        return list(self.categories.keys())

    def get_category_keywords(self, category: str) -> List[str]:
        """
        Get keywords for a specific category.

        Args:
            category: Category name

        Returns:
            List of keywords
        """
        if category not in self.categories:
            self.logger.warning(f"Category '{category}' not found, returning empty list")
            return []
            
        return self.categories[category]["keywords"]

    def get_category_data(self, category: str) -> Dict[str, Any]:
        """
        Get all data for a specific category.

        Args:
            category: Category name

        Returns:
            Dictionary with category data
        """
        if category not in self.categories:
            self.logger.warning(f"Category '{category}' not found, returning general category data")
            return self.categories["general"]
            
        return self.categories[category]
