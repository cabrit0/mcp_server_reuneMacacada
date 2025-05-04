"""
Testes de performance para a API do MCP Server.
"""

import pytest
import time
import statistics
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
        resources = [
            Resource(
                id=f"r{i}",
                title=f"Resource {i}",
                url=f"https://example.com/resource-{i}",
                type="article"
            )
            for i in range(1, 11)
        ]
        mock.return_value = resources
        yield mock


@pytest.fixture
def mock_path_generator():
    """Fixture para simular o path_generator."""
    with patch('core.path_generator.path_generator.generate_learning_path', new_callable=AsyncMock) as mock:
        nodes = {
            f"n{i}": Node(
                id=f"n{i}",
                title=f"Node {i}",
                description=f"Description for node {i}",
                type="lesson",
                resources=[]
            )
            for i in range(10)
        }
        
        mcp = MCP(
            id="mcp1",
            title="Test MCP",
            description="A test MCP",
            rootNodeId="n0",
            nodes=nodes
        )
        
        mock.return_value = mcp
        yield mock


@pytest.fixture
def mock_cache():
    """Fixture para simular o cache."""
    with patch('infrastructure.cache.cache') as mock:
        mock.get.return_value = None
        yield mock


class TestAPIPerformance:
    """Testes de performance para a API."""

    def test_health_endpoint_performance(self, client):
        """Teste de performance do endpoint /health."""
        num_requests = 100
        response_times = []
        
        for _ in range(num_requests):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        p95_response_time = sorted(response_times)[int(num_requests * 0.95)]
        
        print(f"Health endpoint performance:")
        print(f"  Average response time: {avg_response_time:.6f} seconds")
        print(f"  Min response time: {min_response_time:.6f} seconds")
        print(f"  Max response time: {max_response_time:.6f} seconds")
        print(f"  P95 response time: {p95_response_time:.6f} seconds")
        
        # Verificar que o tempo médio de resposta é menor que 10ms
        assert avg_response_time < 0.01, f"Average response time ({avg_response_time:.6f}s) exceeds threshold (0.01s)"

    def test_generate_mcp_endpoint_performance(self, client, mock_content_source, mock_path_generator, mock_cache):
        """Teste de performance do endpoint /generate_mcp."""
        num_requests = 10
        response_times = []
        
        for i in range(num_requests):
            start_time = time.time()
            response = client.get(f"/generate_mcp?topic=test{i}")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        p95_response_time = sorted(response_times)[int(num_requests * 0.95)]
        
        print(f"Generate MCP endpoint performance:")
        print(f"  Average response time: {avg_response_time:.6f} seconds")
        print(f"  Min response time: {min_response_time:.6f} seconds")
        print(f"  Max response time: {max_response_time:.6f} seconds")
        print(f"  P95 response time: {p95_response_time:.6f} seconds")
        
        # Verificar que o tempo médio de resposta é menor que 100ms
        # Este limite pode precisar ser ajustado com base no ambiente de execução
        assert avg_response_time < 0.1, f"Average response time ({avg_response_time:.6f}s) exceeds threshold (0.1s)"

    def test_generate_mcp_async_endpoint_performance(self, client):
        """Teste de performance do endpoint /generate_mcp_async."""
        num_requests = 10
        response_times = []
        
        for i in range(num_requests):
            start_time = time.time()
            response = client.post(f"/generate_mcp_async?topic=test{i}")
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        p95_response_time = sorted(response_times)[int(num_requests * 0.95)]
        
        print(f"Generate MCP Async endpoint performance:")
        print(f"  Average response time: {avg_response_time:.6f} seconds")
        print(f"  Min response time: {min_response_time:.6f} seconds")
        print(f"  Max response time: {max_response_time:.6f} seconds")
        print(f"  P95 response time: {p95_response_time:.6f} seconds")
        
        # Verificar que o tempo médio de resposta é menor que 50ms
        # Este endpoint deve ser mais rápido que o síncrono, pois apenas cria a tarefa
        assert avg_response_time < 0.05, f"Average response time ({avg_response_time:.6f}s) exceeds threshold (0.05s)"
