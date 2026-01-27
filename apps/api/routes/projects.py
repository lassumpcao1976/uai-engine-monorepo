"""
Project routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime, timedelta

from database import get_db
from models import Project, ProjectVersion, Build, ChatMessage, ProjectStatus, BuildStatus
from auth import get_current_user, User
from schemas import (
    ProjectCreateRequest, ProjectResponse, ProjectListResponse,
    PromptRequest, PromptResponse, RebuildResponse, RollbackRequest,
    RollbackResponse, ExportResponse, PublishResponse,
    MessagesResponse, ChatMessageResponse,
    ErrorResponse, ErrorDetail
)
from services.project_orchestrator import ProjectOrchestrator
from services.credit_service import charge_credits, InsufficientCreditsError
from services.rate_limiter import check_rate_limit
from config.credits import CREDIT_COSTS

router = APIRouter(prefix="/projects", tags=["projects"])

RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 10  # Max 10 prompts per minute per user


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response"""
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details)
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project"""
    # Safety checks
    if len(request.prompt) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "PROMPT_TOO_LONG",
                "Prompt exceeds maximum length of 5000 characters"
            ).dict()
        )
    
    orchestrator = ProjectOrchestrator(db)
    
    try:
        project, version, build = orchestrator.create_project(
            current_user.id,
            request.name,
            request.prompt
        )
        
        # Get credit info
        from services.credit_service import get_wallet
        wallet = get_wallet(db, current_user.id)
        latest_transaction = wallet["transactions"][0] if wallet["transactions"] else None
        
        # Get latest version and build for response
        latest_version = db.query(ProjectVersion).filter(
            ProjectVersion.project_id == project.id
        ).order_by(ProjectVersion.version_number.desc()).first()
        
        latest_build = db.query(Build).filter(
            Build.project_id == project.id
        ).order_by(Build.created_at.desc()).first()
        
        response = ProjectResponse.model_validate(project)
        response.latest_version = latest_version
        response.latest_build = latest_build
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response("INSUFFICIENT_CREDITS", str(e)).dict()
        )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's projects"""
    projects = db.query(Project).filter(
        Project.user_id == current_user.id
    ).order_by(Project.created_at.desc()).all()
    
    project_responses = []
    for project in projects:
        latest_version = db.query(ProjectVersion).filter(
            ProjectVersion.project_id == project.id
        ).order_by(ProjectVersion.version_number.desc()).first()
        
        latest_build = db.query(Build).filter(
            Build.project_id == project.id
        ).order_by(Build.created_at.desc()).first()
        
        response = ProjectResponse.model_validate(project)
        response.latest_version = latest_version
        response.latest_build = latest_build
        project_responses.append(response)
    
    return ProjectListResponse(projects=project_responses)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project details"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=create_error_response("FORBIDDEN", "Access denied").dict()
        )
    
    latest_version = db.query(ProjectVersion).filter(
        ProjectVersion.project_id == project_id
    ).order_by(ProjectVersion.version_number.desc()).first()
    
    latest_build = db.query(Build).filter(
        Build.project_id == project_id
    ).order_by(Build.created_at.desc()).first()
    
    response = ProjectResponse.model_validate(project)
    response.latest_version = latest_version
    response.latest_build = latest_build
    
    return response


