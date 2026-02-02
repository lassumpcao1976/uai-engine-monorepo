from fastapi import APIRouter
from app.api.v1 import auth, projects, versions, builds, credits

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(versions.router, prefix="/versions", tags=["versions"])
api_router.include_router(builds.router, prefix="/builds", tags=["builds"])
api_router.include_router(credits.router, prefix="/credits", tags=["credits"])
