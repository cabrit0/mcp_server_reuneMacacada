"""
Factory for creating path generator instances.
"""

from typing import Dict, Any, Optional

from infrastructure.logging import logger
from core.path_generator.path_generator_service import PathGeneratorService
from core.path_generator.default_path_generator import DefaultPathGenerator
from core.path_generator.category_based_subtopic_generator import CategoryBasedSubtopicGenerator
from core.path_generator.tree_based_node_structure import TreeBasedNodeStructure
from core.path_generator.default_quiz_generator import DefaultQuizGenerator
from core.path_generator.default_exercise_generator import DefaultExerciseGenerator


class PathGeneratorFactory:
    """
    Factory for creating path generator instances.
    """

    # Singleton instances
    _instances: Dict[str, PathGeneratorService] = {}

    @classmethod
    def create_path_generator(cls, generator_type: str = "default", config_options: Optional[Dict[str, Any]] = None) -> PathGeneratorService:
        """
        Create a path generator instance.

        Args:
            generator_type: Type of generator to create ("default")
            config_options: Configuration options for the generator

        Returns:
            Path generator instance implementing PathGeneratorService
        """
        # Use singleton pattern for efficiency
        if generator_type in cls._instances:
            return cls._instances[generator_type]

        # Create generator instance
        generator: PathGeneratorService

        if generator_type == "default":
            # Create dependencies
            subtopic_generator = CategoryBasedSubtopicGenerator()
            quiz_generator = DefaultQuizGenerator()
            exercise_generator = DefaultExerciseGenerator()
            node_structure_service = TreeBasedNodeStructure(quiz_generator, exercise_generator)

            # Create path generator
            generator = DefaultPathGenerator(subtopic_generator, node_structure_service)
        else:
            logger.warning(f"Unknown path generator type: {generator_type}, falling back to default")
            return cls.create_path_generator("default", config_options)

        # Store instance for reuse
        cls._instances[generator_type] = generator

        return generator
