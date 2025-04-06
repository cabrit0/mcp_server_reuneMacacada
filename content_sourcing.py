import asyncio
import re
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from pyppeteer import launch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from schemas import Resource
from categories import detect_category, get_resource_queries_for_category
from youtube_integration import search_youtube_videos

# Simple cache for search results and scraped content
search_cache = {}
scrape_cache = {}

# Maximum cache sizes to prevent memory issues
MAX_CACHE_SIZE = 100
MAX_PUPPETEER_INSTANCES = 2  # Limit concurrent Puppeteer instances for Render's free tier


async def scrape_with_puppeteer(url: str, topic: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Scrape content from JavaScript-heavy websites using Puppeteer.

    Args:
        url: The URL to scrape
        topic: The topic to search for

    Returns:
        Dictionary with title, description, and other metadata
    """
    browser = await launch(headless=True)
    page = await browser.newPage()

    # Set a user agent to identify the bot
    await page.setUserAgent('MCPBot/1.0 (+https://mcp-server.example.com/bot-info)')

    try:
        # Check cache first
        cache_key = f"puppeteer_{url}"
        if cache_key in scrape_cache:
            await browser.close()
            return scrape_cache[cache_key]

        # Navigate to the URL with a shorter timeout for Render's free tier
        try:
            await asyncio.wait_for(
                page.goto(url, {'waitUntil': 'networkidle2'}),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print(f"Timeout while loading {url}")
            # Continue with partial content if available

        # Extract title
        title = await page.title()

        # Extract description from meta tags or first paragraph
        description = await page.evaluate('''() => {
            const metaDesc = document.querySelector('meta[name="description"]');
            if (metaDesc) return metaDesc.getAttribute('content');

            const firstPara = document.querySelector('p');
            if (firstPara) return firstPara.textContent.trim();

            return '';
        }''')

        # Determine content type based on URL and page content
        content_type = await determine_content_type(page, url)

        # Estimate read time based on content length
        content_length = await page.evaluate('document.body.innerText.length')
        read_time = estimate_read_time(content_length)

        result = {
            'title': title,
            'url': url,
            'description': description[:200] + '...' if len(description) > 200 else description,
            'type': content_type,
            'readTime': read_time if content_type == 'article' else None,
            'duration': read_time if content_type == 'video' else None
        }

        # Cache the result with size limit
        scrape_cache[cache_key] = result

        # Trim cache if it gets too large
        if len(scrape_cache) > MAX_CACHE_SIZE:
            # Remove oldest entries (first 10%)
            keys_to_remove = list(scrape_cache.keys())[:MAX_CACHE_SIZE // 10]
            for key in keys_to_remove:
                del scrape_cache[key]
    except Exception as e:
        print(f"Error scraping {url} with Puppeteer: {e}")
        result = {
            'title': f"Resource about {topic}",
            'url': url,
            'description': f"A resource about {topic}",
            'type': 'unknown'
        }
    finally:
        await browser.close()

    return result


async def determine_content_type(page, url: str) -> str:
    """Determine the type of content based on the URL and page content."""
    domain = urlparse(url).netloc.lower()

    # Check for video platforms
    if any(platform in domain for platform in ['youtube.com', 'vimeo.com', 'dailymotion.com']):
        return 'video'

    # Check for documentation sites
    if any(platform in domain for platform in ['docs.', 'documentation.', '.dev/docs', 'developer.']):
        return 'documentation'

    # Check for exercise/practice sites
    if any(platform in domain for platform in ['exercism.io', 'leetcode.com', 'hackerrank.com', 'codewars.com']):
        return 'exercise'

    # Check for video elements on the page
    has_video = await page.evaluate('''() => {
        return document.querySelectorAll('video, iframe[src*="youtube"], iframe[src*="vimeo"]').length > 0;
    }''')

    if has_video:
        return 'video'

    # Default to article
    return 'article'


def estimate_read_time(content_length: int) -> int:
    """Estimate reading time in minutes based on content length."""
    # Average reading speed: ~200 words per minute
    # Average word length: ~5 characters
    words = content_length / 5
    minutes = round(words / 200)
    return max(1, minutes)  # Minimum 1 minute


def search_web(query: str, max_results: int = 5, language: str = "en") -> List[Dict[str, Any]]:
    """
    Search the web using DuckDuckGo.

    Args:
        query: The search query
        max_results: Maximum number of results to return

    Returns:
        List of dictionaries with title and URL
    """
    # Check cache first
    cache_key = f"{query}_{max_results}_{language}"
    if cache_key in search_cache:
        return search_cache[cache_key]

    results = []
    try:
        # Add language to the query for better results
        if language != "en":
            query = f"{query} {language}"

        with DDGS() as ddgs:
            # Use region parameter if available for language-specific results
            region = get_region_for_language(language)
            for r in ddgs.text(query, max_results=max_results, region=region):
                results.append({
                    "title": r.get('title'),
                    "url": r.get('href'),
                    "description": r.get('body', '')[:200] + '...' if r.get('body', '') and len(r.get('body', '')) > 200 else r.get('body', ''),
                })
    except Exception as e:
        print(f"Error searching with DuckDuckGo: {e}")

    # Cache the results with size limit
    search_cache[cache_key] = results

    # Trim cache if it gets too large
    if len(search_cache) > MAX_CACHE_SIZE:
        # Remove oldest entries (first 10%)
        keys_to_remove = list(search_cache.keys())[:MAX_CACHE_SIZE // 10]
        for key in keys_to_remove:
            del search_cache[key]

    return results


def get_region_for_language(language: str) -> str:
    """Map language code to DuckDuckGo region code for better search results."""
    language_to_region = {
        "en": "us-en",
        "pt": "br-pt",  # Brazil Portuguese
        "es": "es-es",  # Spain Spanish
        "fr": "fr-fr",  # France French
        "de": "de-de",  # Germany German
        "it": "it-it",  # Italy Italian
        # Add more mappings as needed
    }
    return language_to_region.get(language, "us-en")


def get_stopwords(language: str) -> List[str]:
    """Get stopwords for a specific language."""
    # Basic stopwords for different languages
    stopwords = {
        "en": ["the", "and", "or", "in", "on", "at", "to", "a", "an", "of", "for", "with", "by", "as", "is", "are", "was", "were"],
        "pt": ["o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "por", "para", "com", "e", "ou", "que", "se"],
        "es": ["el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "en", "por", "para", "con", "y", "o", "que", "si"],
        # Add more languages as needed
    }
    return stopwords.get(language, stopwords["en"])


def score_resource_relevance(resources: List[Resource], topic: str, language: str = "en") -> List[Tuple[Resource, float]]:
    """
    Score resources based on their relevance to the topic using TF-IDF.

    Args:
        resources: List of Resource objects
        topic: The search topic
        language: Language code for stopwords

    Returns:
        List of (resource, score) tuples sorted by relevance score
    """
    # Prepare text content from resources
    texts = []
    for resource in resources:
        # Combine title, description with different weights
        text = (resource.title + " ") * 3  # Title has 3x weight
        if resource.description:
            text += (resource.description + " ") * 2  # Description has 2x weight
        texts.append(text.lower())

    # Add the topic as the last document
    texts.append(topic.lower())

    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words=get_stopwords(language))

    try:
        # Transform texts to TF-IDF vectors
        tfidf_matrix = vectorizer.fit_transform(texts)

        # Calculate cosine similarity between each resource and the topic
        topic_vector = tfidf_matrix[-1]  # Last vector is the topic
        resource_vectors = tfidf_matrix[:-1]  # All other vectors are resources

        # Calculate similarity scores
        similarity_scores = cosine_similarity(resource_vectors, topic_vector)

        # Create (resource, score) pairs
        scored_resources = [(resources[i], similarity_scores[i][0])
                           for i in range(len(resources))]

        # Sort by score in descending order
        return sorted(scored_resources, key=lambda x: x[1], reverse=True)

    except Exception as e:
        print(f"Error in TF-IDF calculation: {e}")
        # Return resources with default score if TF-IDF fails
        return [(resource, 0.5) for resource in resources]


def filter_resources_by_relevance(resources: List[Resource], topic: str, threshold: float = 0.3, language: str = "en") -> List[Resource]:
    """
    Filter resources based on relevance to the topic.

    Args:
        resources: List of Resource objects
        topic: The search topic
        threshold: Minimum relevance score (0-1)
        language: Language code

    Returns:
        Filtered list of Resource objects
    """
    if not resources:
        return []

    scored_resources = score_resource_relevance(resources, topic, language)

    # Filter by threshold
    filtered_resources = [resource for resource, score in scored_resources
                         if score >= threshold]

    # If filtering removed too many resources, return at least a few
    if len(filtered_resources) < min(3, len(resources)):
        # Return top 3 resources regardless of threshold
        return [resource for resource, _ in scored_resources[:min(3, len(scored_resources))]]

    return filtered_resources


def scrape_basic_site(url: str, topic: str, language: str = "en") -> Optional[Dict[str, Any]]:
    """
    Scrape content from a website using requests and BeautifulSoup.

    Args:
        url: The URL to scrape
        topic: The topic to search for

    Returns:
        Dictionary with title, description, and other metadata or None if scraping fails
    """
    headers = {
        'User-Agent': 'MCPBot/1.0 (+https://mcp-server.example.com/bot-info)'
    }

    # Check cache first
    cache_key = f"basic_{url}_{language}"
    if cache_key in scrape_cache:
        return scrape_cache[cache_key]

    try:
        # Add language to headers if applicable
        if language != "en":
            headers['Accept-Language'] = f"{language},en;q=0.9"

        response = requests.get(url, headers=headers, timeout=8)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # Extract title
        title = soup.title.text.strip() if soup.title else f"Resource about {topic}"

        # Extract description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        first_para = soup.find('p')

        if meta_desc and meta_desc.get('content'):
            description = meta_desc.get('content')
        elif first_para:
            description = first_para.text.strip()
        else:
            description = f"A resource about {topic}"

        # Truncate description if too long
        if len(description) > 200:
            description = description[:200] + '...'

        # Determine content type
        content_type = 'article'  # Default

        # Check for video platforms in URL
        domain = urlparse(url).netloc.lower()
        if any(platform in domain for platform in ['youtube.com', 'vimeo.com', 'dailymotion.com']):
            content_type = 'video'

        # Check for documentation sites
        if any(platform in domain for platform in ['docs.', 'documentation.', '.dev/docs', 'developer.']):
            content_type = 'documentation'

        # Check for exercise/practice sites
        if any(platform in domain for platform in ['exercism.io', 'leetcode.com', 'hackerrank.com', 'codewars.com']):
            content_type = 'exercise'

        # Check for video elements on the page
        if soup.find('video') or soup.find('iframe', src=re.compile(r'(youtube|vimeo)')):
            content_type = 'video'

        # Estimate read time based on content length
        content_length = len(soup.get_text())
        read_time = estimate_read_time(content_length)

        result = {
            'title': title,
            'url': url,
            'description': description,
            'type': content_type,
            'readTime': read_time if content_type == 'article' else None,
            'duration': read_time if content_type == 'video' else None
        }

        # Cache the result with size limit
        scrape_cache[cache_key] = result

        # Trim cache if it gets too large
        if len(scrape_cache) > MAX_CACHE_SIZE:
            # Remove oldest entries (first 10%)
            keys_to_remove = list(scrape_cache.keys())[:MAX_CACHE_SIZE // 10]
            for key in keys_to_remove:
                del scrape_cache[key]

        return result

    except Exception as e:
        print(f"Error scraping {url} with BeautifulSoup: {e}")
        return None


async def find_resources(topic: str, max_results: int = 15, language: str = "pt", category: Optional[str] = None) -> List[Resource]:
    """
    Find resources about a topic using various methods, including YouTube videos.

    Args:
        topic: The topic to search for
        max_results: Maximum number of results to return
        language: Language code (pt, en, es, etc.)

    Returns:
        List of Resource objects
    """
    # Check cache first
    cache_key = f"{topic}_{max_results}_{language}_{category}"
    if cache_key in search_cache:
        return search_cache[cache_key]

    # Use provided category or detect it automatically
    if category is None:
        category = detect_category(topic)
        print(f"Detected category for '{topic}': {category}")
    else:
        print(f"Using provided category for '{topic}': {category}")

    # Get category-specific search queries
    category_queries = get_resource_queries_for_category(topic, category)

    # Generate search queries with language-specific terms if needed
    if language == "pt":
        language_queries = [
            f"{topic} tutorial",
            f"{topic} documentação",
            f"{topic} guia",
            f"{topic} exemplos",
            f"{topic} exercícios",
            f"{topic} aula",
            f"{topic} curso",
            f"{topic} como aprender"
        ]
    elif language == "es":
        language_queries = [
            f"{topic} tutorial",
            f"{topic} documentación",
            f"{topic} guía",
            f"{topic} ejemplos",
            f"{topic} ejercicios",
            f"{topic} curso",
            f"{topic} cómo aprender"
        ]
    else:  # Default to English
        language_queries = [
            f"{topic} tutorial",
            f"{topic} documentation",
            f"{topic} guide",
            f"{topic} examples",
            f"{topic} exercises",
            f"{topic} video tutorial",
            f"{topic} how to learn"
        ]

    # Combine category-specific and language-specific queries
    queries = list(set(category_queries + language_queries))  # Remove duplicates

    all_results = []

    # Search the web for each query
    for query in queries:
        results = search_web(query, max_results=3, language=language)
        all_results.extend(results)

    # Remove duplicates based on URL
    unique_results = {}
    for result in all_results:
        if result['url'] not in unique_results:
            unique_results[result['url']] = result

    # Scrape additional details for each result
    web_resources = []

    # Process the first few results with Puppeteer for JavaScript-heavy sites
    # Limit to fewer concurrent Puppeteer instances for better performance on Render
    puppeteer_tasks = []
    for i, (url, result) in enumerate(list(unique_results.items())[:MAX_PUPPETEER_INSTANCES]):
        puppeteer_tasks.append(scrape_with_puppeteer(url, topic, timeout=8))

    # Run Puppeteer tasks concurrently
    if puppeteer_tasks:
        puppeteer_results = await asyncio.gather(*puppeteer_tasks, return_exceptions=True)

        # Update results with Puppeteer data
        for i, (url, _) in enumerate(list(unique_results.items())[:5]):
            if i < len(puppeteer_results) and not isinstance(puppeteer_results[i], Exception):
                unique_results[url].update(puppeteer_results[i])

    # Process remaining results with BeautifulSoup
    for url, result in list(unique_results.items())[MAX_PUPPETEER_INSTANCES:]:
        scraped_data = scrape_basic_site(url, topic, language=language)
        if scraped_data:
            unique_results[url].update(scraped_data)

        # Add a small delay to avoid overwhelming the server
        await asyncio.sleep(0.05)  # Reduced delay for better performance

    # Convert to Resource objects
    for url, result in unique_results.items():
        # Generate a unique ID
        resource_id = f"resource_{uuid.uuid4().hex[:8]}"

        # Create Resource object
        resource = Resource(
            id=resource_id,
            title=result.get('title', f"Resource about {topic}"),
            url=url,
            type=result.get('type', 'article'),
            description=result.get('description', f"A resource about {topic}"),
            duration=result.get('duration'),
            readTime=result.get('readTime'),
            difficulty="intermediate",  # Default difficulty
            thumbnail=result.get('thumbnail')  # Add thumbnail if available
        )

        web_resources.append(resource)

    # Search for YouTube videos
    print(f"Searching YouTube for '{topic}'...")
    youtube_resources = await search_youtube_videos(topic, max_results=max_results // 3, language=language)
    print(f"Found {len(youtube_resources)} YouTube videos for '{topic}'")

    # Combine web and YouTube resources
    all_resources = web_resources + youtube_resources

    # Remove duplicates (by URL)
    unique_resources = []
    seen_urls = set()
    for resource in all_resources:
        if resource.url not in seen_urls:
            unique_resources.append(resource)
            seen_urls.add(resource.url)

    # Filter resources by relevance to the topic
    filtered_resources = filter_resources_by_relevance(unique_resources, topic, threshold=0.3, language=language)

    # Log the filtering results
    print(f"Filtered resources by relevance: {len(unique_resources)} -> {len(filtered_resources)}")

    # Cache the results
    result = filtered_resources[:max_results]
    search_cache[cache_key] = result

    # Limit the number of resources
    return result
