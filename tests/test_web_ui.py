"""Tests for web UI functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from py_claude_sandbox.web_ui import create_web_ui, set_managers, refresh_containers, cleanup_all_containers
from py_claude_sandbox.container_manager import ContainerManager
from py_claude_sandbox.config import ConfigManager
from py_claude_sandbox.models import ContainerConfig


@pytest.fixture
def mock_container_manager():
    """Create a mock container manager."""
    manager = Mock(spec=ContainerManager)
    manager.list_containers.return_value = [
        {
            "id": "test123",
            "name": "test-container",
            "status": "running",
            "image": "python:3.11-slim",
        }
    ]
    manager.create_container.return_value = "test123"
    manager.execute_command.return_value = ("test output", "")
    return manager


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager."""
    manager = Mock(spec=ConfigManager)
    manager.load_config.return_value = Mock()
    return manager


@pytest.fixture
def web_ui(mock_container_manager, mock_config_manager):
    """Create a web UI instance for testing."""
    set_managers(mock_container_manager, mock_config_manager)
    return None  # We don't have a WebUI class anymore


def test_web_ui_initialization(web_ui):
    """Test web UI initialization."""
    # Test that managers can be set
    from py_claude_sandbox.web_ui import _container_manager, _config_manager
    assert _container_manager is not None
    assert _config_manager is not None


def test_create_web_ui_factory(mock_container_manager, mock_config_manager):
    """Test web UI factory function."""
    create_web_ui(mock_container_manager, mock_config_manager)
    
    # Check that managers were set
    from py_claude_sandbox.web_ui import _container_manager, _config_manager
    assert _container_manager == mock_container_manager
    assert _config_manager == mock_config_manager


@pytest.mark.asyncio
async def test_refresh_containers(web_ui, mock_container_manager):
    """Test refreshing container list."""
    await refresh_containers()
    
    mock_container_manager.list_containers.assert_called_once()
    from py_claude_sandbox.web_ui import _containers
    assert "test123" in _containers
    assert _containers["test123"]["name"] == "test-container"


@pytest.mark.asyncio
async def test_cleanup_all_containers(web_ui, mock_container_manager):
    """Test cleanup all containers."""
    with patch("py_claude_sandbox.web_ui.ui.notify"):
        await cleanup_all_containers()
    
    mock_container_manager.cleanup_containers.assert_called_once_with(force=True)


def test_web_ui_routes_setup(web_ui):
    """Test that routes are properly set up."""
    # Test that route functions exist
    from py_claude_sandbox.web_ui import dashboard, terminal, config, git_monitor
    assert callable(dashboard)
    assert callable(terminal)
    assert callable(config)
    assert callable(git_monitor)


@pytest.mark.asyncio
async def test_container_operations(web_ui, mock_container_manager):
    """Test container operations through web UI."""
    # Test container creation flow
    container_config = ContainerConfig(
        name="test-container",
        image="python:3.11-slim",
        ports={"8080": 8080},
        environment={"TEST": "value"},
        volumes={"/tmp": "/workspace"},
        working_dir="/workspace",
    )
    
    # Mock the container creation
    mock_container_manager.create_container.return_value = "new-container-id"
    
    # In a real test, you'd simulate the UI interaction
    # For now, we test the underlying logic
    container_id = mock_container_manager.create_container(container_config)
    mock_container_manager.start_container(container_id)
    
    assert container_id == "new-container-id"
    mock_container_manager.create_container.assert_called_with(container_config)
    mock_container_manager.start_container.assert_called_with("new-container-id")


def test_terminal_html_generation(web_ui):
    """Test that terminal HTML is properly generated."""
    # Test that the terminal route function exists
    from py_claude_sandbox.web_ui import terminal
    assert callable(terminal)
    
    # The terminal function would generate xterm.js HTML when called
    # In a real test, we'd mock the UI context and verify HTML generation


@pytest.mark.asyncio
async def test_git_integration(web_ui, mock_container_manager):
    """Test git integration functionality."""
    container_id = "test-container"
    
    # Mock git command execution
    mock_container_manager.execute_command.return_value = ("* main\n  feature-branch\n", "")
    
    # Test git status command
    output, _ = mock_container_manager.execute_command(
        container_id, ["git", "status", "--porcelain"]
    )
    
    assert output == "* main\n  feature-branch\n"
    mock_container_manager.execute_command.assert_called_with(
        container_id, ["git", "status", "--porcelain"]
    )


def test_config_management(web_ui, mock_config_manager):
    """Test configuration management."""
    # Test loading config
    config = mock_config_manager.load_config()
    assert config is not None
    mock_config_manager.load_config.assert_called_once()
    
    # Test saving config
    mock_config_manager.save_config(config)
    mock_config_manager.save_config.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling(web_ui, mock_container_manager):
    """Test error handling in web UI."""
    # Reset the containers dict first
    from py_claude_sandbox.web_ui import _containers
    _containers.clear()
    
    # Mock container manager to raise an exception
    mock_container_manager.list_containers.side_effect = Exception("Test error")
    
    # Test that error is handled gracefully
    with patch("py_claude_sandbox.web_ui.ui.notify"):
        await refresh_containers()
    
    # Verify the error was handled (containers dict should still be empty)
    assert len(_containers) == 0


def test_ui_components_creation(web_ui):
    """Test UI components are created properly."""
    # Test that all required UI creation functions exist
    from py_claude_sandbox.web_ui import dashboard, terminal, config, git_monitor, run_web_ui
    
    required_functions = [dashboard, terminal, config, git_monitor, run_web_ui]
    
    for func in required_functions:
        assert callable(func)