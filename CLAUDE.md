# Claude Code Configuration

## IMPORTANT: Todo File Management

Claude must work with a todo file to show its current status and progress. The file should be named `claude_todo.json`.

### Todo File Format

```json
{
  "description": "Task description here",
  "todos": [
    {
      "description": "Todo item description",
      "status": "open"
    },
    {
      "description": "Another todo item",
      "status": "working"
    }
  ]
}
```

### Status Values
- `open`: Todo item is planned but not started
- `working`: Currently working on this todo item
- `done`: Todo item is completed
- `reviewed`: Todo item has been completed and reviewed

### Claude's Required Workflow

1. **Create and plan**: Create a todo list and write it in JSON format to `claude_todo.json`
2. **Work sequentially**: Work on each todo item consequently
3. **Update progress**: After each step, update the todo list status
4. **Review**: Review all items at the end and mark them as reviewed

This ensures transparency and allows tracking of Claude's progress on any given command or task.

## Git Configuration

When working with git operations, always use HTTPS URLs instead of SSH to avoid authentication issues in containerized environments.

### Git Remote URL Format
- Use: `https://github.com/user/repo.git`
- Avoid: `git@github.com:user/repo.git`

### Commands to Check and Fix Git Remotes

To check current remote URLs:
```bash
git remote -v
```

To change SSH remote to HTTPS:
```bash
git remote set-url origin https://github.com/username/repository.git
```

To change HTTPS remote to use token authentication:
```bash
git remote set-url origin https://token@github.com/username/repository.git
```

### GitHub CLI Integration

The GitHub CLI (`gh`) is available and configured to work with HTTPS authentication. Use `gh` commands for GitHub operations when possible:

```bash
# Clone using gh (automatically uses HTTPS)
gh repo clone username/repository

# Create pull requests
gh pr create --title "Title" --body "Description"

# View repository info
gh repo view
```

### Task Runner Configuration

The task runner should prefer HTTPS remotes for any git operations to ensure compatibility with containerized environments and CI/CD systems.

### Lint and Type Check Commands

To maintain code quality, run these commands after making changes:

```bash
# For Python projects
python -m pytest tests/
python -m flake8 src/
python -m mypy src/

# If using uv
uv run pytest tests/
uv run ruff check src/
uv run mypy src/
```

### Container Environment Notes

When running in Docker containers:
- SSH keys may not be available
- HTTPS with token authentication is preferred
- GitHub CLI is pre-configured for HTTPS operations
- Use environment variables for sensitive tokens