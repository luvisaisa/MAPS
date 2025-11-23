"""
Batch Router

Endpoints for batch job management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..models.responses import BatchJobResponse
from ..dependencies import get_db
from ..services.batch_service import BatchService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/create", response_model=BatchJobResponse)
async def create_batch_job(
    file_paths: List[str],
    profile: str = "lidc_idri_standard",
    db: Session = Depends(get_db)
):
    """Create batch processing job"""
    service = BatchService(db)
    return await service.create_job(file_paths, profile=profile)


@router.get("/{job_id}", response_model=BatchJobResponse)
async def get_batch_status(job_id: str, db: Session = Depends(get_db)):
    """Check batch job status"""
    service = BatchService(db)
    result = service.get_job_status(job_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return result


@router.get("/{job_id}/results")
async def get_batch_results(job_id: str, db: Session = Depends(get_db)):
    """Get batch job results"""
    service = BatchService(db)
    return service.get_job_results(job_id)


@router.delete("/{job_id}")
async def cancel_batch_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel batch job"""
    service = BatchService(db)
    success = service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"status": "cancelled", "job_id": job_id}
