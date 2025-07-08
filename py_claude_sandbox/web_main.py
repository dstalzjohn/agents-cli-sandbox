"""Main entry point for the web UI to satisfy NiceGUI requirements."""

import sys
from typing import Optional

from py_claude_sandbox.container_manager import ContainerManager
from py_claude_sandbox.config import ConfigManager
from py_claude_sandbox.web_ui import create_web_ui, run_web_ui


def main(host: str = "0.0.0.0", port: int = 9876, use_podman: bool = True) -> None:
    """Main entry point for the web UI."""
    try:
        container_manager = ContainerManager(use_podman=use_podman)
        config_manager = ConfigManager()
        
        create_web_ui(container_manager, config_manager)
        run_web_ui(host=host, port=port)
        
    except Exception as e:
        print(f"❌ Failed to start web UI: {e}")
        sys.exit(1)


if __name__ in {"__main__", "__mp_main__"}:
    import argparse
    
    parser = argparse.ArgumentParser(description="Start the Claude Code Sandbox Web UI")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=9876, help="Port to bind to")
    parser.add_argument("--no-podman", action="store_true", help="Use Docker instead of Podman")
    
    args = parser.parse_args()
    
    main(host=args.host, port=args.port, use_podman=not args.no_podman)