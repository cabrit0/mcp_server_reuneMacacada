"""
Implementação simplificada de cache para o MCP Server.
"""

import time
import logging
from typing import Dict, Any, Optional

# Configurar logging
logger = logging.getLogger("mcp_server.simple_cache")

class SimpleCache:
    """
    Cache simples em memória para o MCP Server.
    Implementa uma interface similar ao Redis para facilitar a migração futura.
    """

    def __init__(self, max_size=1000):
        """
        Inicializa o cache.

        Args:
            max_size: Tamanho máximo do cache
        """
        self.cache = {}
        self.expiry = {}
        self.access_times = {}
        self.max_size = max_size
        logger.info(f"Inicializando SimpleCache com tamanho máximo de {max_size} itens")

    def get(self, key: str) -> Optional[Any]:
        """
        Obtém um valor do cache.

        Args:
            key: Chave do cache

        Returns:
            Valor armazenado ou None se não encontrado ou expirado
        """
        # Verifica se a chave existe
        if key not in self.cache:
            return None

        # Verifica se o valor expirou
        if key in self.expiry and self.expiry[key] < time.time():
            # Remove o valor expirado
            self.cache.pop(key, None)
            self.expiry.pop(key, None)
            self.access_times.pop(key, None)
            return None

        # Atualiza o tempo de acesso
        self.access_times[key] = time.time()

        return self.cache[key]

    def setex(self, key: str, ttl: int, value: Any) -> bool:
        """
        Define um valor no cache com TTL.

        Args:
            key: Chave do cache
            ttl: Tempo de vida em segundos
            value: Valor a ser armazenado

        Returns:
            True se bem-sucedido
        """
        # Verifica se o cache está cheio
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove o item menos recentemente acessado
            lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            self.cache.pop(lru_key, None)
            self.expiry.pop(lru_key, None)
            self.access_times.pop(lru_key, None)

        # Armazena o valor
        self.cache[key] = value
        self.expiry[key] = time.time() + ttl
        self.access_times[key] = time.time()

        return True

    def delete(self, key: str) -> int:
        """
        Remove um valor do cache.

        Args:
            key: Chave do cache

        Returns:
            1 se removido, 0 se não encontrado
        """
        if key in self.cache:
            self.cache.pop(key, None)
            self.expiry.pop(key, None)
            self.access_times.pop(key, None)
            return 1
        return 0

    def keys(self, pattern: str = "*") -> list:
        """
        Retorna chaves que correspondem ao padrão.

        Args:
            pattern: Padrão de chave (suporta apenas prefixo*)

        Returns:
            Lista de chaves
        """
        if pattern == "*":
            return list(self.cache.keys())

        prefix = pattern.rstrip("*")
        return [k for k in self.cache.keys() if k.startswith(prefix)]

    def clear(self, pattern: str = "*") -> int:
        """
        Limpa entradas do cache que correspondem ao padrão.

        Args:
            pattern: Padrão para correspondência de chaves. Padrão é "*" que limpa todo o cache.
                    Exemplos: "mcp:*" para todos os MCPs, "search:*" para todos os resultados de busca.

        Returns:
            Número de itens removidos
        """
        if pattern == "*":
            # Limpa todo o cache
            count = len(self.cache)
            self.cache.clear()
            self.expiry.clear()
            self.access_times.clear()
            return count
        else:
            # Remove apenas as chaves que correspondem ao padrão
            prefix = pattern.rstrip("*")
            keys_to_delete = [k for k in list(self.cache.keys()) if k.startswith(prefix)]
            count = len(keys_to_delete)

            for key in keys_to_delete:
                self.cache.pop(key, None)
                self.expiry.pop(key, None)
                self.access_times.pop(key, None)

            return count

    def size(self) -> int:
        """
        Retorna o tamanho atual do cache.

        Returns:
            Número de itens no cache
        """
        return len(self.cache)

    def cleanup_expired(self) -> int:
        """
        Remove itens expirados do cache.

        Returns:
            Número de itens removidos
        """
        now = time.time()
        expired_keys = [k for k, exp in self.expiry.items() if exp < now]

        for key in expired_keys:
            self.cache.pop(key, None)
            self.expiry.pop(key, None)
            self.access_times.pop(key, None)

        return len(expired_keys)

# Instância global
simple_cache = SimpleCache()
