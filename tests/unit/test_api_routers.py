"""
Unit tests for the API routers.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from api.routers.health_router import HealthRouter
from api.routers.mcp_router import MCPRouter
from api.routers.task_router import TaskRouter
from api.routers.cache_router import CacheRouter
from api.models import MCP, TaskInfo, TaskStatus


class TestHealthRouter:
    """Tests for the HealthRouter."""

    def test_health_check(self):
        """Test the health check endpoint."""
        # Create a FastAPI app
        app = FastAPI()

        # Create a health router
        health_router = HealthRouter()

        # Add the router to the app
        app.include_router(health_router.get_router())

        # Create a test client
        client = TestClient(app)

        # Test the health check endpoint
        response = client.get("/health")

        # Check the response
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestMCPRouter:
    """Tests for the MCPRouter."""

    def test_generate_mcp_endpoint(self):
        """Test the generate_mcp endpoint."""
        # Create a FastAPI app
        app = FastAPI()

        # Create an MCP router
        mcp_router = MCPRouter()

        # Add the router to the app
        app.include_router(mcp_router.get_router())

        # Create a test client
        client = TestClient(app)

        # Mock the content_source.find_resources method
        mock_find_resources = AsyncMock(return_value=[
            MagicMock(id="r1", title="Resource 1", url="https://example.com/1"),
            MagicMock(id="r2", title="Resource 2", url="https://example.com/2")
        ])

        # Mock the path_generator.generate_learning_path method
        mock_generate_learning_path = AsyncMock(return_value=MCP(
            id="mcp_123",
            title="Learning Path: Python",
            description="A comprehensive learning path for Python.",
            rootNodeId="n0",
            nodes={},
            metadata={
                "difficulty": "intermediate",
                "estimatedHours": 10,
                "tags": ["python", "programming"]
            }
        ))

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("api.routers.mcp_router.content_source.find_resources", mock_find_resources), \
             patch("api.routers.mcp_router.path_generator.generate_learning_path", mock_generate_learning_path), \
             patch("api.routers.mcp_router.cache", mock_cache):
            # Test the generate_mcp endpoint
            response = client.get("/generate_mcp?topic=Python")

            # Check the response
            assert response.status_code == 200
            assert response.json()["title"] == "Learning Path: Python"
            assert response.json()["description"] == "A comprehensive learning path for Python."

            # Check that the mocks were called
            mock_find_resources.assert_called_once()
            mock_generate_learning_path.assert_called_once()
            mock_cache.get.assert_called_once()
            mock_cache.setex.assert_called_once()

    def test_generate_mcp_async_endpoint(self):
        """Test the generate_mcp_async endpoint."""
        # Create a FastAPI app
        app = FastAPI()

        # Create an MCP router
        mcp_router = MCPRouter()

        # Add the router to the app
        app.include_router(mcp_router.get_router())

        # Create a test client
        client = TestClient(app)

        # Mock the task_service.create_task method
        mock_task = MagicMock()
        mock_task.id = "task_123"
        mock_create_task = MagicMock(return_value=mock_task)

        # Mock the cache
        mock_cache = MagicMock()
        mock_cache.get.return_value = None

        with patch("api.routers.mcp_router.task_service.create_task", mock_create_task), \
             patch("api.routers.mcp_router.cache", mock_cache):
            # Test the generate_mcp_async endpoint
            response = client.post("/generate_mcp_async?topic=Python")

            # Check the response
            assert response.status_code == 200
            assert response.json()["task_id"] == "task_123"

            # Check that the mocks were called
            mock_create_task.assert_called_once()
            mock_cache.get.assert_called_once()


class TestTaskRouter:
    """Tests for the TaskRouter."""

    def test_get_task_status(self):
        """Test the get_task_status endpoint."""
        # Create a FastAPI app
        app = FastAPI()

        # Create a task router
        task_router = TaskRouter()

        # Add the router to the app
        app.include_router(task_router.get_router())

        # Create a test client
        client = TestClient(app)

        # Mock the task_service.get_task method
        mock_task = MagicMock()
        mock_task.to_dict.return_value = {
            "id": "task_123",
            "description": "Test task",
            "status": "completed",
            "progress": 100,
            "result": {"data": "test"},
            "error": None,
            "created_at": 1234567890,
            "updated_at": 1234567890,
            "completed_at": 1234567890,
            "messages": []
        }
        mock_get_task = MagicMock(return_value=mock_task)

        with patch("api.routers.task_router.task_service.get_task", mock_get_task):
            # Test the get_task_status endpoint
            response = client.get("/status/task_123")

            # Check the response
            assert response.status_code == 200
            assert response.json()["id"] == "task_123"
            assert response.json()["status"] == "completed"

            # Check that the mock was called
            mock_get_task.assert_called_once_with("task_123")

    def test_list_tasks(self):
        """Test the list_tasks endpoint."""
        # Create a FastAPI app
        app = FastAPI()

        # Create a task router
        task_router = TaskRouter()

        # Add the router to the app
        app.include_router(task_router.get_router())

        # Create a test client
        client = TestClient(app)

        # Mock the task_service.get_all_tasks method
        mock_task1 = MagicMock()
        mock_task1.to_dict.return_value = {
            "id": "task_1",
            "description": "Task 1",
            "status": "completed",
            "progress": 100
        }

        mock_task2 = MagicMock()
        mock_task2.to_dict.return_value = {
            "id": "task_2",
            "description": "Task 2",
            "status": "running",
            "progress": 50
        }

        mock_get_all_tasks = MagicMock(return_value={
            "task_1": mock_task1,
            "task_2": mock_task2
        })

        with patch("api.routers.task_router.task_service.get_all_tasks", mock_get_all_tasks):
            # Test the list_tasks endpoint
            response = client.get("/tasks")

            # Check the response
            assert response.status_code == 200
            assert len(response.json()) == 2
            assert response.json()[0]["id"] == "task_1"
            assert response.json()[1]["id"] == "task_2"

            # Check that the mock was called
            mock_get_all_tasks.assert_called_once()


class TestCacheRouter:
    """Tests for the CacheRouter."""

    def test_get_cache_stats(self):
        """Test the get_cache_stats endpoint."""
        # Create a FastAPI app
        app = FastAPI()

        # Create a cache router
        cache_router = CacheRouter()

        # Add the router to the app
        app.include_router(cache_router.get_router())

        # Create a test client
        client = TestClient(app)

        # Mock the cache.info method
        mock_cache = MagicMock()
        mock_cache.info.return_value = {"used_memory": 1000, "hits": 100, "misses": 10}
        mock_cache.keys.return_value = ["key1", "key2", "key3"]

        # Mock the scraper.get_domain_method_cache_stats method
        mock_scraper = MagicMock()
        mock_scraper.get_domain_method_cache_stats.return_value = {
            "total_domains": 5,
            "domains": ["example.com", "test.com"]
        }

        with patch("api.routers.cache_router.cache", mock_cache), \
             patch("api.routers.cache_router.scraper", mock_scraper):
            # Test the get_cache_stats endpoint
            response = client.get("/cache_stats")

            # Check the response
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            assert response.json()["cache"]["total_keys"] == 3
            assert response.json()["cache"]["info"]["used_memory"] == 1000

            # Check that the mocks were called
            mock_cache.info.assert_called_once()
            mock_cache.keys.assert_called_once()
            mock_scraper.get_domain_method_cache_stats.assert_called_once()

    def test_clear_cache(self):
        """Test the clear_cache endpoint."""
        # Create a FastAPI app
        app = FastAPI()

        # Create a cache router
        cache_router = CacheRouter()

        # Add the router to the app
        app.include_router(cache_router.get_router())

        # Create a test client
        client = TestClient(app)

        # Mock the cache.clear method
        mock_cache = MagicMock()
        mock_cache.clear.return_value = 5

        # Mock the scraper.clear_domain_method_cache method
        mock_scraper = MagicMock()
        mock_scraper.clear_domain_method_cache.return_value = 3

        with patch("api.routers.cache_router.cache", mock_cache), \
             patch("api.routers.cache_router.scraper", mock_scraper):
            # Test the clear_cache endpoint
            response = client.post("/clear_cache?pattern=mcp:*&clear_domain_cache=true")

            # Check the response
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            assert response.json()["count"] == 5
            assert response.json()["domain_cache_cleared"] == 3

            # Check that the mocks were called
            mock_cache.clear.assert_called_once_with("mcp:*")
            mock_scraper.clear_domain_method_cache.assert_called_once()
