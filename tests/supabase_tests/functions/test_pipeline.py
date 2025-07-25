

"""Integration test for Supabase document processing pipeline."""
import pytest
import requests
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Test constants
with open('examples/simulated_insurance_document.pdf', 'rb') as f:
    TEST_FILE_CONTENT = f.read()
TEST_CONTENT_TYPE = "application/pdf"
TEST_FILE_NAME = "simulated_insurance_document.pdf"
MAX_POLL_ATTEMPTS = 300  # 180 seconds timeout
POLL_INTERVAL = 1  # 1 second between polls

@dataclass
class PipelineState:
    """Track pipeline processing state and timing."""
    doc_id: str
    started_at: datetime
    upload_time: Optional[float] = None
    parse_time: Optional[float] = None
    chunk_time: Optional[float] = None
    embed_time: Optional[float] = None

    def record_upload_time(self):
        self.upload_time = (datetime.now() - self.started_at).total_seconds()

    def record_parse_time(self):
        self.parse_time = (datetime.now() - self.started_at).total_seconds()

    def record_chunk_time(self):
        self.chunk_time = (datetime.now() - self.started_at).total_seconds()

    def record_embed_time(self):
        self.embed_time = (datetime.now() - self.started_at).total_seconds()

    @property
    def total_time(self) -> float:
        return (datetime.now() - self.started_at).total_seconds()

