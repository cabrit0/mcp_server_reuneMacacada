"""
Tests for the documentation factory.
"""

import pytest
from unittest.mock import patch, MagicMock

from services.documentation.documentation_factory import DocumentationFactory, get_documentation_factory
from services.documentation.documentation_service import DocumentationService
from services.documentation.mdn_documentation_service import MDNDocumentationService
from services.documentation.python_documentation_service import PythonDocumentationService
from services.documentation.github_documentation_service import GitHubDocumentationService
from services.documentation.stackoverflow_documentation_service import StackOverflowDocumentationService


def test_get_documentation_factory():
    """Test getting the documentation factory singleton."""
    factory1 = get_documentation_factory()
    factory2 = get_documentation_factory()
    
    assert factory1 is factory2
    assert isinstance(factory1, DocumentationFactory)


def test_get_service():
    """Test getting a service by name."""
    factory = get_documentation_factory()
    
    # Test getting existing services
    mdn_service = factory.get_service("mdn")
    assert isinstance(mdn_service, MDNDocumentationService)
    
    python_service = factory.get_service("python")
    assert isinstance(python_service, PythonDocumentationService)
    
    github_service = factory.get_service("github")
    assert isinstance(github_service, GitHubDocumentationService)
    
    stackoverflow_service = factory.get_service("stackoverflow")
    assert isinstance(stackoverflow_service, StackOverflowDocumentationService)
    
    # Test getting non-existent service
    non_existent = factory.get_service("non_existent")
    assert non_existent is None


def test_get_all_services():
    """Test getting all services."""
    factory = get_documentation_factory()
    services = factory.get_all_services()
    
    assert len(services) == 4
    assert all(isinstance(service, DocumentationService) for service in services)


def test_get_services_for_topic():
    """Test getting services for a topic."""
    factory = get_documentation_factory()
    
    # Mock the _is_topic_supported method for all services
    with patch.object(MDNDocumentationService, '_is_topic_supported', return_value=True), \
         patch.object(PythonDocumentationService, '_is_topic_supported', return_value=False), \
         patch.object(GitHubDocumentationService, '_is_topic_supported', return_value=True), \
         patch.object(StackOverflowDocumentationService, '_is_topic_supported', return_value=True):
        
        services = factory.get_services_for_topic("javascript")
        
        assert len(services) == 3
        assert any(isinstance(service, MDNDocumentationService) for service in services)
        assert not any(isinstance(service, PythonDocumentationService) for service in services)
        assert any(isinstance(service, GitHubDocumentationService) for service in services)
        assert any(isinstance(service, StackOverflowDocumentationService) for service in services)


def test_get_services_for_language():
    """Test getting services for a language."""
    factory = get_documentation_factory()
    
    # Create mock services with different supported languages
    mdn_mock = MagicMock(spec=MDNDocumentationService)
    mdn_mock.supported_languages = ["en", "es", "fr"]
    
    python_mock = MagicMock(spec=PythonDocumentationService)
    python_mock.supported_languages = ["en", "fr"]
    
    github_mock = MagicMock(spec=GitHubDocumentationService)
    github_mock.supported_languages = ["en", "pt"]
    
    stackoverflow_mock = MagicMock(spec=StackOverflowDocumentationService)
    stackoverflow_mock.supported_languages = ["en"]
    
    # Replace the services in the factory
    factory._services = {
        "mdn": mdn_mock,
        "python": python_mock,
        "github": github_mock,
        "stackoverflow": stackoverflow_mock
    }
    
    # Test getting services for English
    en_services = factory.get_services_for_language("en")
    assert len(en_services) == 4
    
    # Test getting services for French
    fr_services = factory.get_services_for_language("fr")
    assert len(fr_services) == 2
    assert mdn_mock in fr_services
    assert python_mock in fr_services
    
    # Test getting services for Portuguese
    pt_services = factory.get_services_for_language("pt")
    assert len(pt_services) == 1
    assert github_mock in pt_services
    
    # Test getting services for unsupported language
    de_services = factory.get_services_for_language("de")
    assert len(de_services) == 0
