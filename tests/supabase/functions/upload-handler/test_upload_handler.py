"""Integration test for Supabase upload handler edge function."""
import os
import pytest
import requests
from typing import Dict, Any

from tests.supabase.functions._shared.conftest import supabase_config, test_user

# Test constants
TEST_FILE_CONTENT = b"Hello, World!"
TEST_CONTENT_TYPE = "application/pdf"
TEST_FILE_NAME = "test.pdf"

class TestUploadHandler:
    """Test suite for upload handler edge function."""
    
    @pytest.fixture(autouse=True)
    def setup(self, supabase_config: Dict[str, str]):
        """Set up test environment."""
        self.base_url = f"{supabase_config['url']}/functions/v1"
        self.endpoint = f"{self.base_url}/upload-handler"
        self.test_file_path = None
        self.test_doc_id = None
    
    async def test_successful_upload(self, test_user: Dict[str, Any]):
        """Test successful file upload and document creation."""
        # Create test file data
        files = {
            'file': (TEST_FILE_NAME, TEST_FILE_CONTENT, TEST_CONTENT_TYPE)
        }
        
        # Make request with auth token
        response = requests.post(
            self.endpoint,
            files=files,
            headers={
                'Authorization': f"Bearer {test_user['token']}"
            }
        )

        print(f"Response: {response.text}")
    
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
        
        # Store document ID for cleanup
        self.test_doc_id = doc['id']
    
    async def test_missing_file(self, test_user: Dict[str, Any]):
        """Test error when file is missing."""
        response = requests.post(
            self.endpoint,
            files={},
            headers={
                'Authorization': f"Bearer {test_user['token']}"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error'] == 'File missing'
    
    async def test_missing_auth(self):
        """Test error when auth is missing."""
        files = {
            'file': (TEST_FILE_NAME, TEST_FILE_CONTENT, TEST_CONTENT_TYPE)
        }
        
        response = requests.post(
            self.endpoint,
            files=files
        )
        
        assert response.status_code == 401
        data = response.json()
        assert data['success'] is False
        assert data['error'] == 'No authorization header'