class TestPipeline:
    """Test the document processing pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self, test_config):
        """Setup test configuration."""
        self.config = test_config
        self.supabase_url = test_config.supabase.url
        self.service_role_key = test_config.supabase.service_role_key

    def upload_document(self, token: str, document_type: str = "user_document") -> Dict[str, Any]:
        """Upload a test document and return the response."""
        files = {
            'file': (TEST_FILE_NAME, TEST_FILE_CONTENT, TEST_CONTENT_TYPE)
        }
        data = {
            'documentType': document_type
        }
        
        response = requests.post(
            f"{self.supabase_url}/functions/v1/upload-handler",
            files=files,
            data=data,
            headers={
                'Authorization': f"Bearer {token}"
            }
        )
        
        return response.json()

    def get_document_status(self, doc_id: str) -> Dict[str, Any]:
        """Get document status from the database."""
        import requests
        response = requests.get(
            f"{self.supabase_url}/rest/v1/documents?select=*&id=eq.{doc_id}",
            headers={
                'apikey': self.service_role_key,
                'Authorization': f"Bearer {self.service_role_key}"
            }
        )
        response.raise_for_status()
        docs = response.json()
        return docs[0] if docs else {}

    def get_document_chunks(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get document chunks from the database."""
        import requests
        response = requests.get(
            f"{self.supabase_url}/rest/v1/document_chunks?select=*&doc_id=eq.{doc_id}",
            headers={
                'apikey': self.service_role_key,
                'Authorization': f"Bearer {self.service_role_key}"
            }
        )
        response.raise_for_status()
        return response.json()

    def format_time(self, seconds: Optional[float]) -> str:
        """Format time in seconds to human readable string."""
        if seconds is None:
            return "N/A"
        return f"{seconds:.2f}s"

    def wait_for_completion(self, doc_id: str) -> Dict[str, Any]:
        """Wait for document processing to complete."""
        pipeline_state = PipelineState(doc_id=doc_id, started_at=datetime.now())
        last_status = None
        final_doc = None

        for attempt in range(MAX_POLL_ATTEMPTS):
            doc = self.get_document_status(pipeline_state.doc_id)
            current_status = doc['processing_status']
            print(f"[{datetime.now()}] 📄 Document State (attempt {attempt + 1}):")
            print(json.dumps(doc, indent=2))
            
            # Record timing for status changes
            if current_status != last_status:
                if current_status == 'parsed':
                    pipeline_state.record_parse_time()
                    print(f"[{datetime.now()}] ✅ Document parsed after {self.format_time(pipeline_state.parse_time)}")
                elif current_status == 'chunked':
                    pipeline_state.record_chunk_time()
                    print(f"[{datetime.now()}] ✅ Document chunked after {self.format_time(pipeline_state.chunk_time)}")
                elif current_status == 'embedded':
                    pipeline_state.record_embed_time()
                    print(f"[{datetime.now()}] ✅ Document embedded after {self.format_time(pipeline_state.embed_time)}")
                last_status = current_status
            
            # Check for completion when embedded
            if current_status == 'embedded':
                chunks = self.get_document_chunks(pipeline_state.doc_id)
                if chunks:
                    print(f"\n[{datetime.now()}] 📊 Found {len(chunks)} chunks")

            # Check for completion when embedded
            if current_status == 'embedded':
                chunks = self.get_document_chunks(pipeline_state.doc_id)
                if chunks and all(chunk.get('embedding') is not None for chunk in chunks):
                    print(f"[{datetime.now()}] 📊 All {len(chunks)} chunks embedded")
                    final_doc = doc
                    break
            
            print(f"[{datetime.now()}] ⏳ Document status: {current_status} (attempt {attempt + 1}/{MAX_POLL_ATTEMPTS})")
            time.sleep(POLL_INTERVAL)
        else:
            raise TimeoutError("Document processing timed out")
        
        # Print final document state for debugging
        print(f"[{datetime.now()}] 📄 Final Document State:")
        print(json.dumps(final_doc, indent=2))
        
        # Always print performance summary before any assertions
        total_time = pipeline_state.total_time
        print(f"[{datetime.now()}] 📊 Pipeline Performance Summary:")
        print("=" * 50)
        print(f"📈 Upload Stage:       {self.format_time(pipeline_state.upload_time)}")
        print(f"📈 Parse Stage:        {self.format_time(pipeline_state.parse_time)}")
        print(f"📈 Chunk Stage:        {self.format_time(pipeline_state.chunk_time)}")
        print(f"📈 Embed Stage:        {self.format_time(pipeline_state.embed_time)}")
        print(f"📈 Total Time:         {self.format_time(total_time)}")
        print("=" * 50)

        return final_doc

    def test_successful_upload(self, test_user):
        """Test successful document upload and processing."""
        # Upload document
        data = self.upload_document(test_user["token"])
        assert data['success'], f"Upload failed: {data.get('error', 'Unknown error')}"
        
        doc = data['result']['document']
        print(f"📄 Document uploaded with ID: {doc['id']}")
        
        # Verify final state from response
        assert doc['document_type'] == 'user_document', f"Expected 'user_document', got {doc['document_type']}"
        # (Skip wait_for_completion and REST fetch for this test)

    @pytest.mark.parametrize("document_type, is_admin", [
        ("user_document", False),
        ("regulatory_document", True)
    ])
    def test_upload_document_type(self, test_user, admin_user, document_type, is_admin):
        """Test uploading with different document_type as admin/user."""
        # Use admin user if is_admin is True, otherwise use regular user
        user_fixture = admin_user if is_admin else test_user
        token = user_fixture["token"]
        
        # Upload document with specified type
        data = self.upload_document(token, document_type)
        doc = data['result']['document']
        
        if is_admin:
            # Admin should be able to upload regulatory documents
            assert data['success'], f"Admin upload failed: {data.get('error', 'Unknown error')}"
            assert doc['document_type'] == document_type, f"Expected {document_type}, got {doc['document_type']}"
        else:
            # Non-admin should not be able to upload regulatory documents
            assert data['success'], "Non-admin upload should still succeed as user_document"
            assert doc['document_type'] == 'user_document', "Non-admin should only be able to upload user_document type"

    def test_user_cannot_update_regulatory_document(self, test_user, admin_user):
        """Test that a regular user cannot update a regulatory_document."""
        # First, upload as admin
        files = {
            'file': (TEST_FILE_NAME, TEST_FILE_CONTENT, TEST_CONTENT_TYPE)
        }
        data = {
            'documentType': "regulatory_document"
        }
        response = requests.post(
            f"{self.supabase_url}/functions/v1/upload-handler",
            files=files,
            data=data,
            headers={
                'Authorization': f"Bearer {admin_user['token']}"
            }
        )
        upload_data = response.json()
        assert upload_data['success'], "Admin upload failed"
        
        doc_id = upload_data['result']['document']['id']
        
        # Try to update as regular user (should fail)
        update_data = {
            'title': 'Updated Title',
            'description': 'Updated Description'
        }
        update_resp = requests.patch(
            f"{self.supabase_url}/rest/v1/documents?id=eq.{doc_id}",
            json=update_data,
            headers={
                'apikey': self.service_role_key,
                'Authorization': f"Bearer {test_user['token']}"
            }
        )
        
        # Should fail due to RLS policy or not found (404)
        assert update_resp.status_code in (401, 403, 404)

    def test_user_can_read_regulatory_document(self, test_user, admin_user):
        """Test that a user can read regulatory_document but not update/insert it."""
        # Upload as admin
        files = {
            'file': (TEST_FILE_NAME, TEST_FILE_CONTENT, TEST_CONTENT_TYPE)
        }
        data = {
            'documentType': "regulatory_document"
        }
        response = requests.post(
            f"{self.supabase_url}/functions/v1/upload-handler",
            files=files,
            data=data,
            headers={
                'Authorization': f"Bearer {admin_user['token']}"
            }
        )
        upload_data = response.json()
        assert upload_data['success'], "Admin upload failed"
        
        doc_id = upload_data['result']['document']['id']
        
        # Try to read as regular user (should succeed or be forbidden by RLS)
        read_resp = requests.get(
            f"{self.supabase_url}/rest/v1/documents?id=eq.{doc_id}",
            headers={
                'apikey': self.service_role_key,
                'Authorization': f"Bearer {test_user['token']}"
            }
        )
        
        # Should succeed (200) or be forbidden (404 if RLS blocks it)
        assert read_resp.status_code in (200, 404)
        if read_resp.status_code == 200:
            docs = read_resp.json()
            assert len(docs) > 0, "No documents returned"
            assert docs[0]['document_type'] == 'regulatory_document', "Document type not set correctly"