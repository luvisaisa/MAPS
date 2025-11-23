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
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    patient_id: Optional[str] = Query(default=None),
    # scan-level filters
    min_slices: Optional[int] = Query(default=None),
    max_slices: Optional[int] = Query(default=None),
    min_thickness: Optional[float] = Query(default=None),
    max_thickness: Optional[float] = Query(default=None),
    min_spacing: Optional[float] = Query(default=None),
    max_spacing: Optional[float] = Query(default=None),
    contrast_used: Optional[bool] = Query(default=None),
    has_nodules: Optional[bool] = Query(default=None),
    min_annotations: Optional[int] = Query(default=None),
    max_annotations: Optional[int] = Query(default=None),
    # annotation characteristic filters (1-5 scale)
    min_subtlety: Optional[int] = Query(default=None, ge=1, le=5),
    max_subtlety: Optional[int] = Query(default=None, ge=1, le=5),
    min_malignancy: Optional[int] = Query(default=None, ge=1, le=5),
    max_malignancy: Optional[int] = Query(default=None, ge=1, le=5),
    min_sphericity: Optional[int] = Query(default=None, ge=1, le=5),
    max_sphericity: Optional[int] = Query(default=None, ge=1, le=5),
    min_margin: Optional[int] = Query(default=None, ge=1, le=5),
    max_margin: Optional[int] = Query(default=None, ge=1, le=5),
    min_lobulation: Optional[int] = Query(default=None, ge=1, le=5),
    max_lobulation: Optional[int] = Query(default=None, ge=1, le=5),
    min_spiculation: Optional[int] = Query(default=None, ge=1, le=5),
    max_spiculation: Optional[int] = Query(default=None, ge=1, le=5),
    min_texture: Optional[int] = Query(default=None, ge=1, le=5),
    max_texture: Optional[int] = Query(default=None, ge=1, le=5),
    calcification: Optional[int] = Query(default=None, ge=1, le=6, description="1=popcorn, 2=laminated, 3=solid, 4=non-central, 5=central, 6=absent"),
    # nodule size filters
    min_diameter: Optional[float] = Query(default=None, description="Minimum nodule diameter in mm"),
    max_diameter: Optional[float] = Query(default=None, description="Maximum nodule diameter in mm"),
    # sorting
    sort_by: str = Query(default="patient_id"),
    sort_order: str = Query(default="asc")
):
    """
    List available PYLIDC scans with comprehensive filtering.
    
    Scan-level filters:
    - patient_id: partial match on patient ID
    - min/max_slices: slice count range
    - min/max_thickness: slice thickness in mm
    - min/max_spacing: slice spacing in mm
    - contrast_used: true/false for contrast agent
    - has_nodules: true/false for annotation presence
    - min/max_annotations: annotation count range
    
    Annotation characteristic filters (1-5 scale):
    - subtlety: how difficult to identify
    - malignancy: likelihood of cancer
    - sphericity: how round the nodule is
    - margin: boundary clarity
    - lobulation: irregular shape degree
    - spiculation: spiky appearance
    - texture: solid/non-solid/part-solid
    
    Perinodular and internal features:
    - calcification: 1=popcorn, 2=laminated, 3=solid, 4=non-central, 5=central, 6=absent
    - min/max_diameter: nodule size in mm
    """
    service = PyLIDCService()
    return service.list_scans(
        page=page,
        page_size=page_size,
        patient_id=patient_id,
        min_slices=min_slices,
        max_slices=max_slices,
        min_thickness=min_thickness,
        max_thickness=max_thickness,
        min_spacing=min_spacing,
        max_spacing=max_spacing,
        contrast_used=contrast_used,
        has_nodules=has_nodules,
        min_annotations=min_annotations,
        max_annotations=max_annotations,
        min_subtlety=min_subtlety,
        max_subtlety=max_subtlety,
        min_malignancy=min_malignancy,
        max_malignancy=max_malignancy,
        min_sphericity=min_sphericity,
        max_sphericity=max_sphericity,
        min_margin=min_margin,
        max_margin=max_margin,
        min_lobulation=min_lobulation,
        max_lobulation=max_lobulation,
        min_spiculation=min_spiculation,
        max_spiculation=max_spiculation,
        min_texture=min_texture,
        max_texture=max_texture,
        calcification=calcification,
        min_diameter=min_diameter,
        max_diameter=max_diameter,
        sort_by=sort_by,
        sort_order=sort_order
    )


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
