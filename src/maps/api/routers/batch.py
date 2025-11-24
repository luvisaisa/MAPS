"""
Batch Router

Endpoints for batch job management with real-time updates.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import logging
import json
import asyncio
from datetime import datetime

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


@router.get("/jobs")
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List batch processing jobs with pagination"""
    service = BatchService(db)
    jobs = service.list_jobs(skip=skip, limit=limit, status=status)
    total = service.count_jobs(status=status)
    
    return {
        "items": jobs,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit,
        "total_pages": (total + limit - 1) // limit
    }


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


@router.websocket("/jobs/{job_id}/ws")
async def job_progress_websocket(websocket: WebSocket, job_id: str):
    """
    WebSocket endpoint for real-time job progress updates.
    Sends progress updates every second while job is processing.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for job {job_id}")
    
    try:
        while True:
            # Get database session (not using Depends in WebSocket)
            from ..dependencies import SessionLocal
            db = SessionLocal()
            
            try:
                service = BatchService(db)
                job = service.get_job_status(job_id)
                
                if not job:
                    await websocket.send_json({
                        "type": "error",
                        "job_id": job_id,
                        "data": {"error": "Job not found"},
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break
                
                # Send progress update
                await websocket.send_json({
                    "type": "progress",
                    "job_id": job_id,
                    "data": {
                        "job_id": job_id,
                        "current": job.get("processed_count", 0),
                        "total": job.get("file_count", 0),
                        "percentage": (job.get("processed_count", 0) / max(job.get("file_count", 1), 1)) * 100,
                        "status": job.get("status"),
                        "message": job.get("error_message")
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # If job is complete or failed, send final message and close
                if job.get("status") in ["completed", "failed", "cancelled"]:
                    await websocket.send_json({
                        "type": "complete",
                        "job_id": job_id,
                        "data": job,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break
                    
            finally:
                db.close()
            
            # Wait before next update
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        await websocket.close()


@router.get("/jobs/{job_id}/progress")
async def job_progress_sse(job_id: str):
    """
    Server-Sent Events endpoint for real-time job progress updates.
    Alternative to WebSocket with better browser compatibility.
    """
    async def event_generator():
        from ..dependencies import SessionLocal
        
        while True:
            db = SessionLocal()
            try:
                service = BatchService(db)
                job = service.get_job_status(job_id)
                
                if not job:
                    yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    break
                
                # Send progress update
                progress_data = {
                    "job_id": job_id,
                    "current": job.get("processed_count", 0),
                    "total": job.get("file_count", 0),
                    "percentage": (job.get("processed_count", 0) / max(job.get("file_count", 1), 1)) * 100,
                    "status": job.get("status"),
                    "message": job.get("error_message"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                yield f"data: {json.dumps(progress_data)}\n\n"
                
                # If job is complete or failed, close stream
                if job.get("status") in ["completed", "failed", "cancelled"]:
                    break
                    
            except Exception as e:
                logger.error(f"SSE error for job {job_id}: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
            finally:
                db.close()
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
