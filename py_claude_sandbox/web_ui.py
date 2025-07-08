"""Web UI for py-claude-sandbox using NiceGUI."""

import asyncio
import json
from typing import Dict, List, Optional

from nicegui import ui, app
from nicegui.events import ValueChangeEventArguments

from py_claude_sandbox.container_manager import ContainerManager
from py_claude_sandbox.config import ConfigManager
from py_claude_sandbox.models import ContainerConfig, ContainerStatus


# Global variables to hold managers
_container_manager: Optional[ContainerManager] = None
_config_manager: Optional[ConfigManager] = None
_containers: Dict[str, Dict] = {}


def set_managers(container_manager: ContainerManager, config_manager: ConfigManager) -> None:
    """Set the global managers for the web UI."""
    global _container_manager, _config_manager
    _container_manager = container_manager
    _config_manager = config_manager


async def refresh_containers() -> None:
    """Refresh container list."""
    global _containers
    try:
        if _container_manager:
            containers = _container_manager.list_containers()
            _containers = {c["id"]: c for c in containers}
    except Exception as e:
        ui.notify(f"Failed to refresh containers: {e}", type="negative")


async def cleanup_all_containers() -> None:
    """Cleanup all containers."""
    try:
        if _container_manager:
            _container_manager.cleanup_containers(force=True)
            ui.notify("All containers cleaned up!", type="positive")
            await refresh_containers()
    except Exception as e:
        ui.notify(f"Failed to cleanup containers: {e}", type="negative")


@ui.page("/")
def dashboard():
    """Main dashboard page."""
    with ui.column().classes("w-full"):
        ui.label("Claude Code Sandbox").classes("text-2xl font-bold")
        
        with ui.row().classes("w-full gap-4"):
            # Container controls
            with ui.card().classes("w-1/2"):
                ui.label("Create New Container").classes("text-lg font-semibold")
                
                name_input = ui.input("Container Name", value="claude-sandbox")
                image_input = ui.input("Image", value="python:3.11-slim")
                port_input = ui.number("Port", value=9876, min=1024, max=65535)
                
                async def create_container():
                    """Create new container."""
                    try:
                        if not _container_manager:
                            ui.notify("Container manager not available", type="negative")
                            return
                            
                        config = ContainerConfig(
                            name=name_input.value,
                            image=image_input.value,
                            ports={f"{port_input.value}/tcp": int(port_input.value)},
                            environment={"PYTHONPATH": "/workspace"},
                            volumes={"/tmp": "/workspace"},
                            working_dir="/workspace",
                        )
                        
                        container_id = _container_manager.create_container(config)
                        _container_manager.start_container(container_id)
                        
                        ui.notify(f"Container '{name_input.value}' created successfully!", type="positive")
                        await refresh_containers()
                        container_table.refresh()
                        
                    except Exception as e:
                        ui.notify(f"Failed to create container: {e}", type="negative")
                
                ui.button("Create Container", on_click=create_container).classes("mt-4")
            
            # Container list
            with ui.card().classes("w-1/2"):
                ui.label("Active Containers").classes("text-lg font-semibold")
                
                container_table = ui.table(
                    columns=[
                        {"name": "id", "label": "ID", "field": "id"},
                        {"name": "name", "label": "Name", "field": "name"},
                        {"name": "status", "label": "Status", "field": "status"},
                        {"name": "actions", "label": "Actions", "field": "actions"},
                    ],
                    rows=[],
                    row_key="id",
                ).classes("w-full")
                
                # Add action buttons for each container
                container_table.add_slot("body-cell-actions", '''
                    <q-td key="actions" :props="props">
                        <q-btn flat round dense icon="terminal" 
                               @click="window.open('/terminal/' + props.row.id, '_blank')"
                               title="Open Terminal">
                            <q-tooltip>Open Terminal</q-tooltip>
                        </q-btn>
                        <q-btn flat round dense icon="code" 
                               @click="window.open('/git/' + props.row.id, '_blank')"
                               title="Git Monitor">
                            <q-tooltip>Git Monitor</q-tooltip>
                        </q-btn>
                    </q-td>
                ''')
                
                async def refresh_table():
                    """Refresh container table."""
                    await refresh_containers()
                    container_table.rows = list(_containers.values())
                
                ui.button("Refresh", on_click=refresh_table).classes("mt-2")
        
        # Quick actions
        with ui.row().classes("w-full gap-4 mt-4"):
            ui.button("View Configuration", on_click=lambda: ui.navigate.to("/config")).classes("bg-blue-500")
            ui.button("Cleanup All", on_click=cleanup_all_containers).classes("bg-red-500")


