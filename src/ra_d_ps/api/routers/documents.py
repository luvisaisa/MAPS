"""
Documents Router

Endpoints for document CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from ..models.responses import DocumentResponse
from ..dependencies import get_db
from ..services.document_service import DocumentService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    parse_case: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List documents with optional filtering"""
    service = DocumentService(db)
    return service.list_documents(
        limit=limit,
        offset=offset,
        parse_case=parse_case
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get specific document by ID"""
    service = DocumentService(db)
    result = service.get_document(document_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    return result


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete document by ID"""
    service = DocumentService(db)
    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    return {"status": "deleted", "document_id": document_id}


@router.get("/filter")
async def filter_documents(
    parse_case: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    has_keywords: Optional[bool] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Advanced document filtering"""
    service = DocumentService(db)
    return service.filter_documents(
        parse_case=parse_case,
        start_date=start_date,
        end_date=end_date,
        has_keywords=has_keywords,
        limit=limit
    )
