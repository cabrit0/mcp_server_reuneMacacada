"""
Unit tests for the category service implementations.
"""

import pytest
from unittest.mock import patch, MagicMock

from services.categories.default_category_service import DefaultCategoryService
from services.categories.ai_category_service import AICategoryService
from services.categories.category_factory import CategoryFactory


class TestDefaultCategoryService:
    """Tests for the DefaultCategoryService implementation."""

    def test_detect_category(self):
        """Test the detect_category method."""
        service = DefaultCategoryService()
        
        # Test technology category
        assert service.detect_category("Python programming") == "technology"
        assert service.detect_category("Web development") == "technology"
        
        # Test finance category
        assert service.detect_category("Investment strategies") == "finance"
        assert service.detect_category("Stock market analysis") == "finance"
        
        # Test health category
        assert service.detect_category("Fitness exercises") == "health"
        assert service.detect_category("Nutrition and diet") == "health"
        
        # Test general category (no specific keywords)
        assert service.detect_category("Random topic") == "general"

    def test_get_subtopics_for_category(self):
        """Test the get_subtopics_for_category method."""
        service = DefaultCategoryService()
        
        # Test with explicit category
        subtopics = service.get_subtopics_for_category("Python", count=5, category="technology")
        
        # Check results
        assert len(subtopics) == 5
        for subtopic in subtopics:
            assert "Python" in subtopic
            
        # Test with detected category
        subtopics = service.get_subtopics_for_category("Python programming", count=5)
        
        # Check results
        assert len(subtopics) == 5
        for subtopic in subtopics:
            assert "Python programming" in subtopic

    def test_get_category_specific_queries(self):
        """Test the get_category_specific_queries method."""
        service = DefaultCategoryService()
        
        # Test with explicit category
        queries = service.get_category_specific_queries("Python", category="technology")
        
        # Check results
        assert len(queries) > 0
        for query in queries:
            assert "Python" in query
            
        # Test with detected category
        queries = service.get_category_specific_queries("Python programming")
        
        # Check results
        assert len(queries) > 0
        for query in queries:
            assert "Python" in query

    def test_get_all_categories(self):
        """Test the get_all_categories method."""
        service = DefaultCategoryService()
        
        # Get all categories
        categories = service.get_all_categories()
        
        # Check results
        assert "technology" in categories
        assert "finance" in categories
        assert "health" in categories
        assert "general" in categories


class TestAICategoryService:
    """Tests for the AICategoryService implementation."""

    def test_detect_category_with_embeddings(self):
        """Test the detect_category method with embeddings."""
        # Create service with mock embeddings
        service = AICategoryService()
        service.has_embeddings = True
        
        # Mock the _get_embedding method
        service._get_embedding = MagicMock(return_value=[1.0] * 768)
        
        # Mock the _calculate_similarity method to return high similarity for technology
        def mock_similarity(embedding1, embedding2):
            if embedding2 is service.category_embeddings.get("technology"):
                return 0.9
            else:
                return 0.1
                
        service._calculate_similarity = MagicMock(side_effect=mock_similarity)
        
        # Mock the category embeddings
        service.category_embeddings = {
            "technology": [1.0] * 768,
            "finance": [1.0] * 768,
            "health": [1.0] * 768,
            "general": [1.0] * 768
        }
        
        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        
        with patch("services.categories.ai_category_service.cache", mock_cache):
            # Test detection
            assert service.detect_category("Python programming") == "technology"
            
            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()

    def test_detect_category_fallback(self):
        """Test the detect_category method with fallback."""
        # Create mock fallback service
        mock_fallback = MagicMock()
        mock_fallback.detect_category.return_value = "technology"
        
        # Create service with mock fallback
        service = AICategoryService(fallback_service=mock_fallback)
        service.has_embeddings = False
        
        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None
        
        with patch("services.categories.ai_category_service.cache", mock_cache):
            # Test detection
            assert service.detect_category("Python programming") == "technology"
            
            # Check that fallback was used
            mock_fallback.detect_category.assert_called_once_with("Python programming")
            
            # Check that cache was used
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()


class TestCategoryFactory:
    """Tests for the CategoryFactory."""

    def test_create_category_service(self):
        """Test the create_category_service method."""
        # Clear existing instances
        CategoryFactory._instances = {}
        
        # Create services
        default_service = CategoryFactory.create_category_service("default")
        ai_service = CategoryFactory.create_category_service("ai")
        
        # Check types
        assert isinstance(default_service, DefaultCategoryService)
        assert isinstance(ai_service, AICategoryService)
        
        # Check singleton pattern
        assert CategoryFactory.create_category_service("default") is default_service
        assert CategoryFactory.create_category_service("ai") is ai_service
