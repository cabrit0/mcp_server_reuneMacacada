"""
Factory for documentation services.
"""

from typing import Dict, List, Optional

from infrastructure.logging import logger
from services.documentation.documentation_service import DocumentationService
from services.documentation.mdn_documentation_service import MDNDocumentationService
from services.documentation.python_documentation_service import PythonDocumentationService
from services.documentation.github_documentation_service import GitHubDocumentationService
from services.documentation.stackoverflow_documentation_service import StackOverflowDocumentationService


class DocumentationFactory:
    """
    Factory for creating documentation services.
    """

    # Singleton instance
    _instance = None

    # Service instances
    _services: Dict[str, DocumentationService] = {}

    def __new__(cls):
        """
        Create a new instance of the factory or return the existing one.

        Returns:
            DocumentationFactory instance
        """
        if cls._instance is None:
            cls._instance = super(DocumentationFactory, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initialize the factory with documentation services.
        """
        self.logger = logger.get_logger("documentation.factory")

        # Create service instances
        self._services = {
            "mdn": MDNDocumentationService(),
            "python": PythonDocumentationService(),
            "github": GitHubDocumentationService(),
            "stackoverflow": StackOverflowDocumentationService()
        }

        self.logger.info(f"Initialized DocumentationFactory with {len(self._services)} services")

    def get_service(self, name: str) -> Optional[DocumentationService]:
        """
        Get a documentation service by name.

        Args:
            name: Service name

        Returns:
            DocumentationService instance or None if not found
        """
        return self._services.get(name)

    def get_all_services(self) -> List[DocumentationService]:
        """
        Get all documentation services.

        Returns:
            List of DocumentationService instances
        """
        return list(self._services.values())

    def get_services_for_topic(self, topic: str) -> List[DocumentationService]:
        """
        Get documentation services that support a specific topic.

        Args:
            topic: Topic to check

        Returns:
            List of DocumentationService instances that support the topic
        """
        return [
            service for service in self._services.values()
            if service._is_topic_supported(topic)
        ]

    def get_services_for_language(self, language: str) -> List[DocumentationService]:
        """
        Get documentation services that support a specific language.

        Args:
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of DocumentationService instances that support the language
        """
        return [
            service for service in self._services.values()
            if language in service.supported_languages
        ]


# Singleton instance
_factory_instance = None


def get_documentation_factory() -> DocumentationFactory:
    """
    Get the documentation factory instance.

    Returns:
        DocumentationFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        _factory_instance = DocumentationFactory()
    return _factory_instance
