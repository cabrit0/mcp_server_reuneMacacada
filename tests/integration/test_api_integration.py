"""
Testes de integração para a API do MCP Server.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from main import app
from api.models import Resource, MCP, Node


@pytest.fixture
def client():
    """Fixture para criar um cliente de teste."""
    return TestClient(app)


@pytest.fixture
def mock_content_source():
    """Fixture para simular o content_source."""
    with patch('core.content_sourcing.content_source.find_resources', new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_path_generator():
    """Fixture para simular o path_generator."""
    with patch('core.path_generator.path_generator.generate_learning_path', new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_task_service():
    """Fixture para simular o task_service."""
    with patch('core.task_manager.task_service') as mock:
        task_mock = MagicMock()
        task_mock.id = "task1"
        mock.create_task.return_value = task_mock
        mock.get_task.return_value = task_mock
        mock.get_all_tasks.return_value = {"task1": task_mock}
        yield mock


class TestAPIIntegration:
    """Testes de integração para a API."""

    def test_health_endpoint(self, client):
        """Teste do endpoint /health."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_generate_mcp_endpoint(self, client, mock_content_source, mock_path_generator):
        """Teste do endpoint /generate_mcp."""
        # Configurar mocks
        resources = [
            Resource(
                id="r1",
                title="Introdução ao Python",
                url="https://example.com/python-intro",
                type="article"
            )
        ]
        mock_content_source.return_value = resources
        
        expected_mcp = MCP(
            id="mcp1",
            title="Aprendendo Python",
            description="Um plano de aprendizagem para Python",
            rootNodeId="n0",
            nodes={
                "n0": Node(
                    id="n0",
                    title="Introdução ao Python",
                    description="Aprenda os conceitos básicos de Python",
                    type="lesson",
                    resources=[]
                )
            }
        )
        mock_path_generator.return_value = expected_mcp
        
        # Fazer a requisição
        response = client.get("/generate_mcp?topic=python")
        
        # Verificar resposta
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "mcp1"
        assert data["title"] == "Aprendendo Python"
        assert "n0" in data["nodes"]

    def test_generate_mcp_async_endpoint(self, client, mock_task_service):
        """Teste do endpoint /generate_mcp_async."""
        # Fazer a requisição
        response = client.post("/generate_mcp_async?topic=python")
        
        # Verificar resposta
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task1"
        assert data["status"] == "accepted"

    def test_get_task_status_endpoint(self, client, mock_task_service):
        """Teste do endpoint /status/{task_id}."""
        # Configurar mock
        task_dict = {
            "id": "task1",
            "description": "Gerar MCP para Python",
            "status": "running",
            "progress": 50,
            "created_at": 1650123456.789,
            "updated_at": 1650123466.789,
            "completed_at": None,
            "messages": []
        }
        mock_task_service.get_task.return_value.to_dict.return_value = task_dict
        
        # Fazer a requisição
        response = client.get("/status/task1")
        
        # Verificar resposta
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "task1"
        assert data["status"] == "running"
        assert data["progress"] == 50

    def test_list_tasks_endpoint(self, client, mock_task_service):
        """Teste do endpoint /tasks."""
        # Configurar mock
        task_dict = {
            "id": "task1",
            "description": "Gerar MCP para Python",
            "status": "running",
            "progress": 50,
            "created_at": 1650123456.789,
            "updated_at": 1650123466.789,
            "completed_at": None,
            "messages": []
        }
        mock_task_service.get_all_tasks.return_value["task1"].to_dict.return_value = task_dict
        
        # Fazer a requisição
        response = client.get("/tasks")
        
        # Verificar resposta
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "task1"
        assert data[0]["status"] == "running"
