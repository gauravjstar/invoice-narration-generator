"""Application Configuration"""
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://invoice_user:invoice_password@localhost:5432/invoice_db"
    DATABASE_ECHO: bool = False
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    
    # OCR
    OCR_ENGINE: str = "paddleocr"
    OCR_LANGUAGE: str = "en"
    OCR_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 52428800
    UPLOAD_FOLDER: str = "./uploads"
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".jpg", ".jpeg", ".png"]
    
    # Batch Processing
    BATCH_SIZE_LIMIT: int = 1000
    MAX_WORKERS: int = 4
    PROCESS_TIMEOUT: int = 300
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    
    # Duplicate Detection
    DUPLICATE_SIMILARITY_THRESHOLD: float = 0.95
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
