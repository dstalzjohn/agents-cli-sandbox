"""Configuration management for py-claude-sandbox."""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

from py_claude_sandbox.models import ContainerConfig, SandboxConfig


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager."""
        self.config_path = config_path or Path.home() / ".py-claude-sandbox.yaml"
        self.config: Optional[SandboxConfig] = None
    
    def load_config(self) -> SandboxConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                config_data = yaml.safe_load(f)
            self.config = SandboxConfig(**config_data)
        else:
            self.config = self._create_default_config()
        
        return self.config
    
    def save_config(self, config: SandboxConfig) -> None:
        """Save configuration to file."""
        with open(self.config_path, "w") as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False)
        self.config = config
    
    def _create_default_config(self) -> SandboxConfig:
        """Create default configuration."""
        container_config = ContainerConfig(
            name="claude-sandbox",
            image="python:3.11-slim",
            ports={"9876": 9876},
            environment={
                "PYTHONPATH": "/workspace",
                "TERM": "xterm-256color",
            },
            volumes={
                str(Path.cwd()): "/workspace",
            },
            working_dir="/workspace",
        )
        
        return SandboxConfig(
            container=container_config,
            web_port=9876,
            auto_commit=True,
            claude_flags=["--dangerously-skip-permissions"],
        )
    
    def get_env_var(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default."""
        return os.getenv(name, default)