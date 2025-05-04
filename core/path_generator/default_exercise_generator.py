"""
Default implementation of the exercise generator.
"""

import uuid
import random
from typing import List, Dict

from infrastructure.logging import logger
from api.models import Exercise, ExerciseSet, Resource
from core.path_generator.exercise_generator_service import ExerciseGeneratorService


class DefaultExerciseGenerator(ExerciseGeneratorService):
    """
    Default implementation of the exercise generator.
    Generates exercises based on resources and keywords.
    """

    def __init__(self):
        """Initialize the default exercise generator."""
        self.logger = logger.get_logger("path_generator.exercise_generator")
        self.logger.info("Initialized DefaultExerciseGenerator")

    def generate_exercise_set(self, topic: str, node_title: str, resources: List[Resource]) -> ExerciseSet:
        """
        Generate an exercise set for a node based on its resources.

        Args:
            topic: The topic of the learning path
            node_title: The title of the node
            resources: List of resources in the node

        Returns:
            ExerciseSet object with exercises
        """
        # Extract keywords from resources
        keywords = self._extract_keywords(resources, topic)

        # Generate exercises based on keywords and node title
        exercises = []

        # Create 2-4 exercises
        num_exercises = min(4, max(2, len(keywords)))

        for i in range(num_exercises):
            if i < len(keywords):
                keyword = keywords[i]
                # Generate an exercise based on the keyword
                exercise = self._generate_exercise(topic, node_title, keyword, i)
                exercises.append(exercise)

        # If we couldn't generate enough exercises, add generic ones
        while len(exercises) < 2:
            exercise = self._generate_generic_exercise(topic, node_title, len(exercises))
            exercises.append(exercise)

        self.logger.debug(f"Generated exercise set with {len(exercises)} exercises for '{node_title}'")
        return ExerciseSet(exercises=exercises, passingScore=70)

    def generate_hints(self, topic: str, node_title: str, exercise_description: str) -> List[str]:
        """
        Generate hints for an exercise.

        Args:
            topic: The topic of the learning path
            node_title: The title of the node
            exercise_description: The description of the exercise

        Returns:
            List of hints for the exercise
        """
        # Generate 3 hints with increasing specificity
        hints = [
            f"Pense sobre os conceitos básicos de {node_title} relacionados a {topic}.",
            f"Considere como {exercise_description.split('.')[0].lower()} se aplica neste contexto.",
            f"A resposta está diretamente relacionada com {topic} no contexto de {node_title}."
        ]
        
        return hints

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

        # Simple keyword extraction (in a real implementation, this would be more sophisticated)
        words = text.lower().split()
        # Remove common words and short words
        filtered_words = [word for word in words if len(word) > 4 and word not in [
            "sobre", "como", "para", "that", "with", "this", "from", "what", "have", "more", "will", "about"
        ]]
        
        # Get unique words
        unique_words = list(set(filtered_words))
        
        # Sort by frequency (in a real implementation, this would use TF-IDF or similar)
        word_counts = {word: filtered_words.count(word) for word in unique_words}
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return top keywords
        return [word for word, _ in sorted_words[:10]]

    def _generate_exercise(self, topic: str, node_title: str, keyword: str, index: int) -> Exercise:
        """
        Generate an exercise based on a keyword.

        Args:
            topic: The topic of the learning path
            node_title: The title of the node
            keyword: The keyword to base the exercise on
            index: Index of the exercise (for variety)

        Returns:
            Exercise object
        """
        exercise_id = f"exercise_{uuid.uuid4().hex[:8]}"
        
        # Generate different types of exercises based on the index
        if index % 3 == 0:
            # Multiple choice exercise
            return self._generate_multiple_choice_exercise(exercise_id, topic, node_title, keyword)
        elif index % 3 == 1:
            # Text match exercise
            return self._generate_text_match_exercise(exercise_id, topic, node_title, keyword)
        else:
            # Code execution exercise (simplified as text match for now)
            return self._generate_code_exercise(exercise_id, topic, node_title, keyword)

    def _generate_multiple_choice_exercise(self, exercise_id: str, topic: str, node_title: str, keyword: str) -> Exercise:
        """Generate a multiple choice exercise."""
        title = f"Exercício sobre {keyword.capitalize()} em {node_title}"
        description = f"Teste seu conhecimento sobre {keyword} no contexto de {node_title}."
        
        # Generate question based on the keyword
        instructions = f"Qual das seguintes opções melhor descreve {keyword} no contexto de {node_title}?"
        
        # Generate options
        options = [
            f"Uma técnica avançada para otimizar {topic}",
            f"Um conceito fundamental em {node_title}",
            f"Uma ferramenta para análise de {topic}",
            f"Um método alternativo para implementar {node_title}"
        ]
        
        # Randomly select the correct answer
        correct_index = random.randint(0, len(options) - 1)
        correct_answer = str(correct_index)
        
        # Generate hints
        hints = self.generate_hints(topic, node_title, description)
        
        # Generate solution
        solution = f"A resposta correta é: {options[correct_index]}"
        
        return Exercise(
            id=exercise_id,
            title=title,
            description=description,
            difficulty="intermediate",
            instructions=instructions,
            hints=hints,
            solution=solution,
            verificationMethod="multiple_choice",
            options=options,
            correctAnswer=correct_answer
        )

    def _generate_text_match_exercise(self, exercise_id: str, topic: str, node_title: str, keyword: str) -> Exercise:
        """Generate a text match exercise."""
        title = f"Conceito de {keyword.capitalize()}"
        description = f"Defina o conceito de {keyword} no contexto de {node_title}."
        
        instructions = f"Escreva uma definição curta para o termo '{keyword}' como usado em {node_title}."
        
        # Generate hints
        hints = self.generate_hints(topic, node_title, description)
        
        # Generate solution
        solution = f"{keyword.capitalize()} é um conceito importante em {node_title} que se refere à forma como {topic} é estruturado e organizado."
        
        return Exercise(
            id=exercise_id,
            title=title,
            description=description,
            difficulty="intermediate",
            instructions=instructions,
            hints=hints,
            solution=solution,
            verificationMethod="text_match",
            correctAnswer=keyword
        )

    def _generate_code_exercise(self, exercise_id: str, topic: str, node_title: str, keyword: str) -> Exercise:
        """Generate a code exercise (simplified)."""
        title = f"Implementação prática de {keyword.capitalize()}"
        description = f"Implemente um exemplo simples usando {keyword} em {node_title}."
        
        instructions = f"Escreva um pequeno trecho de código que demonstre o uso de {keyword} em {topic}."
        
        # Generate hints
        hints = self.generate_hints(topic, node_title, description)
        
        # Generate solution
        solution = f"Um exemplo de implementação seria:\n\n```\n// Código de exemplo para {keyword} em {topic}\nfunction exemplo{keyword.capitalize()}() {{\n  // Implementação\n  console.log('Exemplo de {keyword}');\n}}\n```"
        
        return Exercise(
            id=exercise_id,
            title=title,
            description=description,
            difficulty="advanced",
            instructions=instructions,
            hints=hints,
            solution=solution,
            verificationMethod="manual",
            correctAnswer="N/A"  # Manual verification doesn't have a specific correct answer
        )

    def _generate_generic_exercise(self, topic: str, node_title: str, index: int) -> Exercise:
        """
        Generate a generic exercise when no keywords are available.

        Args:
            topic: The topic of the learning path
            node_title: The title of the node
            index: Index of the exercise (for variety)

        Returns:
            Exercise object
        """
        exercise_id = f"exercise_{uuid.uuid4().hex[:8]}"
        
        if index == 0:
            title = f"Conceitos básicos de {node_title}"
            description = f"Teste seu conhecimento sobre os conceitos básicos de {node_title}."
            instructions = f"Quais são os principais conceitos de {node_title} relacionados a {topic}?"
            options = [
                f"Conceito A, Conceito B e Conceito C",
                f"Conceito X, Conceito Y e Conceito Z",
                f"Todos os conceitos mencionados acima",
                f"Nenhum dos conceitos mencionados acima"
            ]
            correct_index = 0
            correct_answer = str(correct_index)
            verification_method = "multiple_choice"
            
        else:
            title = f"Aplicação prática de {node_title}"
            description = f"Demonstre como aplicar {node_title} em um cenário real."
            instructions = f"Descreva um caso de uso prático para {node_title} no contexto de {topic}."
            correct_answer = "N/A"  # Manual verification
            verification_method = "manual"
            options = None
        
        # Generate hints
        hints = self.generate_hints(topic, node_title, description)
        
        # Generate solution
        if verification_method == "multiple_choice":
            solution = f"A resposta correta é: {options[correct_index]}"
        else:
            solution = f"Um caso de uso prático para {node_title} seria aplicá-lo em um projeto de {topic} para resolver problemas específicos de [exemplo específico]."
        
        return Exercise(
            id=exercise_id,
            title=title,
            description=description,
            difficulty="intermediate",
            instructions=instructions,
            hints=hints,
            solution=solution,
            verificationMethod=verification_method,
            options=options,
            correctAnswer=correct_answer
        )