@router.post("/{project_id}/prompt", response_model=PromptResponse)
async def iterate_project(
    project_id: str,
    request: PromptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process a chat iteration on a project"""
    # Safety checks
    if len(request.message) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "PROMPT_TOO_LONG",
                "Prompt exceeds maximum length of 5000 characters"
            ).dict()
        )
    
    if len(request.message.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(
                "EMPTY_PROMPT",
                "Prompt cannot be empty"
            ).dict()
        )
    
    # Rate limiting
    if not check_rate_limit(db, current_user.id, "prompt", RATE_LIMIT_MAX_REQUESTS, RATE_LIMIT_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=create_error_response(
                "RATE_LIMIT_EXCEEDED",
                f"Maximum {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds"
            ).dict()
        )
    
    # Check build frequency (max 1 build per 10 seconds per project)
    # TODO: Implement build frequency check
    
    orchestrator = ProjectOrchestrator(db)
    
    try:
        version, build, change_size, credits_charged, credit_info = orchestrator.iterate_project(
            project_id,
            current_user.id,
            request.message
        )
        
        response = PromptResponse(
            version=version,
            build=build,
            change_size=change_size,
            credits_charged=credits_charged
        )
        
        # Add credit info to response
        response.credit_info = credit_info
        
        return response
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response("NOT_FOUND", error_msg).dict()
            )
        elif "unauthorized" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=create_error_response("FORBIDDEN", error_msg).dict()
            )
        elif "insufficient" in error_msg.lower() or "credit" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response("INSUFFICIENT_CREDITS", error_msg).dict()
            )
        else:
            # Generic ValueError - preserve the actual error message
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_error_response("BAD_REQUEST", error_msg).dict()
            )
    except Exception as e:
        # Catch-all for unexpected errors - log and return generic message
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Unexpected error in iterate_project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response("INTERNAL_ERROR", f"An unexpected error occurred: {str(e)}").dict()
        )


@router.post("/{project_id}/rebuild", response_model=RebuildResponse)
async def rebuild_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rebuild the latest version"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    # Charge credits
    try:
        new_balance, transaction_id = charge_credits(
            db,
            current_user.id,
            CREDIT_COSTS["rebuild"],
            f"Rebuild {project.name}",
            project_id
        )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response("INSUFFICIENT_CREDITS", str(e)).dict()
        )
    
    # Get latest version
    latest_version = db.query(ProjectVersion).filter(
        ProjectVersion.project_id == project_id
    ).order_by(ProjectVersion.version_number.desc()).first()
    
    if not latest_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response("NO_VERSION", "No version to rebuild").dict()
        )
    
    # Rebuild
    orchestrator = ProjectOrchestrator(db)
    build = orchestrator._build_project(project, latest_version)
    
    db.commit()
    db.refresh(build)
    
    return RebuildResponse(build=build)


@router.post("/{project_id}/rollback", response_model=RollbackResponse)
async def rollback_project(
    project_id: str,
    request: RollbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rollback to a previous version"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    # Charge credits
    try:
        new_balance, transaction_id = charge_credits(
            db,
            current_user.id,
            CREDIT_COSTS["rollback"],
            f"Rollback {project.name}",
            project_id
        )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response("INSUFFICIENT_CREDITS", str(e)).dict()
        )
    
    # Get target version
    target_version = db.query(ProjectVersion).filter(
        ProjectVersion.id == request.version_id,
        ProjectVersion.project_id == project_id
    ).first()
    
    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", "Version not found").dict()
        )
    
    # Rollback: restore spec and rebuild
    project.current_spec = target_version.spec_snapshot
    project.status = ProjectStatus.BUILDING
    
    # Create new version from rollback
    orchestrator = ProjectOrchestrator(db)
    new_version = orchestrator._create_version(
        project_id,
        target_version.spec_snapshot,
        current_user.id,
        target_version.code_diff
    )
    db.add(new_version)
    
    # Rebuild
    build = orchestrator._build_project(project, new_version)
    
    if build.status == BuildStatus.SUCCESS:
        project.status = ProjectStatus.READY
        project.preview_url = build.preview_url
    else:
        project.status = ProjectStatus.FAILED
    
    db.commit()
    db.refresh(new_version)
    db.refresh(build)
    
    return RollbackResponse(version=new_version, build=build)


@router.post("/{project_id}/export", response_model=ExportResponse)
async def export_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export project as ZIP (paywalled)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    # Charge credits
    try:
        new_balance, transaction_id = charge_credits(
            db,
            current_user.id,
            CREDIT_COSTS["export"],
            f"Export {project.name}",
            project_id
        )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response("INSUFFICIENT_CREDITS", str(e)).dict()
        )
    
    # TODO: Generate signed download URL
    # For now, return placeholder
    download_url = f"/api/projects/{project_id}/download?token=placeholder"
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    return ExportResponse(
        download_url=download_url,
        expires_at=expires_at
    )


@router.post("/{project_id}/publish", response_model=PublishResponse)
async def publish_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish project to production (paywalled)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    # Charge credits
    try:
        new_balance, transaction_id = charge_credits(
            db,
            current_user.id,
            CREDIT_COSTS["publish"],
            f"Publish {project.name}",
            project_id
        )
    except InsufficientCreditsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response("INSUFFICIENT_CREDITS", str(e)).dict()
        )
    
    # TODO: Deploy to production via Vercel API
    # For now, return placeholder
    production_url = f"https://{project.name.lower().replace(' ', '-')}.vercel.app"
    
    project.published_url = production_url
    project.status = ProjectStatus.PUBLISHED
    db.commit()
    
    return PublishResponse(
        production_url=production_url,
        message="Project published successfully"
    )


@router.get("/{project_id}/messages", response_model=MessagesResponse)
async def get_project_messages(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat messages for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.project_id == project_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    return MessagesResponse(
        messages=[ChatMessageResponse.model_validate(msg) for msg in messages]
    )
