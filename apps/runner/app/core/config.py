from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_url: str = "http://api:8000"
    docker_socket: str = "/var/run/docker.sock"
    work_dir: str = "/tmp/uai-builds"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
