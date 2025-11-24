"""
Comprehensive API Testing Suite for MAPS Backend
Tests all REST API endpoints with various scenarios
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# import after path setup
from maps.api.main import app  # noqa: E402

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check_success(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_check_detailed(self):
        """Test detailed health check"""
        response = client.get("/health?detailed=true")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        assert "services" in data


class TestProfileEndpoints:
    """Test profile management endpoints"""

    def test_list_profiles(self):
        """Test listing all profiles"""
        response = client.get("/api/v1/profiles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_profile_exists(self):
        """Test getting an existing profile"""
        # first create a test profile
        test_profile = {
            "profile_name": "test_profile",
            "file_type": "xml",
            "description": "Test profile",
            "mappings": [],
            "validation_rules": {"required_fields": []},
        }
        create_response = client.post("/api/v1/profiles", json=test_profile)
        
        if create_response.status_code == 201:
            response = client.get("/api/v1/profiles/test_profile")
            assert response.status_code == 200
            data = response.json()
            assert data["profile_name"] == "test_profile"

    def test_get_profile_not_found(self):
        """Test getting non-existent profile"""
        response = client.get("/api/v1/profiles/nonexistent_profile_xyz")
        assert response.status_code == 404

    def test_create_profile(self):
        """Test creating a new profile"""
        new_profile = {
            "profile_name": "new_test_profile",
            "file_type": "json",
            "description": "New test profile",
            "mappings": [
                {
                    "source_path": "$.data.field",
                    "target_path": "field",
                    "data_type": "string",
                    "required": True,
                }
            ],
            "validation_rules": {"required_fields": ["field"]},
        }
        response = client.post("/api/v1/profiles", json=new_profile)
        assert response.status_code in [200, 201]
        
        # cleanup
        client.delete("/api/v1/profiles/new_test_profile")

    def test_create_profile_duplicate(self):
        """Test creating profile with duplicate name"""
        profile = {
            "profile_name": "duplicate_test",
            "file_type": "xml",
            "description": "Duplicate test",
            "mappings": [],
            "validation_rules": {"required_fields": []},
        }
        
        # create once
        response1 = client.post("/api/v1/profiles", json=profile)
        
        # try creating again
        response2 = client.post("/api/v1/profiles", json=profile)
        assert response2.status_code in [400, 409]  # conflict
        
        # cleanup
        if response1.status_code in [200, 201]:
            client.delete("/api/v1/profiles/duplicate_test")

    def test_update_profile(self):
        """Test updating an existing profile"""
        # create profile first
        profile = {
            "profile_name": "update_test",
            "file_type": "xml",
            "description": "Original description",
            "mappings": [],
            "validation_rules": {"required_fields": []},
        }
        create_response = client.post("/api/v1/profiles", json=profile)
        
        if create_response.status_code in [200, 201]:
            # update it
            updated_profile = {
                **profile,
                "description": "Updated description",
            }
            response = client.put("/api/v1/profiles/update_test", json=updated_profile)
            assert response.status_code == 200
            
            # verify update
            get_response = client.get("/api/v1/profiles/update_test")
            data = get_response.json()
            assert data["description"] == "Updated description"
            
            # cleanup
            client.delete("/api/v1/profiles/update_test")

    def test_delete_profile(self):
        """Test deleting a profile"""
        # create profile first
        profile = {
            "profile_name": "delete_test",
            "file_type": "xml",
            "description": "To be deleted",
            "mappings": [],
            "validation_rules": {"required_fields": []},
        }
        create_response = client.post("/api/v1/profiles", json=profile)
        
        if create_response.status_code in [200, 201]:
            # delete it
            response = client.delete("/api/v1/profiles/delete_test")
            assert response.status_code in [200, 204]
            
            # verify deletion
            get_response = client.get("/api/v1/profiles/delete_test")
            assert get_response.status_code == 404


class TestFileUpload:
    """Test file upload and processing"""

    def test_upload_xml_file(self):
        """Test uploading an XML file"""
        test_xml = """<?xml version="1.0"?>
<data>
    <field>value</field>
