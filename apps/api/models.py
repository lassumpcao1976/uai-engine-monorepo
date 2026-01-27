"""
Database models for UAI Engine
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Boolean, 
    ForeignKey, JSON, Numeric, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
import enum

# Base is imported from database module
from database import Base


class UserRole(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class BuildStatus(str, enum.Enum):
    PENDING = "pending"
    BUILDING = "building"
    SUCCESS = "success"
    FAILED = "failed"
    REPAIRING = "repairing"


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    BUILDING = "building"
    READY = "ready"
    FAILED = "failed"
    PUBLISHED = "published"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.FREE)
    credits = Column(Numeric(10, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    initial_prompt = Column(Text, nullable=False)
    current_spec = Column(JSON)  # Structured project specification
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    preview_url = Column(String)
    published_url = Column(String)
    custom_domain = Column(String)
    watermark_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan", order_by="desc(ProjectVersion.version_number)")
    builds = relationship("Build", back_populates="project", cascade="all, delete-orphan", order_by="desc(Build.created_at)")
    chat_messages = relationship("ChatMessage", back_populates="project", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ProjectVersion(Base):
    __tablename__ = "project_versions"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    spec_snapshot = Column(JSON, nullable=False)
    code_diff = Column(JSON)  # Unified diff format
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)  # User ID or "system"

    project = relationship("Project", back_populates="versions")


class Build(Base):
    __tablename__ = "builds"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    version_id = Column(String, ForeignKey("project_versions.id"))
    status = Column(SQLEnum(BuildStatus), default=BuildStatus.PENDING)
    attempt_number = Column(Integer, default=1)
    build_logs = Column(Text)
    error_message = Column(Text)
    lint_output = Column(Text)
    build_output = Column(Text)
    preview_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    project = relationship("Project", back_populates="builds")
    version = relationship("ProjectVersion")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="chat_messages")


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)  # Positive for credits added, negative for spent
    description = Column(Text)
    transaction_type = Column(String, nullable=False)  # "purchase", "publish", "export", "custom_domain", "refund"
    project_id = Column(String, ForeignKey("projects.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
