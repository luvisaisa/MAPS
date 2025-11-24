"""
Pytest configuration and fixtures for MAPS test suite

Provides database mocking, test data factories, and common fixtures
"""

import pytest
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.maps.database.models import Base


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def in_memory_db_engine():
    """
    Create an in-memory SQLite database engine for testing

    Note: SQLite doesn't support all PostgreSQL features (JSONB, ARRAY types),
    so some tests may need additional mocking
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(in_memory_db_engine) -> Generator[Session, None, None]:
    """
    Provide a test database session with automatic rollback

    Each test gets a fresh session that rolls back after completion,
    ensuring test isolation
    """
    connection = in_memory_db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_db_session(mocker):
    """
    Mock database session for unit tests that don't need real database

    Use this for testing business logic without database overhead
    """
    mock_session = mocker.MagicMock(spec=Session)
    mock_session.query.return_value = mock_session
    mock_session.filter.return_value = mock_session
    mock_session.first.return_value = None
    mock_session.all.return_value = []
    return mock_session


@pytest.fixture
def mock_db_connection(mocker):
    """
    Mock database connection for testing API endpoints

    Prevents actual database queries during API tests
    """
    with patch('src.maps.database.get_session') as mock_get_session:
        mock_session = MagicMock(spec=Session)
        mock_get_session.return_value = mock_session
        yield mock_session


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def mock_keyword_repository(mocker):
    """Mock KeywordRepository for testing without database"""
    mock_repo = mocker.MagicMock()
    mock_repo.search_keywords.return_value = []
    mock_repo.get_keyword_by_id.return_value = None
    mock_repo.get_keyword_directory.return_value = []
    mock_repo.normalize_keyword.return_value = "normalized"
    return mock_repo


@pytest.fixture
def mock_parse_case_repository(mocker):
    """Mock ParseCaseRepository for testing without database"""
    mock_repo = mocker.MagicMock()
    mock_repo.get_parse_case_by_name.return_value = None
    mock_repo.get_all_parse_cases.return_value = []
    mock_repo.create_parse_case.return_value = {"id": "test-id"}
    return mock_repo


@pytest.fixture
def mock_document_repository(mocker):
    """Mock DocumentRepository for testing without database"""
    mock_repo = mocker.MagicMock()
    mock_repo.get_document_by_id.return_value = None
    mock_repo.list_documents.return_value = []
    mock_repo.create_document.return_value = {"id": "test-doc-id"}
    return mock_repo


# ============================================================================
# Test Data Factories
# ============================================================================

@pytest.fixture
def sample_keyword_data():
    """Sample keyword data for testing"""
    return {
        "keyword": "pulmonary nodule",
        "category": "medical_term",
        "frequency": 42,
        "idf_score": 0.85
    }


@pytest.fixture
def sample_parse_case_data():
    """Sample parse case data for testing"""
    return {
        "name": "LIDC_Multi_Session_4",
        "description": "LIDC format with 4 radiologist sessions",
        "detection_criteria": {
            "min_chars": 5,
            "session_count": 4,
            "requires_header": True
        },
        "field_mappings": [
            {"source": "malignancy", "target": "Confidence", "type": "float"},
            {"source": "subtlety", "target": "Subtlety", "type": "float"}
        ],
        "characteristic_fields": ["malignancy", "subtlety", "calcification"],
        "detection_priority": 90,
        "format_type": "LIDC"
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for testing"""
    return {
        "filename": "test_document.xml",
        "document_title": "Test Radiology Report",
        "document_date": "2025-01-15",
        "parse_case": "LIDC_Multi_Session_4",
        "detection_confidence": 0.95,
        "status": "completed",
        "keywords_count": 15
    }


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        "profile_name": "test_profile",
        "file_type": "XML",
        "description": "Test profile for unit tests",
        "mappings": [
            {
                "source_path": "/root/field",
                "target_path": "canonical_field",
                "data_type": "string",
                "required": True
            }
        ],
        "validation_rules": {
            "required_fields": ["canonical_field"]
        }
    }


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_xml_file(tmp_path):
    """Create a temporary XML file for testing"""
    xml_content = """<?xml version="1.0"?>
<RadiologyReport>
    <Header>
        <StudyInstanceUID>1.2.3.4.5</StudyInstanceUID>
        <SeriesInstanceUID>1.2.3.4.6</SeriesInstanceUID>
    </Header>
    <ReadingSession>
        <NoduleID>1</NoduleID>
        <Malignancy>4</Malignancy>
        <Subtlety>3</Subtlety>
    </ReadingSession>
</RadiologyReport>"""

    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content)
    return str(xml_file)


@pytest.fixture
def temp_profile_file(tmp_path, sample_profile_data):
    """Create a temporary profile JSON file for testing"""
    import json
    profile_file = tmp_path / "test_profile.json"
    profile_file.write_text(json.dumps(sample_profile_data, indent=2))
    return str(profile_file)


# ============================================================================
# API Testing Fixtures
# ============================================================================

@pytest.fixture
def mock_fastapi_client():
    """Mock FastAPI TestClient for API endpoint testing"""
    from fastapi.testclient import TestClient

    # Note: Actual TestClient will be created per test
    # This fixture provides configuration
    return {
        "base_url": "http://testserver",
        "headers": {"Content-Type": "application/json"}
    }


@pytest.fixture
def mock_supabase_client(mocker):
    """Mock Supabase client for testing cloud database operations"""
    mock_client = mocker.MagicMock()
    mock_client.table.return_value = mock_client
    mock_client.select.return_value = mock_client
    mock_client.insert.return_value = mock_client
    mock_client.update.return_value = mock_client
    mock_client.delete.return_value = mock_client
    mock_client.execute.return_value = {"data": [], "error": None}
    return mock_client


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def mock_env_variables(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv("DATABASE_BACKEND", "postgresql")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "maps_test")
    monkeypatch.setenv("DB_USER", "test_user")
    monkeypatch.setenv("DB_PASSWORD", "test_password")
    monkeypatch.setenv("LOG_LEVEL", "ERROR")  # Suppress logs during tests


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Pytest configuration hook"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test (fast, no external dependencies)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (may require database)"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API endpoint test"
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically mark tests based on their location/name
    """
    for item in items:
        # Mark API tests
        if "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.api)

        # Mark integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)

        # Mark tests with 'unit' in name as unit tests
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
