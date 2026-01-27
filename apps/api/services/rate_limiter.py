"""
Rate limiting service - Postgres-based for production
"""
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict
from collections import defaultdict

Base = declarative_base()


class RateLimitRecord(Base):
    """Rate limit tracking table"""
    __tablename__ = "rate_limits"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    window_start = Column(DateTime, nullable=False, index=True)
    request_count = Column(Integer, default=1)


def check_rate_limit_postgres(
    db: Session,
    user_id: str,
    endpoint: str,
    max_requests: int = 10,
    window_seconds: int = 60
) -> bool:
    """
    Check rate limit using Postgres (production).
    Returns True if within limit, False if exceeded.
    """
    import uuid
    now = datetime.utcnow()
    window_start = now.replace(second=0, microsecond=0) - timedelta(seconds=now.second % window_seconds)
    
    # Get or create rate limit record
    record = db.query(RateLimitRecord).filter(
        RateLimitRecord.user_id == user_id,
        RateLimitRecord.endpoint == endpoint,
        RateLimitRecord.window_start == window_start
    ).first()
    
    if record:
        if record.request_count >= max_requests:
            return False
        record.request_count += 1
    else:
        # Clean old records for this user/endpoint
        db.query(RateLimitRecord).filter(
            RateLimitRecord.user_id == user_id,
            RateLimitRecord.endpoint == endpoint,
            RateLimitRecord.window_start < window_start - timedelta(seconds=window_seconds * 2)
        ).delete()
        
        # Create new record
        record = RateLimitRecord(
            id=str(uuid.uuid4()),
            user_id=user_id,
            endpoint=endpoint,
            window_start=window_start,
            request_count=1
        )
        db.add(record)
    
    db.commit()
    return True


# In-memory rate limiter for dev
_rate_limit_store: Dict[str, Dict[float, int]] = defaultdict(dict)


def check_rate_limit_memory(
    user_id: str,
    endpoint: str,
    max_requests: int = 10,
    window_seconds: int = 60
) -> bool:
    """
    Check rate limit using in-memory store (development).
    Returns True if within limit, False if exceeded.
    """
    import time
    now = time.time()
    key = f"{user_id}:{endpoint}"
    
    # Clean old entries
    if key in _rate_limit_store:
        _rate_limit_store[key] = {
            ts: count for ts, count in _rate_limit_store[key].items()
            if now - ts < window_seconds
        }
    
    # Count requests in window
    recent_requests = sum(_rate_limit_store[key].values())
    
    if recent_requests >= max_requests:
        return False
    
    # Record this request
    window_start = int(now / window_seconds) * window_seconds
    _rate_limit_store[key][window_start] = _rate_limit_store[key].get(window_start, 0) + 1
    
    return True


def check_rate_limit(
    db: Session,
    user_id: str,
    endpoint: str,
    max_requests: int = 10,
    window_seconds: int = 60
) -> bool:
    """
    Check rate limit - uses Postgres in production, memory in dev.
    """
    use_postgres = os.getenv("USE_POSTGRES_RATE_LIMIT", "false").lower() == "true"
    
    if use_postgres:
        return check_rate_limit_postgres(db, user_id, endpoint, max_requests, window_seconds)
    else:
        return check_rate_limit_memory(user_id, endpoint, max_requests, window_seconds)
