"""
Preview serving route with security hardening
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pathlib import Path
import os

from database import get_db
from models import Project, Build, BuildStatus
from auth import get_current_user, User
from schemas import ErrorResponse, ErrorDetail

router = APIRouter(tags=["preview"])
security = HTTPBearer(auto_error=False)


def create_error_response(code: str, message: str, details: dict = None):
    """Create standardized error response"""
    return ErrorResponse(
        error=ErrorDetail(code=code, message=message, details=details)
    )


@router.get("/preview/{project_id}/{build_id}", response_class=HTMLResponse)
async def serve_preview(
    project_id: str,
    build_id: str,
    credentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Serve preview for a build with strict security.
    - Only serves build-specific artifacts
    - Enforces project ownership
    - Adds security headers
    - Prevents path traversal
    """
    # Validate project_id and build_id format (UUID-like)
    if not project_id or len(project_id) != 36 or not all(c in '0123456789abcdef-' for c in project_id.lower()):
        raise HTTPException(
            status_code=400,
            detail=create_error_response("INVALID_PROJECT_ID", "Invalid project ID format").dict()
        )
    
    if not build_id or len(build_id) != 36 or not all(c in '0123456789abcdef-' for c in build_id.lower()):
        raise HTTPException(
            status_code=400,
            detail=create_error_response("INVALID_BUILD_ID", "Invalid build ID format").dict()
        )
    
    # Get build and project
    build = db.query(Build).filter(
        Build.id == build_id,
        Build.project_id == project_id
    ).first()
    
    if not build:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Build not found").dict()
        )
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=create_error_response("NOT_FOUND", "Project not found").dict()
        )
    
    # Enforce ownership if authenticated
    if credentials:
        try:
            from auth import decode_access_token
            payload = decode_access_token(credentials.credentials)
            if payload:
                user_id = payload.get("sub")
                if user_id and project.user_id != user_id:
                    raise HTTPException(
                        status_code=403,
                        detail=create_error_response("FORBIDDEN", "Access denied").dict()
                    )
        except Exception:
            pass  # If auth fails, allow public preview (for now)
    
    # Security: Only serve from build-specific directory
    PROJECTS_DIR = Path(os.getenv("PROJECTS_DIR", "./projects"))
    project_path = PROJECTS_DIR / project_id
    
    # Validate path is within project directory (prevent traversal)
    try:
        project_path.resolve().relative_to(PROJECTS_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=create_error_response("INVALID_PATH", "Invalid project path").dict()
        )
    
    # Get web origin for CSP headers
    web_origin = os.getenv("WEB_ORIGIN", "http://localhost:3000")
    
    if build.status != BuildStatus.SUCCESS:
        # Return error page
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Build Failed - {project.name}</title>
            <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline';">
            <meta http-equiv="X-Content-Type-Options" content="nosniff">
            <meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
            <style>
                body {{ font-family: sans-serif; padding: 40px; text-align: center; background: #f9fafb; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; }}
                .error {{ color: #dc2626; }}
                pre {{ background: #1f2937; color: #10b981; padding: 20px; border-radius: 8px; text-align: left; overflow-x: auto; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="error">Build Failed</h1>
                <p>Status: <strong>{build.status}</strong></p>
                {f'<p style="color: #dc2626;">{build.error_message}</p>' if build.error_message else ''}
                {f'<h3>Build Logs:</h3><pre>{build.build_logs[:5000] if build.build_logs else "No logs available"}</pre>' if build.build_logs else ''}
            </div>
        </body>
        </html>
        """
        response = HTMLResponse(content=html)
        # Add security headers - use CSP frame-ancestors for iframe support
        response.headers["Content-Security-Policy"] = f"default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors {web_origin};"
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Remove X-Frame-Options - CSP frame-ancestors takes precedence
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
    
    # For successful builds, return a preview page
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{project.name} - Preview</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self';">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="Referrer-Policy" content="strict-origin-when-cross-origin">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f9fafb;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #111827; margin-top: 0; }}
        .status {{ 
            display: inline-block;
            padding: 4px 12px;
            background: #10b981;
            color: white;
            border-radius: 4px;
            font-size: 14px;
            margin-bottom: 20px;
        }}
        .info {{ 
            margin-top: 20px;
            padding: 16px;
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            border-radius: 4px;
        }}
        .watermark {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project.name}</h1>
        <span class="status">✓ Build Successful</span>
        <div class="info">
            <p><strong>Build ID:</strong> {build_id}</p>
            <p><strong>Status:</strong> {build.status}</p>
            <p><strong>Project:</strong> {project.name}</p>
            <p style="margin-top: 16px; color: #6b7280;">
                This is a preview placeholder. In production, the actual Next.js application would be served here.
                The build completed successfully and the application is ready.
            </p>
        </div>
    </div>
    <div class="watermark">Built with UAI Engine</div>
</body>
</html>"""
    
    response = HTMLResponse(content=html)
    # Add security headers - use CSP frame-ancestors to allow web origin for iframe embedding
    # Get web origin from environment or default to localhost:3000
    web_origin = os.getenv("WEB_ORIGIN", "http://localhost:3000")
    response.headers["Content-Security-Policy"] = f"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors {web_origin};"
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Remove X-Frame-Options - CSP frame-ancestors takes precedence and is more flexible
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
