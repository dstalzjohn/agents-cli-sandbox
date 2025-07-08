"""Tests for git monitoring functionality."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from git import Repo

from py_claude_sandbox.git_monitor import GitMonitor, GitCommit, GitMonitorManager


@pytest.fixture
def temp_git_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        repo = Repo.init(repo_path)
        
        # Create initial commit
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])  # Use relative path
        repo.index.commit("Initial commit")
        
        yield repo_path, repo


@pytest.fixture
def git_monitor(temp_git_repo):
    """Create a git monitor for testing."""
    repo_path, _ = temp_git_repo
    return GitMonitor("test-container", str(repo_path))


def test_git_commit_creation():
    """Test GitCommit creation and serialization."""
    commit = GitCommit(
        hash="abc123",
        message="Test commit",
        author="Test Author",
        date=datetime.now(),
    )
    
    assert commit.hash == "abc123"
    assert commit.message == "Test commit"
    assert commit.author == "Test Author"
    
    # Test serialization
    commit_dict = commit.to_dict()
    assert commit_dict["hash"] == "abc123"
    assert commit_dict["message"] == "Test commit"
    assert commit_dict["author"] == "Test Author"
    assert "date" in commit_dict


def test_git_monitor_initialization(git_monitor):
    """Test git monitor initialization."""
    assert git_monitor.container_id == "test-container"
    assert git_monitor.repo is not None
    assert git_monitor.is_git_repo() is True
    assert git_monitor.last_commit_hash is not None


def test_git_monitor_with_non_git_directory():
    """Test git monitor with non-git directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        monitor = GitMonitor("test-container", temp_dir)
        
        assert monitor.is_git_repo() is False
        assert monitor.repo is None


def test_git_status(git_monitor, temp_git_repo):
    """Test getting git status."""
    repo_path, repo = temp_git_repo
    
    # Create a modified file
    test_file = repo_path / "test.txt"
    test_file.write_text("Modified content")
    
    # Create a new untracked file
    new_file = repo_path / "new.txt"
    new_file.write_text("New content")
    
    status = git_monitor.get_status()
    
    assert "modified" in status
    assert "untracked" in status
    assert "new.txt" in status["untracked"]


def test_get_recent_commits(git_monitor, temp_git_repo):
    """Test getting recent commits."""
    repo_path, repo = temp_git_repo
    
    # Create additional commits
    for i in range(3):
        test_file = repo_path / f"test{i}.txt"
        test_file.write_text(f"Content {i}")
        repo.index.add([f"test{i}.txt"])  # Use relative path
        repo.index.commit(f"Commit {i}")
    
    commits = git_monitor.get_recent_commits(count=5)
    
    assert len(commits) == 4  # 3 new + 1 initial
    assert all(isinstance(commit, GitCommit) for commit in commits)
    assert commits[0].message == "Commit 2"  # Most recent first


def test_get_branch_info(git_monitor):
    """Test getting branch information."""
    branch_info = git_monitor.get_branch_info()
    
    assert "current_branch" in branch_info
    assert branch_info["current_branch"] in ["main", "master"]  # Default branch names


def test_create_branch(git_monitor):
    """Test creating a new branch."""
    result = git_monitor.create_branch("feature-branch")
    
    assert result is True
    
    # Verify branch was created and checked out
    branch_info = git_monitor.get_branch_info()
    assert branch_info["current_branch"] == "feature-branch"


def test_switch_branch(git_monitor):
    """Test switching branches."""
    # Get initial branch info
    initial_branch_info = git_monitor.get_branch_info()
    initial_branch = initial_branch_info["current_branch"]
    
    # Create a branch first
    git_monitor.create_branch("test-branch")
    
    # Verify we're on the new branch
    current_info = git_monitor.get_branch_info()
    assert current_info["current_branch"] == "test-branch"
    
    # Switch back to original branch
    result = git_monitor.switch_branch(initial_branch)
    assert result is True
    
    branch_info = git_monitor.get_branch_info()
    assert branch_info["current_branch"] == initial_branch


