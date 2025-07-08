# Claude Code Containerized Development Environment

## Overview

A containerized development environment that integrates Claude Code with GitHub workflows, allowing developers to create isolated environments for AI-assisted development.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                        │
│                    (NiceGUI Web Application)                  │
├─────────────────────────────────────────────────────────────┤
│                      Container Manager                        │
│                    (Python + Podman API)                      │
├─────────────────────────────────────────────────────────────┤
│                          CLI Tool                             │
│                   (Click/Typer Framework)                     │
├─────────────────────────────────────────────────────────────┤
│                     Container Runtime                         │
│                         (Podman)                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Container Management Service (`container_manager.py`)

```python
import asyncio
from typing import List, Dict, Optional
import podman
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ContainerInfo:
    id: str
    name: str
    image: str
    status: str
    created_at: datetime
    github_repo: Optional[str] = None
    issue_number: Optional[int] = None

class ContainerManager:
    def __init__(self):
        self.client = podman.PodmanClient()
        
    async def list_containers(self) -> List[ContainerInfo]:
        """List all Claude Code containers"""
        containers = []
        for container in self.client.containers.list(all=True):
            if container.labels.get('claude-code-env') == 'true':
                containers.append(ContainerInfo(
                    id=container.id[:12],
                    name=container.name,
                    image=container.image.tags[0] if container.image.tags else 'unknown',
                    status=container.status,
                    created_at=container.attrs['Created'],
                    github_repo=container.labels.get('github-repo'),
                    issue_number=int(container.labels.get('issue-number', 0))
                ))
        return containers
    
    async def create_container(self, github_repo: str, issue_number: int) -> str:
        """Create a new development container"""
        container_name = f"claude-dev-{github_repo.split('/')[-1]}-issue-{issue_number}"
        
        # Build custom image with Claude Code and dependencies
        image = self._build_image(github_repo)
        
        # Create container with necessary environment
        container = self.client.containers.run(
            image=image,
            name=container_name,
            detach=True,
            tty=True,
            stdin_open=True,
            environment={
                'GITHUB_TOKEN': '${GITHUB_TOKEN}',
                'ANTHROPIC_API_KEY': '${ANTHROPIC_API_KEY}',
                'GITHUB_REPO': github_repo,
                'ISSUE_NUMBER': str(issue_number)
            },
            labels={
                'claude-code-env': 'true',
                'github-repo': github_repo,
                'issue-number': str(issue_number)
            },
            volumes={
                '/var/run/docker.sock': {'bind': '/var/run/docker.sock', 'mode': 'rw'},
                '~/.ssh': {'bind': '/home/developer/.ssh', 'mode': 'ro'}
            }
        )
        
        return container.id
    
    async def get_container_terminal(self, container_id: str):
        """Get terminal access to a container"""
        container = self.client.containers.get(container_id)
        return container.exec_run('/bin/bash', tty=True, stdin=True, stream=True)
    
    def _build_image(self, github_repo: str) -> str:
        """Build custom Docker image for the project"""
        dockerfile_content = '''
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code
RUN pip install claude-code

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt update && apt install gh -y

# Create development user
RUN useradd -m -s /bin/bash developer
USER developer
WORKDIR /home/developer

# Clone the repository
ARG GITHUB_REPO
RUN git clone https://github.com/${GITHUB_REPO}.git project

WORKDIR /home/developer/project

# Install project dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip install --user -r requirements.txt; fi

# Setup Claude Code configuration
RUN mkdir -p ~/.claude-code && \
    echo '{"auto_commit": false, "pr_creation": true}' > ~/.claude-code/config.json

CMD ["/bin/bash"]
'''
        # Build image logic here
        return f"claude-dev-{github_repo.split('/')[-1]}:latest"
```

### 2. Web UI Application (`ui_app.py`)

