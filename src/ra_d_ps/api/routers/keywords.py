"""
Keywords Router

Endpoints for keyword management and search.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List
import logging

from ..models.responses import KeywordResponse
from ..dependencies import get_db
from ..services.keyword_service import KeywordService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[KeywordResponse])
async def list_keywords(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List canonical keywords"""
    service = KeywordService(db)
    return service.list_keywords(limit=limit, offset=offset, category=category)


@router.get("/directory")
async def get_keyword_directory(db: Session = Depends(get_db)):
    """Get complete keyword catalog"""
    service = KeywordService(db)
    return service.get_directory()


@router.get("/search")
async def search_keywords(
    query: str = Query(..., min_length=1),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Search keywords by term"""
    service = KeywordService(db)
    return service.search(query, limit=limit)


@router.get("/{keyword_id}", response_model=KeywordResponse)
async def get_keyword(keyword_id: str, db: Session = Depends(get_db)):
    """Get keyword details"""
    service = KeywordService(db)
    result = service.get_keyword(keyword_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Keyword {keyword_id} not found")
    return result


@router.get("/{keyword_id}/occurrences")
async def get_keyword_occurrences(keyword_id: str, db: Session = Depends(get_db)):
    """Get where keyword appears"""
    service = KeywordService(db)
    return service.get_occurrences(keyword_id)


@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    """List keyword categories"""
    service = KeywordService(db)
    return service.list_categories()


@router.get("/tags")
async def list_tags(db: Session = Depends(get_db)):
    """List topic tags"""
    service = KeywordService(db)
    return service.list_tags()


@router.post("/extract")
async def extract_keywords(
    text: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Extract keywords from text"""
    service = KeywordService(db)
    return service.extract(text)
