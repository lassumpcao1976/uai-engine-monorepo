"""
Build and file management routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pathlib import Path
import os

from database import get_db
from models import Project, ProjectVersion, Build
from auth import get_current_user, User
from schemas import (
    VersionResponse, BuildResponse, FileNode, FileContentResponse,
    ErrorResponse, ErrorDetail
)

router = APIRouter(tags=["builds"])


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response"""
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details)
    )


@router.get("/projects/{project_id}/versions", response_model=List[VersionResponse])
async def list_versions(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all versions for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    versions = db.query(ProjectVersion).filter(
        ProjectVersion.project_id == project_id
    ).order_by(ProjectVersion.version_number.desc()).all()
    
    # Generate unified diff text for each version
    result = []
    for v in versions:
        version_response = VersionResponse.model_validate(v)
        if v.code_diff:
            unified_diff_parts = []
            diff_dict = v.code_diff
            
            # Add modified files
            for file_path, diff_text in diff_dict.get("modified", {}).items():
                unified_diff_parts.append(diff_text)
            
            # Add added files
            for file_path in diff_dict.get("added", []):
                unified_diff_parts.append(f"+++ b/{file_path}\n@@ -0,0 +1,0 @@\n+[New file: {file_path}]")
            
            # Add deleted files
            for file_path in diff_dict.get("deleted", []):
                unified_diff_parts.append(f"--- a/{file_path}\n+++ /dev/null\n@@ -1,0 +0,0 @@\n-[Deleted file: {file_path}]")
            
            version_response.unified_diff_text = "\n".join(unified_diff_parts) if unified_diff_parts else None
        else:
            version_response.unified_diff_text = None
        result.append(version_response)
    
    return result


@router.get("/projects/{project_id}/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    project_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific version"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    version = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_id,
        ProjectVersion.project_id == project_id
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Version not found").dict()
        )
    
    # Get associated build
    build = db.query(Build).filter(Build.version_id == version_id).first()
    response = VersionResponse.model_validate(version)
    if build:
        response.build = BuildResponse.model_validate(build)
    
    # Generate unified diff text from code_diff
    if version.code_diff:
        unified_diff_parts = []
        diff_dict = version.code_diff
        
        # Add modified files
        for file_path, diff_text in diff_dict.get("modified", {}).items():
            unified_diff_parts.append(diff_text)
        
        # Add added files
        for file_path in diff_dict.get("added", []):
            unified_diff_parts.append(f"+++ b/{file_path}\n@@ -0,0 +1,0 @@\n+[New file: {file_path}]")
        
        # Add deleted files
        for file_path in diff_dict.get("deleted", []):
            unified_diff_parts.append(f"--- a/{file_path}\n+++ /dev/null\n@@ -1,0 +0,0 @@\n-[Deleted file: {file_path}]")
        
        response.unified_diff_text = "\n".join(unified_diff_parts) if unified_diff_parts else None
    else:
        response.unified_diff_text = None
    
    return response


@router.get("/projects/{project_id}/builds", response_model=List[BuildResponse])
async def list_builds(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all builds for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    builds = db.query(Build).filter(
        Build.project_id == project_id
    ).order_by(Build.created_at.desc()).all()
    
    return [BuildResponse.model_validate(b) for b in builds]


@router.get("/projects/{project_id}/builds/{build_id}", response_model=BuildResponse)
async def get_build(
    project_id: str,
    build_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific build with logs"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    build = db.query(Build).filter(
        Build.id == build_id,
        Build.project_id == project_id
    ).first()
    
    if not build:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Build not found").dict()
        )
    
    return BuildResponse.model_validate(build)


@router.get("/projects/{project_id}/files/tree", response_model=List[FileNode])
async def get_file_tree(
    project_id: str,
    version_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file tree for a project version"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    # Get project directory
    PROJECTS_DIR = Path(os.getenv("PROJECTS_DIR", "./projects"))
    project_path = PROJECTS_DIR / project_id
    
    if not project_path.exists():
        return []
    
    def build_tree(path: Path, base_path: Path) -> List[FileNode]:
        """Recursively build file tree"""
        nodes = []
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.'):
                    continue
                
                rel_path = item.relative_to(base_path)
                node = FileNode(
                    name=item.name,
                    path=str(rel_path),
                    type="directory" if item.is_dir() else "file"
                )
                
                if item.is_dir():
                    node.children = build_tree(item, base_path)
                
                nodes.append(node)
        except PermissionError:
            pass
        
        return nodes
    
    tree = build_tree(project_path, project_path)
    return tree


@router.get("/projects/{project_id}/files/content", response_model=FileContentResponse)
async def get_file_content(
    project_id: str,
    path: str = Query(..., description="File path relative to project root"),
    version_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get file content"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    # Security: prevent path traversal
    if ".." in path or path.startswith("/"):
        raise HTTPException(
            status_code=400,
            detail=create_error_response("INVALID_PATH", "Invalid file path").dict()
        )
    
    # Get project directory
    PROJECTS_DIR = Path(os.getenv("PROJECTS_DIR", "./projects"))
    project_path = PROJECTS_DIR / project_id
    file_path = project_path / path
    
    # Ensure file is within project directory
    try:
        file_path.resolve().relative_to(project_path.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=create_error_response("INVALID_PATH", "File path outside project").dict()
        )
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "File not found").dict()
        )
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=create_error_response("READ_ERROR", f"Could not read file: {str(e)}").dict()
        )
    
    return FileContentResponse(
        path=path,
        content=content,
        version_id=version_id
    )
