"""Integration test for Supabase document processing pipeline."""
import pytest
import requests
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from supabase import create_client
import json

from tests.supabase.functions._shared.conftest import supabase_config, test_user

# Test constants
with open('examples/simulated_insurance_document.pdf', 'rb') as f:
    TEST_FILE_CONTENT = f.read()
TEST_CONTENT_TYPE = "application/pdf"
TEST_FILE_NAME = "simulated_insurance_document.pdf"
MAX_POLL_ATTEMPTS = 30  # 30 seconds timeout
POLL_INTERVAL = 1  # 1 second between polls

@dataclass
class PipelineState:
    """Maintains state throughout the pipeline tests."""
    doc_id: Optional[str] = None
    started_at: Optional[datetime] = None
    upload_time: Optional[float] = None
    parse_time: Optional[float] = None
    chunk_time: Optional[float] = None
    embed_time: Optional[float] = None

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

    def record_chunk_time(self):
        """Record chunk stage duration."""
        if self.started_at:
            self.chunk_time = (datetime.now() - self.started_at).total_seconds()

    def record_embed_time(self):
        """Record embed stage duration."""
        if self.started_at:
            self.embed_time = (datetime.now() - self.started_at).total_seconds()

    @property
    def total_time(self) -> Optional[float]:
        """Get total pipeline duration."""
        if self.started_at:
            return (datetime.now() - self.started_at).total_seconds()
        return None

