from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://uai:uai_password@localhost:5432/uai_engine"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "change-me-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Credits
    credits_per_build: int = 10
    credits_per_export: int = 50
    initial_credits: int = 1000
    
    # Runner
    runner_url: str = "http://runner:8001"
    
    # Monitoring
    prometheus_port: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
