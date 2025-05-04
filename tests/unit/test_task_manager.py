"""
Unit tests for the task manager implementations.
"""

import os
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from core.task_manager.task import Task, TaskStatus
from core.task_manager.default_task_service import DefaultTaskService
from core.task_manager.persistent_task_service import PersistentTaskService
from core.task_manager.task_service_factory import TaskServiceFactory


class TestTask:
    """Tests for the Task class."""

    def test_initialization(self):
        """Test task initialization."""
        task = Task("test-id", "Test task")
        
        # Check initial values
        assert task.id == "test-id"
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.progress == 0
        assert task.result is None
        assert task.error is None
        assert task.messages == []

    def test_update_progress(self):
        """Test updating task progress."""
        task = Task("test-id", "Test task")
        
        # Update progress
        task.update_progress(50, "Half done")
        
        # Check values
        assert task.progress == 50
        assert len(task.messages) == 1
        assert task.messages[0]["message"] == "Half done"
        
        # Test progress bounds
        task.update_progress(-10)
        assert task.progress == 0
        
        task.update_progress(110)
        assert task.progress == 100

    def test_status_changes(self):
        """Test changing task status."""
        task = Task("test-id", "Test task")
        
        # Test running
        task.mark_as_running()
        assert task.status == TaskStatus.RUNNING
        assert any("started" in msg["message"].lower() for msg in task.messages)
        
        # Test completed
        result = {"data": "test"}
        task.mark_as_completed(result)
        assert task.status == TaskStatus.COMPLETED
        assert task.progress == 100
        assert task.result == result
        assert task.completed_at is not None
        assert any("completed" in msg["message"].lower() for msg in task.messages)
        
        # Test failed
        task = Task("test-id", "Test task")
        task.mark_as_failed("Error message")
        assert task.status == TaskStatus.FAILED
        assert task.error == "Error message"
        assert task.completed_at is not None
        assert any("failed" in msg["message"].lower() for msg in task.messages)
        
        # Test canceled
        task = Task("test-id", "Test task")
        task.mark_as_canceled("User request")
        assert task.status == TaskStatus.CANCELED
        assert task.completed_at is not None
        assert any("canceled" in msg["message"].lower() for msg in task.messages)

    def test_to_dict(self):
        """Test converting task to dictionary."""
        task = Task("test-id", "Test task")
        task.mark_as_running()
        task.update_progress(50, "Half done")
        
        # Convert to dict
        task_dict = task.to_dict()
        
        # Check values
        assert task_dict["id"] == "test-id"
        assert task_dict["description"] == "Test task"
        assert task_dict["status"] == TaskStatus.RUNNING
        assert task_dict["progress"] == 50
        assert len(task_dict["messages"]) == 2

    def test_from_dict(self):
        """Test creating task from dictionary."""
        # Create a task and convert to dict
        original_task = Task("test-id", "Test task")
        original_task.mark_as_running()
        original_task.update_progress(50, "Half done")
        task_dict = original_task.to_dict()
        
        # Create a new task from the dict
        new_task = Task.from_dict(task_dict)
        
        # Check values
        assert new_task.id == original_task.id
        assert new_task.description == original_task.description
        assert new_task.status == original_task.status
        assert new_task.progress == original_task.progress
        assert len(new_task.messages) == len(original_task.messages)


class TestDefaultTaskService:
    """Tests for the DefaultTaskService implementation."""

    def test_create_task(self):
        """Test creating a task."""
        service = DefaultTaskService()
        
        # Create a task
        task = service.create_task("Test task")
        
        # Check task
        assert task.id is not None
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING
        
        # Check that task is stored
        assert task.id in service.tasks
        assert service.tasks[task.id] is task

    def test_get_task(self):
        """Test getting a task."""
        service = DefaultTaskService()
        
        # Create a task
        task = service.create_task("Test task")
        
        # Get the task
        retrieved_task = service.get_task(task.id)
        
        # Check task
        assert retrieved_task is task
        
        # Test getting non-existent task
        assert service.get_task("non-existent") is None

    def test_get_all_tasks(self):
        """Test getting all tasks."""
        service = DefaultTaskService()
        
        # Create some tasks
        task1 = service.create_task("Task 1")
        task2 = service.create_task("Task 2")
        
        # Get all tasks
        all_tasks = service.get_all_tasks()
        
        # Check tasks
        assert len(all_tasks) == 2
        assert all_tasks[task1.id] is task1
        assert all_tasks[task2.id] is task2

    @pytest.mark.asyncio
    async def test_run_task(self):
        """Test running a task."""
        service = DefaultTaskService()
        
        # Create a task
        task = service.create_task("Test task")
        
        # Define a test function
        async def test_func(a, b):
            return a + b
        
        # Run the task
        result = await service.run_task(task, test_func, 1, 2)
        
        # Check result
        assert result == 3
        
        # Check task status
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 3
        assert task.progress == 100

    @pytest.mark.asyncio
    async def test_run_task_failure(self):
        """Test running a task that fails."""
        service = DefaultTaskService()
        
        # Create a task
        task = service.create_task("Test task")
        
        # Define a test function that raises an exception
        async def test_func():
            raise ValueError("Test error")
        
        # Run the task and expect an exception
        with pytest.raises(ValueError):
            await service.run_task(task, test_func)
        
        # Check task status
        assert task.status == TaskStatus.FAILED
        assert task.error == "Test error"

    @pytest.mark.asyncio
    async def test_run_task_cancellation(self):
        """Test running a task that gets cancelled."""
        service = DefaultTaskService()
        
        # Create a task
        task = service.create_task("Test task")
        
        # Define a test function that can be cancelled
        async def test_func():
            await asyncio.sleep(10)
            return "Done"
        
        # Mock asyncio.CancelledError
        mock_cancelled_error = AsyncMock(side_effect=asyncio.CancelledError())
        
        # Run the task and expect cancellation
        with patch("asyncio.sleep", mock_cancelled_error):
            with pytest.raises(asyncio.CancelledError):
                await service.run_task(task, test_func)
        
        # Check task status
        assert task.status == TaskStatus.CANCELED

    def test_clean_old_tasks(self):
        """Test cleaning old tasks."""
        service = DefaultTaskService(max_tasks=5)
        
        # Create some tasks
        for i in range(10):
            service.create_task(f"Task {i}")
        
        # Check that tasks were cleaned automatically
        assert len(service.tasks) <= 5
        
        # Clean tasks manually
        removed = service.clean_old_tasks(2)
        
        # Check that tasks were removed
        assert removed == 2
        assert len(service.tasks) <= 3


