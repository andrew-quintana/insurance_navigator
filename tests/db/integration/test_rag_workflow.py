"""Test the critical RAG workflow components."""
import pytest
import uuid
import bcrypt
import json
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np

from supabase.client import Client
from tests.db.helpers import get_test_client, cleanup_test_data
from tests.config.test_config import get_rag_test_config, TestConfig

class TestRAGWorkflow:
    @pytest.fixture(scope="class")
    def supabase(self) -> Client:
        return get_test_client()  # Default anon client for basic operations
    
    @pytest.fixture(scope="class")
    def service_client(self) -> Client:
        return get_test_client(auth_type="service_role")  # Service role client for vector operations
    
    @pytest.fixture(scope="class")
    def config(self) -> TestConfig:
        return get_rag_test_config()
    
    @pytest.fixture(scope="class")
    def test_user_id(self, service_client: Client) -> str:
        """Create a test user and return their ID."""
        user_data = {
            "id": str(uuid.uuid4()),
            "email": f"test_{uuid.uuid4()}@example.com",
            "role": "user"
        }
        service_client.table("users").insert(user_data).execute()
        return user_data["id"]
    
    @pytest.fixture(scope="function")
    def test_document(self, service_client: Client, test_user_id: str):
        """Create a test document and clean it up after the test."""
        doc_data = {
            "user_id": test_user_id,
            "original_filename": "test_doc.pdf",
            "document_type": "regulatory",
            "content_type": "application/pdf",
            "storage_path": f"documents/{uuid.uuid4()}/test_doc.pdf",
            "metadata": {
                "jurisdiction": "federal",
                "program": "medicare",
                "document_date": datetime.now().isoformat()
            },
            "status": "active"
        }
        
        response = service_client.table("documents").insert(doc_data).execute()
        doc_id = response.data[0]["id"]
        
        yield doc_id
        
        # Clean up
        service_client.table("document_vectors").delete().eq("document_id", doc_id).execute()
        service_client.table("documents").delete().eq("id", doc_id).execute()
    
    def test_document_upload(self, service_client: Client, test_user_id: str):
        """Test document upload workflow."""
        doc_data = {
            "user_id": test_user_id,
            "original_filename": "upload_test.pdf",
            "document_type": "regulatory",
            "content_type": "application/pdf",
            "storage_path": f"documents/{uuid.uuid4()}/upload_test.pdf",
            "metadata": {
                "jurisdiction": "federal",
                "program": "medicare"
            },
            "status": "pending"
        }
        
        response = service_client.table("documents").insert(doc_data).execute()
        assert response.data, "Document upload failed"
        assert response.data[0]["status"] == "pending"
        
        # Clean up
        doc_id = response.data[0]["id"]
        service_client.table("documents").delete().eq("id", doc_id).execute()
    
    def test_document_vectorization(self, service_client: Client, test_document: str):
        """Test document vectorization workflow."""
        # Create test vectors
        vectors = [
            {
                "document_id": test_document,
                "chunk_index": i,
                "chunk_text": f"Test chunk {i}",
                "content_embedding": [0.1] * 1536,
                "metadata": {
                    "page_number": i + 1,
                    "section": f"section_{i}"
                }
            }
            for i in range(3)
        ]
        
        for vector in vectors:
            response = service_client.table("document_vectors").insert(vector).execute()
            assert response.data, "Vector creation failed"
        
        # Verify vectors were created
        query = service_client.table("document_vectors").select("*").eq("document_id", test_document).execute()
        assert len(query.data) == 3, "Not all vectors were created"
    
    def test_vector_similarity_search(self, service_client: Client, test_document: str):
        """Test vector similarity search workflow."""
        # Create test vectors with known embeddings
        test_vectors = [
            {
                "document_id": test_document,
                "chunk_index": i,
                "chunk_text": f"Test chunk {i}",
                "content_embedding": (np.random.rand(1536) * 2 - 1).tolist(),
                "metadata": {
                    "page_number": i + 1,
                    "section": f"section_{i}"
                }
            }
            for i in range(3)
        ]
        
        for vector in test_vectors:
            service_client.table("document_vectors").insert(vector).execute()
        
        # Test similarity search
        query_vector = (np.random.rand(1536) * 2 - 1).tolist()
        
        similar_vectors = service_client.rpc(
            "search_similar_vectors",
            {
                "query_embedding": query_vector,
                "match_threshold": 0.5,
                "match_count": 5
            }
        ).execute()
        
        assert similar_vectors.data, "Similarity search failed"
 