"""Container management using Podman/Docker for py-claude-sandbox."""

import asyncio
import json
from typing import Dict, List, Optional

import docker
from docker.errors import APIError, NotFound

from py_claude_sandbox.credential_manager import CredentialManager
from py_claude_sandbox.models import ContainerConfig, ContainerStatus


class ContainerManager:
    """Manages Podman/Docker containers for Claude Code sandboxes."""
    
    def __init__(self, use_podman: bool = True):
        """Initialize container manager."""
        self.use_podman = use_podman
        self.client = self._get_client()
        self.credential_manager = CredentialManager()
    
    def _get_client(self) -> docker.DockerClient:
        """Get Docker/Podman client."""
        if self.use_podman:
            # Try to connect to Podman socket
            try:
                return docker.DockerClient(base_url="unix:///run/user/1000/podman/podman.sock")
            except Exception:
                # Fallback to Docker socket
                return docker.from_env()
        else:
            return docker.from_env()
    
    def create_container(self, config: ContainerConfig) -> str:
        """Create a new container."""
        # Discover credentials
        credentials = self.credential_manager.discover_credentials()
        
        # Prepare environment variables
        environment = config.environment.copy()
        environment.update(self.credential_manager.get_environment_vars())
        
        # Prepare volume mounts - convert to Docker SDK format
        volumes = {}
        for host_path, container_path in config.volumes.items():
            volumes[host_path] = {"bind": container_path, "mode": "rw"}
        
        # Add credential manager volumes
        for host_path, container_path in self.credential_manager.get_volume_mounts().items():
            volumes[host_path] = {"bind": container_path, "mode": "rw"}
        
        # Create container
        try:
            # Extract ports for high-level API
            port_bindings = {}
            exposed_ports = []
            
            for container_port, host_port in config.ports.items():
                # Remove protocol if present for exposed ports
                port_num = container_port.split('/')[0] if '/' in container_port else container_port
                exposed_ports.append(int(port_num))
                port_bindings[container_port] = host_port
            
            container = self.client.containers.create(
                image=config.image,
                name=config.name,
                environment=environment,
                volumes=volumes,
                working_dir=config.working_dir,
                command=config.command,
                ports=port_bindings,
                detach=True,
                tty=True,
                stdin_open=True,
            )
            return container.id
        except APIError as e:
            raise RuntimeError(f"Failed to create container: {e}")
    
    def start_container(self, container_id: str) -> None:
        """Start a container."""
        try:
            container = self.client.containers.get(container_id)
            container.start()
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")
        except APIError as e:
            raise RuntimeError(f"Failed to start container: {e}")
    
    def stop_container(self, container_id: str) -> None:
        """Stop a container."""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")
        except APIError as e:
            raise RuntimeError(f"Failed to stop container: {e}")
    
    def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container."""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")
        except APIError as e:
            raise RuntimeError(f"Failed to remove container: {e}")
    
    def get_container_status(self, container_id: str) -> ContainerStatus:
        """Get container status."""
        try:
            container = self.client.containers.get(container_id)
            status = container.status.lower()
            
            if status == "running":
                return ContainerStatus.RUNNING
            elif status in ["created", "restarting"]:
                return ContainerStatus.CREATED
            elif status in ["exited", "dead"]:
                return ContainerStatus.STOPPED
            else:
                return ContainerStatus.FAILED
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")
    
    def execute_command(self, container_id: str, command: List[str]) -> tuple[str, str]:
        """Execute command in container."""
        try:
            container = self.client.containers.get(container_id)
            result = container.exec_run(command, stdout=True, stderr=True)
            return result.output.decode(), ""
        except NotFound:
            raise RuntimeError(f"Container {container_id} not found")
        except APIError as e:
            raise RuntimeError(f"Failed to execute command: {e}")
    
    def install_claude_code(self, container_id: str) -> None:
        """Install Claude Code in container."""
        install_commands = [
            ["apt-get", "update"],
            ["apt-get", "install", "-y", "curl", "git"],
            ["curl", "-fsSL", "https://claude.ai/claude-code/install.sh", "-o", "/tmp/install.sh"],
            ["bash", "/tmp/install.sh"],
        ]
        
        for cmd in install_commands:
            self.execute_command(container_id, cmd)
    
    def list_containers(self) -> List[Dict]:
        """List all containers."""
        containers = []
        
        for container in self.client.containers.list(all=True):
            if "claude-sandbox" in container.name:
                containers.append({
                    "id": container.id[:12],
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown",
                })
        
        return containers
    
    def cleanup_containers(self, force: bool = False) -> None:
        """Clean up all sandbox containers."""
        for container in self.client.containers.list(all=True):
            if "claude-sandbox" in container.name:
                try:
                    container.remove(force=force)
                except APIError:
                    pass  # Ignore errors during cleanup