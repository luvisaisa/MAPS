"""
Documents Router

API endpoints for document management, search, and export.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text
from typing import List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime, date
import io
import json
import csv

from ..dependencies import get_db
from ...database.models import Document, DocumentContent
from ...database.detection_models import DetectionDetails

router = APIRouter()
logger = logging.getLogger(__name__)


class DocumentSummary(BaseModel):
    """Document summary for list view"""
    id: str
    filename: str
    document_title: Optional[str] = None
    parse_case: Optional[str] = None
    confidence: Optional[float] = None
    file_type: str
    file_size_bytes: Optional[int] = None
    keywords_count: int
    status: str
    uploaded_at: str
    parsed_at: Optional[str] = None
    document_date: Optional[str] = None
    uploaded_by: Optional[str] = None
    content_preview: Optional[str] = None


class DocumentDetail(BaseModel):
    """Full document details"""
    id: str
    filename: str
    file_path: str
    document_title: Optional[str] = None
    file_type: str
    file_size_bytes: Optional[int] = None
    parse_case: Optional[str] = None
    confidence: Optional[float] = None
    keywords_count: int
    status: str
    error_message: Optional[str] = None
    processing_duration_ms: Optional[int] = None
    uploaded_at: str
    parsed_at: Optional[str] = None
    document_date: Optional[str] = None
    uploaded_by: Optional[str] = None
    canonical_data: Optional[dict] = None
    tags: Optional[List[str]] = None
    detection_details: Optional[dict] = None


@router.get("", response_model=List[DocumentSummary])
async def list_documents(
    status: Optional[str] = Query(None, regex="^(pending|processing|completed|failed)$"),
    parse_case: Optional[str] = None,
    file_type: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all documents with optional filters.

    Args:
        status: Filter by status
        parse_case: Filter by parse case
        file_type: Filter by file type
        search: Search in filename and title
        date_from: Filter by document date (from)
        date_to: Filter by document date (to)
        limit: Maximum documents to return
        offset: Pagination offset

    Returns:
        List of document summaries
    """
    query = db.query(Document).filter(Document.status != 'archived')

    # Apply filters
    if status:
        query = query.filter(Document.status == status)

    if parse_case:
        query = query.filter(Document.parse_case == parse_case)

    if file_type:
        query = query.filter(Document.file_type == file_type)

    if search:
        query = query.filter(
            or_(
                Document.source_file_name.ilike(f'%{search}%'),
                Document.document_title.ilike(f'%{search}%')
            )
        )

    if date_from:
        query = query.filter(Document.document_date >= date_from)

    if date_to:
        query = query.filter(Document.document_date <= date_to)

    # Order by most recent first
    query = query.order_by(Document.ingestion_timestamp.desc())

    # Apply pagination
    documents = query.offset(offset).limit(limit).all()

    # Build response
    results = []
    for doc in documents:
        results.append(DocumentSummary(
            id=str(doc.id),
            filename=doc.source_file_name,
            document_title=doc.document_title,
            parse_case=doc.parse_case,
            confidence=float(doc.detection_confidence) if doc.detection_confidence else None,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            keywords_count=doc.keywords_count or 0,
            status=doc.status,
            uploaded_at=doc.ingestion_timestamp.isoformat() if doc.ingestion_timestamp else None,
            parsed_at=doc.parsed_at.isoformat() if doc.parsed_at else None,
            document_date=doc.document_date.isoformat() if doc.document_date else None,
            uploaded_by=doc.uploaded_by,
            content_preview=doc.parsed_content_preview
        ))

    return results


