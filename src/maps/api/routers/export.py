"""
Export Router

Endpoints for data export in various formats.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..models.requests import ExportRequest
from ..models.responses import ExportResponse
from ..dependencies import get_db
from ..services.export_service import ExportService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ExportResponse)
async def export_data(export_request: dict, db: Session = Depends(get_db)):
    """
    Unified export endpoint for all formats

    Supports: excel, json, csv, parquet
    """
    format = export_request.get("format", "json").lower()
    filters = export_request.get("filters", {})

    # Validate format
    valid_formats = ["excel", "json", "csv", "parquet"]
    if format not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{format}'. Valid formats: {', '.join(valid_formats)}"
        )

    service = ExportService(db)

    # For now, return a simple response indicating export initiated
    # In production, this would create a background job
    return {
        "status": "success",
        "format": format,
        "record_count": 0,  # Required field - will be populated with actual data
        "filename": None,
        "download_url": None,
        "file_size_bytes": None
    }


@router.get("/universal-wide")
async def export_universal_wide(
    format: str = Query(default="csv", regex="^(csv|excel|json)$"),
    db: Session = Depends(get_db)
):
    """Export universal wide view"""
    service = ExportService(db)
    return await service.export_view("export_universal_wide", format=format)


@router.get("/lidc-analysis-ready")
async def export_lidc_analysis_ready(
    format: str = Query(default="csv"),
    db: Session = Depends(get_db)
):
    """Export LIDC analysis-ready format (SPSS/R/Stata)"""
    service = ExportService(db)
    return await service.export_view("export_lidc_analysis_ready", format=format)


@router.get("/lidc-with-links")
async def export_lidc_with_links(
    format: str = Query(default="csv"),
    db: Session = Depends(get_db)
):
    """Export LIDC with TCIA links"""
    service = ExportService(db)
    return await service.export_view("export_lidc_with_links", format=format)


@router.get("/radiologist-data")
async def export_radiologist_data(
    format: str = Query(default="csv"),
    db: Session = Depends(get_db)
):
    """Export radiologist inter-rater analysis format"""
    service = ExportService(db)
    return await service.export_view("export_radiologist_data", format=format)


@router.get("/top-keywords")
async def export_top_keywords(
    format: str = Query(default="csv"),
    limit: int = Query(default=1000, le=10000),
    db: Session = Depends(get_db)
):
    """Export top keywords by relevance"""
    service = ExportService(db)
    return await service.export_view("export_top_keywords", format=format, limit=limit)


@router.post("/custom", response_model=ExportResponse)
async def export_custom(
    request: ExportRequest,
    db: Session = Depends(get_db)
):
    """Custom export with filtering"""
    service = ExportService(db)
    return await service.export_custom(
        format=request.format,
        view_name=request.view_name,
        document_ids=request.document_ids,
        parse_case=request.parse_case,
        include_metadata=request.include_metadata,
        include_keywords=request.include_keywords
    )


@router.get("/format/{view_name}")
async def export_any_view(
    view_name: str,
    format: str = Query(default="csv"),
    db: Session = Depends(get_db)
):
    """Export any view by name"""
    service = ExportService(db)
    return await service.export_view(view_name, format=format)
