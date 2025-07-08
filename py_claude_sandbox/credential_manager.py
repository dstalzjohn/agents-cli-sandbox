"""Credential discovery and management for py-claude-sandbox."""

import os
from pathlib import Path
from typing import Dict, List, Optional

from py_claude_sandbox.models import Credential, CredentialType


class CredentialManager:
    """Manages credential discovery and forwarding."""
    
    def __init__(self):
        """Initialize credential manager."""
        self.credentials: List[Credential] = []
    
    def discover_credentials(self) -> List[Credential]:
        """Discover credentials from common locations."""
        self.credentials = []
        
        # Anthropic API key
        self._discover_anthropic()
        
        # GitHub credentials
        self._discover_github()
        
        # OpenAI credentials
        self._discover_openai()
        
        # Google credentials
        self._discover_google()
        
        # AWS credentials
        self._discover_aws()
        
        return self.credentials
    
    def _discover_anthropic(self) -> None:
        """Discover Anthropic API credentials."""
        # Environment variable
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.credentials.append(
                Credential(
                    type=CredentialType.ANTHROPIC,
                    name="ANTHROPIC_API_KEY",
                    value=api_key,
                )
            )
        
        # Config file
        config_file = Path.home() / ".anthropic" / "config.json"
        if config_file.exists():
            self.credentials.append(
                Credential(
                    type=CredentialType.ANTHROPIC,
                    name="anthropic_config",
                    value=str(config_file),
                    file_path=str(config_file),
                )
            )
    
    def _discover_github(self) -> None:
        """Discover GitHub credentials."""
        # Environment variable
        token = os.getenv("GITHUB_TOKEN")
        if token:
            self.credentials.append(
                Credential(
                    type=CredentialType.GITHUB,
                    name="GITHUB_TOKEN",
                    value=token,
                )
            )
        
        # Git config
        git_config = Path.home() / ".gitconfig"
        if git_config.exists():
            self.credentials.append(
                Credential(
                    type=CredentialType.GITHUB,
                    name="git_config",
                    value=str(git_config),
                    file_path=str(git_config),
                )
            )
    
    def _discover_openai(self) -> None:
        """Discover OpenAI credentials."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.credentials.append(
                Credential(
                    type=CredentialType.OPENAI,
                    name="OPENAI_API_KEY",
                    value=api_key,
                )
            )
    
    def _discover_google(self) -> None:
        """Discover Google credentials."""
        # Service account key
        service_account = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if service_account and Path(service_account).exists():
            self.credentials.append(
                Credential(
                    type=CredentialType.GOOGLE,
                    name="GOOGLE_APPLICATION_CREDENTIALS",
                    value=service_account,
                    file_path=service_account,
                )
            )
    
    def _discover_aws(self) -> None:
        """Discover AWS credentials."""
        # Environment variables
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        
        if access_key and secret_key:
            self.credentials.extend([
                Credential(
                    type=CredentialType.AWS,
                    name="AWS_ACCESS_KEY_ID",
                    value=access_key,
                ),
                Credential(
                    type=CredentialType.AWS,
                    name="AWS_SECRET_ACCESS_KEY",
                    value=secret_key,
                ),
            ])
        
        # Credentials file
        aws_creds = Path.home() / ".aws" / "credentials"
        if aws_creds.exists():
            self.credentials.append(
                Credential(
                    type=CredentialType.AWS,
                    name="aws_credentials",
                    value=str(aws_creds),
                    file_path=str(aws_creds),
                )
            )
    
    def get_environment_vars(self) -> Dict[str, str]:
        """Get environment variables for container."""
        env_vars = {}
        
        for cred in self.credentials:
            if not cred.file_path:  # Only env vars, not files
                env_vars[cred.name] = cred.value
        
        return env_vars
    
    def get_volume_mounts(self) -> Dict[str, str]:
        """Get volume mounts for credential files."""
        mounts = {}
        
        for cred in self.credentials:
            if cred.file_path:
                container_path = f"/tmp/{cred.name}"
                mounts[cred.file_path] = container_path
        
        return mounts