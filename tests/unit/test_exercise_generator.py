"""
Unit tests for the exercise generator.
"""

import unittest
import uuid
import sys
import os
from typing import List

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from api.models import Resource, Exercise, ExerciseSet
from core.path_generator.default_exercise_generator import DefaultExerciseGenerator


class TestExerciseGenerator(unittest.TestCase):
    """Test cases for the exercise generator."""

    def setUp(self):
        """Set up test fixtures."""
        self.exercise_generator = DefaultExerciseGenerator()
        self.topic = "Python Programming"
        self.node_title = "Functions in Python"
        self.resources = self._create_test_resources()

    def test_generate_exercise_set(self):
        """Test generating an exercise set."""
        exercise_set = self.exercise_generator.generate_exercise_set(
            self.topic, self.node_title, self.resources
        )

        # Check that the exercise set is created
        self.assertIsInstance(exercise_set, ExerciseSet)
        self.assertGreaterEqual(len(exercise_set.exercises), 2)
        self.assertEqual(exercise_set.passingScore, 70)

        # Check that each exercise has the required fields
        for exercise in exercise_set.exercises:
            self.assertIsInstance(exercise, Exercise)
            self.assertTrue(exercise.id.startswith("exercise_"))
            self.assertTrue(exercise.title)
            self.assertTrue(exercise.description)
            self.assertTrue(exercise.instructions)
            self.assertTrue(exercise.solution)
            self.assertIn(exercise.verificationMethod, ["multiple_choice", "text_match", "code_execution", "manual"])
            self.assertGreaterEqual(len(exercise.hints), 1)

            # Check that multiple choice exercises have options
            if exercise.verificationMethod == "multiple_choice":
                self.assertIsNotNone(exercise.options)
                self.assertGreaterEqual(len(exercise.options), 2)

    def test_generate_hints(self):
        """Test generating hints for an exercise."""
        hints = self.exercise_generator.generate_hints(
            self.topic, self.node_title, "Understanding function parameters"
        )

        # Check that hints are generated
        self.assertIsInstance(hints, list)
        self.assertGreaterEqual(len(hints), 1)
        for hint in hints:
            self.assertIsInstance(hint, str)
            self.assertGreater(len(hint), 0)

    def _create_test_resources(self) -> List[Resource]:
        """Create test resources for the tests."""
        return [
            Resource(
                id=f"resource_{uuid.uuid4().hex[:8]}",
                title="Python Functions Tutorial",
                url="https://example.com/python-functions",
                type="article",
                description="Learn about Python functions and how to use them.",
                readTime=15,
                difficulty="intermediate"
            ),
            Resource(
                id=f"resource_{uuid.uuid4().hex[:8]}",
                title="Advanced Function Concepts in Python",
                url="https://example.com/advanced-python-functions",
                type="video",
                description="Dive deep into advanced function concepts in Python.",
                duration=20,
                difficulty="advanced"
            ),
            Resource(
                id=f"resource_{uuid.uuid4().hex[:8]}",
                title="Python Function Exercises",
                url="https://example.com/python-function-exercises",
                type="exercise",
                description="Practice your Python function skills with these exercises.",
                difficulty="intermediate"
            )
        ]


if __name__ == "__main__":
    unittest.main()
