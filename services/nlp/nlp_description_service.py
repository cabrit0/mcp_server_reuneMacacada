"""
NLP-based description generation and validation service.

This service provides methods for generating, validating, and improving
descriptions for resources using NLP techniques.
"""

import re
from typing import List, Dict, Any, Optional
import logging
from bs4 import BeautifulSoup
from infrastructure.logging import logger
from infrastructure.cache import cache

# Try to import NLTK, but don't fail if it's not available
NLTK_AVAILABLE = False
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    from nltk.corpus import stopwords

    # Download NLTK resources if not already downloaded
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)

    NLTK_AVAILABLE = True
    logger.get_logger("nlp_service").info("NLTK is available and initialized")
except ImportError:
    logger.get_logger("nlp_service").warning("NLTK is not available, using fallback methods")


class NLPDescriptionService:
    """
    Service for generating and validating descriptions using NLP techniques.
    """

    def __init__(self):
        """Initialize the NLP description service."""
        self.logger = logger.get_logger(self.__class__.__name__)

        # Initialize stopwords if NLTK is available
        self.stopwords = {}
        self.default_stopwords = set()

        if NLTK_AVAILABLE:
            self.stopwords = {
                'en': set(stopwords.words('english')),
                'pt': set(stopwords.words('portuguese')),
                'es': set(stopwords.words('spanish')),
                # Add more languages as needed
            }
            # Default to English if language not supported
            self.default_stopwords = set(stopwords.words('english'))
        else:
            # Fallback stopwords for common languages
            self.stopwords = {
                'en': set(['a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when',
                          'at', 'from', 'by', 'for', 'with', 'about', 'against', 'between',
                          'into', 'through', 'during', 'before', 'after', 'above', 'below',
                          'to', 'of', 'in', 'on', 'is', 'are', 'was', 'were', 'be', 'been', 'being']),
                'pt': set(['a', 'o', 'e', 'é', 'de', 'da', 'do', 'em', 'no', 'na', 'um', 'uma',
                          'que', 'para', 'com', 'por', 'como', 'mas', 'ou', 'se', 'porque',
                          'quando', 'onde', 'quem', 'qual', 'quais', 'seu', 'sua', 'seus', 'suas']),
                'es': set(['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o',
                          'pero', 'si', 'de', 'del', 'a', 'en', 'por', 'para', 'con', 'sin',
                          'sobre', 'entre', 'como', 'cuando', 'donde', 'quien', 'que', 'cual'])
            }
            self.default_stopwords = self.stopwords['en']

    def generate_description(
        self,
        html_content: str,
        url: str,
        topic: str,
        language: str = "pt"
    ) -> str:
        """
        Generate a description for a resource when none is available.

        Args:
            html_content: HTML content of the resource
            url: URL of the resource
            topic: Topic being searched for
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            Generated description
        """
        # Check cache first
        cache_key = f"description:{url}_{language}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached description for {url}")
            return cached_result

        try:
            # Extract text from HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text
            text = soup.get_text()

            # Break into sentences
            if NLTK_AVAILABLE:
                sentences = sent_tokenize(text)
            else:
                # Simple sentence tokenization fallback
                sentences = []
                for potential_sentence in re.split(r'[.!?]+', text):
                    potential_sentence = potential_sentence.strip()
                    if potential_sentence:
                        sentences.append(potential_sentence)

            # Filter out short sentences
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

            if not sentences:
                self.logger.warning(f"No suitable sentences found for {url}")
                description = f"A resource about {topic}"
            else:
                # Score sentences based on relevance to topic
                scored_sentences = self._score_sentences(sentences, topic, language)

                # Get top sentences
                top_sentences = self._get_top_sentences(scored_sentences, max_sentences=3)

                # Combine sentences into a description
                description = ' '.join(top_sentences)

                # Truncate if too long
                if len(description) > 300:
                    description = description[:297] + '...'

            # Cache the result
            cache.setex(cache_key, 86400, description)  # 1 day

            return description
        except Exception as e:
            self.logger.error(f"Error generating description for {url}: {str(e)}")
            return f"A resource about {topic}"

    def validate_description(
        self,
        description: str,
        topic: str,
        language: str = "pt"
    ) -> bool:
        """
        Validate if a description is relevant to the topic.

        Args:
            description: Description to validate
            topic: Topic being searched for
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            True if the description is relevant, False otherwise
        """
        if not description or len(description) < 10:
            return False

        # Get topic keywords
        topic_keywords = self._extract_keywords(topic, language)

        # Get description keywords
        description_keywords = self._extract_keywords(description, language)

        # Check if there's any overlap
        overlap = set(topic_keywords) & set(description_keywords)

        # Calculate relevance score
        relevance_score = len(overlap) / max(1, len(topic_keywords))

        # Description is relevant if it has at least one topic keyword
        # or if it's long enough and has some substance
        return relevance_score > 0 or len(description) > 100

    def improve_description(
        self,
        description: str,
        html_content: str,
        topic: str,
        language: str = "pt"
    ) -> str:
        """
        Improve an existing description.

        Args:
            description: Existing description
            html_content: HTML content of the resource
            topic: Topic being searched for
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            Improved description
        """
        # If description is already good, return it
        if self.validate_description(description, topic, language) and len(description) > 50:
            return description

        # If description is too short or not relevant, generate a new one
        return self.generate_description(html_content, "", topic, language)

    def extract_key_sentences(
        self,
        html_content: str,
        topic: str,
        language: str = "pt",
        max_sentences: int = 3
    ) -> List[str]:
        """
        Extract key sentences from content.

        Args:
            html_content: HTML content
            topic: Topic being searched for
            language: Language code (e.g., 'pt', 'en', 'es')
            max_sentences: Maximum number of sentences to extract

        Returns:
            List of key sentences
        """
        try:
            # Extract text from HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text
            text = soup.get_text()

            # Break into sentences
            if NLTK_AVAILABLE:
                sentences = sent_tokenize(text)
            else:
                # Simple sentence tokenization fallback
                sentences = []
                for potential_sentence in re.split(r'[.!?]+', text):
                    potential_sentence = potential_sentence.strip()
                    if potential_sentence:
                        sentences.append(potential_sentence)

            # Filter out short sentences
            sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

            if not sentences:
                return []

            # Score sentences based on relevance to topic
            scored_sentences = self._score_sentences(sentences, topic, language)

            # Get top sentences
            return self._get_top_sentences(scored_sentences, max_sentences)
        except Exception as e:
            self.logger.error(f"Error extracting key sentences: {str(e)}")
            return []

    def _extract_keywords(self, text: str, language: str) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Text to extract keywords from
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            List of keywords
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)

        # Tokenize
        words = text.split()

        # Remove stopwords
        lang_stopwords = self.stopwords.get(language, self.default_stopwords)
        words = [w for w in words if w not in lang_stopwords and len(w) > 2]

        return words

    def _score_sentences(
        self,
        sentences: List[str],
        topic: str,
        language: str
    ) -> List[Dict[str, Any]]:
        """
        Score sentences based on relevance to topic.

        Args:
            sentences: List of sentences
            topic: Topic being searched for
            language: Language code (e.g., 'pt', 'en', 'es')

        Returns:
            List of dictionaries with sentence and score
        """
        # Extract topic keywords
        topic_keywords = self._extract_keywords(topic, language)

        scored_sentences = []
        for sentence in sentences:
            # Extract sentence keywords
            sentence_keywords = self._extract_keywords(sentence, language)

            # Calculate score based on keyword overlap
            score = 0
            for keyword in sentence_keywords:
                if keyword in topic_keywords:
                    score += 1

            # Normalize score by sentence length (prefer concise sentences)
            normalized_score = score / max(1, len(sentence) / 50)

            scored_sentences.append({
                'sentence': sentence,
                'score': normalized_score
            })

        return scored_sentences

    def _get_top_sentences(
        self,
        scored_sentences: List[Dict[str, Any]],
        max_sentences: int = 3
    ) -> List[str]:
        """
        Get top-scoring sentences.

        Args:
            scored_sentences: List of dictionaries with sentence and score
            max_sentences: Maximum number of sentences to return

        Returns:
            List of top sentences
        """
        # Sort by score (descending)
        sorted_sentences = sorted(
            scored_sentences,
            key=lambda x: x['score'],
            reverse=True
        )

        # Get top sentences
        top_sentences = [s['sentence'] for s in sorted_sentences[:max_sentences]]

        return top_sentences


# Singleton instance
_instance = None


def get_nlp_description_service() -> NLPDescriptionService:
    """
    Get the NLP description service instance.

    Returns:
        NLPDescriptionService instance
    """
    global _instance
    if _instance is None:
        _instance = NLPDescriptionService()
    return _instance
