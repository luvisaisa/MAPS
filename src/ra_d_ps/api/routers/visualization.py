"""
Visualization Router

Endpoints for 3D visualization data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..dependencies import get_db
from ..services.visualization_service import VisualizationService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/nodule/{patient_id}/{nodule_id}")
async def get_nodule_mesh(
    patient_id: str,
    nodule_id: str,
    format: str = Query(default="json", regex="^(json|stl|obj)$"),
    db: Session = Depends(get_db)
):
    """Get nodule mesh data for visualization"""
    service = VisualizationService(db)
    return await service.get_nodule_mesh(patient_id, nodule_id, format=format)


@router.get("/consensus/{patient_id}/{nodule_id}")
async def get_consensus_contour(
    patient_id: str,
    nodule_id: str,
    method: str = Query(default="average", regex="^(average|union|intersection)$"),
    db: Session = Depends(get_db)
):
    """Get consensus contour from multiple radiologists"""
    service = VisualizationService(db)
    return await service.get_consensus_contour(patient_id, nodule_id, method=method)


@router.get("/contours/{patient_id}/{nodule_id}")
async def get_all_contours(
    patient_id: str,
    nodule_id: str,
    db: Session = Depends(get_db)
):
    """Get all radiologist contours"""
    service = VisualizationService(db)
    return await service.get_all_contours(patient_id, nodule_id)


@router.get("/spatial-stats/{patient_id}")
async def get_spatial_stats(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get spatial statistics for patient"""
    service = VisualizationService(db)
    return await service.get_spatial_stats(patient_id)


@router.post("/generate-mesh")
async def generate_mesh(
    patient_id: str,
    nodule_id: str,
    format: str = Query(default="stl"),
    db: Session = Depends(get_db)
):
    """Generate 3D mesh file (STL/OBJ)"""
    service = VisualizationService(db)
    file_path = await service.generate_mesh_file(patient_id, nodule_id, format=format)
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=f"{patient_id}_{nodule_id}.{format}"
    )
