"""Integration test for Supabase document processing pipeline."""
import os
import pytest
import requests
from typing import Dict, Any
import time

from tests.supabase.functions._shared.conftest import supabase_config, test_user

# Test constants
TEST_FILE_CONTENT = b"Hello, World!"
TEST_CONTENT_TYPE = "application/pdf"
TEST_FILE_NAME = "test.pdf"

class TestDocumentProcessingPipeline:
    """Test suite for document processing pipeline (upload-handler -> doc-parser)."""
    
    @pytest.fixture(autouse=True)
    def setup(self, supabase_config: Dict[str, str]):
        """Set up test environment."""
        self.base_url = f"{supabase_config['url']}/functions/v1"
        self.upload_endpoint = f"{self.base_url}/upload-handler"
        self.doc_parser_endpoint = f"{self.base_url}/doc-parser"
        self.test_file_path = None
        self.test_doc_id = None
    
    async def test_upload_handler_success(self, test_user: Dict[str, Any]):
        """Test successful file upload and document creation."""
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

        print(f"Upload Response: {response.text}")
    
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
        
        # Store file path for cleanup
        self.test_file_path = file_data['filePath']
        
        # Verify document creation
        assert 'document' in result
        doc = result['document']
        assert doc['id'] is not None  # UUID should be present
        assert doc['owner'] == test_user['user'].id
        assert doc['name'] == TEST_FILE_NAME
        assert doc['source_path'] == file_data['filePath']
        assert doc['uploaded_at'] is not None  # Timestamp should be present
        
        # Store document ID for cleanup and doc-parser test
        self.test_doc_id = doc['id']
        
        return self.test_doc_id

    async def test_doc_parser_success(self, test_user: Dict[str, Any]):
        """Test successful document parsing after upload."""
        # First upload a document
        doc_id = await self.test_upload_handler_success(test_user)
        
        # Give upload-handler time to process
        time.sleep(2)
        
        # Call doc-parser with the document ID
        response = requests.post(
            self.doc_parser_endpoint,
            headers={
                'Authorization': f"Bearer {test_user['token']}",
                'Content-Type': 'application/json'
            },
            json={
                'docId': doc_id
            }
        )
        
        print(f"Doc-Parser Response: {response.text}")
        
        # Verify response structure
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['docId'] == doc_id
        assert 'llamaData' in data
        
        # Verify LlamaParse response structure
        llama_data = data['llamaData']
        assert isinstance(llama_data, dict)
        
        # TODO: Add more specific assertions about LlamaParse output structure
        # This will depend on the actual structure of LlamaParse response
        
        return data
    
    async def test_full_pipeline_performance(self, test_user: Dict[str, Any]):
        """Test the performance of the full document processing pipeline."""
        # Record start time
        start_time = time.time()
        
        # Step 1: Upload
        upload_start = time.time()
        doc_id = await self.test_upload_handler_success(test_user)
        upload_duration = time.time() - upload_start
        
        # Step 2: Parse
        parse_start = time.time()
        parse_result = await self.test_doc_parser_success(test_user)
        parse_duration = time.time() - parse_start
        
        # Calculate total duration
        total_duration = time.time() - start_time
        
        # Log performance metrics
        print(f"\nPipeline Performance Metrics:")
        print(f"Upload Duration: {upload_duration:.2f}s")
        print(f"Parse Duration: {parse_duration:.2f}s")
        print(f"Total Pipeline Duration: {total_duration:.2f}s")
        
        # Add some basic performance assertions
        assert upload_duration < 5.0, "Upload took too long"
        assert parse_duration < 10.0, "Parsing took too long"
        assert total_duration < 15.0, "Total pipeline took too long"
    
    async def test_missing_file(self, test_user: Dict[str, Any]):
        """Test error when file is missing in upload."""
        response = requests.post(
            self.upload_endpoint,
            files={},
            headers={
                'Authorization': f"Bearer {test_user['token']}"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error'] == 'File missing'
    
    async def test_missing_doc_id(self, test_user: Dict[str, Any]):
        """Test error when docId is missing in doc-parser."""
        response = requests.post(
            self.doc_parser_endpoint,
            headers={
                'Authorization': f"Bearer {test_user['token']}",
                'Content-Type': 'application/json'
            },
            json={}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert 'Missing docId' in str(data)
    
    async def test_invalid_doc_id(self, test_user: Dict[str, Any]):
        """Test error when an invalid docId is provided to doc-parser."""
        response = requests.post(
            self.doc_parser_endpoint,
            headers={
                'Authorization': f"Bearer {test_user['token']}",
                'Content-Type': 'application/json'
            },
            json={
                'docId': 'invalid-uuid'
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert data['success'] is False
        assert 'Document not found' in str(data)
    
    async def test_missing_auth(self):
        """Test error when auth is missing for both endpoints."""
        # Test upload-handler
        files = {
            'file': (TEST_FILE_NAME, TEST_FILE_CONTENT, TEST_CONTENT_TYPE)
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert data['error'] == 'No authorization header'
        
        # Test doc-parser
        response = requests.post(
            self.doc_parser_endpoint,
            headers={'Content-Type': 'application/json'},
            json={'docId': 'some-id'}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert 'No authorization header' in str(data)