def test_commit_changes(git_monitor, temp_git_repo):
    """Test committing changes."""
    repo_path, repo = temp_git_repo
    
    # Create a new file
    new_file = repo_path / "commit_test.txt"
    new_file.write_text("Test commit content")
    
    # Commit changes
    result = git_monitor.commit_changes("Test commit message")
    
    assert result is True
    
    # Verify commit was created
    commits = git_monitor.get_recent_commits(count=1)
    assert len(commits) == 1
    assert commits[0].message == "Test commit message"


@pytest.mark.asyncio
async def test_check_for_changes(git_monitor, temp_git_repo):
    """Test checking for changes."""
    repo_path, repo = temp_git_repo
    
    # Set up callback to capture events
    events = []
    
    async def test_callback(event_type, data):
        events.append((event_type, data))
    
    git_monitor.add_callback(test_callback)
    
    # Create a new commit
    test_file = repo_path / "change_test.txt"
    test_file.write_text("Change test content")
    repo.index.add(["change_test.txt"])  # Use relative path
    repo.index.commit("Change test commit")
    
    # Update the monitor's last commit hash to trigger change detection
    git_monitor.last_commit_hash = "old-hash"
    
    # Check for changes
    await git_monitor.check_for_changes()
    
    # Verify callback was called
    assert len(events) > 0
    assert events[0][0] == "new_commit"
    assert isinstance(events[0][1], GitCommit)


def test_git_monitor_callbacks(git_monitor):
    """Test adding and managing callbacks."""
    callback1 = Mock()
    callback2 = Mock()
    
    git_monitor.add_callback(callback1)
    git_monitor.add_callback(callback2)
    
    assert len(git_monitor.callbacks) == 2
    assert callback1 in git_monitor.callbacks
    assert callback2 in git_monitor.callbacks


def test_git_monitor_manager():
    """Test git monitor manager."""
    manager = GitMonitorManager()
    
    # Test creating a monitor
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Repo.init(temp_dir)  # Create a git repo
        
        # Create initial commit to avoid empty repo issues
        test_file = Path(temp_dir) / "initial.txt"
        test_file.write_text("initial content")
        repo.index.add(["initial.txt"])
        repo.index.commit("Initial commit")
        
        monitor = manager.create_monitor("container1", temp_dir)
        
        assert isinstance(monitor, GitMonitor)
        assert monitor.container_id == "container1"
        assert "container1" in manager.monitors
        
        # Test getting monitor
        retrieved = manager.get_monitor("container1")
        assert retrieved is monitor
        
        # Test removing monitor
        manager.remove_monitor("container1")
        assert "container1" not in manager.monitors
        
        # Test cleanup
        manager.create_monitor("container2", temp_dir)
        manager.cleanup_all()
        assert len(manager.monitors) == 0


def test_git_monitor_with_invalid_repo():
    """Test git monitor error handling with invalid repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a non-git directory
        non_git_path = Path(temp_dir) / "not-a-repo"
        non_git_path.mkdir()
        
        monitor = GitMonitor("test-container", str(non_git_path))
        
        assert monitor.is_git_repo() is False
    
    # Test methods with invalid repo
    status = monitor.get_status()
    assert "error" in status
    
    commits = monitor.get_recent_commits()
    assert len(commits) == 0
    
    branch_info = monitor.get_branch_info()
    assert "error" in branch_info
    
    # Test operations that should fail gracefully
    assert monitor.create_branch("test") is False
    assert monitor.switch_branch("main") is False
    assert monitor.commit_changes("test") is False


def test_git_commit_diff(git_monitor, temp_git_repo):
    """Test getting commit diff."""
    repo_path, repo = temp_git_repo
    
    # Create a new commit
    test_file = repo_path / "diff_test.txt"
    test_file.write_text("Diff test content")
    repo.index.add(["diff_test.txt"])  # Use relative path
    commit = repo.index.commit("Diff test commit")
    
    # Get diff
    diff = git_monitor.get_commit_diff(commit.hexsha)
    
    assert isinstance(diff, str)
    # The diff should contain information about the change
    assert len(diff) > 0


@pytest.mark.asyncio
async def test_file_monitoring(git_monitor):
    """Test file system monitoring."""
    # Test starting monitoring
    git_monitor.start_monitoring()
    assert git_monitor.observer is not None
    
    # Test stopping monitoring
    git_monitor.stop_monitoring()
    # Observer should be stopped (can't easily test this without actual file changes)