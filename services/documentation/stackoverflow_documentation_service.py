"""
Stack Overflow documentation service.
"""

import re
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
import aiohttp

from infrastructure.logging import logger
from infrastructure.cache import cache
from api.models import Resource
from services.documentation.documentation_service import DocumentationService


class StackOverflowDocumentationService(DocumentationService):
    """
    Stack Overflow documentation service.
    Provides access to Stack Overflow questions and answers for various programming topics.
    """

    # Base URLs for Stack Overflow
    BASE_URL = "https://stackoverflow.com"
    SEARCH_URL = "https://stackoverflow.com/search"

    # Topics supported by Stack Overflow (virtually all programming topics)
    SUPPORTED_TOPICS = [
        "programming", "code", "development", "software", "web", "app",
        "python", "javascript", "java", "c#", "php", "android", "html",
        "css", "jquery", "sql", "mysql", "database", "api", "json",
        "react", "node.js", "angular", "vue.js", "typescript", "swift",
        "kotlin", "flutter", "dart", "go", "rust", "c++", "algorithm",
        "data structure", "machine learning", "ai", "deep learning",
        "frontend", "backend", "fullstack", "devops", "cloud", "aws",
        "azure", "google cloud", "docker", "kubernetes", "linux", "git"
    ]

    # Languages supported by Stack Overflow (English only for search)
    SUPPORTED_LANGUAGES = ["en"]

    def __init__(self, cache_ttl: int = 86400):
        """
        Initialize the Stack Overflow documentation service.

        Args:
            cache_ttl: Cache TTL in seconds (default: 1 day)
        """
        self.cache_ttl = cache_ttl
        self.logger = logger.get_logger("documentation.stackoverflow")
        self.logger.info("Initialized StackOverflowDocumentationService")

    @property
    def name(self) -> str:
        """
        Get the name of the documentation service.

        Returns:
            Service name
        """
        return "Stack Overflow"

    @property
    def supported_languages(self) -> List[str]:
        """
        Get the list of languages supported by this documentation service.

        Returns:
            List of language codes
        """
        return self.SUPPORTED_LANGUAGES

    @property
    def supported_topics(self) -> List[str]:
        """
        Get the list of topics supported by this documentation service.

        Returns:
            List of topic names
        """
        return self.SUPPORTED_TOPICS

    def _is_topic_supported(self, topic: str) -> bool:
        """
        Check if a topic is supported by Stack Overflow.
        Almost all programming topics are supported.

        Args:
            topic: Topic to check

        Returns:
            True if the topic is supported, False otherwise
        """
        topic_lower = topic.lower()

        # Check if it's a programming-related topic
        for supported in self.SUPPORTED_TOPICS:
            if supported in topic_lower:
                return True

        # Most programming topics are supported
        return True

    async def search_documentation(
        self,
        topic: str,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Search for documentation related to a topic on Stack Overflow.

        Args:
            topic: Topic to search for
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of dictionaries with documentation information
        """
        # Stack Overflow search is English-only
        if language != "en":
            self.logger.debug(f"Language '{language}' not supported by Stack Overflow, using English")
            language = "en"

        # Check cache first
        cache_key = f"stackoverflow:search:{topic}_{max_results}"
        cached_result = cache.get(cache_key)
        if cached_result:
            self.logger.debug(f"Using cached Stack Overflow search results for '{topic}'")
            return cached_result

        # Build search URL
        search_url = self.SEARCH_URL
        params = {"q": topic, "tab": "relevance"}

        try:
            # Perform search
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params) as response:
                    if response.status != 200:
                        self.logger.warning(f"Stack Overflow search failed with status {response.status}")
                        return []

                    html = await response.text()

            # Parse search results
            soup = BeautifulSoup(html, "html.parser")
            results = []

            # Log the HTML for debugging
            self.logger.debug(f"Parsing HTML from Stack Overflow search: {len(html)} characters")

            # Try different selectors for search results
            result_items = []

            # Try the main selector
            result_items = soup.select(".js-search-results .js-post-summary")

            # If no results, try alternative selectors
            if not result_items:
                result_items = soup.select(".search-results .search-result")

            if not result_items:
                result_items = soup.select(".question-summary")

            if not result_items:
                # As a fallback, create a simple result with the search URL
                self.logger.warning(f"No search result items found for '{topic}', using fallback")
                results.append({
                    "id": f"stackoverflow_{uuid.uuid4().hex[:8]}",
                    "title": f"Stack Overflow: {topic}",
                    "url": f"https://stackoverflow.com/search?q={quote(topic)}",
                    "description": f"Stack Overflow questions about {topic}",
                    "source": "Stack Overflow",
                    "type": "qa",
                    "voteCount": 0,
                    "answerCount": 0,
                    "tags": [topic]
                })
                return results

            self.logger.debug(f"Found {len(result_items)} result items")

            for item in result_items[:max_results]:
                # Try different selectors for title and URL
                title = ""
                url = ""

                # Try different title selectors
                for selector in ["h3 a", "h3 > a", ".question-hyperlink", "a.question-hyperlink", ".result-link a"]:
                    title_elem = item.select_one(selector)
                    if title_elem and title_elem.get_text().strip():
                        title = title_elem.get_text().strip()
                        url = title_elem.get("href")
                        break

                if not title or not url:
                    continue

                # Make URL absolute if it's relative
                if url.startswith("/"):
                    url = f"{self.BASE_URL}{url}"

                # Extract excerpt using different selectors
                excerpt = ""
                for selector in [".s-post-summary--content-excerpt", ".excerpt", ".summary"]:
                    excerpt_elem = item.select_one(selector)
                    if excerpt_elem:
                        excerpt = excerpt_elem.get_text().strip()
                        break

                # Extract vote count
                vote_count = 0
                for selector in [".s-post-summary--stats-item__number", ".vote-count-post", ".votes .vote-count-post"]:
                    vote_elem = item.select_one(selector)
                    if vote_elem:
                        try:
                            vote_count = int(vote_elem.get_text().strip())
                        except ValueError:
                            pass
                        break

                # Extract answer count
                answer_count = 0
                for selector in [".s-post-summary--stats-item:nth-child(2) .s-post-summary--stats-item__number",
                                ".status strong", ".answered", ".answer-count"]:
                    answer_elem = item.select_one(selector)
                    if answer_elem:
                        try:
                            answer_count = int(answer_elem.get_text().strip())
                        except ValueError:
                            pass
                        break

                # Extract tags
                tags = []
                for selector in [".post-tag", ".tags .post-tag", ".tags a"]:
                    tag_elems = item.select(selector)
                    if tag_elems:
                        tags = [tag.get_text().strip() for tag in tag_elems]
                        break

                # Create result item
                result = {
                    "id": f"stackoverflow_{uuid.uuid4().hex[:8]}",
                    "title": title,
                    "url": url,
                    "description": excerpt or f"Stack Overflow question about {topic}",
                    "source": "Stack Overflow",
                    "type": "qa",
                    "voteCount": vote_count,
                    "answerCount": answer_count,
                    "tags": tags
                }

                results.append(result)

            # Cache the results
            if results:
                cache.setex(cache_key, self.cache_ttl, results)
                self.logger.debug(f"Cached Stack Overflow search results for '{topic}' ({len(results)} items)")
            else:
                self.logger.warning(f"No Stack Overflow questions found for '{topic}'")

            return results
        except Exception as e:
            self.logger.error(f"Error searching Stack Overflow for '{topic}': {str(e)}")
            return []

    async def get_documentation_details(
        self,
        doc_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific Stack Overflow question.

        Args:
            doc_id: Documentation ID or URL

        Returns:
            Dictionary with documentation details or None if not found
        """
        # Check if doc_id is a URL
        if doc_id.startswith("http"):
            url = doc_id
        else:
            # Check cache first
            cache_key = f"stackoverflow:doc:{doc_id}"
            cached_result = cache.get(cache_key)
            if cached_result:
                self.logger.debug(f"Using cached Stack Overflow question details for '{doc_id}'")
                return cached_result

            # We can't get details without a URL
            self.logger.warning(f"Cannot get Stack Overflow question details without a URL: {doc_id}")
            return None

        try:
            # Fetch question page
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.warning(f"Stack Overflow question fetch failed with status {response.status}")
                        return None

                    html = await response.text()

            # Parse question page
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title_elem = soup.select_one("h1 a")
            title = title_elem.get_text().strip() if title_elem else "Stack Overflow Question"

            # Extract question content
            question_elem = soup.select_one(".js-post-body")
            question_content = question_elem.get_text().strip() if question_elem else ""

            # Extract answers
            answers = []
            answer_elems = soup.select(".answer")
            for answer_elem in answer_elems:
                # Extract answer content
                answer_content_elem = answer_elem.select_one(".js-post-body")
                if not answer_content_elem:
                    continue

                # Extract vote count
                vote_elem = answer_elem.select_one(".js-vote-count")
                vote_count = int(vote_elem.get_text().strip()) if vote_elem else 0

                # Check if accepted
                is_accepted = "accepted-answer" in answer_elem.get("class", [])

                # Create answer item
                answer = {
                    "content": answer_content_elem.get_text().strip(),
                    "voteCount": vote_count,
                    "isAccepted": is_accepted
                }

                answers.append(answer)

            # Sort answers by vote count and accepted status
            answers.sort(key=lambda a: (not a["isAccepted"], -a["voteCount"]))

            # Extract tags
            tags = []
            tag_elems = soup.select(".post-tag")
            if tag_elems:
                tags = [tag.get_text().strip() for tag in tag_elems]

            # Create description from question content
            description = question_content[:300] + "..." if len(question_content) > 300 else question_content

            # Create result
            result = {
                "id": f"stackoverflow_{uuid.uuid4().hex[:8]}",
                "title": title,
                "url": url,
                "description": description or f"Stack Overflow question: {title}",
                "questionContent": question_content,
                "answers": answers,
                "source": "Stack Overflow",
                "type": "qa",
                "tags": tags
            }

            # Cache the result
            if doc_id != url:  # Only cache if we have a proper ID
                cache.setex(f"stackoverflow:doc:{doc_id}", self.cache_ttl, result)
                self.logger.debug(f"Cached Stack Overflow question details for '{doc_id}'")

            return result
        except Exception as e:
            self.logger.error(f"Error getting Stack Overflow question details for '{doc_id}': {str(e)}")
            return None

    async def search_documentation_for_topic(
        self,
        topic: str,
        subtopic: str = None,
        max_results: int = 3,
        language: str = "en"
    ) -> List[Resource]:
        """
        Search for Stack Overflow questions related to a topic and convert to Resource objects.

        Args:
            topic: Main topic
            subtopic: Optional subtopic for more specific results
            max_results: Maximum number of results to return
            language: Language code (e.g., 'en', 'pt')

        Returns:
            List of Resource objects
        """
        # Determine search query
        if subtopic:
            query = f"{topic} {subtopic}"
        else:
            query = topic

        # Search for questions
        questions = await self.search_documentation(query, max_results, language)

        # Convert to Resource objects
        resources = []
        for question in questions:
            # Determine difficulty based on tags and vote count
            difficulty = "intermediate"
            tags = question.get("tags", [])
            vote_count = question.get("voteCount", 0)

            # Questions with high vote counts are usually more fundamental
            if vote_count > 100:
                difficulty = "beginner"
            # Questions with advanced tags are usually more difficult
            elif any(tag in ["advanced", "algorithm", "architecture", "optimization"] for tag in tags):
                difficulty = "advanced"

            resource = Resource(
                id=question.get("id"),
                title=question.get("title", ""),
                url=question.get("url", ""),
                type="qa",
                description=question.get("description", ""),
                duration=None,
                readTime=5,  # Estimate 5 minutes read time for Stack Overflow questions
                difficulty=difficulty,
                thumbnail=None
            )

            # Add subtopic information if applicable
            if subtopic:
                resource.title = f"{resource.title} - Relevante para: {subtopic}"

            # Add metadata
            resource.metadata = {
                "voteCount": question.get("voteCount", 0),
                "answerCount": question.get("answerCount", 0),
                "tags": question.get("tags", [])
            }

            resources.append(resource)

        return resources
