#!/usr/bin/env python3
"""
Integration tests for the Claude Code Task Runner
"""

import os
import pytest
import tempfile
import subprocess
import time
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from acs.taskrunner import ClaudeTaskRunner


class TestTaskRunnerIntegration:
    """Integration tests that test the task runner with actual file system operations"""

    @pytest.fixture
    def temp_tasks_dir(self):
        """Create a temporary directory with task files"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tasks_dir = Path(tmp_dir) / "tasks"
            tasks_dir.mkdir()
            
            # Create sample task files
            (tasks_dir / "01_simple_task.md").write_text("""
# Simple Task

This is a simple task that should complete quickly.

```python
print("Hello from task 1")
```
""")
            
            (tasks_dir / "02_echo_task.md").write_text("""
# Echo Task

This task just echoes some text.

```bash
echo "Task 2 executed successfully"
```
""")
            
            (tasks_dir / "03_error_task.md").write_text("""
# Error Task

This task is designed to fail for testing purposes.

```bash
exit 1
```
""")
            
            yield tasks_dir

    def test_task_discovery_and_ordering(self, temp_tasks_dir):
        """Test that tasks are discovered and ordered correctly"""
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        task_files = runner.get_task_files()
        
        assert len(task_files) == 3
        # Should be in alphabetical order
        assert task_files[0].name == "01_simple_task.md"
        assert task_files[1].name == "02_echo_task.md" 
        assert task_files[2].name == "03_error_task.md"

    def test_task_content_reading(self, temp_tasks_dir):
        """Test reading task file contents"""
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        task_files = runner.get_task_files()
        
        content = runner.read_task_content(task_files[0])
        assert "Simple Task" in content
        assert "print(\"Hello from task 1\")" in content

    @patch('acs.taskrunner.subprocess.Popen')
    def test_claude_command_construction(self, mock_popen, temp_tasks_dir):
        """Test that Claude Code commands are constructed correctly"""
        # Mock successful execution
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = ("Success", "")
        mock_process.returncode = 0
        
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        task_files = runner.get_task_files()
        
        result = runner.run_claude_task(task_files[0])
        
        assert result is True
        mock_popen.assert_called_once()
        
        # Verify command arguments
        call_args = mock_popen.call_args[0][0]
        assert call_args[0] == "claude"
        assert call_args[1] == "code"
        assert call_args[2] == "--dangerously-skip-permission"
        assert call_args[3] == str(task_files[0])

    @patch('acs.taskrunner.subprocess.Popen')
    def test_mixed_success_and_failure(self, mock_popen, temp_tasks_dir):
        """Test handling mixed success and failure scenarios"""
        # Mock different return codes for different tasks
        def mock_popen_side_effect(*args, **kwargs):
            mock_process = mock_popen.return_value
            task_file = args[0][3]  # Fourth argument is the task file path
            
            if "01_simple_task" in task_file:
                mock_process.communicate.return_value = ("Success", "")
                mock_process.returncode = 0
            elif "02_echo_task" in task_file:
                mock_process.communicate.return_value = ("Success", "")
                mock_process.returncode = 0
            else:  # error_task
                mock_process.communicate.return_value = ("", "Command failed")
                mock_process.returncode = 1
            
            return mock_process
        
        mock_popen.side_effect = mock_popen_side_effect
        
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        task_files = runner.get_task_files()
        
        # Run each task individually
        results = []
        for task_file in task_files:
            result = runner.run_claude_task(task_file)
            results.append(result)
        
        # Should have 2 successes and 1 failure
        assert results == [True, True, False]
        assert len(runner.completed_tasks) == 2
        assert len(runner.failed_tasks) == 1
        assert "03_error_task" in runner.failed_tasks

    @patch('acs.taskrunner.subprocess.Popen')
    def test_rate_limit_simulation(self, mock_popen, temp_tasks_dir):
        """Test rate limit handling with simulated rate limit error"""
        call_count = 0
        
        def mock_popen_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            mock_process = mock_popen.return_value
            
            if call_count == 1:
                # First call: rate limit error
                mock_process.communicate.return_value = ("", "Error: rate limit exceeded")
                mock_process.returncode = 1
            else:
                # Second call: success
                mock_process.communicate.return_value = ("Success after retry", "")
                mock_process.returncode = 0
            
            return mock_process
        
        mock_popen.side_effect = mock_popen_side_effect
        
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        task_files = runner.get_task_files()
        
        # Mock time.sleep to speed up the test
        with patch('acs.taskrunner.time.sleep'):
            result = runner.run_claude_task(task_files[0])
        
        assert result is True
        assert call_count == 2  # Should have retried once
        assert len(runner.completed_tasks) == 1

    def test_task_runner_state_management(self, temp_tasks_dir):
        """Test that task runner properly manages its internal state"""
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        
        # Initial state
        assert len(runner.completed_tasks) == 0
        assert len(runner.failed_tasks) == 0
        assert len(runner.running_processes) == 0
        
        # Simulate adding completed tasks
        runner.completed_tasks.append("task1")
        runner.completed_tasks.append("task2")
        runner.failed_tasks.append("task3")
        
        # Verify state
        assert len(runner.completed_tasks) == 2
        assert len(runner.failed_tasks) == 1
        assert "task1" in runner.completed_tasks
        assert "task3" in runner.failed_tasks

    @patch('acs.taskrunner.subprocess.Popen')
    def test_process_cleanup_on_exception(self, mock_popen, temp_tasks_dir):
        """Test that processes are cleaned up when exceptions occur"""
        # Mock process that raises exception during communication
        mock_process = mock_popen.return_value
        mock_process.communicate.side_effect = Exception("Communication error")
        
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        task_files = runner.get_task_files()
        
        result = runner.run_claude_task(task_files[0])
        
        assert result is False
        # Process should be removed from running_processes even on exception
        assert len(runner.running_processes) == 0

    def test_summary_generation_integration(self, temp_tasks_dir, capsys):
        """Test summary generation with realistic task data"""
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        
        # Simulate some completed and failed tasks
        runner.completed_tasks = ["01_simple_task", "02_echo_task"]
        runner.failed_tasks = ["03_error_task"]
        
        runner.print_summary()
        
        captured = capsys.readouterr()
        output = captured.out
        
        assert "=== SUMMARY ===" in output
        assert "Total: 3 tasks" in output
        assert "Successful: 2" in output
        assert "Failed: 1" in output
        assert "✓ 01_simple_task" in output
        assert "✓ 02_echo_task" in output
        assert "✗ 03_error_task" in output

    def test_working_directory_handling(self, temp_tasks_dir):
        """Test that the task runner handles working directory correctly"""
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        
        # Verify tasks folder path is correctly set
        assert runner.tasks_folder == temp_tasks_dir
        assert runner.tasks_folder.exists()
        
        # Verify it can find tasks relative to the folder
        task_files = runner.get_task_files()
        assert all(task_file.parent == temp_tasks_dir for task_file in task_files)

    @patch('acs.taskrunner.subprocess.Popen')
    @patch('acs.taskrunner.threading.Thread')
    def test_concurrent_execution_simulation(self, mock_thread, mock_popen, temp_tasks_dir):
        """Test simulation of concurrent execution patterns"""
        # Mock successful process
        mock_process = mock_popen.return_value
        mock_process.communicate.return_value = ("Success", "")
        mock_process.returncode = 0
        
        # Mock thread to track if it was created and started
        mock_thread_instance = mock_thread.return_value
        
        runner = ClaudeTaskRunner(str(temp_tasks_dir))
        
        # This would normally run all tasks, but we're testing the threading setup
        with patch.object(runner, 'get_task_files', return_value=[temp_tasks_dir / "01_simple_task.md"]):
            with patch.object(runner, 'print_summary'):
                runner.run_all_tasks()
        
        # Verify that threading was set up for monitoring
        assert mock_thread.called
        mock_thread_instance.start.assert_called()


class TestConfigurationIntegration:
    """Test integration with configuration constants"""

    def test_configuration_constants_usage(self):
        """Test that configuration constants are properly used"""
        from acs.taskrunner import TASKS_FOLDER, WAIT_TIME_ON_RATE_LIMIT, MAX_RETRIES
        
        # Verify constants have expected values
        assert TASKS_FOLDER == "tasks"
        assert WAIT_TIME_ON_RATE_LIMIT == 2 * 60 * 60  # 2 hours
        assert MAX_RETRIES == 3
        
        # Test with custom folder
        runner = ClaudeTaskRunner("custom_tasks")
        assert str(runner.tasks_folder) == "custom_tasks"

    def test_default_folder_usage(self):
        """Test using default tasks folder"""
        runner = ClaudeTaskRunner()
        assert str(runner.tasks_folder) == "tasks"


if __name__ == "__main__":
    pytest.main([__file__])