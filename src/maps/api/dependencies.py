"""
API Dependencies

Shared dependencies for FastAPI endpoints.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from typing import Generator
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Database engine
engine = None
SessionLocal = None

def get_db_engine():
    """Get or create database engine with connection pooling"""
    global engine
    if engine is None:
        if not settings.DATABASE_URL:
            raise ValueError("DATABASE_URL not configured")
        engine = create_engine(
            settings.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_pre_ping=True,  # Verify connections before using
            echo=False
        )
    return engine


def get_session_local():
    """Get or create session factory"""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_db_engine()
        )
    return SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for database sessions.

    Yields:
        Database session
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_database_connection():
    """Verify database connection is available"""
    if not settings.DATABASE_URL:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured"
        )
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )
