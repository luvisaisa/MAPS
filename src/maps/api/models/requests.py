"""
API Request Models

Pydantic models for validating incoming API requests.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ProfileType(str, Enum):
    """Supported parsing profiles"""
    NYT_STANDARD = "nyt_standard"
    LIDC_IDRI = "lidc_idri_standard"
    CUSTOM = "custom"


class ExportFormat(str, Enum):
    """Supported export formats"""
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    SQLITE = "sqlite"


class ParseRequest(BaseModel):
    """Request model for parsing a single file"""

    profile: ProfileType = Field(
        default=ProfileType.LIDC_IDRI,
        description="Parsing profile to use"
    )
    validate_data: bool = Field(
        default=True,
        description="Whether to validate against schema"
    )
    extract_keywords: bool = Field(
        default=True,
        description="Whether to extract keywords"
    )
    detect_parse_case: bool = Field(
        default=True,
        description="Whether to detect parse case"
    )
    insert_to_db: bool = Field(
        default=True,
        description="Whether to insert into database"
    )


class BatchParseRequest(BaseModel):
    """Request model for batch parsing multiple files"""

    profile: ProfileType = Field(
        default=ProfileType.LIDC_IDRI,
        description="Parsing profile to use"
    )
    batch_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Batch size for processing"
    )
    validate_data: bool = Field(
        default=True,
        description="Whether to validate against schema"
    )
    extract_keywords: bool = Field(
        default=True,
        description="Whether to extract keywords"
    )


class DetectRequest(BaseModel):
    """Request model for parse case detection"""

    analyze_structure: bool = Field(
        default=True,
        description="Include detailed structure analysis"
    )


class PyLIDCImportRequest(BaseModel):
    """Request model for PYLIDC import"""

    patient_id: Optional[str] = Field(
        default=None,
        description="Specific patient ID to import"
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=1000,
        description="Limit number of scans to import"
    )
    extract_keywords: bool = Field(
        default=True,
        description="Extract keywords from annotations"
    )
    detect_parse_case: bool = Field(
        default=True,
        description="Detect and assign parse case"
    )


class SearchRequest(BaseModel):
    """Request model for document search"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query string"
    )
    fields: Optional[List[str]] = Field(
        default=None,
        description="Fields to search (default: all)"
    )
    parse_case: Optional[str] = Field(
        default=None,
        description="Filter by parse case"
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of results"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Results offset for pagination"
    )


class ExportRequest(BaseModel):
    """Request model for data export"""

    format: ExportFormat = Field(
        ...,
        description="Export format"
    )
    view_name: Optional[str] = Field(
        default=None,
        description="Specific view to export"
    )
    document_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific document IDs to export"
    )
    parse_case: Optional[str] = Field(
        default=None,
        description="Filter by parse case"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include document metadata"
    )
    include_keywords: bool = Field(
        default=False,
        description="Include extracted keywords"
    )


class CustomQueryRequest(BaseModel):
    """Request model for custom SQL query"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="SQL query to execute"
    )
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Query parameters"
    )
    limit: Optional[int] = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Result limit"
    )
