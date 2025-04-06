import asyncio
import re
import uuid
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from pyppeteer import launch

from schemas import Resource


async def scrape_with_puppeteer(url: str, topic: str) -> Dict[str, Any]:
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
        # Navigate to the URL
        await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 30000})
        
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


def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        
    Returns:
        List of dictionaries with title and URL
    """
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get('title'),
                    "url": r.get('href'),
                    "description": r.get('body', '')[:200] + '...' if r.get('body', '') and len(r.get('body', '')) > 200 else r.get('body', ''),
                })
    except Exception as e:
        print(f"Error searching with DuckDuckGo: {e}")
    
    return results


def scrape_basic_site(url: str, topic: str) -> Optional[Dict[str, Any]]:
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
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
        
        return {
            'title': title,
            'url': url,
            'description': description,
            'type': content_type,
            'readTime': read_time if content_type == 'article' else None,
            'duration': read_time if content_type == 'video' else None
        }
    
    except Exception as e:
        print(f"Error scraping {url} with BeautifulSoup: {e}")
        return None


async def find_resources(topic: str, max_results: int = 15) -> List[Resource]:
    """
    Find resources about a topic using various methods.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to return
        
    Returns:
        List of Resource objects
    """
    # Generate search queries
    queries = [
        f"{topic} tutorial",
        f"{topic} documentation",
        f"{topic} guide",
        f"{topic} examples",
        f"{topic} exercises",
        f"{topic} video tutorial"
    ]
    
    all_results = []
    
    # Search the web for each query
    for query in queries:
        results = search_web(query, max_results=3)
        all_results.extend(results)
    
    # Remove duplicates based on URL
    unique_results = {}
    for result in all_results:
        if result['url'] not in unique_results:
            unique_results[result['url']] = result
    
    # Scrape additional details for each result
    resources = []
    
    # Process the first few results with Puppeteer for JavaScript-heavy sites
    puppeteer_tasks = []
    for i, (url, result) in enumerate(list(unique_results.items())[:5]):
        puppeteer_tasks.append(scrape_with_puppeteer(url, topic))
    
    # Run Puppeteer tasks concurrently
    if puppeteer_tasks:
        puppeteer_results = await asyncio.gather(*puppeteer_tasks, return_exceptions=True)
        
        # Update results with Puppeteer data
        for i, (url, _) in enumerate(list(unique_results.items())[:5]):
            if i < len(puppeteer_results) and not isinstance(puppeteer_results[i], Exception):
                unique_results[url].update(puppeteer_results[i])
    
    # Process remaining results with BeautifulSoup
    for url, result in list(unique_results.items())[5:]:
        scraped_data = scrape_basic_site(url, topic)
        if scraped_data:
            unique_results[url].update(scraped_data)
    
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
            difficulty="intermediate"  # Default difficulty
        )
        
        resources.append(resource)
    
    # Limit the number of resources
    return resources[:max_results]
