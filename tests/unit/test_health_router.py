"""
Testes unitários para o Health Router.
"""

import pytest
from unittest.mock import MagicMock, patch
from api.routers.health_router import HealthRouter


@pytest.fixture
def mock_logger():
    """Fixture para simular o logger."""
    with patch('api.routers.health_router.logger') as mock:
        mock.get_logger.return_value = MagicMock()
        yield mock


@pytest.fixture
def health_router(mock_logger):
    """Fixture para criar uma instância do HealthRouter com mocks."""
    return HealthRouter()


class TestHealthRouter:
    """Testes para o HealthRouter."""

    @pytest.mark.asyncio
    async def test_health_check(self, health_router):
        """Teste do endpoint health_check."""
        # Chamar o endpoint
        result = await health_router.health_check()
        
        # Verificar resultado
        assert result["status"] == "ok"
