"""
Views Router

Endpoints for accessing Supabase views.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..models.responses import ViewDataResponse
from ..dependencies import get_db
from ..services.view_service import ViewService

router = APIRouter()
logger = logging.getLogger(__name__)


# Universal Views
@router.get("/file-summary")
async def file_summary(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Per-file aggregated statistics"""
    service = ViewService(db)
    return service.get_view("file_summary", limit=limit, offset=offset)


@router.get("/segment-statistics")
async def segment_statistics(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Per-segment metrics"""
    service = ViewService(db)
    return service.get_view("segment_statistics", limit=limit)


@router.get("/numeric-data-flat")
async def numeric_data_flat(limit: int = Query(default=100), db: Session = Depends(get_db)):
    """Auto-extracted numeric fields"""
    service = ViewService(db)
    return service.get_view("numeric_data_flat", limit=limit)


# LIDC Medical Views
@router.get("/lidc/patient-summary")
async def lidc_patient_summary(
    limit: int = Query(default=100),
    db: Session = Depends(get_db)
):
    """Patient-level consensus"""
    service = ViewService(db)
    return service.get_view("lidc_patient_summary", limit=limit)


@router.get("/lidc/nodule-analysis")
async def lidc_nodule_analysis(
    limit: int = Query(default=100),
    db: Session = Depends(get_db)
):
    """Per-nodule analysis"""
    service = ViewService(db)
    return service.get_view("lidc_nodule_analysis", limit=limit)


@router.get("/lidc/3d-contours")
async def lidc_3d_contours(
    patient_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """3D spatial coordinates"""
    service = ViewService(db)
    return service.get_view("lidc_3d_contours", filters={"patient_id": patient_id} if patient_id else None)


# Keyword Navigation Views
@router.get("/keyword-occurrence-map")
async def keyword_occurrence_map(
    limit: int = Query(default=100),
    db: Session = Depends(get_db)
):
    """Keyword locations"""
    service = ViewService(db)
    return service.get_view("keyword_occurrence_map", limit=limit)


@router.get("/file-keyword-summary")
async def file_keyword_summary(
    limit: int = Query(default=100),
    db: Session = Depends(get_db)
):
    """Keywords per file"""
    service = ViewService(db)
    return service.get_view("file_keyword_summary", limit=limit)
