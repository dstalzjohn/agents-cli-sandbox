"""Tests for container manager."""

import pytest
from unittest.mock import Mock, patch

from py_claude_sandbox.container_manager import ContainerManager
from py_claude_sandbox.models import ContainerConfig, ContainerStatus


@pytest.fixture
def container_manager():
    """Create a container manager for testing."""
    with patch("py_claude_sandbox.container_manager.docker"):
        return ContainerManager(use_podman=False)


@pytest.fixture
def container_config():
    """Create a test container config."""
    return ContainerConfig(
        name="test-container",
        image="python:3.11-slim",
        ports={"9876": 9876},
        environment={"TEST": "value"},
        volumes={"/tmp": "/tmp"},
        working_dir="/workspace",
    )


def test_create_container(container_manager, container_config):
    """Test container creation."""
    mock_container = Mock()
    mock_container.id = "test-container-id"
    
    container_manager.client.containers.create.return_value = mock_container
    
    container_id = container_manager.create_container(container_config)
    
    assert container_id == "test-container-id"
    container_manager.client.containers.create.assert_called_once()


def test_start_container(container_manager):
    """Test container start."""
    mock_container = Mock()
    container_manager.client.containers.get.return_value = mock_container
    
    container_manager.start_container("test-id")
    
    mock_container.start.assert_called_once()


def test_stop_container(container_manager):
    """Test container stop."""
    mock_container = Mock()
    container_manager.client.containers.get.return_value = mock_container
    
    container_manager.stop_container("test-id")
    
    mock_container.stop.assert_called_once()


def test_get_container_status(container_manager):
    """Test get container status."""
    mock_container = Mock()
    mock_container.status = "running"
    container_manager.client.containers.get.return_value = mock_container
    
    status = container_manager.get_container_status("test-id")
    
    assert status == ContainerStatus.RUNNING


def test_execute_command(container_manager):
    """Test command execution."""
    mock_container = Mock()
    mock_result = Mock()
    mock_result.output = b"test output"
    mock_container.exec_run.return_value = mock_result
    
    container_manager.client.containers.get.return_value = mock_container
    
    output, error = container_manager.execute_command("test-id", ["echo", "test"])
    
    assert output == "test output"
    assert error == ""
    mock_container.exec_run.assert_called_once_with(
        ["echo", "test"], stdout=True, stderr=True
    )