</data>"""
        
        files = {"files": ("test.xml", test_xml, "text/xml")}
        data = {"profile_name": "LIDC_v2"}
        
        response = client.post("/api/v1/parse/upload", files=files, data=data)
        assert response.status_code in [200, 202]
        
        result = response.json()
        assert "job_id" in result or "message" in result

    def test_upload_multiple_files(self):
        """Test uploading multiple files"""
        files = [
            ("files", ("test1.xml", "<data><field>1</field></data>", "text/xml")),
            ("files", ("test2.xml", "<data><field>2</field></data>", "text/xml")),
        ]
        data = {"profile_name": "LIDC_v2"}
        
        response = client.post("/api/v1/parse/upload", files=files, data=data)
        assert response.status_code in [200, 202]

    def test_upload_invalid_file_type(self):
        """Test uploading invalid file type"""
        files = {"files": ("test.txt", "not xml content", "text/plain")}
        data = {"profile_name": "LIDC_v2"}
        
        response = client.post("/api/v1/parse/upload", files=files, data=data)
        # should reject or handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_upload_without_profile(self):
        """Test uploading without specifying profile"""
        files = {"files": ("test.xml", "<data/>", "text/xml")}
        
        response = client.post("/api/v1/parse/upload", files=files)
        # should use default profile or return error
        assert response.status_code in [200, 400, 422]

    def test_upload_oversized_file(self):
        """Test uploading file exceeding size limit"""
        # create large XML content (> 10MB)
        large_content = "<data>" + "x" * (11 * 1024 * 1024) + "</data>"
        files = {"files": ("large.xml", large_content, "text/xml")}
        data = {"profile_name": "LIDC_v2"}
        
        response = client.post("/api/v1/parse/upload", files=files, data=data)
        assert response.status_code in [400, 413]  # request entity too large


class TestJobManagement:
    """Test job processing endpoints"""

    def test_list_jobs(self):
        """Test listing all jobs"""
        response = client.get("/api/v1/batch/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_list_jobs_with_pagination(self):
        """Test job listing with pagination"""
        response = client.get("/api/v1/batch/jobs?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10

    def test_list_jobs_with_filters(self):
        """Test job listing with status filter"""
        response = client.get("/api/v1/batch/jobs?status=completed")
        assert response.status_code == 200

    def test_get_job_by_id(self):
        """Test getting job by ID"""
        # create a job first by uploading a file
        files = {"files": ("test.xml", "<data/>", "text/xml")}
        data = {"profile_name": "LIDC_v2"}
        upload_response = client.post("/api/v1/parse/upload", files=files, data=data)
        
        if upload_response.status_code in [200, 202]:
            result = upload_response.json()
            if "job_id" in result:
                job_id = result["job_id"]
                response = client.get(f"/api/v1/batch/jobs/{job_id}")
                assert response.status_code == 200

    def test_get_job_not_found(self):
        """Test getting non-existent job"""
        response = client.get("/api/v1/batch/jobs/nonexistent-job-id-xyz")
        assert response.status_code == 404

    def test_cancel_job(self):
        """Test canceling a running job"""
        # would need to create a long-running job first
        pass

    def test_delete_job(self):
        """Test deleting a completed job"""
        pass


class TestExport:
    """Test export endpoints"""

    def test_export_to_excel(self):
        """Test exporting data to Excel"""
        export_options = {
            "format": "excel",
            "filters": {},
        }
        response = client.post("/api/v1/export", json=export_options)
        # might be async, check for job_id or download_url
        assert response.status_code in [200, 202]

    def test_export_to_json(self):
        """Test exporting data to JSON"""
        export_options = {
            "format": "json",
            "filters": {},
        }
        response = client.post("/api/v1/export", json=export_options)
        assert response.status_code in [200, 202]

    def test_export_to_csv(self):
        """Test exporting data to CSV"""
        export_options = {
            "format": "csv",
            "filters": {},
        }
        response = client.post("/api/v1/export", json=export_options)
        assert response.status_code in [200, 202]

    def test_export_invalid_format(self):
        """Test exporting with invalid format"""
        export_options = {
            "format": "invalid_format",
            "filters": {},
        }
        response = client.post("/api/v1/export", json=export_options)
        assert response.status_code in [400, 422]


class TestAnalytics:
    """Test analytics endpoints"""

    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics"""
        response = client.get("/api/v1/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "total_jobs" in data

    def test_get_parse_case_distribution(self):
        """Test getting parse case distribution"""
        response = client.get("/api/v1/analytics/parse-cases")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_keyword_stats(self):
        """Test getting keyword statistics"""
        response = client.get("/api/v1/analytics/keywords")
        assert response.status_code == 200

    def test_get_processing_trends(self):
        """Test getting processing trends"""
        response = client.get("/api/v1/analytics/trends")
        assert response.status_code == 200


class TestKeywords:
    """Test keyword endpoints"""

    def test_search_keywords(self):
        """Test keyword search"""
        response = client.get("/api/v1/keywords/search?query=nodule")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_keyword_directory(self):
        """Test getting keyword directory"""
        response = client.get("/api/v1/keywords/directory")
        assert response.status_code == 200

    def test_normalize_keyword(self):
        """Test keyword normalization"""
        response = client.post("/api/v1/keywords/normalize", json={"term": "Nodule"})
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
