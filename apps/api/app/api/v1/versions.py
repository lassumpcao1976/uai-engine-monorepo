from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.version import Version
from app.schemas.version import VersionCreate, VersionResponse
from app.services.version_service import VersionService

router = APIRouter()


@router.post("/projects/{project_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
def create_version(
    project_id: int,
    version_data: VersionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    # TODO: Call AI service to generate file tree from prompt
    # For now, generate a mock file tree for a Next.js project
    file_tree = {
        "app": {
            "layout.tsx": "",
            "page.tsx": "",
            "globals.css": "",
        },
        "components": {},
        "public": {},
        "package.json": "",
        "next.config.js": "",
        "tsconfig.json": "",
    }
    
    version = VersionService.create_version(project, version_data.prompt, file_tree, db)
    return version


@router.get("/projects/{project_id}/versions", response_model=List[VersionResponse])
def list_versions(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    
    versions = db.query(Version).filter(Version.project_id == project_id).order_by(Version.id.desc()).all()
    return versions


@router.get("/versions/{version_id}", response_model=VersionResponse)
def get_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    version = db.query(Version).join(Project).filter(
        Version.id == version_id,
        Project.owner_id == current_user.id,
    ).first()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )
    return version
