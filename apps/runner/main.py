"""
Build Runner Service - Handles Docker builds for UAI Engine
This service runs in a separate container with Docker access.
"""
import os
import json
import hmac
import hashlib
from pathlib import Path
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import docker
from docker.errors import DockerException

app = FastAPI(title="UAI Engine Build Runner")

RUNNER_SECRET = os.getenv("RUNNER_SECRET")
if not RUNNER_SECRET:
    raise ValueError("RUNNER_SECRET environment variable is required")

PROJECTS_DIR = Path(os.getenv("PROJECTS_DIR", "/app/projects"))
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

# Docker client
try:
    docker_client = docker.from_env()
except DockerException as e:
    print(f"Warning: Could not connect to Docker: {e}")
    docker_client = None


class BuildRequest(BaseModel):
    project_id: str
    project_path: str  # Relative path within PROJECTS_DIR
    timeout: int = 300
    memory_limit: str = "1g"
    cpu_limit: str = "1.0"


class RepairRequest(BaseModel):
    project_id: str
    project_path: str
    error_logs: str
    timeout: int = 300
    memory_limit: str = "1g"
    cpu_limit: str = "1.0"


def verify_secret(authorization: str = Header(None)):
    """Verify RUNNER_SECRET from Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    
    token = authorization[7:]
    
    # Simple secret comparison (use constant-time comparison in production)
    if not hmac.compare_digest(token, RUNNER_SECRET):
        raise HTTPException(status_code=401, detail="Invalid runner secret")
    
    return True


@app.get("/health")
async def health():
    """Health check endpoint"""
    docker_available = docker_client is not None
    return {
        "status": "healthy",
        "docker_available": docker_available
    }


@app.post("/build")
async def run_build(
    request: BuildRequest,
    _: bool = Depends(verify_secret)
):
    """
    Execute a build in Docker container.
    Returns build results with logs and exit code.
    """
    if docker_client is None:
        raise HTTPException(
            status_code=503,
            detail="Docker client not available"
        )
    
    project_path = PROJECTS_DIR / request.project_path
    if not project_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Project path not found: {request.project_path}"
        )
    
    container_name = f"uai-build-{request.project_id}"
    
    try:
        # Clean up any existing container
        _cleanup_container(container_name)
        
        # Create build container with strict limits
        container = docker_client.containers.run(
            "node:18-alpine",
            command="sh -c 'cd /project && npm install && npm run lint && npm run build'",
            volumes={
                str(project_path.resolve()): {"bind": "/project", "mode": "ro"}
            },
            mem_limit=request.memory_limit,
            cpu_quota=int(float(request.cpu_limit) * 100000),
            cpu_period=100000,
            network_disabled=True,  # No network access during build
            remove=False,
            name=container_name,
            detach=True,
            working_dir="/project"
        )
        
        # Wait for container to finish with timeout
        try:
            result = container.wait(timeout=request.timeout)
            exit_code = result.get("StatusCode", 1)
        except Exception as e:
            container.kill()
            container.remove()
            return JSONResponse(
                status_code=200,
                content={
                    "success": False,
                    "error": f"Build timeout after {request.timeout}s",
                    "logs": container.logs().decode() if container else "",
                    "exit_code": 124
                }
            )
        
        # Get logs
        logs = container.logs().decode()
        
        # Extract lint and build outputs
        lint_output = _extract_lint_output(logs)
        build_output = _extract_build_output(logs)
        
        # Cleanup
        container.remove()
        
        success = exit_code == 0
        
        return {
            "success": success,
            "exit_code": exit_code,
            "logs": logs,
            "lint_output": lint_output,
            "build_output": build_output,
            "error": None if success else "Build failed"
        }
    
    except docker.errors.APIError as e:
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "error": f"Docker API error: {str(e)}",
                "logs": "",
                "exit_code": 1
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "logs": "",
                "exit_code": 1
            }
        )
    finally:
        _cleanup_container(container_name)


@app.post("/repair")
async def run_repair(
    request: RepairRequest,
    _: bool = Depends(verify_secret)
):
    """
    Execute a repair build attempt.
    Similar to /build but may include repair-specific logic.
    """
    # For now, repair is the same as build
    # In the future, this could include automatic fixes
    build_request = BuildRequest(
        project_id=request.project_id,
        project_path=request.project_path,
        timeout=request.timeout,
        memory_limit=request.memory_limit,
        cpu_limit=request.cpu_limit
    )
    return await run_build(build_request, _)


def _extract_lint_output(logs: str) -> str:
    """Extract lint output from build logs"""
    lines = logs.split("\n")
    lint_lines = []
    in_lint = False
    for line in lines:
        if "lint" in line.lower() or "eslint" in line.lower():
            in_lint = True
        if in_lint:
            lint_lines.append(line)
        if in_lint and ("error" in line.lower() or "warning" in line.lower() or line.strip() == ""):
            if line.strip() == "" and lint_lines:
                break
    return "\n".join(lint_lines)


def _extract_build_output(logs: str) -> str:
    """Extract build output from build logs"""
    lines = logs.split("\n")
    build_lines = []
    in_build = False
    for line in lines:
        if "build" in line.lower() and ("next build" in line.lower() or "npm run build" in line.lower()):
            in_build = True
        if in_build:
            build_lines.append(line)
    return "\n".join(build_lines)


def _cleanup_container(container_name: str):
    """Clean up Docker container"""
    if docker_client is None:
        return
    try:
        container = docker_client.containers.get(container_name)
        if container.status == "running":
            container.kill()
        container.remove()
    except docker.errors.NotFound:
        pass
    except Exception as e:
        print(f"Warning: Could not cleanup container {container_name}: {e}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
