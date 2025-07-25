# Claude Code Configuration

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