```python
from nicegui import ui, app
from container_manager import ContainerManager
import asyncio
from datetime import datetime

class ClaudeDevUI:
    def __init__(self):
        self.manager = ContainerManager()
        self.current_terminal = None
        
    async def build_ui(self):
        ui.dark_mode().enable()
        
        with ui.header(elevated=True).style('background-color: #1a1a1a'):
            ui.label('Claude Code Container Environment').classes('text-h4')
            ui.space()
            with ui.row():
                ui.button('Refresh', on_click=self.refresh_containers).props('flat')
                ui.button('New Container', on_click=self.show_create_dialog).props('flat')
        
        # Container list
        with ui.splitter(value=30).classes('w-full h-screen') as splitter:
            with splitter.before:
                ui.label('Containers').classes('text-h6 q-pa-md')
                self.container_list = ui.column().classes('w-full')
                
            with splitter.after:
                self.terminal_container = ui.column().classes('w-full h-full')
                
        await self.refresh_containers()
    
    async def refresh_containers(self):
        self.container_list.clear()
        containers = await self.manager.list_containers()
        
        with self.container_list:
            for container in containers:
                with ui.card().classes('w-full cursor-pointer').on('click', 
                    lambda c=container: self.connect_to_container(c)):
                    with ui.row().classes('w-full items-center'):
                        ui.icon('computer', size='lg')
                        with ui.column().classes('flex-grow'):
                            ui.label(container.name).classes('text-weight-bold')
                            ui.label(f'Repo: {container.github_repo}').classes('text-caption')
                            ui.label(f'Issue: #{container.issue_number}').classes('text-caption')
                        ui.badge(container.status, 
                            color='green' if container.status == 'running' else 'grey')
    
    async def connect_to_container(self, container):
        self.terminal_container.clear()
        with self.terminal_container:
            ui.label(f'Terminal - {container.name}').classes('text-h6 q-pa-md')
            
            # Terminal emulator component
            terminal = ui.html('''
                <div id="terminal" style="width: 100%; height: 600px; background: black;"></div>
                <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"></script>
                <link href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" rel="stylesheet">
                <script>
                    const term = new Terminal({
                        cursorBlink: true,
                        fontSize: 14,
                        fontFamily: 'Consolas, monospace'
                    });
                    term.open(document.getElementById('terminal'));
                    
                    // WebSocket connection to container
                    const ws = new WebSocket(`ws://localhost:8080/terminal/${container.id}`);
                    ws.onmessage = (event) => term.write(event.data);
                    term.onData((data) => ws.send(data));
                </script>
            ''')
            
            # Quick actions
            with ui.row().classes('q-pa-md'):
                ui.button('Start Claude Code', 
                    on_click=lambda: self.run_command(container.id, 'claude-code'))
                ui.button('Check Issue', 
                    on_click=lambda: self.run_command(container.id, f'gh issue view {container.issue_number}'))
                ui.button('Git Status', 
                    on_click=lambda: self.run_command(container.id, 'git status'))
    
    def show_create_dialog(self):
        with ui.dialog() as dialog, ui.card():
            ui.label('Create New Container').classes('text-h6')
            
            repo_input = ui.input('GitHub Repository', 
                placeholder='owner/repo').classes('w-full')
            issue_input = ui.number('Issue Number', 
                min=1, step=1).classes('w-full')
            
            with ui.row():
                ui.button('Cancel', on_click=dialog.close)
                ui.button('Create', on_click=lambda: self.create_container(
                    repo_input.value, int(issue_input.value), dialog))
    
    async def create_container(self, repo, issue, dialog):
        dialog.close()
        ui.notify(f'Creating container for {repo} issue #{issue}...')
        
        container_id = await self.manager.create_container(repo, issue)
        await self.refresh_containers()
        
        ui.notify('Container created successfully!', type='positive')

# Run the app
app.on_startup(lambda: ClaudeDevUI().build_ui())
ui.run(port=8080, title='Claude Dev Environment')
```

### 3. CLI Tool (`claude_dev_cli.py`)

```python
import click
import asyncio
from container_manager import ContainerManager
import subprocess
import os

@click.group()
def cli():
    """Claude Code Containerized Development Environment CLI"""
    pass

@cli.command()
@click.option('--repo', '-r', required=True, help='GitHub repository (owner/repo)')
@click.option('--issue', '-i', required=True, type=int, help='Issue number to work on')
@click.option('--start-ui', is_flag=True, help='Start the web UI after creating container')
def create(repo, issue, start_ui):
    """Create a new development container"""
    click.echo(f"Creating container for {repo} issue #{issue}...")
    
    manager = ContainerManager()
    container_id = asyncio.run(manager.create_container(repo, issue))
    
    click.echo(f"✓ Container created: {container_id[:12]}")
    
    if start_ui:
        click.echo("Starting web UI...")
        subprocess.Popen(['python', 'ui_app.py'])
        click.echo("Web UI available at http://localhost:8080")

@cli.command()
def list():
    """List all Claude Code containers"""
    manager = ContainerManager()
    containers = asyncio.run(manager.list_containers())
    
    if not containers:
        click.echo("No containers found.")
        return
    
    click.echo("Active Containers:")
    click.echo("-" * 80)
    
    for container in containers:
        click.echo(f"ID: {container.id}")
        click.echo(f"Name: {container.name}")
        click.echo(f"Repository: {container.github_repo}")
        click.echo(f"Issue: #{container.issue_number}")
        click.echo(f"Status: {container.status}")
        click.echo("-" * 80)

@cli.command()
@click.argument('container_id')
def connect(container_id):
    """Connect to a container's terminal"""
    subprocess.run(['podman', 'exec', '-it', container_id, '/bin/bash'])

@cli.command()
@click.argument('container_id')
def workflow(container_id):
    """Run the complete Claude Code workflow"""
    click.echo("Starting Claude Code workflow...")
    
    # Connect to container and run workflow script
    workflow_script = '''
    #!/bin/bash
    echo "🤖 Starting Claude Code..."
    
    # Authenticate with GitHub
    gh auth status || gh auth login
    
    # Get issue details
    ISSUE_NUM=${ISSUE_NUMBER}
    ISSUE_TITLE=$(gh issue view $ISSUE_NUM --json title -q .title)
    
    echo "📋 Working on: $ISSUE_TITLE"
    
    # Create feature branch
    git checkout -b "claude-issue-$ISSUE_NUM"
    
    # Start Claude Code with issue context
    claude-code --prompt "Please work on GitHub issue #$ISSUE_NUM: $ISSUE_TITLE. 
    Review the issue details, implement the necessary changes, and prepare a pull request."
    
    # Create pull request
    echo "🔄 Creating pull request..."
    gh pr create --title "Fix #$ISSUE_NUM: $ISSUE_TITLE" \
                 --body "This PR addresses issue #$ISSUE_NUM\n\nImplemented by Claude Code" \
                 --base main
    '''
    
    subprocess.run(['podman', 'exec', '-it', container_id, 'bash', '-c', workflow_script])

@cli.command()
def ui():
    """Start the web UI"""
    subprocess.run(['python', 'ui_app.py'])

if __name__ == '__main__':
    cli()
```

### 4. Container Dockerfile Template

```dockerfile
# Base Dockerfile for Claude Code containers
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    build-essential \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code
RUN pip install claude-code

# Install GitHub CLI
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
    gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
    tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt update && apt install gh -y

# Create development user
RUN useradd -m -s /bin/bash developer && \
    usermod -aG sudo developer && \
    echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER developer
WORKDIR /home/developer

# Setup shell environment
RUN echo 'export PS1="\[\033[1;36m\]claude-dev\[\033[0m\]:\[\033[1;34m\]\w\[\033[0m\]$ "' >> ~/.bashrc && \
    echo 'alias ll="ls -la"' >> ~/.bashrc && \
    echo 'alias gs="git status"' >> ~/.bashrc

# Create workspace directory
RUN mkdir -p ~/workspace

# Entrypoint script
COPY --chown=developer:developer entrypoint.sh /home/developer/
RUN chmod +x /home/developer/entrypoint.sh

ENTRYPOINT ["/home/developer/entrypoint.sh"]
CMD ["/bin/bash"]
```

### 5. Entrypoint Script (`entrypoint.sh`)

```bash
#!/bin/bash

# Setup GitHub authentication
if [ -n "$GITHUB_TOKEN" ]; then
    echo $GITHUB_TOKEN | gh auth login --with-token
fi

# Setup Claude Code with API key
if [ -n "$ANTHROPIC_API_KEY" ]; then
    mkdir -p ~/.claude-code
    echo "{\"api_key\": \"$ANTHROPIC_API_KEY\"}" > ~/.claude-code/credentials.json
fi

# Clone repository if specified
if [ -n "$GITHUB_REPO" ]; then
    cd ~/workspace
    if [ ! -d "project" ]; then
        git clone "https://github.com/$GITHUB_REPO.git" project
    fi
    cd project
    
    # Fetch latest changes
    git fetch origin
    
    # Install Python dependencies if present
    if [ -f "requirements.txt" ]; then
        pip install --user -r requirements.txt
    fi
fi

# Display welcome message
echo "🚀 Claude Code Development Environment Ready!"
echo "Repository: $GITHUB_REPO"
echo "Issue: #$ISSUE_NUMBER"
echo ""
echo "Quick commands:"
echo "  claude-code         - Start Claude Code"
echo "  gh issue view \$num  - View GitHub issue"
echo "  gh pr create        - Create pull request"
echo ""

exec "$@"
```

## Setup Instructions

### 1. Prerequisites

```bash
# Install Podman
sudo apt-get update
sudo apt-get install -y podman

# Install Python dependencies
pip install nicegui podman-py click asyncio
```

### 2. Environment Variables

Create a `.env` file:

```bash
GITHUB_TOKEN=your_github_personal_access_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 3. Initial Setup

```bash
# Clone this repository
git clone your-repo/claude-dev-env
cd claude-dev-env

# Install the CLI tool
pip install -e .

# Start the container manager service
python container_manager.py &

# Launch the UI
claude-dev ui
```

## Usage Workflow

### 1. Create a GitHub Issue

```bash
# Using GitHub CLI
gh issue create --title "Add user authentication" --body "Implement JWT-based auth"
```

### 2. Create Development Container

```bash
# Using CLI
claude-dev create --repo myorg/myproject --issue 42 --start-ui

# Or use the web UI
claude-dev ui
# Then click "New Container" and fill in the details
```

### 3. Connect and Work

In the web UI:
1. Click on your container
2. The terminal will open automatically
3. Click "Start Claude Code" or type `claude-code` in the terminal
4. Claude will read the issue and start working

### 4. Review and Merge

Once Claude creates the PR:
```bash
# Review the PR
gh pr view

# Test locally
git checkout pr-branch
pytest

# Merge if satisfied
gh pr merge
```

## Advanced Features

### Custom Project Templates

Create project-specific Dockerfiles:

```python
# In container_manager.py
def get_dockerfile_for_project(self, repo: str) -> str:
    """Select appropriate Dockerfile based on project type"""
    # Detect project type from repo
    if "django" in repo:
        return "dockerfiles/django.Dockerfile"
    elif "fastapi" in repo:
        return "dockerfiles/fastapi.Dockerfile"
    # etc...
```

### Persistent Volumes

Mount volumes for caching dependencies:

```python
volumes = {
    '~/.cache/pip': {'bind': '/home/developer/.cache/pip', 'mode': 'rw'},
    '~/.npm': {'bind': '/home/developer/.npm', 'mode': 'rw'},
}
```

### Multi-Container Workflows

Support for microservices:

```python
async def create_service_containers(self, compose_file: str):
    """Create multiple containers from docker-compose.yml"""
    # Implementation for complex projects
```

## Security Considerations

1. **Credential Management**: Use Podman secrets for sensitive data
2. **Network Isolation**: Create separate networks for each project
3. **Resource Limits**: Set CPU/memory limits per container
4. **Access Control**: Implement user authentication for the web UI

## Monitoring and Logging

```python
# Add to container_manager.py
async def get_container_logs(self, container_id: str, tail: int = 100):
    """Retrieve container logs"""
    container = self.client.containers.get(container_id)
    return container.logs(tail=tail, stream=False)

async def get_container_stats(self, container_id: str):
    """Get container resource usage"""
    container = self.client.containers.get(container_id)
    return container.stats(stream=False)
```

## Future Enhancements

1. **VSCode Integration**: Launch VSCode connected to containers
2. **CI/CD Pipeline**: Automatic testing before PR creation
3. **Team Collaboration**: Share containers between developers
4. **Template Library**: Pre-configured environments for common frameworks
5. **Issue Analytics**: Track time spent and code changes per issue
6. **Backup/Restore**: Save and restore container states