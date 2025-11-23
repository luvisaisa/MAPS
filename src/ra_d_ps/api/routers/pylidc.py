"""
PYLIDC Router

Endpoints for PYLIDC dataset integration.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..models.requests import PyLIDCImportRequest
from ..models.responses import ParseResponse, DocumentResponse
from ..dependencies import get_db
from ..services.pylidc_service import PyLIDCService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/scans")
async def list_scans(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    """List available PYLIDC scans"""
    service = PyLIDCService()
    return service.list_scans(limit=limit, offset=offset)


@router.get("/scans/{patient_id}", response_model=DocumentResponse)
async def get_scan(patient_id: str, db: Session = Depends(get_db)):
    """Get specific PYLIDC scan data"""
    service = PyLIDCService(db)
    result = service.get_scan(patient_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Scan {patient_id} not found")
    return result


@router.post("/import", response_model=ParseResponse)
async def import_scan(
    request: PyLIDCImportRequest,
    db: Session = Depends(get_db)
):
    """Import PYLIDC scan to Supabase"""
    service = PyLIDCService(db)
    try:
        result = await service.import_scan(
            patient_id=request.patient_id,
            extract_keywords=request.extract_keywords,
            detect_parse_case=request.detect_parse_case
        )
        return result
    except Exception as e:
        logger.error(f"PYLIDC import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/batch")
async def import_batch(
    request: PyLIDCImportRequest,
    db: Session = Depends(get_db)
):
    """Import multiple PYLIDC scans in batch"""
    service = PyLIDCService(db)
    try:
        result = await service.import_batch(
            limit=request.limit,
            extract_keywords=request.extract_keywords,
            detect_parse_case=request.detect_parse_case
        )
        return result
    except Exception as e:
        logger.error(f"PYLIDC batch import failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/annotations/{scan_id}")
async def get_annotations(scan_id: str, db: Session = Depends(get_db)):
    """Get annotations for a specific scan"""
    service = PyLIDCService(db)
    return service.get_annotations(scan_id)
