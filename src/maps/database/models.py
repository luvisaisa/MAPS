"""
SQLAlchemy Models for Parse Case Management
Declarative ORM models for PostgreSQL tables
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON,
    ForeignKey, CheckConstraint, Index, ARRAY, Numeric, Date, TypeDecorator
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class JSONBCompat(TypeDecorator):
    """
    Type decorator to use JSONB for PostgreSQL and JSON for SQLite/others
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class UUIDCompat(TypeDecorator):
    """
    Type decorator to use UUID for PostgreSQL and String for SQLite
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        else:
            import uuid
            return uuid.UUID(value)


class ARRAYCompat(TypeDecorator):
    """
    Type decorator to use ARRAY for PostgreSQL and JSON for SQLite
    """
    impl = JSON
    cache_ok = True

    def __init__(self, item_type):
        self.item_type = item_type
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import ARRAY
            return dialect.type_descriptor(ARRAY(self.item_type))
        else:
            return dialect.type_descriptor(JSON())


class ParseCase(Base):
    """
    Parse case definitions with detection criteria
    """
    __tablename__ = 'parse_cases'
    
    id = Column(UUIDCompat, primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    version = Column(String(20), nullable=False, default='1.0')
    
    # Detection criteria as JSONB
    detection_criteria = Column(JSONBCompat, nullable=False)
    field_mappings = Column(JSONBCompat, default=[])
    characteristic_fields = Column(ARRAYCompat(String), default=[])
    
    # Structural requirements
    requires_header = Column(Boolean, default=False)
    requires_modality = Column(Boolean, default=False)
    min_session_count = Column(Integer, default=0)
    max_session_count = Column(Integer, nullable=True)
    
    # Detection priority (0-100)
    detection_priority = Column(
        Integer, 
        default=50,
        nullable=False
    )
    
    # Status and metadata
    is_active = Column(Boolean, default=True, index=True)
    is_legacy_format = Column(Boolean, default=True)
    format_type = Column(String(50), default='LIDC', index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100))
    notes = Column(Text)
    
    # Relationships
    profiles = relationship("ParseCaseProfile", back_populates="parse_case", cascade="all, delete-orphan")
    detection_history = relationship("ParseCaseDetectionHistory", back_populates="parse_case")
    statistics = relationship("ParseCaseStatistics", back_populates="parse_case", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('detection_priority >= 0 AND detection_priority <= 100', name='valid_priority'),
        Index('idx_parse_cases_detection_criteria', 'detection_criteria', postgresql_using='gin'),
    )
    
    def __repr__(self):
        return f"<ParseCase(name='{self.name}', version='{self.version}', format='{self.format_type}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'detection_criteria': self.detection_criteria,
            'field_mappings': self.field_mappings,
            'characteristic_fields': self.characteristic_fields,
            'requires_header': self.requires_header,
            'requires_modality': self.requires_modality,
            'min_session_count': self.min_session_count,
            'max_session_count': self.max_session_count,
            'detection_priority': self.detection_priority,
            'is_active': self.is_active,
            'is_legacy_format': self.is_legacy_format,
            'format_type': self.format_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'notes': self.notes
        }


class ParseCaseProfile(Base):
    """
    Profile configurations linked to parse cases
    """
    __tablename__ = 'parse_case_profiles'
    
    id = Column(UUIDCompat, primary_key=True, default=uuid4)
    parse_case_id = Column(UUIDCompat, ForeignKey('parse_cases.id', ondelete='CASCADE'), nullable=False)
    profile_name = Column(String(100), nullable=False)
    profile_config = Column(JSONBCompat, nullable=False)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parse_case = relationship("ParseCase", back_populates="profiles")
    
    # Constraints
    __table_args__ = (
        Index('idx_parse_case_profiles_parse_case', 'parse_case_id'),
        Index('idx_parse_case_profiles_default', 'is_default', postgresql_where='is_default = true'),
    )
    
    def __repr__(self):
        return f"<ParseCaseProfile(name='{self.profile_name}', is_default={self.is_default})>"


class ParseCaseDetectionHistory(Base):
    """
    Audit trail of parse case detections
    """
    __tablename__ = 'parse_case_detection_history'
    
    id = Column(UUIDCompat, primary_key=True, default=uuid4)
    file_path = Column(Text, nullable=False, index=True)
    file_checksum = Column(String(64))
    parse_case_id = Column(UUIDCompat, ForeignKey('parse_cases.id', ondelete='SET NULL'))
    parse_case_name = Column(String(100), nullable=False)
    detection_metadata = Column(JSONBCompat)
    
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    detection_duration_ms = Column(Integer)
    
    # Relationships
    parse_case = relationship("ParseCase", back_populates="detection_history")
    
    # Indexes
    __table_args__ = (
        Index('idx_detection_history_file', 'file_path'),
        Index('idx_detection_history_detected_at', 'detected_at', postgresql_ops={'detected_at': 'DESC'}),
    )
    
    def __repr__(self):
        return f"<DetectionHistory(file='{self.file_path[:50]}...', case='{self.parse_case_name}')>"


class ParseCaseStatistics(Base):
    """
    Aggregated statistics for parse case usage
    """
    __tablename__ = 'parse_case_statistics'

    id = Column(UUIDCompat, primary_key=True, default=uuid4)
    parse_case_id = Column(UUIDCompat, ForeignKey('parse_cases.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False, default=func.current_date())

    detection_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_detection_time_ms = Column(Numeric(10, 2))

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    parse_case = relationship("ParseCase", back_populates="statistics")

    # Constraints and indexes
    __table_args__ = (
        Index('idx_statistics_parse_case', 'parse_case_id'),
        Index('idx_statistics_date', 'date', postgresql_ops={'date': 'DESC'}),
    )

    def __repr__(self):
        return f"<Statistics(date={self.date}, detections={self.detection_count})>"


# =====================================================================
# DOCUMENT MODELS (for Supabase/PostgreSQL Integration)
# =====================================================================

class Document(Base):
    """
    Metadata for all ingested documents
    Maps to documents table from 001_initial_schema.sql
    """
    __tablename__ = 'documents'

    id = Column(UUIDCompat, primary_key=True, default=uuid4)
    source_file_name = Column(String(500), nullable=False)
    source_file_path = Column(Text, nullable=False)
    file_type = Column(
        String(50),
        nullable=False,
        default='XML'
    )
    file_size_bytes = Column(Integer)
    file_hash = Column(String(64))  # SHA-256 hash for deduplication
    profile_id = Column(UUIDCompat)

    # Ingestion tracking
    ingestion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    last_modified = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    uploaded_by = Column(String(255))

    # Status tracking
    status = Column(
        String(50),
        nullable=False,
        default='pending'
    )
    error_message = Column(Text)
    processing_duration_ms = Column(Integer)

    # Metadata
    original_format_version = Column(String(50))
    source_system = Column(String(255))
    batch_id = Column(UUIDCompat)

    # Parse case detection (NEW - from migration 016)
    parse_case = Column(String(255), index=True)
    detection_confidence = Column(Numeric(5, 4))
    keywords_count = Column(Integer, default=0)
    parsed_at = Column(DateTime(timezone=True))
    parsed_content_preview = Column(Text)
    document_title = Column(String(500))
    document_date = Column(Date)
    content_hash = Column(String(64))

    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    content = relationship("DocumentContent", back_populates="document", uselist=False, cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        CheckConstraint(
            "file_type IN ('XML', 'JSON', 'CSV', 'PDF', 'DOCX', 'OTHER')",
            name='valid_file_type'
        ),
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed', 'archived')",
            name='valid_status'
        ),
        Index('idx_documents_file_type', 'file_type'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_profile_id', 'profile_id'),
        Index('idx_documents_ingestion_timestamp', 'ingestion_timestamp', postgresql_ops={'ingestion_timestamp': 'DESC'}),
        Index('idx_documents_batch_id', 'batch_id'),
        Index('idx_documents_file_hash', 'file_hash'),
        Index('idx_documents_parse_case', 'parse_case'),
        Index('idx_documents_detection_confidence', 'detection_confidence'),
        Index('idx_documents_keywords_count', 'keywords_count'),
        Index('idx_documents_parsed_at', 'parsed_at', postgresql_ops={'parsed_at': 'DESC'}),
        Index('idx_documents_document_date', 'document_date', postgresql_ops={'document_date': 'DESC'}),
        Index('idx_documents_content_hash', 'content_hash'),
    )

    def __repr__(self):
        return f"<Document(id='{self.id}', file='{self.source_file_name}', status='{self.status}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'source_file_name': self.source_file_name,
            'source_file_path': self.source_file_path,
            'file_type': self.file_type,
            'file_size_bytes': self.file_size_bytes,
            'file_hash': self.file_hash,
            'profile_id': str(self.profile_id) if self.profile_id else None,
            'ingestion_timestamp': self.ingestion_timestamp.isoformat() if self.ingestion_timestamp else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'uploaded_by': self.uploaded_by,
            'status': self.status,
            'error_message': self.error_message,
            'processing_duration_ms': self.processing_duration_ms,
            'original_format_version': self.original_format_version,
            'source_system': self.source_system,
            'batch_id': str(self.batch_id) if self.batch_id else None,
            'parse_case': self.parse_case,
            'detection_confidence': float(self.detection_confidence) if self.detection_confidence else None,
            'keywords_count': self.keywords_count,
            'parsed_at': self.parsed_at.isoformat() if self.parsed_at else None,
            'parsed_content_preview': self.parsed_content_preview,
            'document_title': self.document_title,
            'document_date': self.document_date.isoformat() if self.document_date else None,
            'content_hash': self.content_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_canonical(cls, canonical_doc, source_file: str = "pylidc://",
                      uploaded_by: Optional[str] = None) -> "Document":
        """
        Create Document from RadiologyCanonicalDocument

        Args:
            canonical_doc: RadiologyCanonicalDocument instance
            source_file: Source file path or identifier
            uploaded_by: User who uploaded the document

        Returns:
            Document instance
        """
        metadata = canonical_doc.document_metadata

        return cls(
            source_file_name=metadata.title or "Untitled",
            source_file_path=source_file,
            file_type='XML',
            source_system=getattr(metadata, 'source_system', None) or "LIDC-IDRI",
            original_format_version=getattr(metadata, 'format_version', None),
            uploaded_by=uploaded_by,
            status='completed'
        )


class DocumentContent(Base):
    """
    Flexible canonical data storage
    Maps to document_content table from 001_initial_schema.sql
    """
    __tablename__ = 'document_content'

    id = Column(UUIDCompat, primary_key=True, default=uuid4)
    document_id = Column(UUIDCompat, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, unique=True)

    # Canonical data (flexible JSONB structure)
    canonical_data = Column(JSONBCompat, nullable=False)

    # Full-text search optimization
    searchable_text = Column(Text)

    # Extracted entities (structured extraction)
    extracted_entities = Column(JSONBCompat, default={})

    # User-defined tags for categorization
    tags = Column(ARRAYCompat(String), default=[])

    # Schema versioning for migrations
    schema_version = Column(Integer, default=1)

    # Quality metrics
    confidence_score = Column(Numeric(5, 4))  # 0.0000 to 1.0000
    validation_errors = Column(JSONBCompat)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    document = relationship("Document", back_populates="content")

    # Indexes handled by migration SQL
    __table_args__ = (
        Index('idx_content_document_id', 'document_id'),
        Index('idx_content_canonical_data_gin', 'canonical_data', postgresql_using='gin'),
        Index('idx_content_entities_gin', 'extracted_entities', postgresql_using='gin'),
        Index('idx_content_tags_gin', 'tags', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<DocumentContent(document_id='{self.document_id}', version={self.schema_version})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'canonical_data': self.canonical_data,
            'searchable_text': self.searchable_text,
            'extracted_entities': self.extracted_entities,
            'tags': self.tags,
            'schema_version': self.schema_version,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'validation_errors': self.validation_errors,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_canonical(cls, canonical_doc, document_id: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> "DocumentContent":
        """
        Create DocumentContent from RadiologyCanonicalDocument

        Args:
            canonical_doc: RadiologyCanonicalDocument instance
            document_id: UUID of parent document
            tags: Optional tags for categorization

        Returns:
            DocumentContent instance
        """
        # Convert Pydantic model to dict
        canonical_dict = canonical_doc.model_dump(mode='json')

        # Build searchable text from key fields
        searchable_parts = []
        if hasattr(canonical_doc, 'document_metadata'):
            meta = canonical_doc.document_metadata
            if meta.title:
                searchable_parts.append(meta.title)
            if meta.description:
                searchable_parts.append(meta.description)

        # Add radiology-specific searchable content
        if hasattr(canonical_doc, 'study_instance_uid'):
            searchable_parts.append(canonical_doc.study_instance_uid or "")
        if hasattr(canonical_doc, 'series_instance_uid'):
            searchable_parts.append(canonical_doc.series_instance_uid or "")

        searchable_text = " ".join(filter(None, searchable_parts))

        return cls(
            document_id=document_id,
            canonical_data=canonical_dict,
            searchable_text=searchable_text,
            extracted_entities={},
            tags=tags or [],
            schema_version=1,
            confidence_score=1.0  # PYLIDC data is expert-annotated
        )
