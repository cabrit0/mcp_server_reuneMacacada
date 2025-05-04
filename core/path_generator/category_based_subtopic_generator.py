"""
Category-based implementation of the subtopic generator.
"""

import random
from typing import List, Optional

from infrastructure.logging import logger
from services.categories import category_service
from core.path_generator.subtopic_generator_service import SubtopicGeneratorService


class CategoryBasedSubtopicGenerator(SubtopicGeneratorService):
    """
    Category-based implementation of the subtopic generator.
    Uses the category service to generate subtopics based on the topic's category.
    """

    def __init__(self):
        """Initialize the category-based subtopic generator."""
        self.logger = logger.get_logger("path_generator.subtopic_generator")
        
        # Common prefixes and suffixes to create subtopics
        self.prefixes = [
            "Introduction to", "Getting Started with", "Understanding", "Basics of",
            "Advanced", "Mastering", "Practical", "Exploring", "Deep Dive into",
            "Essential", "Fundamentals of", "Working with", "Building with",
            "Developing with", "Professional", "Modern", "Effective", "Efficient",
            "Comprehensive Guide to", "Quick Start with", "Step-by-Step", "Hands-on",
            "Theory of", "Principles of", "Concepts in", "Techniques for", "Strategies for",
            "Best Practices in", "Common Patterns in", "Architecture of", "Design Patterns for"
        ]
        
        self.suffixes = [
            "Basics", "Fundamentals", "Concepts", "Principles", "Techniques",
            "Patterns", "Best Practices", "Applications", "Examples", "Case Studies",
            "Projects", "Exercises", "Challenges", "Tools", "Libraries", "Frameworks",
            "Development", "Implementation", "Deployment", "Testing", "Debugging",
            "Optimization", "Performance", "Security", "Scalability", "Maintenance",
            "Integration", "APIs", "Data Structures", "Algorithms", "UI/UX", "Frontend", "Backend"
        ]
        
        self.logger.info("Initialized CategoryBasedSubtopicGenerator")

    def generate_subtopics(self, topic: str, count: int = 10, category: Optional[str] = None) -> List[str]:
        """
        Generate subtopics based on a main topic using category-specific templates.

        Args:
            topic: The main topic
            count: Number of subtopics to generate
            category: Optional category override (if None, will be detected)

        Returns:
            List of subtopic strings
        """
        # Get category-specific subtopics
        if category is None:
            category = category_service.detect_category(topic)
            self.logger.debug(f"Detected category for '{topic}': {category}")
        else:
            self.logger.debug(f"Using provided category for '{topic}': {category}")
            
        category_subtopics = category_service.get_subtopics_for_category(topic, count, category)
        
        # If we got enough subtopics from the category, return them
        if len(category_subtopics) >= count:
            self.logger.debug(f"Generated {count} category-specific subtopics for '{topic}'")
            return category_subtopics[:count]
            
        # Otherwise, fill in with generic subtopics
        subtopics = category_subtopics.copy()
        
        # Topic-specific terms
        topic_terms = self._generate_topic_terms(topic)
        
        # Add some direct topic terms if needed
        if len(subtopics) < count:
            remaining_terms = [term for term in topic_terms if term not in subtopics]
            subtopics.extend(random.sample(remaining_terms, min(len(remaining_terms), (count - len(subtopics)) // 3)))
        
        # Add prefix + topic combinations if needed
        if len(subtopics) < count:
            for prefix in random.sample(self.prefixes, min(len(self.prefixes), (count - len(subtopics)) // 3)):
                new_subtopic = f"{prefix} {topic}"
                if new_subtopic not in subtopics:
                    subtopics.append(new_subtopic)
        
        # Add topic + suffix combinations if needed
        if len(subtopics) < count:
            for suffix in random.sample(self.suffixes, min(len(self.suffixes), (count - len(subtopics)) // 3)):
                new_subtopic = f"{topic} {suffix}"
                if new_subtopic not in subtopics:
                    subtopics.append(new_subtopic)
        
        # Ensure we have enough subtopics
        while len(subtopics) < count:
            prefix = random.choice(self.prefixes)
            suffix = random.choice(self.suffixes)
            subtopic = f"{prefix} {topic} {suffix}"
            if subtopic not in subtopics:
                subtopics.append(subtopic)
        
        # Shuffle and return the requested number of subtopics
        random.shuffle(subtopics)
        self.logger.debug(f"Generated {count} subtopics for '{topic}' (category: {category})")
        return subtopics[:count]

    def _generate_topic_terms(self, topic: str) -> List[str]:
        """
        Generate topic-specific terms.

        Args:
            topic: The main topic

        Returns:
            List of topic-specific terms
        """
        return [
            f"{topic} for Beginners",
            f"{topic} for Intermediate Users",
            f"{topic} for Advanced Users",
            f"{topic} in Practice",
            f"{topic} Theory",
            f"Real-world {topic}",
            f"{topic} Architecture",
            f"{topic} Design",
            f"{topic} Implementation",
            f"{topic} Testing",
            f"{topic} Deployment",
            f"{topic} Maintenance",
            f"{topic} Best Practices",
            f"{topic} Common Mistakes",
            f"{topic} Tips and Tricks",
            f"{topic} Performance Optimization",
            f"{topic} Security Considerations",
            f"{topic} Scalability",
            f"{topic} vs. Alternatives",
            f"Future of {topic}"
        ]