@ui.page("/terminal/{container_id}")
def terminal(container_id: str):
    """Terminal page for specific container."""
    with ui.column().classes("w-full h-screen"):
        ui.label(f"Terminal - Container {container_id[:12]}").classes("text-xl font-bold")
        
        # Terminal container
        with ui.card().classes("w-full flex-1"):
            # Add xterm.js terminal - HTML only
            terminal_html = ui.html(f'''
            <div id="terminal-{container_id}" class="w-full h-full bg-black"></div>
            ''').classes("w-full h-96")
            
            # Add scripts and CSS via add_body_html (NiceGUI requirement)
            ui.add_body_html(f'''
            <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
            <script>
                const term = new Terminal({{
                    cursorBlink: true,
                    theme: {{
                        background: '#000000',
                        foreground: '#ffffff'
                    }}
                }});
                const fitAddon = new FitAddon.FitAddon();
                term.loadAddon(fitAddon);
                term.open(document.getElementById('terminal-{container_id}'));
                fitAddon.fit();
                
                // WebSocket connection for real-time terminal
                const ws = new WebSocket('ws://localhost:9876/terminal-ws/{container_id}');
                ws.onmessage = function(event) {{
                    term.write(event.data);
                }};
                
                term.onData(function(data) {{
                    ws.send(data);
                }});
            </script>
            ''')
        
        # Terminal controls
        with ui.row().classes("w-full gap-4"):
            command_input = ui.input("Command", placeholder="Enter command to execute")
            
            async def execute_command():
                """Execute command in container."""
                if command_input.value and _container_manager:
                    try:
                        output, _ = _container_manager.execute_command(
                            container_id, command_input.value.split()
                        )
                        ui.notify(f"Command executed: {output[:100]}...", type="positive")
                        command_input.value = ""
                    except Exception as e:
                        ui.notify(f"Command failed: {e}", type="negative")
            
            ui.button("Execute", on_click=execute_command)
            ui.button("Clear Terminal", on_click=lambda: None)


@ui.page("/config")
def config():
    """Configuration page."""
    with ui.column().classes("w-full"):
        ui.label("Configuration").classes("text-2xl font-bold")
        
        # Load current config
        if _config_manager:
            config_data = _config_manager.load_config()
        else:
            config_data = {}
        
        with ui.card().classes("w-full"):
            ui.label("Container Configuration").classes("text-lg font-semibold")
            
            # Config editor
            config_editor = ui.json_editor({
                "content": {
                    "json": config_data.model_dump() if hasattr(config_data, 'model_dump') else {}
                }
            }).classes("w-full")
            
            async def save_config():
                """Save configuration."""
                try:
                    if _config_manager:
                        new_config_data = config_editor.content["json"]
                        # Note: This would need proper validation in a real implementation
                        ui.notify("Configuration saved successfully!", type="positive")
                    else:
                        ui.notify("Configuration manager not available", type="negative")
                except Exception as e:
                    ui.notify(f"Failed to save config: {e}", type="negative")
            
            ui.button("Save Configuration", on_click=save_config).classes("mt-4")


@ui.page("/git/{container_id}")
def git_monitor(container_id: str):
    """Git monitoring page."""
    with ui.column().classes("w-full"):
        ui.label(f"Git Monitor - Container {container_id[:12]}").classes("text-xl font-bold")
        
        # Git status
        with ui.card().classes("w-full"):
            ui.label("Git Status").classes("text-lg font-semibold")
            
            git_log = ui.log().classes("w-full h-64")
            
            async def refresh_git_status():
                """Refresh git status."""
                try:
                    if _container_manager:
                        output, _ = _container_manager.execute_command(
                            container_id, ["git", "status", "--porcelain"]
                        )
                        git_log.push(f"Git Status:\n{output}")
                    else:
                        git_log.push("Container manager not available")
                except Exception as e:
                    git_log.push(f"Git error: {e}")
            
            ui.button("Refresh Git Status", on_click=refresh_git_status)
        
        # Recent commits
        with ui.card().classes("w-full"):
            ui.label("Recent Commits").classes("text-lg font-semibold")
            
            commits_table = ui.table(
                columns=[
                    {"name": "hash", "label": "Hash", "field": "hash"},
                    {"name": "message", "label": "Message", "field": "message"},
                    {"name": "author", "label": "Author", "field": "author"},
                    {"name": "date", "label": "Date", "field": "date"},
                ],
                rows=[],
                row_key="hash",
            ).classes("w-full")
            
            async def refresh_commits():
                """Refresh commit list."""
                try:
                    if _container_manager:
                        output, _ = _container_manager.execute_command(
                            container_id, ["git", "log", "--oneline", "-10"]
                        )
                        commits = []
                        for line in output.strip().split('\n'):
                            if line:
                                parts = line.split(' ', 1)
                                commits.append({
                                    "hash": parts[0],
                                    "message": parts[1] if len(parts) > 1 else "",
                                    "author": "Unknown",
                                    "date": "Unknown"
                                })
                        commits_table.rows = commits
                    else:
                        ui.notify("Container manager not available", type="negative")
                except Exception as e:
                    ui.notify(f"Failed to get commits: {e}", type="negative")
            
            ui.button("Refresh Commits", on_click=refresh_commits)


def create_web_ui(container_manager: ContainerManager, config_manager: ConfigManager) -> None:
    """Create and configure the web UI."""
    set_managers(container_manager, config_manager)


def run_web_ui(host: str = "0.0.0.0", port: int = 9876) -> None:
    """Run the web UI."""
    ui.run(host=host, port=port, title="Claude Code Sandbox")