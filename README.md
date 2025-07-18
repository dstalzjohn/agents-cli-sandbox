# Claude Code Development Container

A containerized development environment for working with Claude Code CLI in an isolated, reproducible setup.

## What This Is

This repository provides a **Podman/Docker container** that comes pre-configured with:

- **Python 3.11** development environment
- **Git** for version control
- **GitHub CLI** (`gh`) for GitHub operations
- **Claude Code CLI** for AI-assisted development
- **Custom Claude commands** for enhanced workflows

## Prerequisites

- **Podman** (recommended) or Docker
- **Git** (for cloning this repository)

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-repo/py-claude-sandbox.git
cd py-claude-sandbox
```

### 2. Create Environment File

```bash
# Create .env file with your credentials
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GITHUB_TOKEN=your_github_token_here
EOF
```

### 3. Container Management

```bash
# Build the container image
make build

# Run the container in detached mode
make run

# Get an interactive shell inside the container
make shell

# Stop the container
make stop

# Remove the container
make remove

# Stop and remove in one command
make stop_and_remove
```

## Inside the Container

Once you run `make shell`, you'll be in a fully configured development environment:

### Available Tools

```bash
# Verify installations
python --version     # Python 3.11
git --version        # Git
gh --version         # GitHub CLI
claude --version     # Claude Code CLI
```

### Authentication

The container automatically loads your credentials from the `.env` file:

```bash
# GitHub CLI should be authenticated
gh auth status

# Claude Code CLI should be authenticated
claude auth status
```

### Custom Commands

The container includes a custom Claude command located at `/home/devuser/.claude/commands/issue.md`:

- **`claude issue`** - Smart DevOps workflow for handling GitHub issues and PR feedback

## Project Structure

```
py-claude-sandbox/
├── Dockerfile              # Container definition
├── Makefile               # Container management commands
├── .env                   # Environment variables (you create this)
├── README.md              # This file
├── claude-settings/       # Claude Code CLI configuration
│   └── settings.json      # Permissions and settings
└── commands/              # Custom Claude commands
    └── issue.md           # GitHub issue workflow command
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make build` | Build the container image |
| `make run` | Run container in detached mode |
| `make shell` | Open interactive shell in container |
| `make stop` | Stop the running container |
| `make remove` | Remove the container |
| `make stop_and_remove` | Stop and remove container |

## Environment Variables

Create a `.env` file in the project root with:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional (for GitHub integration)
GITHUB_TOKEN=your_github_token_here
```

## Usage Examples

### Working with GitHub Issues

```bash
# Inside the container
claude issue https://github.com/owner/repo/issues/123
```

This will intelligently handle the issue by either:
- Improving an existing PR based on review feedback
- Creating a new PR implementation from scratch

### Regular Development

```bash
# Start a new Claude session
claude

# Use Claude with specific files
claude --file src/main.py --file tests/test_main.py

# Work with a specific repository
git clone https://github.com/user/repo.git
cd repo
claude
```

## Custom Commands

### Issue Command

The `issue` command provides a smart DevOps workflow:

- **Detects existing PRs** for the issue
- **Analyzes review feedback** and creates improvement checklists
- **Implements fixes** based on review comments
- **Creates new PRs** with comprehensive templates
- **Follows TDD approach** for new features

## Troubleshooting

### Container Issues

```bash
# Check if container is running
podman ps

# View container logs
podman logs my-dev-client

# Inspect container
podman inspect my-dev-client
```

### Authentication Issues

```bash
# Re-authenticate GitHub CLI
gh auth login

# Re-authenticate Claude Code CLI
claude login
```

### Permission Issues

```bash
# Check file permissions
ls -la /home/devuser/.claude/

# The container runs as non-root user 'devuser'
whoami  # Should show 'devuser'
```

## Why Use This Container?

1. **Isolation** - Keep development tools isolated from your host system
2. **Reproducibility** - Same environment across different machines
3. **Pre-configured** - All tools installed and configured
4. **Custom Commands** - Enhanced workflows for common tasks
5. **Non-root Security** - Runs as unprivileged user

## Contributing

1. Fork the repository
2. Make your changes to the Dockerfile or commands
3. Test with `make build && make run && make shell`
4. Submit a pull request

## License

This project is licensed under the MIT License.