class TestPipeline:
    """Test suite for document processing pipeline (upload-handler -> doc-parser -> chunker)."""

    @pytest.fixture
    def pipeline_state(self) -> PipelineState:
        """Create and maintain pipeline state across tests."""
        return PipelineState().start_timer()

    @pytest.fixture(autouse=True)
    def setup(self, supabase_config: Dict[str, str]):
        """Set up test environment."""
        self.base_url = f"{supabase_config['url']}/functions/v1"
        self.upload_endpoint = f"{self.base_url}/upload-handler"
        
        # Initialize Supabase client for status checks
        self.supabase = create_client(
            supabase_config["url"],
            supabase_config["service_role_key"]
        )

    def get_document_status(self, doc_id: str) -> Dict[str, Any]:
        """Get current document status from database."""
        result = self.supabase.schema("documents").from_("documents").select("*").eq("id", doc_id).single().execute()
        return result.data

    def get_document_chunks(self, doc_id: str) -> list[Dict[str, Any]]:
        """Get chunks for a document."""
        result = self.supabase.schema("documents").from_("document_chunks").select("*").eq("doc_id", doc_id).execute()
        return result.data

    @pytest.fixture
    async def trigger_pipeline(self, test_user: Dict[str, Any], pipeline_state: PipelineState):
        """Trigger the document processing pipeline and return initial state."""
        # Create and upload test file
        files = {
            'file': (TEST_FILE_NAME, TEST_FILE_CONTENT, TEST_CONTENT_TYPE)
        }
        
        response = requests.post(
            self.upload_endpoint,
            files=files,
            headers={
                'Authorization': f"Bearer {test_user['token']}"
            }
        )

        # Verify basic response and store document ID
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        pipeline_state.doc_id = data['result']['document']['id']
        
        # Record upload timing
        pipeline_state.record_upload_time()
        print(f"\n⏱️  Upload triggered in {pipeline_state.upload_time:.2f}s")
        
        # Return state for tests
        return pipeline_state

    async def test_successful_upload(self, trigger_pipeline: PipelineState):
        """Test the complete document processing pipeline."""
        pipeline_state = trigger_pipeline
        assert pipeline_state.doc_id, "Pipeline not triggered successfully"
        
        # Poll for document status through parsing and chunking
        print("\n🔄 Monitoring document processing...")
        final_doc = None
        for attempt in range(MAX_POLL_ATTEMPTS):
            doc = self.get_document_status(pipeline_state.doc_id)
            print(f"\n📄 Document State (attempt {attempt + 1}):")
            print(json.dumps(doc, indent=2))
            
            # Record timing for parse completion
            if doc['processing_status'] == 'parsed' and not pipeline_state.parse_time:
                pipeline_state.record_parse_time()
                print(f"✅ Document parsed after {pipeline_state.parse_time:.2f}s")
            
            # Record timing and check chunks for chunking completion
            if doc['processing_status'] == 'chunked':
                if not pipeline_state.chunk_time:
                    pipeline_state.record_chunk_time()
                    print(f"✅ Document chunked after {pipeline_state.chunk_time:.2f}s")
                
                chunks = self.get_document_chunks(pipeline_state.doc_id)
                if chunks:
                    print(f"\n📊 Found {len(chunks)} chunks")

            # Record timing for embedding completion
            if doc['processing_status'] == 'embedded':
                if not pipeline_state.embed_time:
                    pipeline_state.record_embed_time()
                    print(f"✅ Document embedded after {pipeline_state.embed_time:.2f}s")
                
                chunks = self.get_document_chunks(pipeline_state.doc_id)
                if chunks and all(chunk.get('embedding') is not None for chunk in chunks):
                    print(f"\n📊 All {len(chunks)} chunks embedded")
                    final_doc = doc
                    break
            
            print(f"⏳ Document status: {doc['processing_status']} (attempt {attempt + 1}/{MAX_POLL_ATTEMPTS})")
            time.sleep(POLL_INTERVAL)
        else:
            raise TimeoutError("Document processing timed out")
        
        # Print final document state for debugging
        print("\n📄 Final Document State:")
        print(json.dumps(final_doc, indent=2))
        
        # Verify final document state
        assert final_doc['processing_status'] == 'embedded'
        assert 'source_path' in final_doc, "Document should have source_path field"
        assert final_doc['source_path'], "source_path should not be empty"
            
        # Check for parsed_at timestamp
        assert 'parsed_at' in final_doc, "Document should have parsed_at timestamp"
        assert final_doc['parsed_at'] is not None, "parsed_at should not be null"
        
        # Verify chunks
        chunks = self.get_document_chunks(pipeline_state.doc_id)
        assert chunks, "Document should have chunks"
        assert len(chunks) > 0, "At least one chunk should be created"
        
        # Verify chunk structure and embeddings
        for chunk in chunks:
            assert 'id' in chunk, "Chunk should have ID"
            assert 'doc_id' in chunk, "Chunk should have document ID"
            assert chunk['doc_id'] == pipeline_state.doc_id, "Chunk should reference correct document"
            assert 'content' in chunk, "Chunk should have text content"
            assert 'embedding' in chunk, "Chunk should have embedding"
            assert chunk['embedding'] is not None, "Chunk embedding should not be null"
            assert isinstance(chunk['embedding'], list), "Chunk embedding should be a vector"
            assert len(chunk['embedding']) > 0, "Chunk embedding should not be empty"
            
        # Verify performance
        total_time = pipeline_state.total_time
        assert total_time is not None
        
        print(f"\n📊 Pipeline Performance Summary:")
        print(f"Upload Stage: {pipeline_state.upload_time:.2f}s")
        print(f"Processing Time: {pipeline_state.parse_time:.2f}s")
        print(f"Chunking Time: {pipeline_state.chunk_time:.2f}s")
        print(f"Embedding Time: {pipeline_state.embed_time:.2f}s")
        print(f"Total Pipeline Time: {total_time:.2f}s")
        
        assert pipeline_state.upload_time < 5.0, "Upload stage took too long"
        assert pipeline_state.parse_time < 30.0, "Processing took too long"
        assert pipeline_state.chunk_time < 35.0, "Chunking took too long"
        assert pipeline_state.embed_time < 40.0, "Embedding took too long"
        assert total_time < 110.0, "Total pipeline took too long"