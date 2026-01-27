"""
UAI Engine API - Main application
"""
import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from database import get_db, init_db
from models import Base
from routes import auth, projects, credits, builds, preview
from config.credits import get_credit_costs

app = FastAPI(
    title="UAI Engine API",
    version="2.0.0",
    description="AI-powered application builder platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://web:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format"""
    # If detail is already a dict (from create_error_response), use it
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    # If detail is a string, wrap it
    elif isinstance(exc.detail, str):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "details": None
                }
            }
        )
    # Fallback
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": "An error occurred",
                    "details": exc.detail
                }
            }
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors with consistent format"""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"type": type(exc).__name__}
            }
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            init_db()
            print("Database tables created successfully")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Database not ready, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                print(f"Warning: Could not create database tables after {max_retries} attempts: {e}")
                print("Tables will be created on first database request.")


# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


# Credit costs endpoint (for frontend)
@app.get("/credits/costs")
async def get_credit_costs_endpoint():
    """Get all credit costs (for frontend display)"""
    return get_credit_costs()


# Include routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(credits.router)
app.include_router(builds.router)
app.include_router(preview.router)
