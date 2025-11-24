"""
Detection Details Router

API endpoints for retrieving parse case detection analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ..dependencies import get_db
from ...database.detection_models import DetectionDetails, DetectionSummary
from ...detectors.parse_case_schemas import (
    get_expected_attributes,
    get_all_parse_cases,
    get_parse_case_summary,
    validate_parse_case
)

router = APIRouter()
logger = logging.getLogger(__name__)


class DetectionDetailsResponse(BaseModel):
    """Detection details API response"""
    id: str
    queue_item_id: Optional[str] = None
    document_id: Optional[str] = None
    parse_case: str
    confidence: float
    expected_attributes: List[dict]
    detected_attributes: List[dict]
    missing_attributes: List[dict]
    match_percentage: float
    total_expected: int
    total_detected: int
    field_analysis: List[dict]
    detector_type: str
    detected_at: str


class ParseCaseSchemaResponse(BaseModel):
    """Parse case schema API response"""
    parse_case: str
    total_attributes: int
    required_attributes: int
    optional_attributes: int
    attribute_names: List[str]
    required_attribute_names: List[str]
    attributes: List[dict]


@router.get("/queue-item/{queue_item_id}", response_model=DetectionDetailsResponse)
async def get_detection_by_queue_item(
    queue_item_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detection details for a queue item.

    Args:
        queue_item_id: Queue item ID

    Returns:
        Detection details with attribute analysis

    Raises:
        404: Detection details not found
    """
    # Note: Since approval queue is in-memory, we check both database and in-memory queue
    detection = db.query(DetectionDetails).filter(
        DetectionDetails.queue_item_id == queue_item_id
    ).first()

    if not detection:
        raise HTTPException(
            status_code=404,
            detail=f"Detection details not found for queue item '{queue_item_id}'"
        )

    return DetectionDetailsResponse(**detection.to_dict())


@router.get("/document/{document_id}", response_model=DetectionDetailsResponse)
async def get_detection_by_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detection details for a document.

    Args:
        document_id: Document UUID

    Returns:
        Detection details with attribute analysis

    Raises:
        404: Detection details not found
    """
    detection = db.query(DetectionDetails).filter(
        DetectionDetails.document_id == document_id
    ).first()

    if not detection:
        raise HTTPException(
            status_code=404,
            detail=f"Detection details not found for document '{document_id}'"
        )

    return DetectionDetailsResponse(**detection.to_dict())


@router.get("/parse-cases", response_model=List[str])
async def list_parse_cases():
    """
    Get list of all registered parse cases.

    Returns:
        List of parse case names
    """
    return get_all_parse_cases()


@router.get("/parse-cases/{parse_case}/schema", response_model=ParseCaseSchemaResponse)
async def get_parse_case_schema(parse_case: str):
    """
    Get expected attributes schema for a parse case.

    Args:
        parse_case: Parse case name

    Returns:
        Parse case schema with expected attributes

    Raises:
        404: Parse case not found
    """
    if not validate_parse_case(parse_case):
        raise HTTPException(
            status_code=404,
            detail=f"Parse case '{parse_case}' not found in registry"
        )

    summary = get_parse_case_summary(parse_case)
    attributes = get_expected_attributes(parse_case)

    return ParseCaseSchemaResponse(
        parse_case=summary["parse_case"],
        total_attributes=summary["total_attributes"],
        required_attributes=summary["required_attributes"],
        optional_attributes=summary["optional_attributes"],
        attribute_names=summary["attribute_names"],
        required_attribute_names=summary["required_attribute_names"],
        attributes=attributes
    )


@router.get("/stats")
async def get_detection_stats(db: Session = Depends(get_db)):
    """
    Get detection statistics.

    Returns:
        Statistics about detection performance
    """
    from sqlalchemy import func

    total_detections = db.query(func.count(DetectionDetails.id)).scalar()

    if total_detections == 0:
        return {
            "total_detections": 0,
            "avg_confidence": 0.0,
            "avg_match_percentage": 0.0,
            "by_parse_case": {}
        }

    avg_confidence = db.query(func.avg(DetectionDetails.confidence)).scalar()
    avg_match = db.query(func.avg(DetectionDetails.match_percentage)).scalar()

    # Group by parse case
    from sqlalchemy import distinct
    parse_cases = db.query(distinct(DetectionDetails.parse_case)).all()

    by_parse_case = {}
    for (parse_case,) in parse_cases:
        case_stats = db.query(
            func.count(DetectionDetails.id),
            func.avg(DetectionDetails.confidence),
            func.avg(DetectionDetails.match_percentage)
        ).filter(DetectionDetails.parse_case == parse_case).first()

        by_parse_case[parse_case] = {
            "count": case_stats[0],
            "avg_confidence": float(case_stats[1]) if case_stats[1] else 0.0,
            "avg_match_percentage": float(case_stats[2]) if case_stats[2] else 0.0
        }

    return {
        "total_detections": total_detections,
        "avg_confidence": float(avg_confidence) if avg_confidence else 0.0,
        "avg_match_percentage": float(avg_match) if avg_match else 0.0,
        "by_parse_case": by_parse_case
    }


@router.get("/recent", response_model=List[DetectionDetailsResponse])
async def list_recent_detections(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get recent detection details.

    Args:
        limit: Maximum number of detections to return

    Returns:
        List of recent detection details
    """
    detections = db.query(DetectionDetails).order_by(
        DetectionDetails.detected_at.desc()
    ).limit(limit).all()

    return [DetectionDetailsResponse(**d.to_dict()) for d in detections]


@router.get("/low-confidence", response_model=List[DetectionDetailsResponse])
async def list_low_confidence_detections(
    threshold: float = Query(0.6, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get detections with low confidence scores.

    Args:
        threshold: Confidence threshold (default 0.6)
        limit: Maximum number to return

    Returns:
        List of low-confidence detections
    """
    detections = db.query(DetectionDetails).filter(
        DetectionDetails.confidence < threshold
    ).order_by(DetectionDetails.confidence).limit(limit).all()

    return [DetectionDetailsResponse(**d.to_dict()) for d in detections]
