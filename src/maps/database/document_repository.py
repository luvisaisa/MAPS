"""
Document Repository - Data Access Layer for Radiology Documents

Repository pattern for managing document ingestion and retrieval.
Supports PYLIDC data import and canonical document storage in Supabase/PostgreSQL.

Usage:
    from maps.database.document_repository import DocumentRepository
    from maps.adapters.pylidc_adapter import PyLIDCAdapter
    import pylidc as pl

    # Initialize repository with Supabase connection
    repo = DocumentRepository(connection_string="postgresql://...")

    # Convert PYLIDC scan to canonical
    adapter = PyLIDCAdapter()
    scan = pl.query(pl.Scan).first()
    canonical_doc = adapter.scan_to_canonical(scan)

    # Store in Supabase
    document = repo.insert_canonical_document(canonical_doc, source_file=f"pylidc://{scan.patient_id}")
"""

import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from uuid import uuid4, UUID

from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, Session, joinedload
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.dialects.postgresql import insert

from .models import Base, Document, DocumentContent
from .db_config import db_config

logger = logging.getLogger(__name__)


class DocumentRepository:
    """
    Repository for document and canonical data operations

    Provides CRUD operations for:
    - Documents (metadata and status tracking)
    - Document content (canonical JSONB data)
    - Batch operations for PYLIDC imports
    - Query methods for retrieval and search
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize repository with database connection

        Args:
            connection_string: Optional custom connection string for Supabase
                             If None, uses db_config from environment
        """
        if connection_string is None:
            connection_string = db_config.postgresql.get_connection_string()

        # Determine if using SQLite (for testing) or PostgreSQL
        is_sqlite = connection_string.startswith('sqlite')

        # Create engine with appropriate options
        if is_sqlite:
            self.engine = create_engine(
                connection_string,
                echo=False  # Disable SQL echo for SQLite tests
            )
        else:
            self.engine = create_engine(
                connection_string,
                **db_config.postgresql.get_engine_kwargs()
            )

        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False  # Prevent detached instance errors
        )

        logger.info(f"DocumentRepository initialized with database: {connection_string[:50]}...")

    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions
        Ensures proper session cleanup and error handling
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

    def create_tables(self):
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop tables: {e}")
            raise

    # =========================================================================
    # DOCUMENT CRUD OPERATIONS
    # =========================================================================

    def create_document(
        self,
        source_file_name: str,
        source_file_path: str,
        file_type: str = 'XML',
        uploaded_by: Optional[str] = None,
        source_system: Optional[str] = None,
        batch_id: Optional[UUID] = None
    ) -> Document:
        """
        Create a new document record

        Args:
            source_file_name: Name of the source file
            source_file_path: Full path or identifier
            file_type: Type of file (XML, JSON, CSV, etc.)
            uploaded_by: User who uploaded the document
            source_system: Source system identifier
            batch_id: Optional batch identifier for grouping

        Returns:
            Created Document object
        """
        with self.get_session() as session:
            document = Document(
                source_file_name=source_file_name,
                source_file_path=source_file_path,
                file_type=file_type,
                uploaded_by=uploaded_by,
                source_system=source_system,
                batch_id=batch_id,
                status='pending'
            )
            session.add(document)
            session.flush()  # Get the ID
            logger.info(f"Created document: {document.id}")
            return document

    def get_document(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID"""
        with self.get_session() as session:
            return session.query(Document).filter(Document.id == document_id).first()

    def get_document_with_content(self, document_id: UUID) -> Optional[Document]:
        """Get document with content eagerly loaded"""
        with self.get_session() as session:
            return session.query(Document)\
                .options(joinedload(Document.content))\
                .filter(Document.id == document_id)\
                .first()

    def update_document_status(
        self,
        document_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        processing_duration_ms: Optional[int] = None
    ):
        """Update document processing status"""
        with self.get_session() as session:
            document = session.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = status
                document.error_message = error_message
                document.processing_duration_ms = processing_duration_ms
                logger.info(f"Updated document {document_id} status to {status}")

    def delete_document(self, document_id: UUID):
        """Delete document and cascade to content"""
        with self.get_session() as session:
            document = session.query(Document).filter(Document.id == document_id).first()
            if document:
                session.delete(document)
                logger.info(f"Deleted document: {document_id}")

    # =========================================================================
    # DOCUMENT CONTENT OPERATIONS
    # =========================================================================

    def create_document_content(
        self,
        document_id: UUID,
        canonical_data: Dict[str, Any],
        searchable_text: Optional[str] = None,
        tags: Optional[List[str]] = None,
        confidence_score: Optional[float] = None
    ) -> DocumentContent:
        """
        Create document content

        Args:
            document_id: UUID of parent document
            canonical_data: Canonical document as dict
            searchable_text: Text for full-text search
            tags: Tags for categorization
            confidence_score: Quality score 0.0-1.0

        Returns:
            Created DocumentContent object
        """
        with self.get_session() as session:
            content = DocumentContent(
                document_id=document_id,
                canonical_data=canonical_data,
                searchable_text=searchable_text,
                tags=tags or [],
                confidence_score=confidence_score,
                schema_version=1
            )
            session.add(content)
            session.flush()
            logger.info(f"Created content for document: {document_id}")
            return content

    def get_document_content(self, document_id: UUID) -> Optional[DocumentContent]:
        """Get document content by document ID"""
        with self.get_session() as session:
            return session.query(DocumentContent)\
                .filter(DocumentContent.document_id == document_id)\
                .first()

    def update_document_content(
        self,
        document_id: UUID,
        canonical_data: Optional[Dict[str, Any]] = None,
        searchable_text: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """Update document content"""
        with self.get_session() as session:
            content = session.query(DocumentContent)\
                .filter(DocumentContent.document_id == document_id)\
                .first()

            if content:
                if canonical_data is not None:
                    content.canonical_data = canonical_data
                if searchable_text is not None:
                    content.searchable_text = searchable_text
                if tags is not None:
                    content.tags = tags
                logger.info(f"Updated content for document: {document_id}")

    # =========================================================================
    # CANONICAL DOCUMENT OPERATIONS (High-Level API)
    # =========================================================================

    def insert_canonical_document(
        self,
        canonical_doc,
        source_file: str = "pylidc://",
        uploaded_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        batch_id: Optional[UUID] = None
    ) -> Tuple[Document, DocumentContent]:
        """
        Insert a canonical document (metadata + content)

        Args:
            canonical_doc: RadiologyCanonicalDocument instance
            source_file: Source file identifier
            uploaded_by: User who uploaded
            tags: Optional tags
            batch_id: Optional batch identifier

        Returns:
            Tuple of (Document, DocumentContent)
        """
        with self.get_session() as session:
            # Create document metadata
            doc = Document.from_canonical(
                canonical_doc,
                source_file=source_file,
                uploaded_by=uploaded_by
            )
            doc.batch_id = batch_id
            session.add(doc)
            session.flush()  # Get the document ID

            # Create document content
            content = DocumentContent.from_canonical(
                canonical_doc,
                document_id=doc.id,
                tags=tags
            )
            session.add(content)
            session.flush()

            logger.info(f"Inserted canonical document: {doc.id} from {source_file}")
            return doc, content

    def upsert_canonical_document(
        self,
        canonical_doc,
        source_file: str,
        uploaded_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        batch_id: Optional[UUID] = None
    ) -> Tuple[Document, DocumentContent]:
        """
        Insert or update canonical document (idempotent)

        Uses source_file_path as unique key for upsert logic.

        Args:
            canonical_doc: RadiologyCanonicalDocument instance
            source_file: Source file identifier (used as unique key)
            uploaded_by: User who uploaded
            tags: Optional tags
            batch_id: Optional batch identifier

        Returns:
            Tuple of (Document, DocumentContent)
        """
        with self.get_session() as session:
            # Check if document exists
            existing_doc = session.query(Document)\
                .filter(Document.source_file_path == source_file)\
                .first()

            if existing_doc:
                # Update existing document
                logger.info(f"Updating existing document: {existing_doc.id}")
                existing_doc.status = 'completed'
                existing_doc.last_modified = datetime.utcnow()

                # Update content
                existing_content = session.query(DocumentContent)\
                    .filter(DocumentContent.document_id == existing_doc.id)\
                    .first()

                if existing_content:
                    canonical_dict = canonical_doc.model_dump(mode='json')
                    existing_content.canonical_data = canonical_dict
                    existing_content.tags = tags or existing_content.tags
                    return existing_doc, existing_content

            # Create new document
            return self.insert_canonical_document(
                canonical_doc,
                source_file=source_file,
                uploaded_by=uploaded_by,
                tags=tags,
                batch_id=batch_id
            )

    def batch_insert_canonical_documents(
        self,
        canonical_docs: List,
        source_files: List[str],
        uploaded_by: Optional[str] = None,
        tags: Optional[List[str]] = None,
        batch_id: Optional[UUID] = None,
        progress_callback=None
    ) -> List[Tuple[Document, DocumentContent]]:
        """
        Batch insert multiple canonical documents efficiently

        Args:
            canonical_docs: List of RadiologyCanonicalDocument instances
            source_files: List of source file identifiers (same length as canonical_docs)
            uploaded_by: User who uploaded
            tags: Tags to apply to all documents
            batch_id: Batch identifier for grouping
            progress_callback: Optional callback(current, total) for progress tracking

        Returns:
            List of (Document, DocumentContent) tuples
        """
        if len(canonical_docs) != len(source_files):
            raise ValueError("canonical_docs and source_files must have same length")

        if batch_id is None:
            batch_id = uuid4()

        results = []
        total = len(canonical_docs)

        for i, (canonical_doc, source_file) in enumerate(zip(canonical_docs, source_files)):
            try:
                doc, content = self.insert_canonical_document(
                    canonical_doc,
                    source_file=source_file,
                    uploaded_by=uploaded_by,
                    tags=tags,
                    batch_id=batch_id
                )
                results.append((doc, content))

                if progress_callback:
                    progress_callback(i + 1, total)

            except Exception as e:
                logger.error(f"Failed to insert document {i}/{total}: {e}")
                continue

        logger.info(f"Batch insert complete: {len(results)}/{total} documents")
        return results

    # =========================================================================
    # QUERY OPERATIONS
    # =========================================================================

    def get_documents_by_batch(self, batch_id: UUID) -> List[Document]:
        """Get all documents in a batch"""
        with self.get_session() as session:
            return session.query(Document)\
                .filter(Document.batch_id == batch_id)\
                .all()

    def get_documents_by_source_system(self, source_system: str) -> List[Document]:
        """Get documents from a specific source system"""
        with self.get_session() as session:
            return session.query(Document)\
                .filter(Document.source_system == source_system)\
                .all()

    def search_documents(
        self,
        search_text: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tuple[Document, DocumentContent]]:
        """
        Full-text search across documents

        Args:
            search_text: Text to search for
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            List of (Document, DocumentContent) tuples
        """
        with self.get_session() as session:
            # PostgreSQL full-text search
            results = session.query(Document, DocumentContent)\
                .join(DocumentContent, Document.id == DocumentContent.document_id)\
                .filter(
                    or_(
                        Document.source_file_name.ilike(f'%{search_text}%'),
                        DocumentContent.searchable_text.ilike(f'%{search_text}%')
                    )
                )\
                .limit(limit)\
                .offset(offset)\
                .all()

            return results

    def get_recent_documents(
        self,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Document]:
        """Get most recently ingested documents"""
        with self.get_session() as session:
            query = session.query(Document)\
                .order_by(desc(Document.ingestion_timestamp))

            if status:
                query = query.filter(Document.status == status)

            return query.limit(limit).all()

    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics"""
        with self.get_session() as session:
            total_docs = session.query(func.count(Document.id)).scalar()

            status_counts = session.query(
                Document.status,
                func.count(Document.id)
            ).group_by(Document.status).all()

            system_counts = session.query(
                Document.source_system,
                func.count(Document.id)
            ).group_by(Document.source_system).all()

            return {
                'total_documents': total_docs,
                'by_status': dict(status_counts),
                'by_source_system': dict(system_counts)
            }
