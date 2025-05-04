"""
Testes unitários para o Cache Router.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch, AsyncMock
from api.routers.cache_router import CacheRouter


@pytest.fixture
def mock_logger():
    """Fixture para simular o logger."""
    with patch('api.routers.cache_router.logger') as mock:
        mock.get_logger.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_cache():
    """Fixture para simular o cache."""
    with patch('api.routers.cache_router.cache') as mock:
        yield mock


@pytest.fixture
def cache_router(mock_logger, mock_cache):
    """Fixture para criar uma instância do CacheRouter com mocks."""
    return CacheRouter()


class TestCacheRouter:
    """Testes para o CacheRouter."""

    @pytest.mark.asyncio
    async def test_get_cache_stats(self, cache_router, mock_cache):
        """Teste do endpoint get_cache_stats."""
        # Configurar mock
        mock_cache.info.return_value = {
            "used_memory": "1.2MB",
            "hits": 156,
            "misses": 89
        }
        mock_cache.keys.return_value = ["key1", "key2", "key3", "key4", "key5", "key6", "key7", "key8", "key9", "key10",
                                       "key11", "key12", "key13", "key14", "key15", "key16", "key17", "key18", "key19", "key20",
                                       "key21", "key22", "key23", "key24", "key25", "key26", "key27", "key28", "key29", "key30",
                                       "key31", "key32", "key33", "key34", "key35", "key36", "key37", "key38", "key39", "key40",
                                       "key41", "key42"]

        # Mock the scraper module
        domain_cache_stats = {
            "totalDomains": 0,
            "simpleMethodCount": 0,
            "puppeteerMethodCount": 0,
            "domains": []
        }

        with patch("api.routers.cache_router.scraper", create=True) as mock_scraper:
            mock_scraper.get_domain_method_cache_stats.return_value = domain_cache_stats

            # Chamar o endpoint
            result = await cache_router.get_cache_stats()

            # Verificar resultado
            assert result["status"] == "success"
            assert result["cache"]["total_keys"] == 42
            assert result["cache"]["info"]["hits"] == 156
            assert result["domain_method_cache"] == domain_cache_stats

        # Verificar que os métodos do cache foram chamados corretamente
        mock_cache.info.assert_called_once()
        mock_cache.keys.assert_called_once_with("*")

    @pytest.mark.asyncio
    async def test_clear_cache(self, cache_router, mock_cache):
        """Teste do endpoint clear_cache."""
        # Configurar mock
        mock_cache.clear.return_value = 15

        # Chamar o endpoint
        result = await cache_router.clear_cache(pattern="mcp:*", clear_domain_cache=False)

        # Verificar resultado
        assert result["status"] == "success"
        assert result["message"] == "Cleared 15 items from cache"
        assert result["pattern"] == "mcp:*"
        assert result["count"] == 15
        assert result["domain_cache_cleared"] == 0

        # Verificar que os métodos do cache foram chamados corretamente
        mock_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_with_domain_cache(self, cache_router, mock_cache):
        """Teste do endpoint clear_cache com limpeza do cache de domínio."""
        # Configurar mock
        mock_cache.clear.return_value = 15

        # Chamar o endpoint com mock para o módulo scraper
        with patch("services.scraping.scraper", create=True) as mock_scraper:
            # Configurar o mock
            mock_scraper.clear_domain_method_cache.return_value = 5

            # Chamar o endpoint
            result = await cache_router.clear_cache(pattern="mcp:*", clear_domain_cache=True)

            # Verificar resultado
            assert result["status"] == "success"
            assert result["message"] == "Cleared 15 items from cache, including domain method cache"
            assert result["pattern"] == "mcp:*"
            assert result["count"] == 15

            # Verificar que os métodos do cache foram chamados corretamente
            mock_cache.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_cache_all(self, cache_router, mock_cache):
        """Teste do endpoint clear_cache com padrão '*'."""
        # Configurar mock
        mock_cache.clear.return_value = 100

        # Chamar o endpoint
        result = await cache_router.clear_cache(pattern="*", clear_domain_cache=False)

        # Verificar resultado
        assert result["status"] == "success"
        assert result["message"] == "Cleared 100 items from cache"
        assert result["pattern"] == "*"
        assert result["count"] == 100

        # Verificar que os métodos do cache foram chamados corretamente
        mock_cache.clear.assert_called_once()
