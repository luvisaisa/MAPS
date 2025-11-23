"""
Parse Service

Business logic for file parsing operations.
Uses ra_d_ps.parser and ra_d_ps.parsers modules.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import UploadFile
import time
import tempfile
import os
from pathlib import Path

from ..models.responses import ParseResponse, BatchJobResponse
from datetime import datetime

# Lazy imports to avoid tkinter dependency at module level
def _get_parser_functions():
    """Lazy import of parser functions to avoid tkinter dependency"""
    from ...parser import parse_radiology_sample, detect_parse_case
    return parse_radiology_sample, detect_parse_case

def _get_pdf_extractor():
    """Lazy import of PDF extractor"""
    from ...pdf_keyword_extractor import PDFKeywordExtractor
    return PDFKeywordExtractor


class ParseService:
    """Service for parsing XML/PDF files"""

    def __init__(self, db: Optional[Session]):
        self.db = db

    async def parse_xml(
        self,
        content: bytes,
        filename: str,
        profile: str,
        validate: bool,
        extract_keywords: bool,
        detect_parse_case: bool,
        insert_to_db: bool
    ) -> ParseResponse:
        """Parse XML file using ra_d_ps.parser.parse_radiology_sample"""
        start_time = time.time()

        try:
            # Save content to temporary file (parser expects file path)
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                # Use existing parse_radiology_sample function
                parse_func, detect_func = _get_parser_functions()
                main_df, unblinded_df = parse_func(tmp_path)

                # Detect parse case if requested
                detected_parse_case = None
                if detect_parse_case:
                    detected_parse_case = detect_func(tmp_path)

                # TODO: Insert to database if requested
                document_id = None
                if insert_to_db and self.db:
                    # Will implement database insertion here
                    document_id = "placeholder-doc-id"

                # TODO: Extract keywords if requested
                keywords_count = 0
                if extract_keywords:
                    # Will implement keyword extraction here
                    keywords_count = 0

                processing_time = (time.time() - start_time) * 1000

                return ParseResponse(
                    status="success",
                    document_id=document_id,
                    parse_case=detected_parse_case,
                    keywords_extracted=keywords_count,
                    processing_time_ms=processing_time,
                    errors=None
                )
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            return ParseResponse(
                status="error",
                errors=[str(e)],
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def parse_pdf(
        self,
        content: bytes,
        filename: str,
        extract_keywords: bool,
        insert_to_db: bool
    ) -> ParseResponse:
        """Parse PDF file using ra_d_ps.pdf_keyword_extractor"""
        start_time = time.time()

        try:
            # Save content to temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                document_id = None
                keywords_count = 0

                if extract_keywords:
                    # Use PDFKeywordExtractor
                    PDFKeywordExtractor = _get_pdf_extractor()
                    extractor = PDFKeywordExtractor()
                    metadata, keywords = extractor.extract_from_pdf(tmp_path)

                    keywords_count = len(keywords)

                    # TODO: Insert to database if requested
                    if insert_to_db and self.db:
                        document_id = "placeholder-pdf-doc-id"

                processing_time = (time.time() - start_time) * 1000

                return ParseResponse(
                    status="success",
                    document_id=document_id,
                    parse_case="PDF_Document",
                    keywords_extracted=keywords_count,
                    processing_time_ms=processing_time,
                    errors=None
                )
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            return ParseResponse(
                status="error",
                errors=[str(e)],
                processing_time_ms=(time.time() - start_time) * 1000
            )

    async def parse_batch(
        self,
        files: List[UploadFile],
        profile: str,
        batch_size: int,
        validate: bool,
        extract_keywords: bool
    ) -> BatchJobResponse:
        """Batch parse files"""
        # TODO: Implement using ra_d_ps.batch_processor
        job_id = f"batch-{int(time.time())}"

        return BatchJobResponse(
            job_id=job_id,
            status="created",
            total_files=len(files),
            processed_files=0,
            failed_files=0,
            created_at=datetime.utcnow(),
            errors=[]
        )

    def list_profiles(self):
        """List available profiles"""
        # TODO: Use ra_d_ps.profile_manager
        from ...profile_manager import get_profile_manager

        try:
            manager = get_profile_manager()
            profiles = manager.list_profiles()

            return {
                "profiles": [
                    {"name": p, "description": f"Profile: {p}"}
                    for p in profiles
                ]
            }
        except Exception as e:
            return {
                "profiles": [
                    {"name": "lidc_idri_standard", "description": "LIDC-IDRI standard format"},
                    {"name": "nyt_standard", "description": "NYT XML format"}
                ],
                "error": str(e)
            }
