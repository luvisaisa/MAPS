"""
API Response Models

Pydantic models for API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    path: Optional[str] = None


class ParseCaseInfo(BaseModel):
    """Information about a parse case"""
    name: str
    description: str
    fields: List[str]
    required_fields: List[str]
    example_count: Optional[int] = None


class ParseCaseListResponse(BaseModel):
    """List of parse cases"""
    parse_cases: List[ParseCaseInfo]
    total: int


class ParseCaseStatsResponse(BaseModel):
    """Parse case statistics"""
    total_documents: int
    parse_case_distribution: Dict[str, int]
    last_updated: datetime


class StructureAnalysis(BaseModel):
    """XML/File structure analysis"""
    root_element: Optional[str] = None
    session_count: Optional[int] = None
    has_unblinded_reads: Optional[bool] = None
    element_count: Optional[int] = None
    depth: Optional[int] = None


class DetectResponse(BaseModel):
    """Parse case detection response"""
    detected_parse_case: str
    confidence: float = Field(ge=0.0, le=1.0)
    file_type: str
    structure_analysis: Optional[StructureAnalysis] = None
    possible_fields: Optional[List[str]] = None


class ParseResponse(BaseModel):
    """File parsing response"""
    status: str
    document_id: Optional[str] = None
    parse_case: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Detection confidence score")
    queue_item_id: Optional[str] = Field(None, description="Approval queue item ID if pending review")
    keywords_extracted: Optional[int] = None
    processing_time_ms: Optional[float] = None
    errors: Optional[List[str]] = None


class DocumentResponse(BaseModel):
    """Document data response"""
    document_id: str
    source_file: str
    parse_case: Optional[str] = None
    created_at: datetime
    content: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    keywords: Optional[List[str]] = None


class KeywordResponse(BaseModel):
    """Keyword information response"""
    keyword_id: str
    term: str
    category: Optional[str] = None
    subject_category: Optional[str] = None
    topic_tags: Optional[List[str]] = None
    occurrence_count: Optional[int] = None
    citations: Optional[List[str]] = None


class ExportResponse(BaseModel):
    """Export operation response"""
    status: str
    format: str
    filename: Optional[str] = None
    download_url: Optional[str] = None
    record_count: int
    file_size_bytes: Optional[int] = None


class AnalyticsResponse(BaseModel):
    """Analytics data response"""
    metric: str
    value: Any
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class BatchJobResponse(BaseModel):
    """Batch job status response"""
    job_id: str
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    errors: Optional[List[str]] = None


class ViewDataResponse(BaseModel):
    """Supabase view data response"""
    view_name: str
    data: List[Dict[str, Any]]
    total_rows: int
    page: int
    page_size: int
