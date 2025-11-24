"""
Search Router

Endpoints for search and query operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..models.requests import SearchRequest, CustomQueryRequest
from ..dependencies import get_db
from ..services.search_service import SearchService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/full-text")
async def full_text_search(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """Full-text search across documents"""
    service = SearchService(db)
    return service.full_text_search(query, limit=limit, offset=offset)


@router.get("/semantic")
async def semantic_search(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=100),
    db: Session = Depends(get_db)
):
    """Semantic keyword search"""
    service = SearchService(db)
    return service.semantic_search(query, limit=limit)


@router.post("/query/sql")
async def custom_sql_query(
    request: CustomQueryRequest,
    db: Session = Depends(get_db)
):
    """Custom SQL query (admin only - implement auth)"""
    service = SearchService(db)
    try:
        result = service.execute_query(
            request.query,
            params=request.params,
            limit=request.limit
        )
        return result
    except Exception as e:
        logger.error(f"Custom query failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/query/filter")
async def advanced_filter(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Advanced filtering"""
    service = SearchService(db)
    return service.advanced_filter(
        query=request.query,
        fields=request.fields,
        parse_case=request.parse_case,
        limit=request.limit,
        offset=request.offset
    )
