"""
Integration Tests for MAPS System
Tests end-to-end workflows across multiple components
"""

import pytest
import sys
from pathlib import Path
import tempfile
import shutil

# add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestXMLParsingWorkflow:
    """Test complete XML parsing workflow"""

    @pytest.fixture
    def sample_xml_file(self):
        """Create a temporary XML file for testing"""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<LidcReadMessage>
    <ResponseHeader>
        <SeriesInstanceUid>1.3.6.1.4.1.14519.5.2.1.series123</SeriesInstanceUid>
        <StudyInstanceUID>1.3.6.1.4.1.14519.5.2.1.study456</StudyInstanceUID>
    </ResponseHeader>
    <readingSession>
        <annotationVersion>1.0</annotationVersion>
        <unblindedReadNodule>
            <noduleID>Nodule001</noduleID>
            <characteristics>
                <subtlety>4</subtlety>
                <internalStructure>1</internalStructure>
                <calcification>6</calcification>
                <sphericity>3</sphericity>
                <margin>1</margin>
                <lobulation>1</lobulation>
                <spiculation>1</spiculation>
                <texture>5</texture>
                <malignancy>3</malignancy>
            </characteristics>
        </unblindedReadNodule>
    </readingSession>
</LidcReadMessage>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        yield temp_path
        
        # cleanup
        Path(temp_path).unlink(missing_ok=True)

    def test_parse_xml_to_dataframe(self, sample_xml_file):
        """Test parsing XML file to pandas DataFrame"""
        try:
            from ra_d_ps.parser import parse_radiology_sample
            
            main_df, unblinded_df = parse_radiology_sample(sample_xml_file)
            
            assert main_df is not None
            assert len(main_df) > 0
            assert 'Study UID' in main_df.columns
            assert 'Series UID' in main_df.columns
            
        except ImportError:
            pytest.skip("Parser module not available")

    def test_parse_xml_to_excel(self, sample_xml_file):
        """Test parsing XML and exporting to Excel"""
        try:
            from ra_d_ps.parser import parse_radiology_sample
            from ra_d_ps.exporters.excel_exporter import export_excel
            
            main_df, unblinded_df = parse_radiology_sample(sample_xml_file)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                records = [(main_df, unblinded_df)]
                output_path = export_excel(records, temp_dir, sheet="test")
                
                assert Path(output_path).exists()
                assert Path(output_path).suffix == '.xlsx'
                
        except ImportError:
            pytest.skip("Parser or exporter modules not available")

    def test_parse_multiple_xmls(self):
        """Test parsing multiple XML files in batch"""
        try:
            from ra_d_ps.parser import parse_multiple
            
            # create multiple temp XML files
            xml_files = []
            for i in range(3):
                content = f"""<?xml version="1.0"?>
<LidcReadMessage>
    <ResponseHeader>
        <StudyInstanceUID>1.3.6.1.4.1.study{i}</StudyInstanceUID>
    </ResponseHeader>
</LidcReadMessage>"""
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                    f.write(content)
                    xml_files.append(f.name)
            
            try:
                results = parse_multiple(xml_files)
                assert len(results) == 3
                
            finally:
                # cleanup
                for f in xml_files:
                    Path(f).unlink(missing_ok=True)
                    
        except ImportError:
            pytest.skip("Parser module not available")


