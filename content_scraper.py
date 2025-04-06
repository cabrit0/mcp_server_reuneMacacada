"""
Módulo de scraping otimizado para o MCP Server.
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Dict, List, Optional, Any

from puppeteer_pool import puppeteer_pool
from simple_cache import simple_cache

# Domínios que requerem JavaScript
JS_REQUIRED_DOMAINS = {
    'twitter.com', 'linkedin.com', 'instagram.com',
    'facebook.com', 'medium.com', 'stackoverflow.com'
}

async def scrape_url(url: str, timeout: int = 30, cache_enabled: bool = True) -> Optional[str]:
    """
    Faz scraping de uma URL usando o método mais eficiente disponível.

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

    domain = urlparse(url).netloc
    content = None

    # Decide qual método usar baseado no domínio
    if any(js_domain in domain for js_domain in JS_REQUIRED_DOMAINS):
        content = await scrape_with_puppeteer(url, timeout)
    else:
        # Tenta primeiro com requests
        try:
            content = await scrape_with_requests(url, timeout)
            # Verifica se o conteúdo parece completo
            if content and len(content) > 1000:
                pass
            else:
                # Se o conteúdo parece incompleto, tenta com Puppeteer
                content = await scrape_with_puppeteer(url, timeout)
        except Exception as e:
            logging.warning(f"Falha ao fazer scraping de {url} com requests: {str(e)}")
            # Fallback para Puppeteer se requests falhar
            content = await scrape_with_puppeteer(url, timeout)

    # Armazena o conteúdo em cache se bem-sucedido e o cache estiver habilitado
    if content and cache_enabled:
        simple_cache.setex(cache_key, 604800, content)  # 1 semana

    return content

async def scrape_with_requests(url: str, timeout: int = 30) -> Optional[str]:
    """Faz scraping de uma URL usando aiohttp (leve)"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logging.warning(f"Falha ao fazer scraping de {url}: Status {response.status}")
                    return None
        except Exception as e:
            logging.warning(f"Erro ao fazer scraping de {url}: {str(e)}")
            return None

async def handle_request(request):
    """Manipula a interceptação de requisições para bloquear recursos desnecessários"""
    if request.resourceType in ['stylesheet', 'font', 'image']:
        await request.abort()
    else:
        await request.continue_()

async def scrape_with_puppeteer(url: str, timeout: int = 30) -> Optional[str]:
    """Faz scraping de uma URL usando Puppeteer (para sites com JavaScript pesado)"""
    browser = None
    try:
        browser = await puppeteer_pool.get_browser()
        page = await browser.newPage()

        # Otimiza o carregamento da página
        await page.setRequestInterception(True)

        # Define o manipulador de requisições
        async def request_handler(req):
            if req.resourceType in ['stylesheet', 'font', 'image']:
                await req.abort()
            else:
                await req.continue_()

        page.on('request', lambda req: asyncio.ensure_future(request_handler(req)))

        # Define o timeout
        await page.setDefaultNavigationTimeout(timeout * 1000)

        # Navega para a página
        await page.goto(url, {'waitUntil': 'domcontentloaded'})

        # Obtém o conteúdo da página
        content = await page.content()

        # Fecha a página
        await page.close()

        return content
    except Exception as e:
        logging.warning(f"Erro ao fazer scraping de {url} com Puppeteer: {str(e)}")
        return None
    finally:
        if browser:
            await puppeteer_pool.release_browser(browser)


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
