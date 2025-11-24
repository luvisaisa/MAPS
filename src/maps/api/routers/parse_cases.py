"""
Parse Cases Router

Endpoints for parse case management and detection.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..models.requests import DetectRequest
from ..models.responses import (
    ParseCaseListResponse,
    ParseCaseInfo,
    ParseCaseStatsResponse,
    DetectResponse,
    StructureAnalysis
)
from ..dependencies import get_db
from ..services.parse_case_service import ParseCaseService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=ParseCaseListResponse)
async def list_parse_cases():
    """
    List all recognized parse cases.

    Returns information about all parse case types supported by the system.
    """
    service = ParseCaseService()
    parse_cases = service.get_all_parse_cases()
    return ParseCaseListResponse(
        parse_cases=parse_cases,
        total=len(parse_cases)
    )


@router.get("/{name}", response_model=ParseCaseInfo)
async def get_parse_case(name: str):
    """
    Get details about a specific parse case.

    Args:
        name: Parse case name

    Returns:
        Parse case information including fields and requirements
    """
    service = ParseCaseService()
    parse_case = service.get_parse_case(name)
    if not parse_case:
        raise HTTPException(status_code=404, detail=f"Parse case '{name}' not found")
    return parse_case


@router.post("/detect", response_model=DetectResponse)
async def detect_parse_case(
    file: UploadFile = File(...),
    request: DetectRequest = Depends()
):
    """
    Detect parse case from uploaded file.

    Does not insert data into database, only analyzes structure.

    Args:
        file: XML/PDF file to analyze
        request: Detection options

    Returns:
        Detected parse case with confidence score and structure analysis
    """
    service = ParseCaseService()

    try:
        content = await file.read()
        result = service.detect_from_content(
            content,
            file.filename,
            analyze_structure=request.analyze_structure
        )
        return result
    except Exception as e:
        logger.error(f"Parse case detection failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=ParseCaseStatsResponse)
async def get_parse_case_stats(db: Session = Depends(get_db)):
    """
    Get parse case statistics from database.

    Returns:
        Distribution of parse cases across all documents
    """
    service = ParseCaseService(db)
    return service.get_statistics()
