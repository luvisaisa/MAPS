"""
Comprehensive Unit Tests for API Services

Tests service layer business logic with mocked database dependencies.
"""

import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from src.maps.api.services.analytics_service import AnalyticsService
from src.maps.api.services.batch_service import BatchService
from src.maps.api.services.export_service import ExportService


class TestAnalyticsService:
    """Test suite for AnalyticsService"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """Create AnalyticsService instance"""
        return AnalyticsService(mock_db)

    def test_service_initialization(self, service, mock_db):
        """Test service initializes with database session"""
        assert service.db == mock_db

    def test_get_summary(self, service):
        """Test get_summary returns dict with total_documents"""
        result = service.get_summary()

        assert isinstance(result, dict)
        assert "total_documents" in result
        assert isinstance(result["total_documents"], int)

    def test_get_parse_case_distribution(self, service):
        """Test get_parse_case_distribution returns list"""
        result = service.get_parse_case_distribution()

        assert isinstance(result, list)

    def test_get_keyword_stats(self, service):
        """Test get_keyword_stats returns dict"""
        result = service.get_keyword_stats()

        assert isinstance(result, dict)

    def test_get_inter_rater_reliability(self, service):
        """Test get_inter_rater_reliability returns dict"""
        result = service.get_inter_rater_reliability()

        assert isinstance(result, dict)

    def test_get_completeness_metrics(self, service):
        """Test get_completeness_metrics returns dict"""
        result = service.get_completeness_metrics()

        assert isinstance(result, dict)

    def test_get_case_identifier_stats(self, service):
        """Test get_case_identifier_stats returns dict"""
        result = service.get_case_identifier_stats()

        assert isinstance(result, dict)


class TestBatchService:
    """Test suite for BatchService"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """Create BatchService instance"""
        return BatchService(mock_db)

    def test_service_initialization(self, service, mock_db):
        """Test service initializes with database session"""
        assert service.db == mock_db

    def test_create_job(self, service):
        """Test create_job returns BatchJobResponse"""
        import asyncio

        file_paths = ["/path/to/file1.xml", "/path/to/file2.xml"]
        profile = {"profile_name": "test_profile"}

        result = asyncio.run(service.create_job(file_paths, profile))

        assert result is not None
        assert hasattr(result, "job_id")
        assert hasattr(result, "status")
        assert hasattr(result, "total_files")
        assert result.total_files == 2
        assert result.status == "created"

    def test_get_job_status(self, service):
        """Test get_job_status returns None for non-existent job"""
        result = service.get_job_status("fake-job-id")

        # Stub implementation returns None
        assert result is None

    def test_get_job_results(self, service):
        """Test get_job_results returns empty dict"""
        result = service.get_job_results("fake-job-id")

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_cancel_job(self, service):
        """Test cancel_job returns False for stub"""
        result = service.cancel_job("fake-job-id")

        assert isinstance(result, bool)
        assert result is False

    def test_list_jobs_empty(self, service):
        """Test list_jobs returns empty list"""
        result = service.list_jobs()

        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_jobs_with_pagination(self, service):
        """Test list_jobs accepts pagination parameters"""
        result = service.list_jobs(skip=10, limit=20)

        assert isinstance(result, list)

    def test_list_jobs_with_status_filter(self, service):
        """Test list_jobs accepts status filter"""
        result = service.list_jobs(status="completed")

        assert isinstance(result, list)

    def test_count_jobs_default(self, service):
        """Test count_jobs returns 0 for empty database"""
        result = service.count_jobs()

        assert isinstance(result, int)
        assert result == 0

    def test_count_jobs_with_status_filter(self, service):
        """Test count_jobs accepts status filter"""
        result = service.count_jobs(status="pending")

        assert isinstance(result, int)


class TestExportService:
    """Test suite for ExportService"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        mock = Mock(spec=Session)
        # Mock execute to return a result with fetchall
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            {"id": 1, "name": "Test1"},
            {"id": 2, "name": "Test2"}
        ]
        mock.execute.return_value = mock_result
        return mock

    @pytest.fixture
    def service(self, mock_db):
        """Create ExportService instance"""
        return ExportService(mock_db)

    def test_service_initialization(self, service, mock_db):
        """Test service initializes with database session"""
        assert service.db == mock_db

    @pytest.mark.asyncio
    async def test_export_view_csv(self, service, tmp_path, monkeypatch):
        """Test export_view with CSV format"""
        # Change to temp directory for file operations
        monkeypatch.chdir(tmp_path)

        result = await service.export_view("test_view", "csv")

        assert result.status == "success"
        assert result.format == "csv"
        assert result.filename == "test_view.csv"
        assert result.record_count == 2

    @pytest.mark.asyncio
    async def test_export_view_excel(self, service, tmp_path, monkeypatch):
        """Test export_view with Excel format"""
        monkeypatch.chdir(tmp_path)

        result = await service.export_view("test_view", "excel")

        assert result.status == "success"
        assert result.format == "excel"
        assert result.filename == "test_view.xlsx"
        assert result.record_count == 2

    @pytest.mark.asyncio
    async def test_export_view_json(self, service, tmp_path, monkeypatch):
        """Test export_view with JSON format"""
        monkeypatch.chdir(tmp_path)

        result = await service.export_view("test_view", "json")

        assert result.status == "success"
        assert result.format == "json"
        assert result.filename == "test_view.json"
        assert result.record_count == 2

    @pytest.mark.asyncio
    async def test_export_view_with_limit(self, service, tmp_path, monkeypatch):
        """Test export_view with limit parameter"""
        monkeypatch.chdir(tmp_path)

        result = await service.export_view("test_view", "csv", limit=10)

        assert result.status == "success"
        # Verify limit was applied in query
        service.db.execute.assert_called_once()
        call_args = service.db.execute.call_args[0][0]
        assert "LIMIT 10" in call_args

    @pytest.mark.asyncio
    async def test_export_view_error_handling(self):
        """Test export_view handles database errors"""
        # Create service with failing database
        mock_db = Mock(spec=Session)
        mock_db.execute.side_effect = Exception("Database error")
        service = ExportService(mock_db)

        result = await service.export_view("test_view", "csv")

        assert result.status == "error"
        assert result.format == "csv"
        assert result.record_count == 0

    @pytest.mark.asyncio
    async def test_export_custom(self, service, tmp_path, monkeypatch):
        """Test export_custom delegates to export_view"""
        monkeypatch.chdir(tmp_path)

        result = await service.export_custom(view_name="custom_view", format="json")

        assert result.status == "success"
        assert result.format == "json"
        assert result.filename == "custom_view.json"

    @pytest.mark.asyncio
    async def test_export_custom_defaults(self, service, tmp_path, monkeypatch):
        """Test export_custom uses default values"""
        monkeypatch.chdir(tmp_path)

        result = await service.export_custom()

        assert result.status == "success"
        assert result.format == "csv"
        assert result.filename == "documents.csv"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
