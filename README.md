# Python Claude Code Sandbox

A Python implementation of Claude Code Sandbox - run Claude AI in isolated Podman/Docker containers with autonomous capabilities and real-time monitoring.

## Prerequisites

- Python 3.11+
- Podman (recommended) or Docker
- Git
- GitHub CLI (`gh`)
- Claude Code CLI

## Quick Setup

### 1. Clone and Install

```bash
git clone https://github.com/your-repo/py-claude-sandbox.git
cd py-claude-sandbox
uv sync  # or pip install -e ".[dev]"
```

### 2. Authentication Setup

```bash
# Login to GitHub CLI
gh auth login

# Login to Claude Code CLI
claude login
```

### 3. Environment Setup

Create a `.env` file in the project root:

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
# ANTHROPIC_API_KEY=your_api_key_here
# GITHUB_TOKEN=your_github_token_here
```

### 4. Container Management with Makefile

```bash
# Build the development container
make build

# Run the container (requires .env file)
make run

# Get a shell inside the running container
make shell

# Stop and remove the container
make stop_and_remove
```

## Development Workflow

### Container Operations

The Makefile provides convenient commands for managing the development container:

- `make build` - Build the container image with Python, Git, GitHub CLI, and Claude Code CLI
- `make run` - Run the container in detached mode with environment variables from `.env`
- `make shell` - Connect to an interactive shell inside the running container
- `make stop_and_remove` - Stop and remove the container

### Inside the Container

Once you have a shell in the container (`make shell`), you can:

```bash
# Verify installations
python --version
git --version
gh --version
claude --version

# Work with the project
cd /usr/src/app
python main.py
```

## Authentication

### GitHub CLI Authentication

```bash
# Login with web browser
gh auth login

# Or use a token
gh auth login --with-token < your_token.txt

# Verify authentication
gh auth status
```

### Claude Code CLI Authentication

```bash
# Login (will prompt for API key)
claude login

# Verify authentication
claude auth status
```

## Project Structure

```
py-claude-sandbox/
├── Dockerfile              # Container definition with all tools
├── Makefile                # Container management commands
├── .env                    # Environment variables (create from .env.example)
├── main.py                 # Main application entry point
├── pyproject.toml          # Python project configuration
├── uv.lock                 # UV dependency lock file
├── commands/               # Custom Claude Code commands
├── claude-settings/        # Claude Code configuration
├── tests/                  # Test suite
└── docs/                   # Documentation
```

## Features

- **Isolated Development** - Run Claude in secure Podman containers
- **Pre-configured Environment** - Python, Git, GitHub CLI, and Claude Code CLI ready to use
- **Environment Management** - Easy credential and configuration management
- **Development Tools** - Testing, linting, and pre-commit hooks included

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