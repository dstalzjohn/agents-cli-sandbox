# Python Claude Code Sandbox

A Python implementation of Claude Code Sandbox - run Claude AI in isolated Podman/Docker containers with autonomous capabilities and real-time monitoring.

## Features

- **Isolated Sandboxes** - Run Claude in secure Podman/Docker containers
- **Web UI** - Beautiful NiceGUI-based interface for monitoring and control
- **Real-time Terminal** - xterm.js integration for live terminal streaming
- **Git Monitoring** - Automatic commit detection and diff visualization
- **Credential Management** - Automatic discovery and secure forwarding
- **Multi-container Support** - Manage multiple Claude instances simultaneously
- **Pure Python** - No separate frontend/backend, everything in Python

## Installation

### Prerequisites

- Python 3.11+
- Podman or Docker
- Git (optional, for git monitoring)

### Install from Source

```bash
git clone https://github.com/your-repo/py-claude-sandbox.git
cd py-claude-sandbox
pip install -e .
```

### Install Dependencies

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install
```

## Quick Start

### 1. Start the Web UI

```bash
py-claude-sandbox web --host 0.0.0.0 --port 9876
```

Open your browser to `http://localhost:9876` to access the dashboard.

### 2. Create a Container

```bash
# Basic container
py-claude-sandbox create --name my-sandbox

# With git repository
py-claude-sandbox create --name my-project \
    --repo https://github.com/user/repo.git \
    --branch main \
    --port 9876
```

### 3. Manage Containers

```bash
# List containers
py-claude-sandbox list

# Start/stop containers
py-claude-sandbox start my-sandbox
py-claude-sandbox stop my-sandbox

# Remove container
py-claude-sandbox remove my-sandbox --force

# Clean up all containers
py-claude-sandbox cleanup --force
```

## Web Interface

The web UI provides:

### Dashboard
- **Container Management** - Create, start, stop, remove containers
- **Resource Monitoring** - View container status and resource usage
- **Quick Actions** - One-click operations for common tasks

### Terminal Interface
- **Real-time Terminal** - Live terminal streaming with xterm.js
- **Command Execution** - Execute commands directly in containers
- **Copy/Paste Support** - Full terminal interaction capabilities

### Git Monitoring
- **Commit Notifications** - Real-time alerts when Claude makes commits
- **Diff Visualization** - Syntax-highlighted diffs for all changes
- **Branch Management** - View and switch between branches
- **File Status** - Track modified, added, and deleted files

### Configuration
- **JSON Editor** - Edit container and sandbox configurations
- **Credential Management** - Manage API keys and authentication
- **Environment Variables** - Configure container environments

## Configuration

### Default Configuration

The sandbox creates a default configuration file at `~/.py-claude-sandbox.yaml`:

```yaml
container:
  name: claude-sandbox
  image: python:3.11-slim
  ports:
    "9876": 9876
  environment:
    PYTHONPATH: /workspace
    TERM: xterm-256color
  volumes:
    /current/directory: /workspace
  working_dir: /workspace
  command: null

credentials: []
git_repo: null
git_branch: null
web_port: 9876
auto_commit: true
claude_flags:
  - "--dangerously-skip-permissions"
```

### Credential Discovery

The sandbox automatically discovers and forwards credentials:

- **Anthropic API**: `ANTHROPIC_API_KEY` environment variable, `~/.anthropic/config.json`
- **GitHub**: `GITHUB_TOKEN` environment variable, `~/.gitconfig`
- **OpenAI**: `OPENAI_API_KEY` environment variable
- **Google**: `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- **AWS**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `~/.aws/credentials`

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=py_claude_sandbox

# Run specific test file
pytest tests/test_web_ui.py -v

# Run with live logs
pytest -s
```

### Code Quality

```bash
# Format code
ruff format

# Lint code
ruff check

# Run pre-commit hooks
pre-commit run --all-files
```

### Project Structure

```
py-claude-sandbox/
├── py_claude_sandbox/
│   ├── __init__.py
│   ├── cli.py              # Typer CLI interface
│   ├── web_ui.py           # NiceGUI web interface
│   ├── container_manager.py # Podman/Docker management
│   ├── credential_manager.py # Credential discovery
│   ├── git_monitor.py      # Git monitoring and notifications
│   ├── config.py           # Configuration management
│   └── types.py            # Type definitions
├── tests/
│   ├── test_cli.py
│   ├── test_web_ui.py
│   ├── test_container_manager.py
│   ├── test_credential_manager.py
│   ├── test_git_monitor.py
│   └── test_config.py
├── static/                 # Static files for web UI
├── pyproject.toml          # Project configuration
├── .pre-commit-config.yaml # Pre-commit hooks
└── README.md
```

## Security

### Sandboxing
- Containers run in isolated environments
- Volume mounts are restricted to specified directories
- Network access can be controlled per container

### Credential Handling
- Credentials are forwarded securely as environment variables
- Sensitive files are mounted with appropriate permissions
- No credentials are stored in container images

### Claude Permissions
- Uses `--dangerously-skip-permissions` flag for autonomous operation
- Isolated from host system through containerization
- Git operations are contained within the sandbox

## Troubleshooting

### Container Issues

```bash
# Check container logs
podman logs claude-sandbox

# Inspect container
podman inspect claude-sandbox

# Access container directly
podman exec -it claude-sandbox /bin/bash
```

### Web UI Issues

```bash
# Check if port is available
netstat -tlnp | grep :9876

# Start with debug logging
py-claude-sandbox web --host 0.0.0.0 --port 9876 --log-level debug
```

### Git Issues

```bash
# Check git configuration in container
py-claude-sandbox exec my-sandbox git config --list

# Verify git repository
py-claude-sandbox exec my-sandbox git status
```

## API Reference

### CLI Commands

| Command | Description | Options |
|---------|-------------|---------|
| `create` | Create new container | `--name`, `--image`, `--port`, `--repo`, `--branch` |
| `start` | Start container | `--podman/--no-podman` |
| `stop` | Stop container | `--podman/--no-podman` |
| `remove` | Remove container | `--force`, `--podman/--no-podman` |
| `list` | List containers | `--podman/--no-podman` |
| `cleanup` | Clean up all containers | `--force`, `--podman/--no-podman` |
| `web` | Start web UI | `--host`, `--port`, `--podman/--no-podman` |

### Python API

```python
from py_claude_sandbox import ContainerManager, ConfigManager, create_web_ui

# Create managers
container_manager = ContainerManager(use_podman=True)
config_manager = ConfigManager()

# Create container
container_id = container_manager.create_container(config)
container_manager.start_container(container_id)

# Start web UI
web_ui = create_web_ui(container_manager, config_manager)
web_ui.run(host="0.0.0.0", port=8080)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-repo/py-claude-sandbox.git
cd py-claude-sandbox

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Claude Code](https://claude.ai/code) - The original Claude Code tool
- [TextCortex Claude Code Sandbox](https://github.com/textcortex/claude-code-sandbox) - Inspiration for this project
- [NiceGUI](https://nicegui.io/) - Beautiful Python web framework
- [xterm.js](https://xtermjs.org/) - Terminal emulator for the web

## Support

- **Issues**: [GitHub Issues](https://github.com/your-repo/py-claude-sandbox/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/py-claude-sandbox/discussions)
- **Documentation**: [Full Documentation](https://your-repo.github.io/py-claude-sandbox/)

---

**Made with Python**