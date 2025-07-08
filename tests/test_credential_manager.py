"""Tests for credential manager."""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from py_claude_sandbox.credential_manager import CredentialManager
from py_claude_sandbox.models import CredentialType


@pytest.fixture
def credential_manager():
    """Create a credential manager for testing."""
    return CredentialManager()


def test_discover_anthropic_env_var(credential_manager):
    """Test discovering Anthropic API key from environment."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        credentials = credential_manager.discover_credentials()
        
        anthropic_creds = [c for c in credentials if c.type == CredentialType.ANTHROPIC]
        assert len(anthropic_creds) >= 1
        
        env_cred = next((c for c in anthropic_creds if c.name == "ANTHROPIC_API_KEY"), None)
        assert env_cred is not None
        assert env_cred.value == "test-key"


def test_discover_github_env_var(credential_manager):
    """Test discovering GitHub token from environment."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test-token"}):
        credentials = credential_manager.discover_credentials()
        
        github_creds = [c for c in credentials if c.type == CredentialType.GITHUB]
        assert len(github_creds) >= 1
        
        env_cred = next((c for c in github_creds if c.name == "GITHUB_TOKEN"), None)
        assert env_cred is not None
        assert env_cred.value == "test-token"


def test_get_environment_vars(credential_manager):
    """Test getting environment variables."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        credential_manager.discover_credentials()
        env_vars = credential_manager.get_environment_vars()
        
        assert "ANTHROPIC_API_KEY" in env_vars
        assert env_vars["ANTHROPIC_API_KEY"] == "test-key"


def test_get_volume_mounts(credential_manager):
    """Test getting volume mounts for credential files."""
    with patch("pathlib.Path.exists", return_value=True):
        credential_manager.discover_credentials()
        mounts = credential_manager.get_volume_mounts()
        
        # Should have volume mounts for credential files
        assert isinstance(mounts, dict)