class TestDatabaseIntegration:
    """Test database integration workflows"""

    def test_document_repository_create_and_read(self):
        """Test creating and reading documents from repository"""
        try:
            from ra_d_ps.database.enhanced_document_repository import EnhancedDocumentRepository
            
            repo = EnhancedDocumentRepository()
            
            # create test document
            test_doc = {
                "source": "test",
                "source_file": "test.xml",
                "parse_case": "LIDC_v2",
                "content": {"field": "value"},
            }
            
            doc_id = repo.store_document(test_doc)
            assert doc_id is not None
            
            # read it back
            retrieved = repo.get_document(doc_id)
            assert retrieved is not None
            assert retrieved["source"] == "test"
            
            # cleanup
            repo.delete_document(doc_id)
            
        except ImportError:
            pytest.skip("Database repository not available")

    def test_keyword_extraction_and_storage(self):
        """Test extracting keywords and storing in database"""
        try:
            from ra_d_ps.xml_keyword_extractor import XMLKeywordExtractor
            
            extractor = XMLKeywordExtractor()
            
            # create sample XML
            xml_content = """<?xml version="1.0"?>
<LidcReadMessage>
    <readingSession>
        <unblindedReadNodule>
            <characteristics>
                <subtlety>5</subtlety>
                <malignancy>4</malignancy>
            </characteristics>
        </unblindedReadNodule>
    </readingSession>
</LidcReadMessage>"""
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(xml_content)
                temp_path = f.name
            
            try:
                keywords = extractor.extract_from_xml(temp_path, store_in_db=False)
                assert len(keywords) > 0
                assert any(k['keyword'] == 'subtlety:5' for k in keywords)
                
            finally:
                Path(temp_path).unlink(missing_ok=True)
                
        except ImportError:
            pytest.skip("Keyword extractor not available")


class TestExportWorkflows:
    """Test export workflows"""

    def test_export_to_multiple_formats(self):
        """Test exporting data to different formats"""
        try:
            from ra_d_ps.parser import parse_radiology_sample
            from ra_d_ps.exporters.excel_exporter import export_excel
            import pandas as pd
            
            # create sample dataframe
            df = pd.DataFrame({
                'Study UID': ['123', '456'],
                'file #': [1, 2],
                'NoduleID': ['N1', 'N2'],
            })
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # export to Excel
                records = [(df, pd.DataFrame())]
                excel_path = export_excel(records, temp_dir, sheet="test")
                assert Path(excel_path).exists()
                
        except ImportError:
            pytest.skip("Export modules not available")


class TestGUIIntegration:
    """Test GUI integration (headless)"""

    def test_gui_initialization(self):
        """Test that GUI can be initialized without display"""
        try:
            import os
            os.environ['DISPLAY'] = ''  # force headless
            
            # GUI tests would go here but require tkinter with display
            pytest.skip("GUI requires display for testing")
            
        except ImportError:
            pytest.skip("GUI module not available")


class TestAPIIntegration:
    """Test API integration workflows"""

    def test_upload_and_process_workflow(self):
        """Test complete upload and process workflow via API"""
        from fastapi.testclient import TestClient
        from start_api import app
        
        client = TestClient(app)
        
        # 1. Upload files
        xml_content = """<?xml version="1.0"?>
<LidcReadMessage>
    <ResponseHeader>
        <StudyInstanceUID>1.3.6.1.test</StudyInstanceUID>
    </ResponseHeader>
</LidcReadMessage>"""
        
        files = {"files": ("test.xml", xml_content, "text/xml")}
        data = {"profile_name": "LIDC_v2"}
        
        upload_response = client.post("/api/v1/parse/upload", files=files, data=data)
        assert upload_response.status_code in [200, 202]
        
        # 2. Check job status
        if "job_id" in upload_response.json():
            job_id = upload_response.json()["job_id"]
            job_response = client.get(f"/api/v1/batch/jobs/{job_id}")
            assert job_response.status_code == 200
            
            # 3. Export results
            export_options = {"format": "json", "job_id": job_id}
            export_response = client.post("/api/v1/export", json=export_options)
            assert export_response.status_code in [200, 202]


class TestPYLIDCIntegration:
    """Test PYLIDC integration if available"""

    def test_pylidc_adapter(self):
        """Test PYLIDC adapter functionality"""
        try:
            import pylidc as pl
            from ra_d_ps.adapters.pylidc_adapter import PyLIDCAdapter
            
            adapter = PyLIDCAdapter()
            
            # query first scan
            scans = pl.query(pl.Scan).limit(1).all()
            if scans:
                scan = scans[0]
                canonical_doc = adapter.scan_to_canonical(scan, cluster_nodules=True)
                assert canonical_doc is not None
                assert canonical_doc.document_type == 'radiology'
            else:
                pytest.skip("No PYLIDC scans available")
                
        except ImportError:
            pytest.skip("PYLIDC not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
