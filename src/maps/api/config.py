"""
API Configuration

Environment variables and configuration settings for the API.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class Settings(BaseModel):
    """API configuration settings"""

    # API Settings
    API_TITLE: str = "MAPS API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Medical Annotation Processing System - FastAPI Backend with Real-time Updates"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # CORS Settings
    CORS_ORIGINS: list = ["*"]  # Configure for production

    # Supabase Settings
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: Optional[str] = os.getenv("SUPABASE_KEY")
    SUPABASE_DB_URL: Optional[str] = os.getenv("SUPABASE_DB_URL")

    # Database Settings
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", os.getenv("SUPABASE_DB_URL"))

    # File Storage Settings
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set = {".xml", ".pdf", ".json"}

    # Processing Settings
    DEFAULT_BATCH_SIZE: int = 100
    MAX_BATCH_SIZE: int = 1000

    # Profiles Directory
    PROFILE_DIR: Path = Path("./src/ra_d_ps/profiles")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Caching Settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes default
    PYLIDC_CACHE_TTL: int = int(os.getenv("PYLIDC_CACHE_TTL", "3600"))  # 1 hour for PYLIDC metadata
    ENABLE_RESPONSE_COMPRESSION: bool = os.getenv("ENABLE_RESPONSE_COMPRESSION", "true").lower() == "true"

    # Database Connection Pooling
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "20"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # Recycle connections after 1 hour
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    class Config:
        case_sensitive = True


# Global settings instance
settings = Settings()

# Ensure upload directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
