from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/lms.db"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    STATIC_DIR: str = "static"
    UPLOAD_DIR: str = "uploads"
    DATA_DIR: str = "data"
    LOGS_DIR: str = "logs"
    
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    
    WEBSOCKET_HEARTBEAT_INTERVAL: int = 30
    
    SIGNIN_TIMEOUT_MINUTES: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
