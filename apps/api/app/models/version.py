from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    prompt = Column(Text, nullable=False)
    file_tree = Column(JSON, nullable=True)  # Tree structure of files
    unified_diff = Column(Text, nullable=True)  # Unified diff from previous version
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="versions")
    builds = relationship("Build", back_populates="version")
