#!/usr/bin/env python3
"""
Tests for the Claude Code Task Runner
"""

import os
import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch, call, MagicMock
from subprocess import CompletedProcess

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from acs.taskrunner import ClaudeTaskRunner, TASKS_FOLDER, WAIT_TIME_ON_RATE_LIMIT, MAX_RETRIES


class TestClaudeTaskRunner:
    """Test cases for ClaudeTaskRunner class"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)

    @pytest.fixture
    def task_runner(self, temp_dir):
        """Create a ClaudeTaskRunner instance with temp directory"""
        return ClaudeTaskRunner(str(temp_dir))

    @pytest.fixture
    def sample_task_files(self, temp_dir):
        """Create sample task files for testing"""
        task1 = temp_dir / "task1.md"
        task2 = temp_dir / "task2.md"
        task1.write_text("# Task 1\nThis is task 1 content")
        task2.write_text("# Task 2\nThis is task 2 content")
        return [task1, task2]

    def test_init(self, temp_dir):
        """Test ClaudeTaskRunner initialization"""
        runner = ClaudeTaskRunner(str(temp_dir))
        assert runner.tasks_folder == temp_dir
        assert runner.running_processes == {}
        assert runner.completed_tasks == []
        assert runner.failed_tasks == []

    def test_get_task_files_success(self, task_runner, sample_task_files):
        """Test get_task_files returns sorted list of .md files"""
        files = task_runner.get_task_files()
        assert len(files) == 2
        assert all(f.suffix == '.md' for f in files)
        assert files[0].name == 'task1.md'
        assert files[1].name == 'task2.md'

    def test_get_task_files_no_folder(self):
        """Test get_task_files raises FileNotFoundError when folder doesn't exist"""
        runner = ClaudeTaskRunner("/nonexistent/folder")
        with pytest.raises(FileNotFoundError, match="Tasks folder .* not found"):
            runner.get_task_files()

    def test_get_task_files_empty_folder(self, task_runner):
        """Test get_task_files returns empty list when no .md files found"""
        files = task_runner.get_task_files()
        assert files == []

    def test_read_task_content_success(self, task_runner, sample_task_files):
        """Test read_task_content successfully reads file content"""
        content = task_runner.read_task_content(sample_task_files[0])
        assert content == "# Task 1\nThis is task 1 content"

    def test_read_task_content_file_not_found(self, task_runner, temp_dir):
        """Test read_task_content handles file not found gracefully"""
        non_existent_file = temp_dir / "nonexistent.md"
        content = task_runner.read_task_content(non_existent_file)
        assert content == ""

    def test_is_rate_limit_error_positive_cases(self, task_runner):
        """Test is_rate_limit_error detects rate limiting errors"""
        test_cases = [
            "Error: rate limit exceeded",
            "HTTP 429: Too many requests",
            "quota exceeded for this API",
            "Rate_limit_exceeded error occurred",
            "RATE LIMIT reached"
        ]
        
        for error_msg in test_cases:
            assert task_runner.is_rate_limit_error(error_msg) is True

    def test_is_rate_limit_error_negative_cases(self, task_runner):
        """Test is_rate_limit_error doesn't falsely detect rate limiting"""
        test_cases = [
            "File not found",
            "Syntax error in code",
            "Connection timeout",
            "Invalid API key",
            "Server error 500"
        ]
        
        for error_msg in test_cases:
            assert task_runner.is_rate_limit_error(error_msg) is False

    @patch('acs.taskrunner.subprocess.Popen')
    def test_run_claude_task_success(self, mock_popen, task_runner, sample_task_files):
        """Test run_claude_task handles successful execution"""
        # Mock successful process
        mock_process = Mock()
        mock_process.communicate.return_value = ("Success output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = task_runner.run_claude_task(sample_task_files[0])

        assert result is True
        assert "task1" in task_runner.completed_tasks
        assert len(task_runner.failed_tasks) == 0
        
        # Verify subprocess was called with correct arguments
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        assert args == ["claude", "code", "--dangerously-skip-permission", str(sample_task_files[0])]

    @patch('acs.taskrunner.subprocess.Popen')
    def test_run_claude_task_failure(self, mock_popen, task_runner, sample_task_files):
        """Test run_claude_task handles failed execution"""
        # Mock failed process
        mock_process = Mock()
        mock_process.communicate.return_value = ("", "Error: command failed")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        result = task_runner.run_claude_task(sample_task_files[0])

        assert result is False
        assert len(task_runner.completed_tasks) == 0
        assert "task1" in task_runner.failed_tasks

    @patch('acs.taskrunner.subprocess.Popen')
    @patch('acs.taskrunner.time.sleep')
    def test_run_claude_task_rate_limit(self, mock_sleep, mock_popen, task_runner, sample_task_files):
        """Test run_claude_task handles rate limiting"""
        # Mock rate limit error first, then success
        mock_process_fail = Mock()
        mock_process_fail.communicate.return_value = ("", "Error: rate limit exceeded")
        mock_process_fail.returncode = 1
        
        mock_process_success = Mock()
        mock_process_success.communicate.return_value = ("Success", "")
        mock_process_success.returncode = 0
        
        mock_popen.side_effect = [mock_process_fail, mock_process_success]

        result = task_runner.run_claude_task(sample_task_files[0])

        assert result is True
        assert "task1" in task_runner.completed_tasks
        assert mock_sleep.call_count > 0  # Should have slept during rate limit wait

    @patch('acs.taskrunner.subprocess.Popen')
    def test_run_claude_task_exception(self, mock_popen, task_runner, sample_task_files):
        """Test run_claude_task handles subprocess exceptions"""
        mock_popen.side_effect = Exception("Subprocess error")

        result = task_runner.run_claude_task(sample_task_files[0])

        assert result is False
        assert len(task_runner.completed_tasks) == 0
        assert len(task_runner.failed_tasks) == 0  # Exception prevents adding to failed_tasks

    def test_handle_rate_limit_max_retries(self, task_runner, sample_task_files):
        """Test handle_rate_limit respects maximum retry limit"""
        result = task_runner.handle_rate_limit(sample_task_files[0], MAX_RETRIES)

        assert result is False
        assert "task1" in task_runner.failed_tasks

    @patch('acs.taskrunner.time.sleep')
    @patch.object(ClaudeTaskRunner, 'run_claude_task')
    def test_handle_rate_limit_retry(self, mock_run_task, mock_sleep, task_runner, sample_task_files):
        """Test handle_rate_limit retries after waiting"""
        # Avoid infinite recursion by making the retry return True
        mock_run_task.return_value = True

        result = task_runner.handle_rate_limit(sample_task_files[0], 1)

        assert result is True
        assert mock_sleep.call_count > 0  # Should have slept
        mock_run_task.assert_called_once_with(sample_task_files[0], 2)

    def test_monitor_processes_empty(self, task_runner):
        """Test monitor_processes handles empty process list"""
        # Should exit immediately when no running processes
        start_time = time.time()
        task_runner.monitor_processes()
        end_time = time.time()
        
        # Should complete quickly since no processes to monitor
        assert end_time - start_time < 1

    @patch('acs.taskrunner.time.sleep')
    def test_monitor_processes_with_running_process(self, mock_sleep, task_runner):
        """Test monitor_processes monitors running processes"""
        # Create a mock process
        mock_process = Mock()
        mock_process.poll.side_effect = [None, None, 0]  # Running, running, then finished
        
        task_runner.running_processes = {
            'test_task': {
                'process': mock_process,
                'start_time': time.time(),
                'task_file': Path('test.md'),
                'attempt': 1
            }
        }

        # Run monitoring in a thread to avoid blocking
        monitor_thread = threading.Thread(target=task_runner.monitor_processes, daemon=True)
        monitor_thread.start()
        
        # Give it some time to run
        time.sleep(0.1)
        
        # Clear running processes to stop monitoring
        task_runner.running_processes.clear()
        monitor_thread.join(timeout=1)

        # Verify sleep was called (monitoring interval)
        assert mock_sleep.call_count >= 1

    def test_cleanup_processes(self, task_runner):
        """Test cleanup_processes terminates running processes"""
        # Create mock processes
        mock_process1 = Mock()
        mock_process1.poll.return_value = None  # Still running
        mock_process2 = Mock()
        mock_process2.poll.return_value = 0  # Already finished

        task_runner.running_processes = {
            'task1': {'process': mock_process1},
            'task2': {'process': mock_process2}
        }

        task_runner.cleanup_processes()

        # Only the running process should be terminated
        mock_process1.terminate.assert_called_once()
        mock_process2.terminate.assert_not_called()

    def test_print_summary_empty(self, task_runner, capsys):
        """Test print_summary with no completed or failed tasks"""
        task_runner.print_summary()
        
        captured = capsys.readouterr()
        assert "=== SUMMARY ===" in captured.out
        assert "Total: 0 tasks" in captured.out

    def test_print_summary_with_results(self, task_runner, capsys):
        """Test print_summary with completed and failed tasks"""
        task_runner.completed_tasks = ['task1', 'task2']
        task_runner.failed_tasks = ['task3']
        
        task_runner.print_summary()
        
        captured = capsys.readouterr()
        assert "Total: 3 tasks" in captured.out
        assert "Successful: 2" in captured.out
        assert "Failed: 1" in captured.out
        assert "✓ task1" in captured.out
        assert "✓ task2" in captured.out
        assert "✗ task3" in captured.out

    @patch.object(ClaudeTaskRunner, 'get_task_files')
    @patch.object(ClaudeTaskRunner, 'run_claude_task')
    @patch.object(ClaudeTaskRunner, 'print_summary')
    def test_run_all_tasks_success(self, mock_summary, mock_run_task, mock_get_files, task_runner, sample_task_files):
        """Test run_all_tasks executes all tasks successfully"""
        mock_get_files.return_value = sample_task_files
        mock_run_task.return_value = True

        task_runner.run_all_tasks()

        assert mock_run_task.call_count == 2
        mock_summary.assert_called_once()

    @patch.object(ClaudeTaskRunner, 'get_task_files')
    def test_run_all_tasks_no_files(self, mock_get_files, task_runner):
        """Test run_all_tasks handles no task files gracefully"""
        mock_get_files.return_value = []

        # Should not raise an exception
        task_runner.run_all_tasks()

    @patch.object(ClaudeTaskRunner, 'get_task_files')
    @patch.object(ClaudeTaskRunner, 'cleanup_processes')
    def test_run_all_tasks_keyboard_interrupt(self, mock_cleanup, mock_get_files, task_runner, sample_task_files):
        """Test run_all_tasks handles KeyboardInterrupt"""
        mock_get_files.return_value = sample_task_files
        
        # Mock run_claude_task to raise KeyboardInterrupt
        with patch.object(task_runner, 'run_claude_task', side_effect=KeyboardInterrupt):
            task_runner.run_all_tasks()
        
        mock_cleanup.assert_called_once()

    @patch.object(ClaudeTaskRunner, 'get_task_files')
    @patch.object(ClaudeTaskRunner, 'cleanup_processes')
    def test_run_all_tasks_unexpected_exception(self, mock_cleanup, mock_get_files, task_runner, sample_task_files):
        """Test run_all_tasks handles unexpected exceptions"""
        mock_get_files.return_value = sample_task_files
        
        # Mock run_claude_task to raise an unexpected exception
        with patch.object(task_runner, 'run_claude_task', side_effect=Exception("Unexpected error")):
            task_runner.run_all_tasks()
        
        mock_cleanup.assert_called_once()


class TestMainFunction:
    """Test cases for the main function and CLI interface"""

    @patch('builtins.input')
    @patch.object(ClaudeTaskRunner, 'run_all_tasks')
    def test_main_user_confirms(self, mock_run_tasks, mock_input):
        """Test main function when user confirms execution"""
        mock_input.return_value = 'y'
        
        from acs.taskrunner import main
        main()
        
        mock_run_tasks.assert_called_once()

    @patch('builtins.input')
    @patch.object(ClaudeTaskRunner, 'run_all_tasks')
    def test_main_user_cancels(self, mock_run_tasks, mock_input):
        """Test main function when user cancels execution"""
        mock_input.return_value = 'n'
        
        from acs.taskrunner import main
        main()
        
        mock_run_tasks.assert_not_called()

    @patch('builtins.input')
    @patch.object(ClaudeTaskRunner, 'run_all_tasks')
    def test_main_various_confirmations(self, mock_run_tasks, mock_input):
        """Test main function handles various confirmation inputs"""
        # Test different positive responses
        for response in ['j', 'ja', 'y', 'yes', 'Y', 'YES']:
            mock_input.return_value = response
            mock_run_tasks.reset_mock()
            
            from acs.taskrunner import main
            main()
            
            mock_run_tasks.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])