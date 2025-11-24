"""
Keywords Router

Endpoints for keyword management and search.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import logging

from ..models.responses import KeywordResponse
from ..dependencies import get_db
from ..services.keyword_service import KeywordService

router = APIRouter()
logger = logging.getLogger(__name__)


class KeywordDefinitionUpdate(BaseModel):
    """Update keyword definition"""
    definition: str
    source_refs: Optional[str] = None
    vocabulary_source: Optional[str] = None


class KeywordAliasCreate(BaseModel):
    """Create keyword alias/synonym"""
    alias: str
    synonym_type: str = "variant"


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


@router.post("/definitions/import")
async def import_keyword_definitions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Bulk import keyword definitions from CSV"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    service = KeywordService(db)
    result = await service.import_definitions_csv(file)
    return result


@router.put("/{keyword_id}/definition")
async def update_keyword_definition(
    keyword_id: str,
    update: KeywordDefinitionUpdate,
    db: Session = Depends(get_db)
):
    """Update keyword definition"""
    service = KeywordService(db)
    result = service.update_definition(keyword_id, update.dict())
    if not result:
        raise HTTPException(status_code=404, detail=f"Keyword {keyword_id} not found")
    return result


@router.get("/{keyword_id}/citations")
async def get_keyword_citations(keyword_id: str, db: Session = Depends(get_db)):
    """Get citations for keyword definition"""
    service = KeywordService(db)
    result = service.get_citations(keyword_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Keyword {keyword_id} not found")
    return result


@router.post("/{keyword_id}/aliases")
async def add_keyword_alias(
    keyword_id: str,
    alias_data: KeywordAliasCreate,
    db: Session = Depends(get_db)
):
    """Add synonym/alias to keyword"""
    service = KeywordService(db)
    result = service.add_alias(keyword_id, alias_data.alias, alias_data.synonym_type)
    if not result:
        raise HTTPException(status_code=404, detail=f"Keyword {keyword_id} not found")
    return result
