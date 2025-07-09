"""Integration test for Supabase document processing pipeline."""
import os
import pytest
import requests
from typing import Dict, Any, Optional
import time
from dataclasses import dataclass
from datetime import datetime

from tests.supabase.functions._shared.conftest import supabase_config, test_user

# Test constants
TEST_FILE_CONTENT = b"Hello, World!"
TEST_CONTENT_TYPE = "application/pdf"
TEST_FILE_NAME = "test.pdf"

@dataclass
class PipelineState:
    """Maintains state throughout the pipeline tests."""
    doc_id: Optional[str] = None
    file_path: Optional[str] = None
    upload_time: Optional[float] = None
    parse_time: Optional[float] = None
    llama_data: Optional[dict] = None
    started_at: Optional[datetime] = None

    def start_timer(self):
        """Start pipeline timer."""
        self.started_at = datetime.now()
        return self

    def record_upload_time(self):
        """Record upload stage duration."""
        if self.started_at:
            self.upload_time = (datetime.now() - self.started_at).total_seconds()

    def record_parse_time(self):
        """Record parse stage duration."""
        if self.started_at:
            self.parse_time = (datetime.now() - self.started_at).total_seconds()

    @property
    def total_time(self) -> Optional[float]:
        """Get total pipeline duration."""
        if self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None

class TestDocumentProcessingPipeline:
    """Test suite for document processing pipeline (upload-handler -> doc-parser)."""
    
    @pytest.fixture(autouse=True)
    def setup(self, supabase_config: Dict[str, str]):
        """Set up test environment."""
        self.base_url = f"{supabase_config['url']}/functions/v1"
        self.upload_endpoint = f"{self.base_url}/upload-handler"
        self.doc_parser_endpoint = f"{self.base_url}/doc-parser"

    @pytest.fixture(scope="class")
    def pipeline_state(self) -> PipelineState:
        """Create and maintain pipeline state across tests."""
        return PipelineState().start_timer()

    @pytest.mark.order(1)
    async def test_upload_stage(self, test_user: Dict[str, Any], pipeline_state: PipelineState):
        """Test the upload stage of the pipeline."""
        # Create test file data
        files = {
            'file': (TEST_FILE_NAME, TEST_FILE_CONTENT, TEST_CONTENT_TYPE)
        }
        
        # Make request with auth token
        response = requests.post(
            self.upload_endpoint,
            files=files,
            headers={
                'Authorization': f"Bearer {test_user['token']}"
            }
        )

        print(f"\n📤 Upload Stage Response: {response.text}")
    
        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'result' in data
        
        result = data['result']
        
        # Verify file upload details
        assert 'file' in result
        file_data = result['file']
        assert file_data['fileName'] == TEST_FILE_NAME
        assert file_data['userId'] == test_user['user'].id
        assert file_data['filePath'].startswith(f"user/{test_user['user'].id}/raw/")
        assert file_data['filePath'].endswith(TEST_FILE_NAME)
        assert file_data['contentType'] == TEST_CONTENT_TYPE
        assert file_data['size'] == len(TEST_FILE_CONTENT)
        
        # Store file path in pipeline state
        pipeline_state.file_path = file_data['filePath']
        
        # Verify document creation
        assert 'document' in result
        doc = result['document']
        assert doc['id'] is not None  # UUID should be present
        assert doc['owner'] == test_user['user'].id
        assert doc['name'] == TEST_FILE_NAME
        assert doc['source_path'] == file_data['filePath']
        assert doc['uploaded_at'] is not None  # Timestamp should be present
        
        # Update pipeline state
        pipeline_state.doc_id = doc['id']
        pipeline_state.record_upload_time()
        
        print(f"\n⏱️  Upload stage completed in {pipeline_state.upload_time:.2f}s")
        assert pipeline_state.upload_time < 5.0, "Upload stage took too long"

    @pytest.mark.order(2)
    async def test_parse_stage(self, test_user: Dict[str, Any], pipeline_state: PipelineState):
        """Test the parsing stage of the pipeline."""
        assert pipeline_state.doc_id, "Upload stage must be completed first"
        
        # Give upload-handler time to process
        time.sleep(1)
        
        # Call doc-parser with the document ID
        response = requests.post(
            self.doc_parser_endpoint,
            headers={
                'Authorization': f"Bearer {test_user['token']}",
                'Content-Type': 'application/json'
            },
            json={
                'docId': pipeline_state.doc_id
            }
        )
        
        print(f"\n📑 Parse Stage Response: {response.text}")
        
        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['docId'] == pipeline_state.doc_id
        assert 'llamaData' in data
        
        # Store parse results in pipeline state
        pipeline_state.llama_data = data['llamaData']
        pipeline_state.record_parse_time()
        
        print(f"\n⏱️  Parse stage completed in {pipeline_state.parse_time:.2f}s")
        assert pipeline_state.parse_time < 10.0, "Parse stage took too long"

    @pytest.mark.order(3)
    async def test_pipeline_performance(self, pipeline_state: PipelineState):
        """Verify overall pipeline performance."""
        assert pipeline_state.upload_time is not None, "Upload stage not completed"
        assert pipeline_state.parse_time is not None, "Parse stage not completed"
        
        total_time = pipeline_state.total_time
        assert total_time is not None
        
        print(f"\n📊 Pipeline Performance Summary:")
        print(f"Upload Stage: {pipeline_state.upload_time:.2f}s")
        print(f"Parse Stage: {pipeline_state.parse_time:.2f}s")
        print(f"Total Pipeline Time: {total_time:.2f}s")
        
        assert total_time < 15.0, "Total pipeline took too long"