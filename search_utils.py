"""
Utilitários para busca na web com mecanismos anti-bloqueio.
"""

import random
import logging
from typing import List, Dict, Any
import asyncio

from duckduckgo_search import DDGS

# Configure logging
logger = logging.getLogger("mcp_server.search_utils")

# Lista de User Agents para rotação
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
]

# Mapeamento de idiomas para regiões do DuckDuckGo
LANGUAGE_TO_REGION = {
    "en": "us-en",
    "pt": "br-pt",
    "es": "es-es",
    "fr": "fr-fr",
    "de": "de-de",
    "it": "it-it",
    "nl": "nl-nl",
    "ru": "ru-ru",
    "ja": "jp-jp",
    "zh": "cn-zh",
}


def get_region_for_language(language: str) -> str:
    """
    Obtém a região correspondente ao idioma para o DuckDuckGo.

    Args:
        language: Código do idioma (ex: 'pt', 'en')

    Returns:
        Código da região para o DuckDuckGo
    """
    return LANGUAGE_TO_REGION.get(language, "wt-wt")  # wt-wt é o padrão global

def get_random_user_agent() -> str:
    """
    Retorna um User Agent aleatório da lista.

    Returns:
        String com o User Agent
    """
    return random.choice(USER_AGENTS)

async def _perform_search(query: str, max_results: int, region: str) -> List[Dict[str, Any]]:
    """
    Função interna para realizar a busca.
    """
    # Usar um User Agent aleatório
    user_agent = get_random_user_agent()
    results = []

    try:
        # A biblioteca DDGS não aceita user_agent como parâmetro no construtor
        # Vamos usar headers para definir o User-Agent
        headers = {'User-Agent': user_agent}
        with DDGS(headers=headers) as ddgs:
            for r in ddgs.text(query, max_results=max_results, region=region):
                results.append({
                    "title": r.get('title'),
                    "url": r.get('href'),
                    "description": r.get('body', '')[:200] + '...' if r.get('body', '') and len(r.get('body', '')) > 200 else r.get('body', ''),
                })
        return results
    except Exception as e:
        logger.error(f"Erro na busca com DuckDuckGo: {str(e)}")
        raise

async def search_with_backoff(query: str, max_results: int = 5, language: str = "en") -> List[Dict[str, Any]]:
    """
    Realiza busca na web com backoff exponencial para evitar rate limits.

    Args:
        query: Consulta de busca
        max_results: Número máximo de resultados
        language: Idioma da busca

    Returns:
        Lista de resultados da busca
    """
    # Adicionar idioma à consulta para melhores resultados
    if language != "en":
        query = f"{query} {language}"

    # Obter região para o idioma
    region = get_region_for_language(language)

    # Adicionar atraso aleatório para evitar padrões de requisição
    await asyncio.sleep(random.uniform(0.5, 2.0))

    # Implementar retry manual com backoff exponencial
    max_retries = 3
    retries = 0

    while retries < max_retries:
        try:
            # Tentar realizar a busca
            results = await _perform_search(query, max_results, region)

            if results:
                logger.info(f"Busca bem-sucedida para '{query}' ({len(results)} resultados)")
                return results
            else:
                logger.warning(f"Nenhum resultado encontrado para '{query}'")
                return []

        except Exception as e:
            retries += 1

            if retries < max_retries:
                # Calcular tempo de espera com backoff exponencial e jitter
                wait_time = (2 ** retries) * random.uniform(0.5, 1.5)
                logger.warning(f"Tentativa {retries}/{max_retries} falhou para '{query}'. Aguardando {wait_time:.2f}s antes da próxima tentativa.")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Todas as {max_retries} tentativas de busca falharam para '{query}': {str(e)}")

    # Se chegou aqui, todas as tentativas falharam
    return []
