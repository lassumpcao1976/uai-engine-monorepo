"""
Database configuration and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://uaiengine:uaiengine@localhost:5432/uaiengine")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import here to avoid circular import
    from models import Base
    from services.rate_limiter import Base as RateLimitBase
    Base.metadata.create_all(bind=engine)
    RateLimitBase.metadata.create_all(bind=engine)
