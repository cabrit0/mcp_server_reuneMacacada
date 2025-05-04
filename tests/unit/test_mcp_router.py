"""
Testes unitários para o MCP Router.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from api.models import MCP, Resource, Node, TaskCreationResponse
from api.routers.mcp_router import MCPRouter


@pytest.fixture
def mock_logger():
    """Fixture para simular o logger."""
    with patch('api.routers.mcp_router.logger') as mock:
        mock.get_logger.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_cache():
    """Fixture para simular o cache."""
    with patch('api.routers.mcp_router.cache') as mock:
        mock.get.return_value = None
        yield mock


@pytest.fixture
def mock_content_source():
    """Fixture para simular o content_source."""
    with patch('api.routers.mcp_router.content_source') as mock:
        mock.find_resources = AsyncMock()
        yield mock


@pytest.fixture
def mock_path_generator():
    """Fixture para simular o path_generator."""
    with patch('api.routers.mcp_router.path_generator') as mock:
        mock.generate_learning_path = AsyncMock()
        yield mock


@pytest.fixture
def mock_task_service():
    """Fixture para simular o task_service."""
    with patch('api.routers.mcp_router.task_service') as mock:
        mock.create_task.return_value = MagicMock()
        yield mock


@pytest.fixture
def mcp_router(mock_logger, mock_cache, mock_content_source, mock_path_generator, mock_task_service):
    """Fixture para criar uma instância do MCPRouter com mocks."""
    return MCPRouter()


class TestMCPRouter:
    """Testes para o MCPRouter."""

    @pytest.mark.asyncio
    async def test_generate_mcp_endpoint_success(self, mcp_router, mock_content_source, mock_path_generator, mock_cache):
        """Teste de sucesso do endpoint generate_mcp."""
        # Configurar mocks
        resources = [
            Resource(
                id="r1",
                title="Introdução ao Python",
                url="https://example.com/python-intro",
                type="article"
            )
        ]
        mock_content_source.find_resources.return_value = resources

        expected_mcp = MCP(
            id="mcp1",
            title="Aprendendo Python",
            description="Um plano de aprendizagem para Python",
            topic="python",
            category="technology",
            language="pt",
            rootNodeId="n0",
            nodes={
                "n0": Node(
                    id="n0",
                    title="Introdução ao Python",
                    description="Aprenda os conceitos básicos de Python",
                    type="lesson",
                    resources=[]
                )
            },
            totalHours=5,
            tags=["python", "programming", "technology"]
        )
        mock_path_generator.generate_learning_path.return_value = expected_mcp

        # Chamar o endpoint
        result = await mcp_router.generate_mcp_endpoint(
            topic="python",
            max_resources=15,
            num_nodes=15,
            min_width=3,
            max_width=5,
            min_height=3,
            max_height=7,
            language="pt",
            category=None
        )

        # Verificar resultado
        assert result == expected_mcp
        mock_content_source.find_resources.assert_called_once_with(
            "python", max_results=15, language="pt", category=None
        )
        mock_path_generator.generate_learning_path.assert_called_once()
        mock_cache.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_mcp_endpoint_cached(self, mcp_router, mock_content_source, mock_path_generator, mock_cache):
        """Teste do endpoint generate_mcp com resultado em cache."""
        # Configurar mock do cache para retornar um resultado
        cached_mcp = {
            "id": "mcp1",
            "title": "Aprendendo Python",
            "description": "Um plano de aprendizagem para Python",
            "topic": "python",
            "category": "technology",
            "language": "pt",
            "rootNodeId": "n0",
            "nodes": {
                "n0": {
                    "id": "n0",
                    "title": "Introdução ao Python",
                    "description": "Aprenda os conceitos básicos de Python",
                    "type": "lesson",
                    "resources": [],
                    "prerequisites": [],
                    "rewards": [],
                    "hints": [],
                    "visualPosition": {"x": 0, "y": 0, "level": 0},
                    "state": "available"
                }
            },
            "totalHours": 5,
            "tags": ["python", "programming", "technology"]
        }
        mock_cache.get.return_value = cached_mcp

        # Chamar o endpoint
        result = await mcp_router.generate_mcp_endpoint(
            topic="python",
            max_resources=15,
            num_nodes=15,
            min_width=3,
            max_width=5,
            min_height=3,
            max_height=7,
            language="pt",
            category=None
        )

        # Verificar resultado
        assert result.id == "mcp1"
        assert result.title == "Aprendendo Python"
        # Verificar que os métodos de busca e geração não foram chamados
        mock_content_source.find_resources.assert_not_called()
        mock_path_generator.generate_learning_path.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_mcp_endpoint_no_resources(self, mcp_router, mock_content_source):
        """Teste do endpoint generate_mcp quando não há recursos."""
        # Configurar mock para retornar lista vazia
        mock_content_source.find_resources.return_value = []

        # Chamar o endpoint e verificar que lança exceção
        with pytest.raises(HTTPException) as excinfo:
            await mcp_router.generate_mcp_endpoint(
                topic="python",
                max_resources=15,
                num_nodes=15,
                min_width=3,
                max_width=5,
                min_height=3,
                max_height=7,
                language="pt",
                category=None
            )

        # Verificar exceção
        assert excinfo.value.status_code == 500
        assert "No resources found for topic" in str(excinfo.value.detail)

    @pytest.mark.asyncio
    async def test_generate_mcp_endpoint_path_generator_error(self, mcp_router, mock_content_source, mock_path_generator):
        """Teste do endpoint generate_mcp quando o path_generator lança erro."""
        # Configurar mocks
        resources = [
            Resource(
                id="r1",
                title="Introdução ao Python",
                url="https://example.com/python-intro",
                type="article"
            )
        ]
        mock_content_source.find_resources.return_value = resources

        # Configurar path_generator para lançar erro
        mock_path_generator.generate_learning_path.side_effect = ValueError("Could not generate enough nodes")

        # Chamar o endpoint e verificar que lança exceção
        with pytest.raises(HTTPException) as excinfo:
            await mcp_router.generate_mcp_endpoint(
                topic="python",
                max_resources=15,
                num_nodes=15,
                min_width=3,
                max_width=5,
                min_height=3,
                max_height=7,
                language="pt",
                category=None
            )

        # Verificar exceção
        assert excinfo.value.status_code == 500
        assert "Could not generate enough nodes" in str(excinfo.value.detail)

    @pytest.mark.asyncio
    async def test_generate_mcp_async_endpoint_success(self, mcp_router, mock_task_service):
        """Teste de sucesso do endpoint generate_mcp_async."""
        # Configurar mock
        task_mock = MagicMock()
        task_mock.id = "task1"
        mock_task_service.create_task.return_value = task_mock

        # Criar mock para BackgroundTasks
        background_tasks = MagicMock()

        # Chamar o endpoint
        result = await mcp_router.generate_mcp_async_endpoint(
            background_tasks=background_tasks,
            topic="python",
            max_resources=15,
            num_nodes=15,
            min_width=3,
            max_width=5,
            min_height=3,
            max_height=7,
            language="pt",
            category=None
        )

        # Verificar resultado
        assert isinstance(result, TaskCreationResponse)
        assert result.task_id == "task1"
        assert result.status == "accepted"

        # Verificar que a tarefa foi criada e adicionada às tarefas de fundo
        mock_task_service.create_task.assert_called_once()
        background_tasks.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_mcp_async_endpoint_cached(self, mcp_router, mock_cache, mock_task_service):
        """Teste do endpoint generate_mcp_async com resultado em cache."""
        # Configurar mock do cache para retornar um resultado
        cached_mcp = {
            "id": "mcp1",
            "title": "Aprendendo Python",
            "description": "Um plano de aprendizagem para Python",
            "topic": "python",
            "category": "technology",
            "language": "pt",
            "rootNodeId": "n0",
            "nodes": {},
            "totalHours": 5,
            "tags": ["python", "programming", "technology"]
        }
        mock_cache.get.return_value = cached_mcp

        # Configurar mock da tarefa
        task_mock = MagicMock()
        task_mock.id = "task1"
        mock_task_service.create_task.return_value = task_mock

        # Criar mock para BackgroundTasks
        background_tasks = MagicMock()

        # Chamar o endpoint
        result = await mcp_router.generate_mcp_async_endpoint(
            background_tasks=background_tasks,
            topic="python",
            max_resources=15,
            num_nodes=15,
            min_width=3,
            max_width=5,
            min_height=3,
            max_height=7,
            language="pt",
            category=None
        )

        # Verificar resultado
        assert isinstance(result, TaskCreationResponse)
        assert result.task_id == "task1"
        assert "cached result" in result.message.lower()

        # Verificar que a tarefa foi criada mas não adicionada às tarefas de fundo
        mock_task_service.create_task.assert_called_once()
        background_tasks.add_task.assert_not_called()
        task_mock.mark_as_completed.assert_called_once_with(cached_mcp)
