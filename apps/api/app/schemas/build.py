from pydantic import BaseModel
from datetime import datetime
from app.models.build import BuildStatus as BuildStatusEnum


class BuildStatus(BaseModel):
    status: BuildStatusEnum


class BuildCreate(BaseModel):
    version_id: int


class BuildResponse(BaseModel):
    id: int
    project_id: int
    version_id: int
    status: BuildStatusEnum
    logs: str | None
    preview_url: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True
