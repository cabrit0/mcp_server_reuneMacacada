"""
Unit tests for the semantic filter service.
"""

import unittest
import sys
import os
from typing import List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.models import Resource
from core.content_sourcing.semantic_filter_service import SemanticFilterService


class TestSemanticFilterService(unittest.TestCase):
    """Test cases for the semantic filter service."""

    def setUp(self):
        """Set up test fixtures."""
        self.filter_service = SemanticFilterService()
        self.topic = "Python Programming"
        self.resources = self._create_test_resources()

    def test_filter_resources_by_similarity(self):
        """Test filtering resources by semantic similarity."""
        # Test with low threshold
        filtered_resources = self.filter_service.filter_resources_by_similarity(
            self.resources, self.topic, "en", 0.05
        )

        # Should keep relevant resources
        self.assertGreaterEqual(len(filtered_resources), 3)

        # Test with higher threshold
        filtered_resources_high = self.filter_service.filter_resources_by_similarity(
            self.resources, self.topic, "en", 0.3
        )

        # Should keep fewer resources with higher threshold
        self.assertLessEqual(len(filtered_resources_high), len(filtered_resources))

    def test_calculate_resource_similarity(self):
        """Test calculating similarity between a resource and a topic."""
        # Test with relevant resource
        relevant_resource = self.resources[0]  # Python tutorial
        similarity = self.filter_service.calculate_resource_similarity(
            relevant_resource, self.topic, "en"
        )

        # Should have high similarity
        self.assertGreaterEqual(similarity, 0.1)

        # Test with irrelevant resource
        irrelevant_resource = self.resources[3]  # JavaScript tutorial
        similarity = self.filter_service.calculate_resource_similarity(
            irrelevant_resource, self.topic, "en"
        )

        # Relevant resource should have higher similarity than irrelevant resource
        relevant_similarity = self.filter_service.calculate_resource_similarity(
            relevant_resource, self.topic, "en"
        )
        irrelevant_similarity = self.filter_service.calculate_resource_similarity(
            irrelevant_resource, self.topic, "en"
        )
        self.assertGreater(relevant_similarity, irrelevant_similarity)

    def _create_test_resources(self) -> List[Resource]:
        """Create test resources for the tests."""
        return [
            Resource(
                id="resource_1",
                title="Python Programming Tutorial",
                url="https://example.com/python-tutorial",
                type="tutorial",
                description="Learn Python programming from scratch with this comprehensive tutorial.",
                readTime=30,
                difficulty="beginner"
            ),
            Resource(
                id="resource_2",
                title="Advanced Python Concepts",
                url="https://example.com/advanced-python",
                type="article",
                description="Dive deep into advanced Python concepts like decorators, generators, and context managers.",
                readTime=45,
                difficulty="advanced"
            ),
            Resource(
                id="resource_3",
                title="Data Science with Python",
                url="https://example.com/python-data-science",
                type="tutorial",
                description="Learn how to use Python for data science and machine learning.",
                readTime=60,
                difficulty="intermediate"
            ),
            Resource(
                id="resource_4",
                title="JavaScript Fundamentals",
                url="https://example.com/javascript-fundamentals",
                type="tutorial",
                description="Learn the basics of JavaScript programming.",
                readTime=25,
                difficulty="beginner"
            ),
            Resource(
                id="resource_5",
                title="Web Development Basics",
                url="https://example.com/web-development",
                type="article",
                description="Introduction to web development with HTML, CSS, and JavaScript.",
                readTime=20,
                difficulty="beginner"
            )
        ]


if __name__ == "__main__":
    unittest.main()
