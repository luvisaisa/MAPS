"""
Database Router

Endpoints for database operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from ..dependencies import get_db
from ..services.database_service import DatabaseService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/refresh-views")
async def refresh_views(db: Session = Depends(get_db)):
    """Refresh materialized views"""
    service = DatabaseService(db)
    try:
        result = service.refresh_views()
        return {"status": "success", "refreshed_views": result}
    except Exception as e:
        logger.error(f"Refresh views failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backfill-keywords")
async def backfill_keywords(db: Session = Depends(get_db)):
    """Backfill canonical keyword links"""
    service = DatabaseService(db)
    try:
        result = service.backfill_canonical_keywords()
        return {"status": "success", "backfilled_count": result}
    except Exception as e:
        logger.error(f"Backfill keywords failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_database_statistics(db: Session = Depends(get_db)):
    """Public database statistics"""
    service = DatabaseService(db)
    return service.get_statistics()


@router.post("/vacuum")
async def vacuum_database(db: Session = Depends(get_db)):
    """Optimize database (admin only)"""
    service = DatabaseService(db)
    try:
        service.vacuum()
        return {"status": "success", "message": "Database optimized"}
    except Exception as e:
        logger.error(f"Vacuum failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
