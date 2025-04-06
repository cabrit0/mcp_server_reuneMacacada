"""
Módulo de scraping otimizado para o MCP Server.
Utiliza um sistema adaptativo que escolhe automaticamente o método mais eficiente
para cada site, reduzindo o uso de recursos e melhorando a performance.
"""

import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, Optional, Any

# Importar o novo sistema de scraping adaptativo
from adaptive_scraper import adaptiveScrape, clearDomainMethodCache, getDomainMethodCacheStats
from simple_cache import simple_cache

# Domínios que sabemos que requerem JavaScript (usado como fallback)
JS_REQUIRED_DOMAINS = {
    'twitter.com', 'linkedin.com', 'instagram.com',
    'facebook.com', 'medium.com', 'stackoverflow.com'
}

async def scrape_url(url: str, timeout: int = 30, cache_enabled: bool = True) -> Optional[str]:
    """
    Faz scraping de uma URL usando o método mais eficiente disponível.
    Utiliza o sistema adaptativo que escolhe automaticamente entre métodos leves e pesados.

    Args:
        url: A URL para fazer scraping
        timeout: Timeout em segundos
        cache_enabled: Se deve usar cache

    Returns:
        Conteúdo HTML como string ou None se falhar
    """
    # Verifica o cache primeiro se habilitado
    if cache_enabled:
        cache_key = f"page:{url}"
        cached_content = simple_cache.get(cache_key)
        if cached_content:
            logging.info(f"Usando conteúdo em cache para {url}")
            return cached_content

    try:
        # Determinar se devemos forçar um método específico baseado em domínios conhecidos
        domain = urlparse(url).netloc
        force_method = None

        if any(js_domain in domain for js_domain in JS_REQUIRED_DOMAINS):
            force_method = 'puppeteer'

        # Usar o sistema adaptativo para escolher o melhor método
        result = await adaptiveScrape(url, {
            'timeout': timeout,
            'method': force_method
        })

        if not result or not result.get('html'):
            logging.warning(f"Scraping adaptativo falhou para {url}")
            return None

        content = result['html']

        # Armazena o conteúdo em cache se bem-sucedido e o cache estiver habilitado
        if content and cache_enabled:
            # Armazenar por 1 semana (604800 segundos)
            simple_cache.setex(cache_key, 604800, content)
            logging.info(f"Armazenado em cache: {url} (método: {result.get('method', 'desconhecido')})")

        return content
    except Exception as e:
        logging.error(f"Erro ao fazer scraping de {url}: {str(e)}")
        return None

def clear_domain_method_cache() -> int:
    """
    Limpa o cache de métodos por domínio.

    Returns:
        Número de entradas removidas do cache
    """
    try:
        # Limpar o cache de métodos por domínio
        clearDomainMethodCache()
        logging.info("Cache de métodos por domínio foi limpo")
        return 1
    except Exception as e:
        logging.error(f"Erro ao limpar cache de métodos: {str(e)}")
        return 0


def get_domain_method_cache_stats() -> Dict[str, Any]:
    """
    Obtém estatísticas do cache de métodos por domínio.

    Returns:
        Dicionário com estatísticas do cache
    """
    try:
        stats = getDomainMethodCacheStats()
        return stats
    except Exception as e:
        logging.error(f"Erro ao obter estatísticas do cache de métodos: {str(e)}")
        return {
            "error": str(e),
            "totalDomains": 0,
            "domains": []
        }


def extract_metadata_from_html(html_content: str, url: str, topic: str) -> Dict[str, Any]:
    """Extrai metadados de conteúdo HTML."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extrai o título
        title = soup.title.text.strip() if soup.title else f"Recurso sobre {topic}"
        if not title or len(title) < 3:
            title = f"Recurso sobre {topic}"

        # Extrai a descrição
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc and 'content' in meta_desc.attrs else ''

        if not description or len(description) < 10:
            # Tenta extrair o primeiro parágrafo
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.text.strip()
                if len(text) > 50:
                    description = text[:300] + '...' if len(text) > 300 else text
                    break

        if not description or len(description) < 10:
            description = f"Um recurso sobre {topic}"

        # Determina o tipo de conteúdo
        content_type = determine_content_type(soup, url)

        return {
            'title': title,
            'url': url,
            'description': description,
            'type': content_type
        }
    except Exception as e:
        logging.warning(f"Erro ao extrair metadados de {url}: {str(e)}")
        return {
            'title': f"Recurso sobre {topic}",
            'url': url,
            'description': f"Um recurso sobre {topic}",
            'type': 'unknown'
        }


def determine_content_type(soup: BeautifulSoup, url: str) -> str:
    """Determina o tipo de conteúdo baseado na URL e no conteúdo HTML."""
    domain = urlparse(url).netloc.lower()

    # Verifica plataformas de vídeo
    if any(platform in domain for platform in ['youtube.com', 'vimeo.com', 'dailymotion.com']):
        return 'video'

    # Verifica sites de documentação
    if any(platform in domain for platform in ['docs.', 'documentation.', '.dev/docs', 'developer.']):
        return 'documentation'

    # Verifica sites de exercícios/prática
    if any(platform in domain for platform in ['exercism.io', 'leetcode.com', 'hackerrank.com', 'codewars.com']):
        return 'exercise'

    # Verifica elementos de vídeo na página
    video_elements = soup.select('video, iframe[src*="youtube"], iframe[src*="vimeo"]')
    if video_elements:
        return 'video'

    # Verifica elementos de código ou conteúdo tipo código
    code_elements = soup.select('code, pre, .code, .codehilite, .highlight')
    if code_elements:
        return 'tutorial'

    # Verifica conteúdo de quiz ou exercício
    if soup.body:
        text = soup.body.get_text().lower()
        has_quiz = (
            ('quiz' in text or 'exercise' in text or 'practice' in text) and
            ('question' in text or 'answer' in text or 'solution' in text)
        )
        if has_quiz:
            return 'quiz'

    # Padrão para artigo
    return 'article'
