from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class BuildStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Build(Base):
    __tablename__ = "builds"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    version_id = Column(Integer, ForeignKey("versions.id"), nullable=False)
    status = Column(SQLEnum(BuildStatus), default=BuildStatus.PENDING, nullable=False)
    logs = Column(Text, nullable=True)
    preview_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="builds")
    version = relationship("Version", back_populates="builds")
