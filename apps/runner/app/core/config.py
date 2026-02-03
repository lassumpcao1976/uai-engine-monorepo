from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_url: str = "http://api:8000"
    build_host: str = "tcp://buildkit:1234"
    work_dir: str = "/tmp/uai-builds"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
