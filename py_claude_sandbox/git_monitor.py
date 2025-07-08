"""Git monitoring and commit notifications for py-claude-sandbox."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from git import Repo, InvalidGitRepositoryError
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from py_claude_sandbox.models import ContainerStatus


class GitCommit:
    """Represents a git commit."""
    
    def __init__(self, hash: str, message: str, author: str, date: datetime):
        """Initialize git commit."""
        self.hash = hash
        self.message = message
        self.author = author
        self.date = date
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "hash": self.hash,
            "message": self.message,
            "author": self.author,
            "date": self.date.isoformat(),
        }


class GitFileHandler(FileSystemEventHandler):
    """File system event handler for git changes."""
    
    def __init__(self, git_monitor: "GitMonitor"):
        """Initialize handler."""
        self.git_monitor = git_monitor
    
    def on_modified(self, event):
        """Handle file modification."""
        if not event.is_directory and event.src_path.endswith(('.py', '.js', '.ts', '.md', '.txt')):
            asyncio.create_task(self.git_monitor.check_for_changes())


class GitMonitor:
    """Monitors git repositories for changes and commits."""
    
    def __init__(self, container_id: str, repo_path: str):
        """Initialize git monitor."""
        self.container_id = container_id
        self.repo_path = Path(repo_path)
        self.repo: Optional[Repo] = None
        self.observer: Optional[Observer] = None
        self.callbacks: List[callable] = []
        self.last_commit_hash: Optional[str] = None
        
        # Initialize repository
        self._init_repo()
    
    def _init_repo(self) -> None:
        """Initialize git repository."""
        try:
            self.repo = Repo(self.repo_path)
            self.last_commit_hash = self.repo.head.commit.hexsha
        except InvalidGitRepositoryError:
            self.repo = None
    
    def is_git_repo(self) -> bool:
        """Check if path is a git repository."""
        return self.repo is not None
    
    def get_status(self) -> Dict[str, List[str]]:
        """Get git status."""
        if not self.repo:
            return {"error": ["Not a git repository"]}
        
        try:
            status = {
                "modified": [],
                "added": [],
                "deleted": [],
                "untracked": [],
            }
            
            # Get modified files
            for item in self.repo.index.diff(None):
                if item.change_type == 'M':
                    status["modified"].append(item.a_path)
                elif item.change_type == 'A':
                    status["added"].append(item.a_path)
                elif item.change_type == 'D':
                    status["deleted"].append(item.a_path)
            
            # Get untracked files
            status["untracked"] = self.repo.untracked_files
            
            return status
        except Exception as e:
            return {"error": [str(e)]}
    
    def get_recent_commits(self, count: int = 10) -> List[GitCommit]:
        """Get recent commits."""
        if not self.repo:
            return []
        
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=count):
                commits.append(GitCommit(
                    hash=commit.hexsha[:8],
                    message=commit.message.strip(),
                    author=commit.author.name,
                    date=datetime.fromtimestamp(commit.committed_date),
                ))
            return commits
        except Exception:
            return []
    
    def get_commit_diff(self, commit_hash: str) -> str:
        """Get diff for a specific commit."""
        if not self.repo:
            return "Not a git repository"
        
        try:
            commit = self.repo.commit(commit_hash)
            if commit.parents:
                diff = commit.diff(commit.parents[0])
                return str(diff)
            else:
                # First commit
                return str(commit.diff(None))
        except Exception as e:
            return f"Error getting diff: {e}"
    
    def get_branch_info(self) -> Dict[str, str]:
        """Get current branch information."""
        if not self.repo:
            return {"error": "Not a git repository"}
        
        try:
            return {
                "current_branch": self.repo.active_branch.name,
                "remote": str(self.repo.remote()) if self.repo.remotes else "No remote",
                "ahead": len(list(self.repo.iter_commits('origin/main..HEAD'))) if self.repo.remotes else 0,
                "behind": len(list(self.repo.iter_commits('HEAD..origin/main'))) if self.repo.remotes else 0,
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def check_for_changes(self) -> None:
        """Check for git changes and notify callbacks."""
        if not self.repo:
            return
        
        try:
            # Check for new commits
            current_commit = self.repo.head.commit.hexsha
            if current_commit != self.last_commit_hash:
                self.last_commit_hash = current_commit
                
                # Get the new commit
                commit = self.repo.commit(current_commit)
                git_commit = GitCommit(
                    hash=commit.hexsha[:8],
                    message=commit.message.strip(),
                    author=commit.author.name,
                    date=datetime.fromtimestamp(commit.committed_date),
                )
                
                # Notify callbacks
                for callback in self.callbacks:
                    await callback("new_commit", git_commit)
            
            # Check for file changes
            status = self.get_status()
            if any(status.get(key, []) for key in ["modified", "added", "deleted", "untracked"]):
                for callback in self.callbacks:
                    await callback("file_changes", status)
        
        except Exception as e:
            for callback in self.callbacks:
                await callback("error", str(e))
    
    def add_callback(self, callback: callable) -> None:
        """Add a callback for git events."""
        self.callbacks.append(callback)
    
    def start_monitoring(self) -> None:
        """Start monitoring git repository."""
        if not self.repo_path.exists():
            return
        
        self.observer = Observer()
        handler = GitFileHandler(self)
        self.observer.schedule(handler, str(self.repo_path), recursive=True)
        self.observer.start()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring git repository."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
    
    def create_branch(self, branch_name: str) -> bool:
        """Create a new git branch."""
        if not self.repo:
            return False
        
        try:
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            return True
        except Exception:
            return False
    
    def switch_branch(self, branch_name: str) -> bool:
        """Switch to a git branch."""
        if not self.repo:
            return False
        
        try:
            self.repo.git.checkout(branch_name)
            return True
        except Exception:
            return False
    
    def commit_changes(self, message: str) -> bool:
        """Commit current changes."""
        if not self.repo:
            return False
        
        try:
            # Add all changes
            self.repo.git.add(A=True)
            
            # Commit
            self.repo.index.commit(message)
            return True
        except Exception:
            return False


class GitMonitorManager:
    """Manages git monitors for multiple containers."""
    
    def __init__(self):
        """Initialize git monitor manager."""
        self.monitors: Dict[str, GitMonitor] = {}
    
    def create_monitor(self, container_id: str, repo_path: str) -> GitMonitor:
        """Create a git monitor for a container."""
        monitor = GitMonitor(container_id, repo_path)
        self.monitors[container_id] = monitor
        return monitor
    
    def get_monitor(self, container_id: str) -> Optional[GitMonitor]:
        """Get git monitor for a container."""
        return self.monitors.get(container_id)
    
    def remove_monitor(self, container_id: str) -> None:
        """Remove git monitor for a container."""
        if container_id in self.monitors:
            self.monitors[container_id].stop_monitoring()
            del self.monitors[container_id]
    
    def cleanup_all(self) -> None:
        """Clean up all git monitors."""
        for monitor in self.monitors.values():
            monitor.stop_monitoring()
        self.monitors.clear()