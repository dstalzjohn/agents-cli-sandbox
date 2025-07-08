# py-claude-sandbox Instructions

This guide will help you use py-claude-sandbox with your GitHub repository.

## Architecture Overview

**Port Management:**
- **Web UI Management**: Always runs on port 9876
- **Container Services**: Auto-assigned ports starting from 9877, 9878, etc.
- **No Port Conflicts**: Each container gets its own unique port

**Why This Design:**
- The Web UI acts as a central management interface
- Containers run isolated services on their own ports
- Web UI connects to containers via their assigned ports for terminal/monitoring

## Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install -e .
```

Ensure you have Podman installed and running:
```bash
podman --version
```

## Getting Started

### Option 1: Clone Repository and Create Sandbox

```bash
# Clone your repository
git clone git@github.com:dstalzjohn/flowutils.git
cd flowutils

# Create a sandbox container with your repository
python -m py_claude_sandbox.cli create --name flowutils-sandbox --repo git@github.com:dstalzjohn/flowutils.git
```

### Option 2: Use Existing Local Repository

If you already have the repository cloned locally:

```bash
# Navigate to your repository
cd /path/to/flowutils

# Create sandbox (it will mount current directory as /workspace)
python -m py_claude_sandbox.cli create --name flowutils-sandbox
```

## Container Management

### List Containers
```bash
python -m py_claude_sandbox.cli list
```

### Stop Container
```bash
python -m py_claude_sandbox.cli stop flowutils-sandbox
```

### Start Container
```bash
python -m py_claude_sandbox.cli start flowutils-sandbox
```

### Remove Container
```bash
# Remove stopped container
python -m py_claude_sandbox.cli remove flowutils-sandbox

# Force remove running container
python -m py_claude_sandbox.cli remove flowutils-sandbox --force
```

### Clean Up All Containers
```bash
python -m py_claude_sandbox.cli cleanup --force
```

## Web Interface

### Start Web Management UI
```bash
python -m py_claude_sandbox.cli web
```

This will start a web interface at `http://localhost:9876` where you can:
- Create and manage containers through a GUI
- Access terminal interfaces
- Monitor git changes
- View container configurations

### Access Container Web UI
After creating a container, you can access it directly at:
```
http://localhost:9876
```

### Access Terminal Interface

**Method 1: Direct URL**
Replace `CONTAINER_ID` with your actual container ID:
```
http://localhost:9876/terminal/CONTAINER_ID
```

**Method 2: From Dashboard (Recommended)**
1. Go to `http://localhost:9876`
2. Click "Refresh" to see your containers
3. Click the terminal icon (📟) in the Actions column
4. This will open the terminal in a new tab

**Method 3: Command Execution**
On the main dashboard, you can also execute individual commands:
1. Find the command input field
2. Type your command (e.g., `ls -la`)
3. Click "Execute"

**Finding Your Container ID:**
```bash
python -m py_claude_sandbox.cli list
```
Or check with Podman directly:
```bash
podman ps
```

**Port Information:**
When you create a container, you'll see output like:
```
Assigning container port: 9877
Container accessible on port: 9877
Manage via Web UI: http://localhost:9876
```
- Container port 9877 is for container services
- Web UI port 9876 is for management interface

## Container Environment

When you create a container, it includes:

- **Base Image**: Python 3.11-slim
- **Working Directory**: `/workspace` (your repository)
- **Port**: 9876 exposed for web interface
- **Environment Variables**:
  - `PYTHONPATH=/workspace`
  - `TERM=xterm-256color`
- **Pre-installed**: Claude Code CLI
- **Volume Mount**: Your local repository → `/workspace`

## Available CLI Commands

### create
Create a new sandbox container:
```bash
python -m py_claude_sandbox.cli create [OPTIONS]
```

**Options:**
- `--name TEXT`: Container name (default: claude-sandbox)
- `--image TEXT`: Container image (default: python:3.11-slim)
- `--port INTEGER`: Web UI port (default: 9876)
- `--repo TEXT`: Git repository URL
- `--branch TEXT`: Git branch
- `--podman/--no-podman`: Use Podman vs Docker (default: Podman)

### start
Start a stopped container:
```bash
python -m py_claude_sandbox.cli start CONTAINER_NAME
```

### stop
Stop a running container:
```bash
python -m py_claude_sandbox.cli stop CONTAINER_NAME
```

### remove
Remove a container:
```bash
python -m py_claude_sandbox.cli remove CONTAINER_NAME [--force]
```

### list
List all sandbox containers:
```bash
python -m py_claude_sandbox.cli list
```

### cleanup
Remove all sandbox containers:
```bash
python -m py_claude_sandbox.cli cleanup [--force]
```

### web
Start the web management interface:
```bash
python -m py_claude_sandbox.cli web [--host HOST] [--port PORT]
```

## Example Workflow

1. **Create sandbox with your repository**:
   ```bash
   python -m py_claude_sandbox.cli create --name flowutils-sandbox
   ```

2. **Verify it's running**:
   ```bash
   python -m py_claude_sandbox.cli list
   ```

3. **Access the web interface**:
   - Open browser to `http://localhost:9876`
   - Use the terminal interface to run commands
   - Your repository files are available at `/workspace`

4. **Work with your code**:
   - Edit files in the web terminal
   - Run tests: `python -m pytest`
   - Install dependencies: `pip install -r requirements.txt`
   - Run your application

5. **Clean up when done**:
   ```bash
   python -m py_claude_sandbox.cli remove flowutils-sandbox --force
   ```

## Troubleshooting

### Container Not Found
- Ensure container name includes "claude-sandbox" (e.g., `flowutils-sandbox`)
- Check if container exists: `podman ps -a`

### Port Already in Use
- Stop other containers using port 9876
- Use different port: `--port 8080`

### Image Not Found
- Pull the image manually: `podman pull python:3.11-slim`
- Check available images: `podman images`

### Permission Issues
- Ensure Podman is running: `podman info`
- Check file permissions in your repository

### Container Won't Start
- Check logs: `podman logs CONTAINER_NAME`
- Try force remove and recreate: `python -m py_claude_sandbox.cli remove CONTAINER_NAME --force`

## Tips

- **Container Naming**: Always include "claude-sandbox" in container names for CLI recognition
- **Port Conflicts**: Use different ports if 9876 is occupied
- **Data Persistence**: Your local files are mounted, so changes persist
- **Multiple Repos**: You can create multiple sandboxes for different repositories
- **Git Integration**: The web interface includes git monitoring features

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify Podman is running and accessible
3. Ensure all dependencies are installed
4. Check container logs for detailed error messages