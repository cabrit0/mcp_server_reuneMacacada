"""
Tests for the NLP description service.
"""

import pytest
from unittest.mock import patch, MagicMock

from services.nlp.nlp_description_service import NLPDescriptionService, get_nlp_description_service


@pytest.fixture
def nlp_service():
    """Create an NLP description service for testing."""
    return NLPDescriptionService()


@pytest.fixture
def html_content():
    """Sample HTML content for testing."""
    return """
    <html>
        <head>
            <title>Test Page About Python Programming</title>
            <meta name="description" content="Learn Python programming with this tutorial">
        </head>
        <body>
            <h1>Python Programming Tutorial</h1>
            <p>Python is a high-level programming language known for its readability and simplicity.</p>
            <p>This tutorial will teach you the basics of Python programming.</p>
            <p>You will learn about variables, functions, loops, and more.</p>
        </body>
    </html>
    """


def test_extract_keywords(nlp_service):
    """Test keyword extraction."""
    text = "Python is a high-level programming language known for its readability"
    keywords = nlp_service._extract_keywords(text, "en")
    
    assert len(keywords) > 0
    assert "python" in keywords
    assert "programming" in keywords
    assert "language" in keywords
    
    # Stopwords should be removed
    assert "is" not in keywords
    assert "a" not in keywords
    assert "for" not in keywords


def test_generate_description(nlp_service, html_content):
    """Test description generation."""
    with patch('infrastructure.cache.cache.get', return_value=None), \
         patch('infrastructure.cache.cache.setex'):
        
        description = nlp_service.generate_description(
            html_content, 
            "https://example.com", 
            "Python programming", 
            "en"
        )
        
        assert len(description) > 0
        assert "Python" in description
        assert "programming" in description


def test_validate_description(nlp_service):
    """Test description validation."""
    # Valid description
    valid = nlp_service.validate_description(
        "Python is a high-level programming language known for its readability",
        "Python programming",
        "en"
    )
    assert valid is True
    
    # Invalid description (unrelated)
    invalid = nlp_service.validate_description(
        "JavaScript is a scripting language used for web development",
        "Python programming",
        "en"
    )
    assert invalid is False
    
    # Empty description
    empty = nlp_service.validate_description("", "Python programming", "en")
    assert empty is False


def test_improve_description(nlp_service, html_content):
    """Test description improvement."""
    with patch('infrastructure.cache.cache.get', return_value=None), \
         patch('infrastructure.cache.cache.setex'), \
         patch.object(nlp_service, 'validate_description', return_value=False), \
         patch.object(nlp_service, 'generate_description', return_value="Improved description"):
        
        # Invalid description should be improved
        improved = nlp_service.improve_description(
            "Short desc",
            html_content,
            "Python programming",
            "en"
        )
        
        assert improved == "Improved description"
        nlp_service.generate_description.assert_called_once()


def test_get_nlp_description_service():
    """Test singleton instance."""
    service1 = get_nlp_description_service()
    service2 = get_nlp_description_service()
    
    assert service1 is service2
    assert isinstance(service1, NLPDescriptionService)
