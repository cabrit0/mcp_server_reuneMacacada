"""
Módulo de cache para o MCP Server.

Este módulo fornece funcionalidades de cache para armazenar e recuperar
resultados de MCPs, reduzindo o tempo de resposta para tópicos frequentemente solicitados.
"""

from cachetools import TTLCache
from functools import wraps
import json
import logging

# Configurar logging
logger = logging.getLogger("mcp_server.cache")

# Cache com TTL de 7 dias e máximo de 100 itens
mcp_cache = TTLCache(maxsize=100, ttl=60*60*24*7)  # 7 dias em segundos

def cache_mcp(func):
    """
    Decorator para cachear resultados de MCPs por tópico.
    
    Args:
        func: A função a ser cacheada, que deve receber 'topic' como primeiro argumento.
        
    Returns:
        Uma função wrapper que verifica o cache antes de executar a função original.
    """
    @wraps(func)
    async def wrapper(topic, *args, **kwargs):
        # Normalizar o tópico para uso como chave de cache
        cache_key = f"mcp:{topic.lower().strip()}"
        
        # Verificar se existe no cache
        if cache_key in mcp_cache:
            logger.info(f"Cache hit for topic: {topic}")
            return mcp_cache[cache_key]
        
        logger.info(f"Cache miss for topic: {topic}, generating new MCP")
        
        # Se não estiver no cache, gerar MCP
        result = await func(topic, *args, **kwargs)
        
        # Armazenar no cache
        mcp_cache[cache_key] = result
        logger.info(f"Cached result for topic: {topic}")
        
        return result
    
    return wrapper

def get_cache_stats():
    """
    Retorna estatísticas sobre o cache atual.
    
    Returns:
        Um dicionário com estatísticas do cache.
    """
    return {
        "cache_size": len(mcp_cache),
        "max_size": mcp_cache.maxsize,
        "ttl_seconds": mcp_cache.ttl,
        "cached_topics": [key.split(":", 1)[1] for key in mcp_cache.keys()]
    }

def clear_cache():
    """
    Limpa todo o cache.
    
    Returns:
        O número de itens removidos do cache.
    """
    size = len(mcp_cache)
    mcp_cache.clear()
    logger.info(f"Cache cleared, {size} items removed")
    return size

def remove_from_cache(topic):
    """
    Remove um tópico específico do cache.
    
    Args:
        topic: O tópico a ser removido do cache.
        
    Returns:
        True se o tópico foi encontrado e removido, False caso contrário.
    """
    cache_key = f"mcp:{topic.lower().strip()}"
    if cache_key in mcp_cache:
        del mcp_cache[cache_key]
        logger.info(f"Removed topic from cache: {topic}")
        return True
    return False
