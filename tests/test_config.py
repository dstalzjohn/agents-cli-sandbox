"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest

from py_claude_sandbox.config import ConfigManager
from py_claude_sandbox.models import SandboxConfig


@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("""
container:
  name: test-sandbox
  image: python:3.11-slim
  ports:
    "9876": 9876
  environment:
    TEST: value
  volumes:
    "/tmp": "/tmp"
  working_dir: /workspace
  command: null
credentials: []
git_repo: null
git_branch: null
web_port: 9876
auto_commit: true
claude_flags:
  - "--dangerously-skip-permissions"
""")
        return Path(f.name)


def test_load_config_from_file(temp_config_file):
    """Test loading configuration from file."""
    config_manager = ConfigManager(temp_config_file)
    config = config_manager.load_config()
    
    assert isinstance(config, SandboxConfig)
    assert config.container.name == "test-sandbox"
    assert config.web_port == 9876
    assert config.auto_commit is True
    
    # Cleanup
    temp_config_file.unlink()


def test_load_default_config():
    """Test loading default configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "nonexistent.yaml"
        config_manager = ConfigManager(config_path)
        config = config_manager.load_config()
        
        assert isinstance(config, SandboxConfig)
        assert config.container.name == "claude-sandbox"
        assert config.web_port == 9876


def test_save_config():
    """Test saving configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test-config.yaml"
        config_manager = ConfigManager(config_path)
        
        # Create and save config
        config = config_manager.load_config()
        config_manager.save_config(config)
        
        assert config_path.exists()
        
        # Load saved config
        new_config = config_manager.load_config()
        assert new_config.container.name == config.container.name


def test_get_env_var():
    """Test getting environment variable."""
    import os
    from unittest.mock import patch
    
    config_manager = ConfigManager()
    
    # Test with existing env var
    with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
        value = config_manager.get_env_var("TEST_VAR")
        assert value == "test_value"
    
    # Test with default
    value = config_manager.get_env_var("NONEXISTENT_VAR", "default")
    assert value == "default"