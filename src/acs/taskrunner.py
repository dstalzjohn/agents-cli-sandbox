#!/usr/bin/env python3
"""
Claude Code Task Runner
Automates the execution of Claude Code for multiple Markdown tasks
"""

import os
import time
import threading
import subprocess
import logging
import glob
from pathlib import Path
from typing import List, Optional
import re

# Configuration
TASKS_FOLDER = "tasks"  # Folder with .md files
WAIT_TIME_ON_RATE_LIMIT = 2 * 60 * 60  # 2 hours in seconds
CHECK_INTERVAL = 10  # Check every 10 seconds
MAX_RETRIES = 3  # Maximum retries per task

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('claude_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ClaudeTaskRunner:
    def __init__(self, tasks_folder: str = TASKS_FOLDER):
        self.tasks_folder = Path(tasks_folder)
        self.running_processes = {}
        self.completed_tasks = []
        self.failed_tasks = []

    def get_task_files(self) -> List[Path]:
        """Find all .md files in the tasks folder"""
        if not self.tasks_folder.exists():
            raise FileNotFoundError(f"Tasks folder '{self.tasks_folder}' not found")

        md_files = list(self.tasks_folder.glob("*.md"))
        md_files.sort()  # Alphabetical order
        logger.info(f"Found tasks: {[f.name for f in md_files]}")
        return md_files

    def read_task_content(self, task_file: Path) -> str:
        """Read content of a task file"""
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {task_file}: {e}")
            return ""

    def is_rate_limit_error(self, error_output: str) -> bool:
        """Check if the error indicates rate limiting"""
        rate_limit_indicators = [
            "rate limit",
            "too many requests",
            "quota exceeded",
            "429",
            "rate_limit_exceeded"
        ]
        error_lower = error_output.lower()
        return any(indicator in error_lower for indicator in rate_limit_indicators)

    def run_claude_task(self, task_file: Path, attempt: int = 1) -> bool:
        """
        Execute a single task with Claude Code
        Returns True on success, False on error
        """
        task_name = task_file.stem
        logger.info(f"Starting task '{task_name}' (attempt {attempt})")

        try:
            # Assemble Claude Code command
            cmd = [
                "claude",
                "code",
                "--dangerously-skip-permission",
                str(task_file)
            ]

            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=task_file.parent
            )

            self.running_processes[task_name] = {
                'process': process,
                'start_time': time.time(),
                'task_file': task_file,
                'attempt': attempt
            }

            # Wait for process to finish
            stdout, stderr = process.communicate()

            # Remove process from list
            if task_name in self.running_processes:
                del self.running_processes[task_name]

            # Evaluate result
            if process.returncode == 0:
                logger.info(f"Task '{task_name}' completed successfully")
                self.completed_tasks.append(task_name)
                return True
            else:
                logger.error(f"Task '{task_name}' failed (Exit Code: {process.returncode})")
                logger.error(f"STDERR: {stderr}")

                # Check for rate limiting
                if self.is_rate_limit_error(stderr):
                    logger.warning(f"Rate limit detected for task '{task_name}'")
                    return self.handle_rate_limit(task_file, attempt)
                else:
                    self.failed_tasks.append(task_name)
                    return False

        except Exception as e:
            logger.error(f"Error executing task '{task_name}': {e}")
            if task_name in self.running_processes:
                del self.running_processes[task_name]
            return False

    def handle_rate_limit(self, task_file: Path, attempt: int) -> bool:
        """Rate limit handling - wait and retry"""
        task_name = task_file.stem

        if attempt >= MAX_RETRIES:
            logger.error(f"Maximum retries reached for task '{task_name}'")
            self.failed_tasks.append(task_name)
            return False

        logger.info(f"Waiting {WAIT_TIME_ON_RATE_LIMIT / 3600:.1f}h due to rate limit...")

        # Show countdown
        for remaining in range(WAIT_TIME_ON_RATE_LIMIT, 0, -60):
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            logger.info(f"Remaining wait time: {hours}h {minutes}m")
            time.sleep(60)

        logger.info(f"Retrying task '{task_name}' (attempt {attempt + 1})")
        return self.run_claude_task(task_file, attempt + 1)

    def monitor_processes(self):
        """Monitor running processes every 10 seconds"""
        while self.running_processes:
            time.sleep(CHECK_INTERVAL)

            for task_name, info in list(self.running_processes.items()):
                process = info['process']
                runtime = time.time() - info['start_time']

                if process.poll() is None:  # Process still running
                    logger.info(f"Task '{task_name}' running for {runtime:.0f}s")
                else:
                    # Process finished
                    logger.info(f"Task '{task_name}' finished after {runtime:.0f}s")

    def run_all_tasks(self):
        """Execute all tasks sequentially"""
        try:
            task_files = self.get_task_files()
            if not task_files:
                logger.warning("No .md files found in tasks folder")
                return

            logger.info(f"Starting execution of {len(task_files)} tasks")

            # Start monitoring thread
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()

            # Process tasks sequentially
            for i, task_file in enumerate(task_files, 1):
                logger.info(f"=== Task {i}/{len(task_files)}: {task_file.name} ===")

                # Execute task in own thread
                task_thread = threading.Thread(
                    target=self.run_claude_task,
                    args=(task_file,),
                    daemon=False
                )
                task_thread.start()
                task_thread.join()  # Wait until task is finished

                logger.info(f"Task {i} completed\n")

            # Summary
            self.print_summary()

        except KeyboardInterrupt:
            logger.info("Execution interrupted by user")
            self.cleanup_processes()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.cleanup_processes()

    def cleanup_processes(self):
        """Terminate running processes"""
        for task_name, info in self.running_processes.items():
            try:
                process = info['process']
                if process.poll() is None:
                    logger.info(f"Terminating running process for task '{task_name}'")
                    process.terminate()
                    time.sleep(2)
                    if process.poll() is None:
                        process.kill()
            except Exception as e:
                logger.error(f"Error terminating process '{task_name}': {e}")

    def print_summary(self):
        """Print execution summary"""
        total_tasks = len(self.completed_tasks) + len(self.failed_tasks)

        logger.info("=== SUMMARY ===")
        logger.info(f"Total: {total_tasks} tasks")
        logger.info(f"Successful: {len(self.completed_tasks)}")
        logger.info(f"Failed: {len(self.failed_tasks)}")

        if self.completed_tasks:
            logger.info("Successful tasks:")
            for task in self.completed_tasks:
                logger.info(f"  ✓ {task}")

        if self.failed_tasks:
            logger.info("Failed tasks:")
            for task in self.failed_tasks:
                logger.info(f"  ✗ {task}")


def main():
    """Main function"""
    print("Claude Code Task Runner")
    print("======================")

    # Show configuration
    print(f"Tasks folder: {TASKS_FOLDER}")
    print(f"Rate limit wait time: {WAIT_TIME_ON_RATE_LIMIT / 3600:.1f}h")
    print(f"Check interval: {CHECK_INTERVAL}s")
    print(f"Max retries: {MAX_RETRIES}")
    print()

    # Ask for confirmation
    response = input("Do you want to continue? (y/N): ").strip().lower()
    if response not in ['j', 'ja', 'y', 'yes']:
        print("Cancelled.")
        return

    # Create and start task runner
    runner = ClaudeTaskRunner(TASKS_FOLDER)
    runner.run_all_tasks()


if __name__ == "__main__":
    main()