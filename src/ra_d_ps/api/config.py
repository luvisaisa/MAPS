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
    API_TITLE: str = "RA-D-PS API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Radiology XML Data Processing System REST API"

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

    class Config:
        case_sensitive = True


# Global settings instance
settings = Settings()

# Ensure upload directory exists
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
