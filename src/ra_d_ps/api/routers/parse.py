"""
Parsing Router

Endpoints for parsing XML/PDF files.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from ..models.requests import ParseRequest, BatchParseRequest
from ..models.responses import ParseResponse, BatchJobResponse
from ..dependencies import get_db
from ..services.parse_service import ParseService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/xml", response_model=ParseResponse)
async def parse_xml(
    file: UploadFile = File(...),
    request: ParseRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Parse XML file and optionally insert into database.

    Args:
        file: XML file to parse
        request: Parsing options
        db: Database session

    Returns:
        Parse results including document ID and parse case
    """
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="File must be XML format")

    service = ParseService(db)

    try:
        content = await file.read()
        result = await service.parse_xml(
            content,
            file.filename,
            profile=request.profile,
            validate=request.validate,
            extract_keywords=request.extract_keywords,
            detect_parse_case=request.detect_parse_case,
            insert_to_db=request.insert_to_db
        )
        return result
    except Exception as e:
        logger.error(f"XML parsing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf", response_model=ParseResponse)
async def parse_pdf(
    file: UploadFile = File(...),
    request: ParseRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Parse PDF file and extract keywords.

    Args:
        file: PDF file to parse
        request: Parsing options
        db: Database session

    Returns:
        Parse results including extracted keywords
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be PDF format")

    service = ParseService(db)

    try:
        content = await file.read()
        result = await service.parse_pdf(
            content,
            file.filename,
            extract_keywords=request.extract_keywords,
            insert_to_db=request.insert_to_db
        )
        return result
    except Exception as e:
        logger.error(f"PDF parsing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    profile: str = "lidc_idri_standard",
    db: Session = Depends(get_db)
):
    """
    Upload and parse multiple files.

    Args:
        files: List of files to upload and parse
        profile: Parsing profile to use
        db: Database session

    Returns:
        Upload response with job ID
    """
    service = ParseService(db)

    try:
        # Create batch job for the uploaded files
        result = await service.parse_batch(
            files,
            profile=profile,
            batch_size=len(files),
            validate=True,
            extract_keywords=True
        )
        
        return {
            "job_id": result.job_id,
            "files_uploaded": len(files),
            "message": f"Successfully created batch job for {len(files)} file(s)"
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=BatchJobResponse)
async def parse_batch(
    files: List[UploadFile] = File(...),
    request: BatchParseRequest = Depends(),
    db: Session = Depends(get_db)
):
    """
    Parse multiple files in batch.

    Args:
        files: List of files to parse
        request: Batch parsing options
        db: Database session

    Returns:
        Batch job status
    """
    service = ParseService(db)

    try:
        result = await service.parse_batch(
            files,
            profile=request.profile,
            batch_size=request.batch_size,
            validate=request.validate,
            extract_keywords=request.extract_keywords
        )
        return result
    except Exception as e:
        logger.error(f"Batch parsing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview", response_model=ParseResponse)
async def parse_preview(
    file: UploadFile = File(...),
    request: ParseRequest = Depends()
):
    """
    Parse file without inserting into database (preview only).

    Args:
        file: File to parse
        request: Parsing options

    Returns:
        Parse results without database insertion
    """
    service = ParseService(None)

    try:
        content = await file.read()

        if file.filename.endswith('.xml'):
            result = await service.parse_xml(
                content,
                file.filename,
                profile=request.profile,
                validate=request.validate,
                extract_keywords=request.extract_keywords,
                detect_parse_case=request.detect_parse_case,
                insert_to_db=False
            )
        elif file.filename.endswith('.pdf'):
            result = await service.parse_pdf(
                content,
                file.filename,
                extract_keywords=request.extract_keywords,
                insert_to_db=False
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        return result
    except Exception as e:
        logger.error(f"Parse preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/zip")
async def extract_and_parse_zip(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Extract ZIP file and return contained files for parsing.

    Args:
        file: ZIP file to extract
        db: Database session

    Returns:
        List of extracted files with metadata
    """
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be ZIP format")

    service = ParseService(db)

    try:
        content = await file.read()
        result = await service.extract_zip(
            content,
            file.filename
        )
        return result
    except Exception as e:
        logger.error(f"ZIP extraction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles")
async def list_profiles():
    """
    List available parsing profiles.

    Returns:
        List of parsing profile names and descriptions
    """
    service = ParseService(None)
    return service.list_profiles()
