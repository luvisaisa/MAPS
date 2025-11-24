"""
MAPS FastAPI Application

Main FastAPI application with all routers and middleware.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging

from .config import settings
from .routers import (
    parse_cases,
    parse,
    pylidc,
    documents,
    keywords,
    views,
    export,
    visualization,
    analytics,
    database,
    batch,
    search,
    profiles,
    approval_queue,
    detection_details
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add response compression for large payloads
if settings.ENABLE_RESPONSE_COMPRESSION:
    app.add_middleware(GZipMiddleware, minimum_size=1000)  # Compress responses > 1KB


# Add file size limit middleware for uploads
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Limit upload file size to prevent memory issues"""
    max_upload_size = 10 * 1024 * 1024  # 10MB

    if request.method in ["POST", "PUT"]:
        content_type = request.headers.get("content-type", "")
        if "multipart/form-data" in content_type or "application/octet-stream" in content_type:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > max_upload_size:
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "File too large",
                        "detail": f"Maximum upload size is {max_upload_size // (1024*1024)}MB",
                        "max_size_bytes": max_upload_size
                    }
                )

    response = await call_next(request)
    return response


# Include routers
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["Profiles"])
app.include_router(approval_queue.router, prefix="/api/v1/approval-queue", tags=["Approval Queue"])
app.include_router(detection_details.router, prefix="/api/v1/detection-details", tags=["Detection Details"])
app.include_router(parse_cases.router, prefix="/api/v1/parse-cases", tags=["Parse Cases"])
app.include_router(parse.router, prefix="/api/v1/parse", tags=["Parsing"])
app.include_router(pylidc.router, prefix="/api/v1/pylidc", tags=["PYLIDC"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(keywords.router, prefix="/api/v1/keywords", tags=["Keywords"])
app.include_router(views.router, prefix="/api/v1/views", tags=["Views"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])
app.include_router(visualization.router, prefix="/api/v1/3d", tags=["3D Visualization"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(database.router, prefix="/api/v1/db", tags=["Database"])
app.include_router(batch.router, prefix="/api/v1/batch", tags=["Batch"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])


@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with service information"""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": settings.API_DESCRIPTION,
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "parse_cases": "/api/v1/parse-cases",
            "parse": "/api/v1/parse",
            "pylidc": "/api/v1/pylidc",
            "documents": "/api/v1/documents",
            "keywords": "/api/v1/keywords",
            "views": "/api/v1/views",
            "export": "/api/v1/export",
            "3d": "/api/v1/3d",
            "analytics": "/api/v1/analytics",
            "database": "/api/v1/db",
            "batch": "/api/v1/batch",
            "search": "/api/v1/search"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check(detailed: bool = False):
    """
    Health check endpoint

    Args:
        detailed: If True, includes database and service status checks
    """
    response = {
        "status": "healthy",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION
    }

    if detailed:
        # Check database connectivity
        try:
            from .database import get_session
            db = next(get_session())
            db.execute("SELECT 1")
            db.close()
            database_status = "connected"
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            database_status = "unavailable"

        response["database"] = {
            "status": database_status,
            "backend": settings.DATABASE_BACKEND if hasattr(settings, 'DATABASE_BACKEND') else "unknown"
        }

        response["services"] = {
            "api": "operational",
            "parsing": "operational",
            "export": "operational"
        }

    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": request.url.path
        }
    )


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info(f"Documentation available at /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info(f"Shutting down {settings.API_TITLE}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )
