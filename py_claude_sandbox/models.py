"""Type definitions for py-claude-sandbox."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class ContainerStatus(str, Enum):
    """Container status enum."""
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"


class CredentialType(str, Enum):
    """Credential type enum."""
    ANTHROPIC = "anthropic"
    GITHUB = "github"
    OPENAI = "openai"
    GOOGLE = "google"
    AWS = "aws"


@dataclass
class Credential:
    """Credential data."""
    type: CredentialType
    name: str
    value: str
    file_path: Optional[str] = None


class ContainerConfig(BaseModel):
    """Container configuration."""
    name: str
    image: str = "python:3.11-slim"
    ports: Dict[str, int] = {}
    environment: Dict[str, str] = {}
    volumes: Dict[str, str] = {}
    working_dir: str = "/workspace"
    command: Optional[List[str]] = None


class SandboxConfig(BaseModel):
    """Sandbox configuration."""
    container: ContainerConfig
    credentials: List[Credential] = []
    git_repo: Optional[str] = None
    git_branch: Optional[str] = None
    web_port: int = 9876
    auto_commit: bool = True
    claude_flags: List[str] = ["--dangerously-skip-permissions"]