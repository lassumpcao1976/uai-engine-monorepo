"""
Pydantic schemas for request/response validation
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


# Error response schema
class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Auth schemas
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    credits: float

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Build schemas (defined first as it's referenced by VersionResponse)
class BuildResponse(BaseModel):
    id: str
    project_id: str
    version_id: Optional[str]
    status: str
    attempt_number: int
    build_logs: Optional[str]
    error_message: Optional[str]
    lint_output: Optional[str]
    build_output: Optional[str]
    preview_url: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Version schemas (defined before ProjectResponse as it's referenced)
class VersionResponse(BaseModel):
    id: str
    project_id: str
    version_number: int
    spec_snapshot: Dict[str, Any]
    code_diff: Optional[Dict[str, Any]]
    unified_diff_text: Optional[str] = None  # Human-readable unified diff
    created_at: datetime
    created_by: Optional[str]
    build: Optional[BuildResponse] = None

    class Config:
        from_attributes = True


# Project schemas
class ProjectCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    prompt: str = Field(..., min_length=1)


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str]
    initial_prompt: str
    status: str
    preview_url: Optional[str]
    published_url: Optional[str]
    watermark_enabled: bool
    created_at: datetime
    updated_at: datetime
    latest_version: Optional[VersionResponse] = None
    latest_build: Optional[BuildResponse] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]


# Chat schemas
class PromptRequest(BaseModel):
    message: str = Field(..., min_length=1)


class PromptResponse(BaseModel):
    version: VersionResponse
    build: BuildResponse
    change_size: str  # "small", "medium", "large"
    credits_charged: float
    credit_info: Optional[Dict[str, Any]] = None  # charged_action, charged_amount, wallet_balance_after, transaction_id


# File schemas
class FileNode(BaseModel):
    name: str
    path: str
    type: str  # "file" or "directory"
    children: Optional[List[FileNode]] = None


class FileContentResponse(BaseModel):
    path: str
    content: str
    version_id: Optional[str]


# Credit schemas (TransactionResponse defined first as it's referenced by WalletResponse)
class TransactionResponse(BaseModel):
    id: str
    amount: float
    description: Optional[str]
    transaction_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class WalletResponse(BaseModel):
    credits: float
    transactions: List[TransactionResponse]


class TopUpIntentRequest(BaseModel):
    amount: float = Field(..., gt=0)


class TopUpIntentResponse(BaseModel):
    client_secret: str  # Stripe client secret placeholder
    amount: float


class GrantCreditsRequest(BaseModel):
    user_id: str
    amount: float = Field(..., gt=0)
    reason: str = "Admin grant"


# Rebuild/Rollback schemas
class RebuildResponse(BaseModel):
    build: BuildResponse


class RollbackRequest(BaseModel):
    version_id: str


class RollbackResponse(BaseModel):
    version: VersionResponse
    build: BuildResponse


# Export/Publish schemas
class ExportResponse(BaseModel):
    download_url: str
    expires_at: datetime


class PublishResponse(BaseModel):
    production_url: str
    message: str


# Chat message schemas
class ChatMessageResponse(BaseModel):
    id: str
    project_id: str
    user_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessagesResponse(BaseModel):
    messages: List[ChatMessageResponse]


# Rebuild models after all forward references are resolved
# This ensures Pydantic v2 can properly resolve all forward references
# when using string annotations (from __future__ import annotations)
FileNode.model_rebuild()
