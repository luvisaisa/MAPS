#!/usr/bin/env python3
"""
MAPS API Startup Script

Medical Annotation Processing System - FastAPI Backend
Launches the FastAPI server with WebSocket support for real-time updates.
"""

import uvicorn
from src.ra_d_ps.api.config import settings

if __name__ == "__main__":
    print(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    print(f"Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"ReDoc: http://{settings.HOST}:{settings.PORT}/redoc")

    uvicorn.run(
        "src.ra_d_ps.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )
