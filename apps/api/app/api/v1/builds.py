from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.version import Version
from app.models.build import Build
from app.schemas.build import BuildCreate, BuildResponse
from app.services.build_service import BuildService
from app.services.credit_service import CreditService

router = APIRouter()


@router.post("/versions/{version_id}/builds", response_model=BuildResponse, status_code=status.HTTP_201_CREATED)
async def create_build(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify version ownership
    version = db.query(Version).join(Project).filter(
        Version.id == version_id,
        Project.owner_id == current_user.id,
    ).first()
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )
    
    # Check credits
    if not CreditService.check_balance(current_user, 10):  # credits_per_build
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits",
        )
    
    # Create build
    build = await BuildService.create_build(version, db)
    
    # Charge credits
    CreditService.charge_build(current_user, build, db)
    
    return build


@router.get("/builds/{build_id}", response_model=BuildResponse)
def get_build(
    build_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    build = db.query(Build).join(Project).filter(
        Build.id == build_id,
        Project.owner_id == current_user.id,
    ).first()
    if not build:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build not found",
        )
    return build


@router.get("/projects/{project_id}/builds", response_model=List[BuildResponse])
def list_builds(
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
    
    builds = db.query(Build).filter(Build.project_id == project_id).order_by(Build.id.desc()).all()
    return builds


@router.post("/builds/{build_id}/status", response_model=BuildResponse)
def update_build_status(
    build_id: int,
    status_update: dict,
    db: Session = Depends(get_db),
):
    """Internal endpoint for runner service to update build status."""
    from app.models.build import BuildStatus
    from pydantic import BaseModel
    
    class StatusUpdate(BaseModel):
        status: str
        logs: str | None = None
        preview_url: str | None = None
        error_message: str | None = None
    
    update = StatusUpdate(**status_update)
    build_status = BuildStatus(update.status)
    
    build = BuildService.update_build_status(
        build_id=build_id,
        status=build_status,
        logs=update.logs,
        preview_url=update.preview_url,
        error_message=update.error_message,
        db=db,
    )
    
    if not build:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Build not found",
        )
    
    return build
