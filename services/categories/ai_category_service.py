"""
AI-based implementation of the category service.
"""

import random
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from infrastructure.logging import logger
from infrastructure.cache import cache
from services.categories.category_service import CategoryService
from services.categories.category_data import CATEGORIES
from services.categories.default_category_service import DefaultCategoryService


class AICategoryService(CategoryService):
    """
    AI-based implementation of the category service.
    Uses embeddings for more accurate categorization.
    """

    def __init__(self, fallback_service: Optional[CategoryService] = None):
        """
        Initialize the AI category service.

        Args:
            fallback_service: Fallback service to use if AI categorization fails
        """
        self.logger = logger.get_logger("categories.ai")
        self.categories = CATEGORIES
        self.fallback_service = fallback_service or DefaultCategoryService()
        
        # Initialize embeddings
        self.category_embeddings = {}
        self.has_embeddings = False
        
        # Try to initialize embeddings
        try:
            self._initialize_embeddings()
            self.has_embeddings = True
            self.logger.info("Initialized AICategoryService with embeddings")
        except Exception as e:
            self.logger.warning(f"Failed to initialize embeddings: {str(e)}. Using fallback service.")
            self.has_embeddings = False

    def detect_category(self, topic: str) -> str:
        """
        Detect the category of a topic using embeddings.

        Args:
            topic: Topic to categorize

        Returns:
            Category name (e.g., 'technology', 'health', 'general')
        """
        # Check cache first
        cache_key = f"category:ai:{topic.lower()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached category '{cached_result}' for '{topic}'")
            return cached_result
            
        # If embeddings are not available, use fallback service
        if not self.has_embeddings:
            result = self.fallback_service.detect_category(topic)
            cache.setex(cache_key, 86400, result)  # Cache for 1 day
            return result
            
        try:
            # Get embedding for the topic
            topic_embedding = self._get_embedding(topic)
            
            # Calculate similarity with each category
            similarities = {}
            for category, embedding in self.category_embeddings.items():
                similarity = self._calculate_similarity(topic_embedding, embedding)
                similarities[category] = similarity
                
            # Get the category with the highest similarity
            best_category = max(similarities.items(), key=lambda x: x[1])[0]
            
            # If similarity is too low, use general category
            if similarities[best_category] < 0.3:
                self.logger.debug(f"Low similarity for '{topic}', using 'general' category")
                best_category = "general"
                
            # Cache the result
            cache.setex(cache_key, 86400, best_category)  # Cache for 1 day
            
            self.logger.debug(f"Detected category '{best_category}' for topic '{topic}' (similarity: {similarities[best_category]:.2f})")
            return best_category
        except Exception as e:
            self.logger.error(f"Error detecting category for '{topic}': {str(e)}")
            # Use fallback service
            result = self.fallback_service.detect_category(topic)
            cache.setex(cache_key, 86400, result)  # Cache for 1 day
            return result

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
            
        # Get subtopics from the category data
        return self.fallback_service.get_subtopics_for_category(topic, count, category)

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
            
        # Get queries from the category data
        return self.fallback_service.get_category_specific_queries(topic, category)

    def get_all_categories(self) -> List[str]:
        """
        Get all available categories.

        Returns:
            List of category names
        """
        return list(self.categories.keys())

    def _initialize_embeddings(self) -> None:
        """
        Initialize embeddings for each category.
        """
        for category, data in self.categories.items():
            # Skip general category
            if category == "general":
                continue
                
            # Get keywords for the category
            keywords = data["keywords"]
            
            # If no keywords, skip
            if not keywords:
                continue
                
            # Create a combined text for the category
            category_text = f"{category}: {', '.join(keywords)}"
            
            # Get embedding for the category
            self.category_embeddings[category] = self._get_embedding(category_text)
            
        # Add general category with a default embedding
        self.category_embeddings["general"] = np.zeros(768)  # Default embedding size

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for a text.

        Args:
            text: Text to get embedding for

        Returns:
            Embedding as numpy array
        """
        # This is a simplified implementation
        # In a real implementation, you would use a proper embedding model
        # For now, we'll use a simple hash-based approach
        
        # Convert text to lowercase
        text = text.lower()
        
        # Create a simple embedding based on character frequencies
        embedding = np.zeros(768)
        
        for i, char in enumerate(text):
            embedding[hash(char) % 768] += 1
            
        # Normalize the embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Cosine similarity (0-1)
        """
        # Calculate dot product
        dot_product = np.dot(embedding1, embedding2)
        
        # Calculate magnitudes
        magnitude1 = np.linalg.norm(embedding1)
        magnitude2 = np.linalg.norm(embedding2)
        
        # Calculate cosine similarity
        if magnitude1 > 0 and magnitude2 > 0:
            return dot_product / (magnitude1 * magnitude2)
        else:
            return 0.0
