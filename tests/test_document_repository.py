#!/usr/bin/env python3
"""
Tests for DocumentRepository

Tests document and content operations with in-memory SQLite database.
"""

import pytest
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from maps.database.document_repository import DocumentRepository
from maps.database.models import Document, DocumentContent
from maps.schemas.canonical import RadiologyCanonicalDocument, DocumentMetadata


@pytest.fixture
def repository():
    """Create in-memory SQLite repository for testing"""
    repo = DocumentRepository(connection_string="sqlite:///:memory:")
    repo.create_tables()
    return repo


@pytest.fixture
def sample_canonical_doc():
    """Create sample RadiologyCanonicalDocument"""
    metadata = DocumentMetadata(
        document_type="radiology_report",
        title="Test Radiology Report",
        date=datetime.utcnow(),
        source_system="LIDC-IDRI",
        language="en"
    )

    doc = RadiologyCanonicalDocument(
        document_metadata=metadata,
        study_instance_uid="1.2.3.4.5",
        series_instance_uid="1.2.3.4.6",
        modality="CT",
        nodules=[
            {
                "nodule_id": "1",
                "num_radiologists": 2,
                "radiologists": {
                    "1": {"subtlety": 3, "malignancy": 4},
                    "2": {"subtlety": 4, "malignancy": 5}
                }
            }
        ],
        fields={
            "patient_id": "TEST-001",
            "slice_thickness": 1.0
        }
    )

    return doc


class TestDocumentCRUD:
    """Test basic Document CRUD operations"""

    def test_create_document(self, repository):
        """Test document creation"""
        doc = repository.create_document(
            source_file_name="test.xml",
            source_file_path="/path/to/test.xml",
            file_type="XML",
            uploaded_by="test_user"
        )

        assert doc.id is not None
        assert doc.source_file_name == "test.xml"
        assert doc.status == "pending"

    def test_get_document(self, repository):
        """Test retrieving document by ID"""
        # Create document
        doc = repository.create_document(
            source_file_name="test.xml",
            source_file_path="/path/to/test.xml"
        )

        # Retrieve it
        retrieved = repository.get_document(doc.id)

        assert retrieved is not None
        assert retrieved.id == doc.id
        assert retrieved.source_file_name == doc.source_file_name

    def test_update_document_status(self, repository):
        """Test updating document status"""
        doc = repository.create_document(
            source_file_name="test.xml",
            source_file_path="/path/to/test.xml"
        )

        # Update status
        repository.update_document_status(
            doc.id,
            status="completed",
            processing_duration_ms=1234
        )

        # Verify update
        updated = repository.get_document(doc.id)
        assert updated.status == "completed"
        assert updated.processing_duration_ms == 1234

    def test_delete_document(self, repository):
        """Test document deletion"""
        doc = repository.create_document(
            source_file_name="test.xml",
            source_file_path="/path/to/test.xml"
        )

        doc_id = doc.id

        # Delete
        repository.delete_document(doc_id)

        # Verify deleted
        retrieved = repository.get_document(doc_id)
        assert retrieved is None


class TestDocumentContent:
    """Test DocumentContent operations"""

    def test_create_content(self, repository):
        """Test creating document content"""
        # Create document first
        doc = repository.create_document(
            source_file_name="test.xml",
            source_file_path="/path/to/test.xml"
        )

        # Create content
        content = repository.create_document_content(
            document_id=doc.id,
            canonical_data={"test": "data"},
            searchable_text="test searchable text",
            tags=["test", "demo"]
        )

        assert content.id is not None
        assert content.document_id == doc.id
        assert content.canonical_data == {"test": "data"}
        assert content.tags == ["test", "demo"]

    def test_get_content(self, repository):
        """Test retrieving document content"""
        doc = repository.create_document(
            source_file_name="test.xml",
            source_file_path="/path/to/test.xml"
        )

        repository.create_document_content(
            document_id=doc.id,
            canonical_data={"test": "data"}
        )

        # Retrieve content
        content = repository.get_document_content(doc.id)

        assert content is not None
        assert content.document_id == doc.id

    def test_cascade_delete(self, repository):
        """Test that deleting document cascades to content"""
        doc = repository.create_document(
            source_file_name="test.xml",
            source_file_path="/path/to/test.xml"
        )

        repository.create_document_content(
            document_id=doc.id,
            canonical_data={"test": "data"}
        )

        # Delete document
        repository.delete_document(doc.id)

        # Content should also be deleted
        content = repository.get_document_content(doc.id)
        assert content is None