@router.get("/stats")
async def get_documents_stats(db: Session = Depends(get_db)):
    """
    Get document statistics.

    Returns:
        Statistics about documents in the system
    """
    total = db.query(func.count(Document.id)).filter(
        Document.status != 'archived'
    ).scalar()

    by_status = db.query(
        Document.status,
        func.count(Document.id)
    ).filter(Document.status != 'archived').group_by(Document.status).all()

    by_parse_case = db.query(
        Document.parse_case,
        func.count(Document.id)
    ).filter(
        Document.parse_case.isnot(None),
        Document.status != 'archived'
    ).group_by(Document.parse_case).all()

    by_file_type = db.query(
        Document.file_type,
        func.count(Document.id)
    ).filter(Document.status != 'archived').group_by(Document.file_type).all()

    return {
        "total_documents": total,
        "by_status": {status: count for status, count in by_status},
        "by_parse_case": {case: count for case, count in by_parse_case if case},
        "by_file_type": {ft: count for ft, count in by_file_type}
    }


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get full document details.

    Args:
        document_id: Document UUID

    Returns:
        Complete document information including content and detection details

    Raises:
        404: Document not found
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    # Get document content
    content = db.query(DocumentContent).filter(
        DocumentContent.document_id == document_id
    ).first()

    # Get detection details
    detection = db.query(DetectionDetails).filter(
        DetectionDetails.document_id == document_id
    ).first()

    return DocumentDetail(
        id=str(document.id),
        filename=document.source_file_name,
        file_path=document.source_file_path,
        document_title=document.document_title,
        file_type=document.file_type,
        file_size_bytes=document.file_size_bytes,
        parse_case=document.parse_case,
        confidence=float(document.detection_confidence) if document.detection_confidence else None,
        keywords_count=document.keywords_count or 0,
        status=document.status,
        error_message=document.error_message,
        processing_duration_ms=document.processing_duration_ms,
        uploaded_at=document.ingestion_timestamp.isoformat() if document.ingestion_timestamp else None,
        parsed_at=document.parsed_at.isoformat() if document.parsed_at else None,
        document_date=document.document_date.isoformat() if document.document_date else None,
        uploaded_by=document.uploaded_by,
        canonical_data=content.canonical_data if content else None,
        tags=content.tags if content else None,
        detection_details=detection.to_dict() if detection else None
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document (marks as archived).

    Args:
        document_id: Document UUID

    Returns:
        Success message

    Raises:
        404: Document not found
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    # Mark as archived instead of deleting
    document.status = 'archived'
    db.commit()

    logger.info(f"Document {document_id} archived")

    return {
        "status": "success",
        "message": f"Document '{document_id}' archived"
    }


@router.post("/search")
async def search_documents(
    query: str,
    parse_case_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Full-text search across documents.

    Args:
        query: Search query text
        parse_case_filter: Optional parse case filter
        status_filter: Optional status filter
        limit: Maximum results to return

    Returns:
        List of matching documents with relevance scores
    """
    # Use PostgreSQL full-text search function from migration
    sql = text("""
        SELECT * FROM search_documents(:query, :parse_case, :status, :limit)
    """)

    results = db.execute(sql, {
        "query": query,
        "parse_case": parse_case_filter,
        "status": status_filter,
        "limit": limit
    }).fetchall()

    return [
        {
            "document_id": str(row[0]),
            "filename": row[1],
            "parse_case": row[2],
            "confidence": float(row[3]) if row[3] else None,
            "status": row[4],
            "relevance": float(row[5])
        }
        for row in results
    ]


@router.get("/{document_id}/export")
async def export_document(
    document_id: str,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    Export a single document.

    Args:
        document_id: Document UUID
        format: Export format (json or csv)

    Returns:
        Document data in specified format

    Raises:
        404: Document not found
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail=f"Document '{document_id}' not found")

    content = db.query(DocumentContent).filter(
        DocumentContent.document_id == document_id
    ).first()

    if format == "json":
        data = {
            "document": document.to_dict(),
            "content": content.canonical_data if content else None
        }
        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={document.source_file_name}.json"}
        )

    else:  # csv
        # Flatten data for CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow([
            "document_id", "filename", "parse_case", "confidence",
            "status", "uploaded_at", "keywords_count"
        ])

        # Write data
        writer.writerow([
            str(document.id),
            document.source_file_name,
            document.parse_case or "",
            document.detection_confidence or "",
            document.status,
            document.ingestion_timestamp.isoformat() if document.ingestion_timestamp else "",
            document.keywords_count or 0
        ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={document.source_file_name}.csv"}
        )


@router.post("/batch-export")
async def batch_export_documents(
    document_ids: List[str],
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    Export multiple documents.

    Args:
        document_ids: List of document UUIDs
        format: Export format (json or csv)

    Returns:
        Documents data in specified format
    """
    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()

    if not documents:
        raise HTTPException(status_code=404, detail="No documents found")

    if format == "json":
        data = []
        for doc in documents:
            content = db.query(DocumentContent).filter(
                DocumentContent.document_id == doc.id
            ).first()

            data.append({
                "document": doc.to_dict(),
                "content": content.canonical_data if content else None
            })

        return Response(
            content=json.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=documents_export.json"}
        )

    else:  # csv
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        writer.writerow([
            "document_id", "filename", "parse_case", "confidence",
            "status", "uploaded_at", "keywords_count"
        ])

        # Write data rows
        for doc in documents:
            writer.writerow([
                str(doc.id),
                doc.source_file_name,
                doc.parse_case or "",
                doc.detection_confidence or "",
                doc.status,
                doc.ingestion_timestamp.isoformat() if doc.ingestion_timestamp else "",
                doc.keywords_count or 0
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=documents_export.csv"}
        )
