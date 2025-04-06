import asyncio
import re
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from schemas import Resource
from categories import detect_category, get_resource_queries_for_category
from youtube_integration import search_youtube_videos
from simple_cache import simple_cache
from search_utils import search_with_backoff

# Importações para o scraper otimizado
import content_scraper

# Configure logging
logger = logging.getLogger("mcp_server.content_sourcing")

# Maximum cache sizes to prevent memory issues
MAX_CACHE_SIZE = 100
MAX_PUPPETEER_INSTANCES = 2  # Limit concurrent Puppeteer instances for Render's free tier

# Simple cache for scraped content (will be migrated to distributed cache)
scrape_cache = {}
search_cache = {}


async def scrape_with_optimized_scraper(url: str, topic: str, timeout: int = 8) -> Dict[str, Any]:
    """
    Scrape content from websites using the optimized scraper.
    Implementação mais resiliente com timeout rigoroso e fallback para métodos mais simples.

    Args:
        url: URL to scrape
        topic: Topic being searched for
        timeout: Timeout in seconds (reduzido para 8 segundos para evitar bloqueios)

    Returns:
        Dictionary with title, description, and content type
    """
    # Check cache first
    cache_key = f"resource:{url}"
    cached_result = simple_cache.get(cache_key)
    if cached_result:
        logger.info(f"Using cached resource for {url}")
        return cached_result

    # Resultado padrão em caso de falha
    default_result = {
        'title': f"Resource about {topic}",
        'url': url,
        'description': f"A resource about {topic}",
        'type': 'unknown'
    }

    # Usar um timeout rigoroso para evitar que a tarefa fique presa
    try:
        # Criar uma tarefa com timeout
        scraping_task = asyncio.create_task(content_scraper.scrape_url(url, timeout))

        # Aguardar a tarefa com timeout
        try:
            html_content = await asyncio.wait_for(scraping_task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout scraping {url} after {timeout} seconds")
            return default_result

        # Se não conseguiu obter conteúdo, retornar resultado padrão
        if not html_content:
            logger.warning(f"No content returned for {url}")
            return default_result

        # Extract metadata
        result = content_scraper.extract_metadata_from_html(html_content, url, topic)

        # Cache the result
        simple_cache.setex(cache_key, 604800, result)  # 1 semana

        return result

    except Exception as e:
        logger.warning(f"Error scraping {url}: {str(e)}")
        return default_result


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


async def search_web(query: str, max_results: int = 5, language: str = "en") -> List[Dict[str, Any]]:
    """
    Search the web using DuckDuckGo with anti-blocking measures.

    Args:
        query: The search query
        max_results: Maximum number of results to return
        language: Language code (e.g., 'en', 'pt')

    Returns:
        List of dictionaries with title and URL
    """
    # Check cache first
    cache_key = f"search:{query}_{max_results}_{language}"
    cached_result = simple_cache.get(cache_key)
    if cached_result:
        logger.info(f"Using cached search results for '{query}'")
        return cached_result

    # Use our enhanced search function with backoff
    results = await search_with_backoff(query, max_results, language)

    # Cache the results if successful
    if results:
        # Cache for 1 day (86400 seconds)
        simple_cache.setex(cache_key, 86400, results)
        logger.info(f"Cached search results for '{query}' ({len(results)} results)")
    else:
        logger.warning(f"No search results found for '{query}'")

    return results


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
    cache_key = f"search:{topic}_{max_results}_{language}_{category}"
    cached_results = simple_cache.get(cache_key)
    if cached_results:
        logger.info(f"Found cached search results for topic: {topic}")
        return [Resource(**r) for r in cached_results]

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

    # Search the web for each query (concorrentemente)
    search_tasks = []
    for query in queries:
        search_tasks.append(search_web(query, max_results=3, language=language))

    # Executar buscas concorrentemente
    if search_tasks:
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Processar resultados
        for i, result in enumerate(search_results):
            if not isinstance(result, Exception) and result:
                all_results.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Erro na busca para '{queries[i]}': {str(result)}")

    # Remove duplicates based on URL
    unique_results = {}
    for result in all_results:
        if result['url'] not in unique_results:
            unique_results[result['url']] = result

    # Scrape additional details for each result
    web_resources = []

    # Process all results with the optimized scraper
    # Limitar o número de tarefas concorrentes para evitar sobrecarga
    max_concurrent_tasks = 5  # Limitar a 5 tarefas concorrentes

    # Processar URLs em lotes para evitar sobrecarga
    all_urls = list(unique_results.items())
    for i in range(0, len(all_urls), max_concurrent_tasks):
        batch = all_urls[i:i+max_concurrent_tasks]

        # Criar tarefas para este lote
        scraper_tasks = []
        for url, result in batch:
            scraper_tasks.append(scrape_with_optimized_scraper(url, topic, timeout=8))

        # Executar tarefas concorrentemente com timeout global
        try:
            # Usar wait_for para garantir que não fique preso
            scraper_results = await asyncio.wait_for(
                asyncio.gather(*scraper_tasks, return_exceptions=True),
                timeout=20  # Timeout global de 20 segundos para todo o lote
            )

            # Atualizar resultados com dados obtidos
            for j, (url, _) in enumerate(batch):
                if j < len(scraper_results) and not isinstance(scraper_results[j], Exception):
                    unique_results[url].update(scraper_results[j])

        except asyncio.TimeoutError:
            logger.warning(f"Timeout processing batch of URLs starting with {batch[0][0]}")

        # Adicionar um pequeno atraso para evitar sobrecarregar o servidor
        await asyncio.sleep(0.1)

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

    # Search for YouTube videos with timeout
    print(f"Searching YouTube for '{topic}'...")
    try:
        # Usar wait_for para garantir que não fique preso
        youtube_task = asyncio.create_task(
            search_youtube_videos(topic, max_results=max_results // 3, language=language)
        )
        youtube_resources = await asyncio.wait_for(youtube_task, timeout=15)  # 15 segundos de timeout
        print(f"Found {len(youtube_resources)} YouTube videos for '{topic}'")
    except asyncio.TimeoutError:
        logger.warning(f"Timeout searching YouTube videos for '{topic}'")
        youtube_resources = []  # Lista vazia em caso de timeout
    except Exception as e:
        logger.error(f"Error searching YouTube videos: {str(e)}")
        youtube_resources = []

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
    simple_cache.setex(cache_key, 86400, [r.model_dump() for r in filtered_resources])  # 1 dia

    # Limit the number of resources
    result = filtered_resources[:max_results]
    return result
