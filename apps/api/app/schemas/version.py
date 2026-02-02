from pydantic import BaseModel
from datetime import datetime
from typing import Any


class VersionCreate(BaseModel):
    prompt: str


class VersionResponse(BaseModel):
    id: int
    project_id: int
    prompt: str
    file_tree: dict[str, Any] | None
    unified_diff: str | None
    created_at: datetime

    class Config:
        from_attributes = True
