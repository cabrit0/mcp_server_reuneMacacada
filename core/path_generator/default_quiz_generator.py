"""
Default implementation of the quiz generator.
"""

import uuid
from typing import List, Dict

from infrastructure.logging import logger
from api.models import Quiz, Question, Resource
from core.path_generator.quiz_generator_service import QuizGeneratorService


class DefaultQuizGenerator(QuizGeneratorService):
    """
    Default implementation of the quiz generator.
    Generates quizzes based on resources and keywords.
    """

    def __init__(self):
        """Initialize the default quiz generator."""
        self.logger = logger.get_logger("path_generator.quiz_generator")
        self.logger.info("Initialized DefaultQuizGenerator")

    def generate_quiz(self, topic: str, node_title: str, resources: List[Resource]) -> Quiz:
        """
        Generate a quiz for a node based on its resources.

        Args:
            topic: The topic of the learning path
            node_title: The title of the node
            resources: List of resources in the node

        Returns:
            Quiz object with questions
        """
        # Extract keywords from resources
        keywords = self._extract_keywords(resources, topic)

        # Generate questions based on keywords and node title
        questions = []

        # Create 3-5 questions
        num_questions = min(5, max(3, len(keywords)))

        for i in range(num_questions):
            if i < len(keywords):
                keyword = keywords[i]
                # Generate a question based on the keyword
                question = self._generate_question(topic, node_title, keyword, i)
                questions.append(question)

        # If we couldn't generate enough questions, add generic ones
        while len(questions) < 3:
            question = self._generate_generic_question(topic, node_title, len(questions))
            questions.append(question)

        self.logger.debug(f"Generated quiz with {len(questions)} questions for '{node_title}'")
        return Quiz(questions=questions, passingScore=70)

    def _extract_keywords(self, resources: List[Resource], _topic: str) -> List[str]:
        """
        Extract keywords from resources.

        Args:
            resources: List of resources
            _topic: The main topic

        Returns:
            List of keywords
        """
        # Combine all resource titles and descriptions
        text = ""
        for resource in resources:
            text += resource.title + " "
            if resource.description:
                text += resource.description + " "

        # Simple keyword extraction (could be enhanced with NLP)
        words = text.lower().split()
        # Remove common words and short words
        stopwords = ["the", "and", "or", "in", "on", "at", "to", "a", "an", "of", "for", "with",
                    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
                    "do", "does", "did", "but", "by", "from"]
        words = [word for word in words if word not in stopwords and len(word) > 3]

        # Count word frequency
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

        # Return top keywords
        return [word for word, _ in sorted_words[:10]]

    def _generate_question(self, topic: str, node_title: str, keyword: str, question_index: int) -> Question:
        """
        Generate a question based on a keyword.

        Args:
            topic: The main topic
            node_title: The title of the node
            keyword: The keyword to use
            question_index: Index of the question

        Returns:
            Question object
        """
        question_id = f"q_{uuid.uuid4().hex[:8]}"

        # Different question types based on index
        if question_index == 0:
            # Definition question
            text = f"What is {keyword} in the context of {topic}?"
            options = [
                f"A fundamental concept in {topic}",
                f"An advanced technique used in {topic}",
                f"A tool commonly used with {topic}",
                f"A historical aspect of {topic}"
            ]
            correct_index = 0

        elif question_index == 1:
            # Purpose question
            text = f"What is the main purpose of {keyword} in {topic}?"
            options = [
                f"To simplify {topic} processes",
                f"To optimize {topic} performance",
                f"To enhance {topic} functionality",
                f"To standardize {topic} implementation"
            ]
            correct_index = 2

        elif question_index == 2:
            # Relationship question
            text = f"How does {keyword} relate to {node_title}?"
            options = [
                f"It's a prerequisite for understanding {node_title}",
                f"It's an advanced concept that builds on {node_title}",
                f"It's a key component of {node_title}",
                f"It's an alternative approach to {node_title}"
            ]
            correct_index = 2

        else:
            # Negative question
            text = f"Which of the following is NOT associated with {keyword} in {topic}?"
            options = [
                f"Understanding core principles",
                f"Implementing best practices",
                f"Avoiding common pitfalls",
                f"Replacing traditional methods"
            ]
            correct_index = 3

        return Question(
            id=question_id,
            text=text,
            options=options,
            correctOptionIndex=correct_index
        )

    def _generate_generic_question(self, _topic: str, node_title: str, index: int) -> Question:
        """
        Generate a generic question when keywords aren't available.

        Args:
            _topic: The main topic
            node_title: The title of the node
            index: Index of the question

        Returns:
            Question object
        """
        question_id = f"q_{uuid.uuid4().hex[:8]}"

        if index == 0:
            text = f"What is the most important aspect of {node_title}?"
            options = [
                f"Understanding the fundamentals",
                f"Practicing with examples",
                f"Learning advanced techniques",
                f"Exploring related topics"
            ]
            correct_index = 0

        elif index == 1:
            text = f"Which approach is best for learning about {node_title}?"
            options = [
                f"Reading comprehensive guides",
                f"Watching video tutorials",
                f"Hands-on practice with examples",
                f"Discussing with experts"
            ]
            correct_index = 2

        else:
            text = f"What skill is most valuable when working with {node_title}?"
            options = [
                f"Attention to detail",
                f"Creative problem-solving",
                f"Systematic approach",
                f"Technical knowledge"
            ]
            correct_index = 1

        return Question(
            id=question_id,
            text=text,
            options=options,
            correctOptionIndex=correct_index
        )