class TestPersistentTaskService:
    """Tests for the PersistentTaskService implementation."""

    def setup_method(self):
        """Set up the test environment."""
        # Create a temporary directory for task storage
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up the test environment."""
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_create_and_save_task(self):
        """Test creating and saving a task."""
        service = PersistentTaskService(self.temp_dir)
        
        # Create a task
        task = service.create_task("Test task")
        
        # Check that task file was created
        task_file = os.path.join(self.temp_dir, f"{task.id}.json")
        assert os.path.exists(task_file)
        
        # Check task
        assert task.id is not None
        assert task.description == "Test task"
        assert task.status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_run_task_and_save(self):
        """Test running a task and saving its state."""
        service = PersistentTaskService(self.temp_dir)
        
        # Create a task
        task = service.create_task("Test task")
        
        # Define a test function
        async def test_func(a, b):
            return a + b
        
        # Run the task
        result = await service.run_task(task, test_func, 1, 2)
        
        # Check result
        assert result == 3
        
        # Check task status
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 3
        
        # Check that task file was updated
        task_file = os.path.join(self.temp_dir, f"{task.id}.json")
        assert os.path.exists(task_file)
        
        # Create a new service instance to test loading
        new_service = PersistentTaskService(self.temp_dir)
        
        # Check that task was loaded
        loaded_task = new_service.get_task(task.id)
        assert loaded_task is not None
        assert loaded_task.id == task.id
        assert loaded_task.status == TaskStatus.COMPLETED
        assert loaded_task.result == 3

    def test_clean_old_tasks(self):
        """Test cleaning old tasks."""
        service = PersistentTaskService(self.temp_dir, max_tasks=5)
        
        # Create some tasks
        for i in range(10):
            service.create_task(f"Task {i}")
        
        # Check that tasks were cleaned automatically
        assert len(service.get_all_tasks()) <= 5
        
        # Count task files
        task_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.json')]
        assert len(task_files) <= 5
        
        # Clean tasks manually
        removed = service.clean_old_tasks(2)
        
        # Check that tasks were removed
        assert removed == 2
        assert len(service.get_all_tasks()) <= 3
        
        # Count task files again
        task_files = [f for f in os.listdir(self.temp_dir) if f.endswith('.json')]
        assert len(task_files) <= 3


class TestTaskServiceFactory:
    """Tests for the TaskServiceFactory."""

    def test_create_default_task_service(self):
        """Test creating a default task service."""
        # Clear existing instances
        TaskServiceFactory._instances = {}
        
        # Create service
        service = TaskServiceFactory.create_task_service("default")
        
        # Check type
        assert isinstance(service, DefaultTaskService)
        
        # Check singleton pattern
        assert TaskServiceFactory.create_task_service("default") is service

    def test_create_persistent_task_service(self):
        """Test creating a persistent task service."""
        # Clear existing instances
        TaskServiceFactory._instances = {}
        
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Create service
            service = TaskServiceFactory.create_task_service(
                "persistent",
                {"storage_dir": temp_dir}
            )
            
            # Check type
            assert isinstance(service, PersistentTaskService)
            
            # Check singleton pattern
            assert TaskServiceFactory.create_task_service("persistent") is service
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir)

    def test_create_unknown_service_type(self):
        """Test creating an unknown service type."""
        # Clear existing instances
        TaskServiceFactory._instances = {}
        
        # Create service with unknown type
        service = TaskServiceFactory.create_task_service("unknown")
        
        # Check that it falls back to default
        assert isinstance(service, DefaultTaskService)
