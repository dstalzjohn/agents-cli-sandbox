"""Tests for CLI functionality."""

import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from py_claude_sandbox.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Python Claude Code Sandbox" in result.stdout


def test_list_command(runner):
    """Test list command."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.list_containers.return_value = [
            {
                "id": "test123",
                "name": "test-container",
                "status": "running",
                "image": "python:3.11-slim",
            }
        ]
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        mock_instance.list_containers.assert_called_once()


def test_create_command(runner):
    """Test create command."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.create_container.return_value = "test-container-id"
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, [
            "create",
            "--name", "test-container",
            "--image", "python:3.11-slim",
            "--port", "8080"
        ])
        
        assert result.exit_code == 0
        mock_instance.create_container.assert_called_once()
        mock_instance.start_container.assert_called_once_with("test-container-id")
        mock_instance.install_claude_code.assert_called_once_with("test-container-id")


def test_start_command(runner):
    """Test start command."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.list_containers.return_value = [
            {
                "id": "test123",
                "name": "test-container",
                "status": "stopped",
                "image": "python:3.11-slim",
            }
        ]
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["start", "test-container"])
        assert result.exit_code == 0
        mock_instance.start_container.assert_called_once_with("test123")


def test_stop_command(runner):
    """Test stop command."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.list_containers.return_value = [
            {
                "id": "test123",
                "name": "test-container",
                "status": "running",
                "image": "python:3.11-slim",
            }
        ]
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["stop", "test-container"])
        assert result.exit_code == 0
        mock_instance.stop_container.assert_called_once_with("test123")


def test_remove_command(runner):
    """Test remove command."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.list_containers.return_value = [
            {
                "id": "test123",
                "name": "test-container",
                "status": "stopped",
                "image": "python:3.11-slim",
            }
        ]
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["remove", "test-container"])
        assert result.exit_code == 0
        mock_instance.remove_container.assert_called_once_with("test123", force=False)


def test_remove_command_with_force(runner):
    """Test remove command with force flag."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.list_containers.return_value = [
            {
                "id": "test123",
                "name": "test-container",
                "status": "running",
                "image": "python:3.11-slim",
            }
        ]
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["remove", "test-container", "--force"])
        assert result.exit_code == 0
        mock_instance.remove_container.assert_called_once_with("test123", force=True)


def test_cleanup_command(runner):
    """Test cleanup command."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["cleanup"])
        assert result.exit_code == 0
        mock_instance.cleanup_containers.assert_called_once_with(force=False)


def test_cleanup_command_with_force(runner):
    """Test cleanup command with force flag."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["cleanup", "--force"])
        assert result.exit_code == 0
        mock_instance.cleanup_containers.assert_called_once_with(force=True)


def test_web_command(runner):
    """Test web command."""
    with patch("subprocess.run") as mock_subprocess:
        # Mock subprocess to avoid actually starting the web UI
        mock_subprocess.return_value = None
        
        result = runner.invoke(app, ["web", "--host", "127.0.0.1", "--port", "9000"])
        
        assert result.exit_code == 0
        mock_subprocess.assert_called_once()
        
        # Check that the subprocess was called with correct arguments
        call_args = mock_subprocess.call_args[0][0]
        assert "--host" in call_args
        assert "127.0.0.1" in call_args
        assert "--port" in call_args
        assert "9000" in call_args


def test_container_not_found_error(runner):
    """Test error handling when container is not found."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.list_containers.return_value = []  # No containers
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["start", "nonexistent-container"])
        assert result.exit_code == 1
        assert "not found" in result.stdout


def test_container_manager_error(runner):
    """Test error handling when container manager fails."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.list_containers.side_effect = Exception("Container manager error")
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1
        assert "Failed to list containers" in result.stdout


def test_podman_flag(runner):
    """Test podman flag usage."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.list_containers.return_value = []
        mock_manager.return_value = mock_instance
        
        # Test with podman=True (default)
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        mock_manager.assert_called_with(use_podman=True)
        
        # Test with podman=False
        result = runner.invoke(app, ["list", "--no-podman"])
        assert result.exit_code == 0
        mock_manager.assert_called_with(use_podman=False)


def test_create_command_with_git_repo(runner):
    """Test create command with git repository."""
    with patch("py_claude_sandbox.cli.ContainerManager") as mock_manager:
        mock_instance = Mock()
        mock_instance.create_container.return_value = "test-container-id"
        mock_manager.return_value = mock_instance
        
        result = runner.invoke(app, [
            "create",
            "--name", "test-container",
            "--repo", "https://github.com/test/repo.git",
            "--branch", "main"
        ])
        
        assert result.exit_code == 0
        mock_instance.create_container.assert_called_once()
        mock_instance.start_container.assert_called_once_with("test-container-id")


def test_main_function():
    """Test main function."""
    from py_claude_sandbox.cli import main
    
    # Test that main function exists and is callable
    assert callable(main)