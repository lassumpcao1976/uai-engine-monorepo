"""
Build service for validating and executing builds via runner service
"""
import os
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple

RUNNER_URL = os.getenv("RUNNER_URL", "http://runner:8001")
RUNNER_SECRET = os.getenv("RUNNER_SECRET")
if not RUNNER_SECRET:
    raise ValueError("RUNNER_SECRET environment variable is required")


class BuildService:
    def __init__(self, projects_dir: Path):
        self.projects_dir = projects_dir
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = 3
        self.build_timeout = 300  # 5 minutes
        self.memory_limit = "1g"
        self.cpu_limit = "1.0"

    def validate_build(self, project_id: str, project_path: Path) -> Tuple[bool, Dict]:
        """
        Validate a project build via runner service.
        Returns (success: bool, results: dict with logs, errors, etc.)
        """
        # Get relative path from projects_dir
        try:
            rel_path = str(project_path.relative_to(self.projects_dir))
        except ValueError:
            # If project_path is not under projects_dir, use project_id as path
            rel_path = project_id
        
        # Call runner service
        try:
            response = requests.post(
                f"{RUNNER_URL}/build",
                json={
                    "project_id": project_id,
                    "project_path": rel_path,
                    "timeout": self.build_timeout,
                    "memory_limit": self.memory_limit,
                    "cpu_limit": self.cpu_limit
                },
                headers={
                    "Authorization": f"Bearer {RUNNER_SECRET}",
                    "Content-Type": "application/json"
                },
                timeout=self.build_timeout + 60  # Add buffer for HTTP overhead
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False), {
                    "exit_code": result.get("exit_code", 1),
                    "logs": result.get("logs", ""),
                    "lint_output": result.get("lint_output", ""),
                    "build_output": result.get("build_output", ""),
                    "error": result.get("error")
                }
            else:
                return False, {
                    "error": f"Runner service error: {response.status_code}",
                    "logs": response.text
                }
        
        except requests.exceptions.ConnectionError:
            return False, {
                "error": "Cannot connect to runner service. Is it running?",
                "logs": ""
            }
        except requests.exceptions.Timeout:
            return False, {
                "error": f"Build request timeout after {self.build_timeout + 60}s",
                "logs": ""
            }
        except Exception as e:
            return False, {
                "error": f"Unexpected error calling runner: {str(e)}",
                "logs": ""
            }

    def repair_build(self, project_id: str, project_path: Path, error_logs: str) -> Tuple[bool, Dict]:
        """
        Run a repair build attempt via runner service.
        Returns (success: bool, results: dict with logs, errors, etc.)
        """
        # Get relative path from projects_dir
        try:
            rel_path = str(project_path.relative_to(self.projects_dir))
        except ValueError:
            # If project_path is not under projects_dir, use project_id as path
            rel_path = project_id
        
        # Call runner service
        try:
            response = requests.post(
                f"{RUNNER_URL}/repair",
                json={
                    "project_id": project_id,
                    "project_path": rel_path,
                    "error_logs": error_logs,
                    "timeout": self.build_timeout,
                    "memory_limit": self.memory_limit,
                    "cpu_limit": self.cpu_limit
                },
                headers={
                    "Authorization": f"Bearer {RUNNER_SECRET}",
                    "Content-Type": "application/json"
                },
                timeout=self.build_timeout + 60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("success", False), {
                    "exit_code": result.get("exit_code", 1),
                    "logs": result.get("logs", ""),
                    "lint_output": result.get("lint_output", ""),
                    "build_output": result.get("build_output", ""),
                    "error": result.get("error")
                }
            else:
                return False, {
                    "error": f"Runner service error: {response.status_code}",
                    "logs": response.text
                }
        
        except requests.exceptions.ConnectionError:
            return False, {
                "error": "Cannot connect to runner service. Is it running?",
                "logs": ""
            }
        except requests.exceptions.Timeout:
            return False, {
                "error": f"Repair request timeout after {self.build_timeout + 60}s",
                "logs": ""
            }
        except Exception as e:
            return False, {
                "error": f"Unexpected error calling runner: {str(e)}",
                "logs": ""
            }

    def get_project_path(self, project_id: str) -> Path:
        """Get the filesystem path for a project"""
        return self.projects_dir / project_id