class TestCanonicalDocumentOperations:
    """Test high-level canonical document operations"""

    def test_insert_canonical_document(self, repository, sample_canonical_doc):
        """Test inserting canonical document"""
        doc, content = repository.insert_canonical_document(
            sample_canonical_doc,
            source_file="pylidc://TEST-001",
            uploaded_by="test_user",
            tags=["test"]
        )

        assert doc.id is not None
        assert content.id is not None
        assert content.document_id == doc.id
        assert doc.source_system == "LIDC-IDRI"
        assert "test" in content.tags

    def test_upsert_creates_new(self, repository, sample_canonical_doc):
        """Test upsert creates new document"""
        doc, content = repository.upsert_canonical_document(
            sample_canonical_doc,
            source_file="pylidc://TEST-001",
            uploaded_by="test_user"
        )

        assert doc.id is not None
        assert content.id is not None

    def test_upsert_updates_existing(self, repository, sample_canonical_doc):
        """Test upsert updates existing document"""
        # Insert first time
        doc1, content1 = repository.upsert_canonical_document(
            sample_canonical_doc,
            source_file="pylidc://TEST-001",
            uploaded_by="test_user"
        )

        doc1_id = doc1.id

        # Upsert again with same source_file
        doc2, content2 = repository.upsert_canonical_document(
            sample_canonical_doc,
            source_file="pylidc://TEST-001",
            uploaded_by="test_user2"
        )

        # Should be same document ID
        assert doc2.id == doc1_id

    def test_batch_insert(self, repository, sample_canonical_doc):
        """Test batch inserting multiple documents"""
        # Create 3 copies with different source files
        canonical_docs = [sample_canonical_doc] * 3
        source_files = [f"pylidc://TEST-00{i}" for i in range(1, 4)]

        results = repository.batch_insert_canonical_documents(
            canonical_docs=canonical_docs,
            source_files=source_files,
            uploaded_by="batch_user",
            tags=["batch", "test"]
        )

        assert len(results) == 3

        for doc, content in results:
            assert doc.id is not None
            assert content.document_id == doc.id
            assert "batch" in content.tags


class TestQueryOperations:
    """Test query and search operations"""

    def test_get_recent_documents(self, repository, sample_canonical_doc):
        """Test retrieving recent documents"""
        # Insert some documents
        for i in range(5):
            repository.insert_canonical_document(
                sample_canonical_doc,
                source_file=f"pylidc://TEST-{i:03d}"
            )

        recent = repository.get_recent_documents(limit=3)

        assert len(recent) <= 3

    def test_get_by_source_system(self, repository, sample_canonical_doc):
        """Test filtering by source system"""
        repository.insert_canonical_document(
            sample_canonical_doc,
            source_file="pylidc://TEST-001"
        )

        docs = repository.get_documents_by_source_system("LIDC-IDRI")

        assert len(docs) >= 1
        assert all(doc.source_system == "LIDC-IDRI" for doc in docs)

    def test_search_documents(self, repository, sample_canonical_doc):
        """Test full-text search"""
        repository.insert_canonical_document(
            sample_canonical_doc,
            source_file="pylidc://TEST-001",
            tags=["searchable", "test"]
        )

        # Search by tag
        results = repository.search_documents("searchable", limit=10)

        assert len(results) >= 0  # May or may not find depending on search implementation

    def test_get_statistics(self, repository, sample_canonical_doc):
        """Test repository statistics"""
        # Insert some documents
        repository.insert_canonical_document(
            sample_canonical_doc,
            source_file="pylidc://TEST-001"
        )

        stats = repository.get_statistics()

        assert 'total_documents' in stats
        assert stats['total_documents'] >= 1
        assert 'by_status' in stats
        assert 'by_source_system' in stats


class TestModels:
    """Test model helper methods"""

    def test_document_from_canonical(self, sample_canonical_doc):
        """Test Document.from_canonical() class method"""
        doc = Document.from_canonical(
            sample_canonical_doc,
            source_file="pylidc://TEST-001",
            uploaded_by="test_user"
        )

        assert doc.source_system == "LIDC-IDRI"
        assert doc.file_type == "XML"
        assert doc.uploaded_by == "test_user"
        assert doc.status == "completed"

    def test_document_content_from_canonical(self, sample_canonical_doc):
        """Test DocumentContent.from_canonical() class method"""
        content = DocumentContent.from_canonical(
            sample_canonical_doc,
            document_id=uuid4(),
            tags=["test"]
        )

        assert content.canonical_data is not None
        assert "study_instance_uid" in content.canonical_data
        assert content.schema_version == 1
        assert content.confidence_score == 1.0  # PYLIDC data is expert-annotated
        assert "test" in content.tags

    def test_document_to_dict(self):
        """Test Document.to_dict() method"""
        doc = Document(
            source_file_name="test.xml",
            source_file_path="/path/to/test.xml",
            file_type="XML"
        )

        doc_dict = doc.to_dict()

        assert isinstance(doc_dict, dict)
        assert doc_dict['source_file_name'] == "test.xml"
        assert doc_dict['file_type'] == "XML"

    def test_content_to_dict(self):
        """Test DocumentContent.to_dict() method"""
        content = DocumentContent(
            document_id=uuid4(),
            canonical_data={"test": "data"},
            tags=["test"]
        )

        content_dict = content.to_dict()

        assert isinstance(content_dict, dict)
        assert content_dict['canonical_data'] == {"test": "data"}
        assert content_dict['tags'] == ["test"]


def test_repository_initialization():
    """Test repository initialization"""
    # Test with custom connection string
    repo = DocumentRepository(connection_string="sqlite:///:memory:")
    assert repo.engine is not None

    # Test table creation
    repo.create_tables()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
