"""Tests for Docker/Podman setup and compatibility."""

import os
import subprocess
import unittest
from pathlib import Path


class TestDockerSetup(unittest.TestCase):
    """Test Docker/Podman setup and configuration."""
    
    def setUp(self):
        """Set up test environment."""
        self.project_root = Path(__file__).parent.parent
        
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        dockerfile = self.project_root / "Dockerfile"
        self.assertTrue(dockerfile.exists(), "Dockerfile not found")
        
    def test_dockerignore_exists(self):
        """Test that .dockerignore exists."""
        dockerignore = self.project_root / ".dockerignore"
        self.assertTrue(dockerignore.exists(), ".dockerignore not found")
        
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists."""
        compose_file = self.project_root / "docker-compose.yml"
        self.assertTrue(compose_file.exists(), "docker-compose.yml not found")
        
    def test_makefile_exists(self):
        """Test that Makefile exists."""
        makefile = self.project_root / "Makefile"
        self.assertTrue(makefile.exists(), "Makefile not found")
        
    def test_sample_env_exists(self):
        """Test that sample.env exists."""
        sample_env = self.project_root / "sample.env"
        self.assertTrue(sample_env.exists(), "sample.env not found")
        
    def test_dockerfile_syntax(self):
        """Test Dockerfile has correct syntax."""
        dockerfile = self.project_root / "Dockerfile"
        with open(dockerfile, 'r') as f:
            content = f.read()
            
        # Check for required instructions
        self.assertIn("FROM python:", content, "Python base image not found")
        self.assertIn("WORKDIR /usr/src/app", content, "WORKDIR not set")
        self.assertIn("USER devuser", content, "Non-root user not set")
        self.assertIn("HEALTHCHECK", content, "Health check not defined")
        
    def test_docker_compose_syntax(self):
        """Test docker-compose.yml has correct syntax."""
        compose_file = self.project_root / "docker-compose.yml"
        with open(compose_file, 'r') as f:
            content = f.read()
            
        # Check for required sections
        self.assertIn("version:", content, "Version not specified")
        self.assertIn("services:", content, "Services not defined")
        self.assertIn("dev-client:", content, "dev-client service not defined")
        self.assertIn("volumes:", content, "Volumes not defined")
        
    def test_makefile_targets(self):
        """Test Makefile has all required targets."""
        makefile = self.project_root / "Makefile"
        with open(makefile, 'r') as f:
            content = f.read()
            
        # Check for required targets
        required_targets = [
            "build:", "run:", "stop:", "remove:", "shell:",
            "start:", "logs:", "compose-up:", "compose-down:", "info:"
        ]
        
        for target in required_targets:
            self.assertIn(target, content, f"Target {target} not found in Makefile")
            
    def test_makefile_runtime_detection(self):
        """Test Makefile has runtime detection logic."""
        makefile = self.project_root / "Makefile"
        with open(makefile, 'r') as f:
            content = f.read()
            
        # Check for runtime detection
        self.assertIn("CONTAINER_RUNTIME", content, "Runtime detection not found")
        self.assertIn("command -v docker", content, "Docker detection not found")
        self.assertIn("command -v podman", content, "Podman detection not found")
        
    def test_docker_setup_script(self):
        """Test docker-setup.sh script exists and is executable."""
        setup_script = self.project_root / "scripts" / "docker-setup.sh"
        self.assertTrue(setup_script.exists(), "docker-setup.sh not found")
        
        # Check if executable
        self.assertTrue(os.access(setup_script, os.X_OK), "docker-setup.sh not executable")
        
    def test_dockerignore_patterns(self):
        """Test .dockerignore has appropriate patterns."""
        dockerignore = self.project_root / ".dockerignore"
        with open(dockerignore, 'r') as f:
            content = f.read()
            
        # Check for important patterns
        patterns = [".git", "__pycache__", ".env", "*.pyc", ".venv", "tests/"]
        for pattern in patterns:
            self.assertIn(pattern, content, f"Pattern {pattern} not in .dockerignore")


if __name__ == "__main__":
    unittest.main()