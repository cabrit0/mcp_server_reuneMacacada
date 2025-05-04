"""
Testes unitários para o Task Router.
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from api.models import TaskInfo, TaskStatus
from api.routers.task_router import TaskRouter


@pytest.fixture
def mock_logger():
    """Fixture para simular o logger."""
    with patch('api.routers.task_router.logger') as mock:
        mock.get_logger.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_task_service():
    """Fixture para simular o task_service."""
    with patch('api.routers.task_router.task_service') as mock:
        yield mock


@pytest.fixture
def task_router(mock_logger, mock_task_service):
    """Fixture para criar uma instância do TaskRouter com mocks."""
    return TaskRouter()


class TestTaskRouter:
    """Testes para o TaskRouter."""

    @pytest.mark.asyncio
    async def test_get_task_status_success(self, task_router, mock_task_service):
        """Teste de sucesso do endpoint get_task_status."""
        # Configurar mock
        task_mock = MagicMock()
        task_mock.to_dict.return_value = {
            "id": "task1",
            "description": "Gerar MCP para Python",
            "status": "running",
            "progress": 50,
            "created_at": 1650123456.789,
            "updated_at": 1650123466.789,
            "completed_at": None,
            "messages": []
        }
        mock_task_service.get_task.return_value = task_mock
        
        # Chamar o endpoint
        result = await task_router.get_task_status(task_id="task1")
        
        # Verificar resultado
        assert result["id"] == "task1"
        assert result["status"] == "running"
        assert result["progress"] == 50
        
        # Verificar que o serviço foi chamado corretamente
        mock_task_service.get_task.assert_called_once_with("task1")

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, task_router, mock_task_service):
        """Teste do endpoint get_task_status quando a tarefa não é encontrada."""
        # Configurar mock para retornar None
        mock_task_service.get_task.return_value = None
        
        # Chamar o endpoint e verificar que lança exceção
        with pytest.raises(HTTPException) as excinfo:
            await task_router.get_task_status(task_id="task1")
        
        # Verificar exceção
        assert excinfo.value.status_code == 404
        assert "Task with ID task1 not found" in str(excinfo.value.detail)
        
        # Verificar que o serviço foi chamado corretamente
        mock_task_service.get_task.assert_called_once_with("task1")

    @pytest.mark.asyncio
    async def test_list_tasks(self, task_router, mock_task_service):
        """Teste do endpoint list_tasks."""
        # Configurar mock
        task1 = MagicMock()
        task1.to_dict.return_value = {
            "id": "task1",
            "description": "Gerar MCP para Python",
            "status": "completed",
            "progress": 100,
            "created_at": 1650123456.789,
            "updated_at": 1650123466.789,
            "completed_at": 1650123466.789,
            "messages": []
        }
        
        task2 = MagicMock()
        task2.to_dict.return_value = {
            "id": "task2",
            "description": "Gerar MCP para JavaScript",
            "status": "running",
            "progress": 50,
            "created_at": 1650123556.789,
            "updated_at": 1650123566.789,
            "completed_at": None,
            "messages": []
        }
        
        mock_task_service.get_all_tasks.return_value = {"task1": task1, "task2": task2}
        
        # Chamar o endpoint
        result = await task_router.list_tasks()
        
        # Verificar resultado
        assert len(result) == 2
        assert result[0]["id"] == "task1"
        assert result[0]["status"] == "completed"
        assert result[1]["id"] == "task2"
        assert result[1]["status"] == "running"
        
        # Verificar que o serviço foi chamado corretamente
        mock_task_service.get_all_tasks.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, task_router, mock_task_service):
        """Teste do endpoint list_tasks quando não há tarefas."""
        # Configurar mock para retornar dicionário vazio
        mock_task_service.get_all_tasks.return_value = {}
        
        # Chamar o endpoint
        result = await task_router.list_tasks()
        
        # Verificar resultado
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Verificar que o serviço foi chamado corretamente
        mock_task_service.get_all_tasks.assert_called_once()
