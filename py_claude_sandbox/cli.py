"""Command-line interface for py-claude-sandbox."""

import socket
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from py_claude_sandbox.config import ConfigManager
from py_claude_sandbox.container_manager import ContainerManager
from py_claude_sandbox.models import ContainerConfig, SandboxConfig

app = typer.Typer(help="Python Claude Code Sandbox - Run Claude in isolated Podman containers")
console = Console()


def _find_available_port(start_port: int = 9877) -> int:
    """Find an available port starting from start_port."""
    port = start_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('127.0.0.1', port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("No available ports found")


@app.command()
def create(
    name: str = typer.Option("claude-sandbox", help="Container name"),
    image: str = typer.Option("python:3.11-slim", help="Container image"),
    repo: Optional[str] = typer.Option(None, help="Git repository URL"),
    branch: Optional[str] = typer.Option(None, help="Git branch"),
    podman: bool = typer.Option(True, help="Use Podman instead of Docker"),
) -> None:
    """Create a new Claude Code sandbox container."""
    config_manager = ConfigManager()
    container_manager = ContainerManager(use_podman=podman)
    
    # Find available port for this container (starting from 9877)
    container_port = _find_available_port()
    console.print(f"Assigning container port: {container_port}", style="blue")
    
    # Create container config with dynamic port
    container_config = ContainerConfig(
        name=name,
        image=image,
        ports={"8888/tcp": container_port},  # Container internal port 8888 -> Host port (dynamic)
        environment={
            "PYTHONPATH": "/workspace",
            "TERM": "xterm-256color",
        },
        volumes={
            str(Path.cwd()): "/workspace",
        },
        working_dir="/workspace",
    )
    
    # Create sandbox config
    sandbox_config = SandboxConfig(
        container=container_config,
        git_repo=repo,
        git_branch=branch,
        web_port=container_port,
    )
    
    try:
        # Create and start container
        container_id = container_manager.create_container(container_config)
        container_manager.start_container(container_id)
        
        # Install Claude Code
        console.print("Installing Claude Code...", style="yellow")
        container_manager.install_claude_code(container_id)
        
        console.print(f"✅ Sandbox '{name}' created successfully!", style="green")
        console.print(f"Container ID: {container_id[:12]}")
        console.print(f"Container accessible on port: {container_port}")
        console.print(f"Manage via Web UI: http://localhost:9876")
        
    except Exception as e:
        console.print(f"❌ Failed to create sandbox: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def start(
    name: str = typer.Argument(..., help="Container name"),
    podman: bool = typer.Option(True, help="Use Podman instead of Docker"),
) -> None:
    """Start a sandbox container."""
    container_manager = ContainerManager(use_podman=podman)
    
    try:
        # Find container by name
        containers = container_manager.list_containers()
        container_id = None
        
        for container in containers:
            if container["name"] == name:
                container_id = container["id"]
                break
        
        if not container_id:
            console.print(f"❌ Container '{name}' not found", style="red")
            raise typer.Exit(1)
        
        container_manager.start_container(container_id)
        console.print(f"✅ Sandbox '{name}' started successfully!", style="green")
        
    except Exception as e:
        console.print(f"❌ Failed to start sandbox: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def stop(
    name: str = typer.Argument(..., help="Container name"),
    podman: bool = typer.Option(True, help="Use Podman instead of Docker"),
) -> None:
    """Stop a sandbox container."""
    container_manager = ContainerManager(use_podman=podman)
    
    try:
        # Find container by name
        containers = container_manager.list_containers()
        container_id = None
        
        for container in containers:
            if container["name"] == name:
                container_id = container["id"]
                break
        
        if not container_id:
            console.print(f"❌ Container '{name}' not found", style="red")
            raise typer.Exit(1)
        
        container_manager.stop_container(container_id)
        console.print(f"✅ Sandbox '{name}' stopped successfully!", style="green")
        
    except Exception as e:
        console.print(f"❌ Failed to stop sandbox: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def remove(
    name: str = typer.Argument(..., help="Container name"),
    force: bool = typer.Option(False, help="Force removal"),
    podman: bool = typer.Option(True, help="Use Podman instead of Docker"),
) -> None:
    """Remove a sandbox container."""
    container_manager = ContainerManager(use_podman=podman)
    
    try:
        # Find container by name
        containers = container_manager.list_containers()
        container_id = None
        
        for container in containers:
            if container["name"] == name:
                container_id = container["id"]
                break
        
        if not container_id:
            console.print(f"❌ Container '{name}' not found", style="red")
            raise typer.Exit(1)
        
        container_manager.remove_container(container_id, force=force)
        console.print(f"✅ Sandbox '{name}' removed successfully!", style="green")
        
    except Exception as e:
        console.print(f"❌ Failed to remove sandbox: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def list(
    podman: bool = typer.Option(True, help="Use Podman instead of Docker"),
) -> None:
    """List all sandbox containers."""
    container_manager = ContainerManager(use_podman=podman)
    
    try:
        containers = container_manager.list_containers()
        
        if not containers:
            console.print("No sandbox containers found", style="yellow")
            return
        
        table = Table(title="Claude Code Sandbox Containers")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Image", style="blue")
        
        for container in containers:
            table.add_row(
                container["id"],
                container["name"],
                container["status"],
                container["image"],
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"❌ Failed to list containers: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def cleanup(
    force: bool = typer.Option(False, help="Force cleanup"),
    podman: bool = typer.Option(True, help="Use Podman instead of Docker"),
) -> None:
    """Clean up all sandbox containers."""
    container_manager = ContainerManager(use_podman=podman)
    
    try:
        container_manager.cleanup_containers(force=force)
        console.print("✅ All sandbox containers cleaned up!", style="green")
        
    except Exception as e:
        console.print(f"❌ Failed to cleanup containers: {e}", style="red")
        raise typer.Exit(1)


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(9876, help="Port to bind to"),
    podman: bool = typer.Option(True, help="Use Podman instead of Docker"),
) -> None:
    """Start the web UI for managing containers."""
    import subprocess
    import sys
    from pathlib import Path
    
    try:
        console.print(f"🚀 Starting web UI at http://{host}:{port}", style="green")
        
        # Get the path to the web_main.py module
        web_main_path = Path(__file__).parent / "web_main.py"
        
        # Build command arguments
        cmd = [
            sys.executable, str(web_main_path),
            "--host", host,
            "--port", str(port)
        ]
        
        if not podman:
            cmd.append("--no-podman")
        
        # Start the web UI in a subprocess
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Web UI process failed with exit code {e.returncode}", style="red")
        raise typer.Exit(e.returncode)
    except KeyboardInterrupt:
        console.print("🛑 Web UI stopped by user", style="yellow")
    except Exception as e:
        console.print(f"❌ Failed to start web UI: {e}", style="red")
        raise typer.Exit(1)


def main() -> None:
    """Main entry point."""
    app()


if __name__ in {"__main__", "__mp_main__"}:
    main()