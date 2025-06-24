import pytest
import uuid
import numpy as np
from datetime import datetime
from typing import List

from supabase.client import Client
from tests.db.helpers import get_test_client
from tests.config.test_config import get_test_config

class TestDocumentVectors:
    @pytest.fixture(scope="class")
    def supabase(self) -> Client:
        return get_test_client()  # Default anon client for basic operations
    
    @pytest.fixture(scope="class")
    def service_client(self) -> Client:
        return get_test_client(auth_type="service_role")  # Service role client for vector operations
    
    @pytest.fixture(scope="class")
    def config(self):
        return get_test_config()
    
    @pytest.fixture(scope="class")
    def test_user_id(self) -> str:
        """Create a test user ID that will be used across all tests."""
        return str(uuid.uuid4())
    
    @pytest.fixture(scope="function")
    def test_document(self, supabase: Client, test_user_id: str):
        """Create a test document and clean it up after the test."""
        doc_data = {
            "user_id": test_user_id,
            "original_filename": "vector_test.pdf",
            "document_type": "regulatory",
            "content_type": "application/pdf",
            "storage_path": f"documents/{uuid.uuid4()}/vector_test.pdf",
            "metadata": {
                "jurisdiction": "federal",
                "program": "medicare",
                "document_date": datetime.now().isoformat()
            },
            "status": "active"
        }
        
        response = supabase.table("documents").insert(doc_data).execute()
        doc_id = response.data[0]["id"]
        
        yield doc_id
        
        # Clean up using service client for vector operations
        service_client = get_test_client(auth_type="service_role")
        service_client.table("document_vectors").delete().eq("document_id", doc_id).execute()
        supabase.table("documents").delete().eq("id", doc_id).execute()

    def test_vector_creation(self, service_client: Client, test_document: str):
        """Test creating document vectors."""
        vector_data = {
            "document_id": test_document,
            "chunk_index": 0,
            "chunk_text": "This is a test chunk for vector creation",
            "content_embedding": [0.1] * 1536,  # Example embedding
            "metadata": {
                "page_number": 1,
                "section": "introduction"
            }
        }
        
        response = service_client.table("document_vectors").insert(vector_data).execute()
        assert response.data, "Vector creation failed"
        assert response.data[0]["document_id"] == test_document
        assert len(response.data[0]["content_embedding"]) == 1536

    def test_vector_similarity_search(self, service_client: Client, test_document: str):
        """Test vector similarity search."""
        # Create multiple test vectors
        test_vectors = [
            {
                "document_id": test_document,
                "chunk_index": i,
                "chunk_text": f"Test chunk {i} for similarity search",
                "content_embedding": (np.random.rand(1536) * 2 - 1).tolist(),  # Random unit vector
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
        query_vector = (np.random.rand(1536) * 2 - 1).tolist()  # Random query vector
        
        # Note: This assumes you have a vector similarity search function in your database
        similar_vectors = service_client.rpc(
            "search_similar_vectors",
            {
                "query_embedding": query_vector,
                "match_threshold": 0.5,
                "match_count": 5
            }
        ).execute()
        
        assert similar_vectors.data, "Similarity search failed"

    def test_vector_metadata(self, service_client: Client, test_document: str):
        """Test vector metadata operations."""
        vector_data = {
            "document_id": test_document,
            "chunk_index": 0,
            "chunk_text": "Test chunk for metadata operations",
            "content_embedding": [0.1] * 1536,
            "metadata": {
                "page_number": 1,
                "section": "test_section",
                "custom_field": "test_value"
            }
        }
        
        response = service_client.table("document_vectors").insert(vector_data).execute()
        vector_id = response.data[0]["id"]
        
        # Update metadata
        update_data = {
            "metadata": {
                **vector_data["metadata"],
                "updated_field": "new_value"
            }
        }
        
        update_response = service_client.table("document_vectors").update(update_data).eq("id", vector_id).execute()
        assert update_response.data[0]["metadata"]["updated_field"] == "new_value"

    def test_vector_batch_operations(self, service_client: Client, test_document: str):
        """Test batch vector operations."""
        # Create batch of vectors
        batch_vectors = [
            {
                "document_id": test_document,
                "chunk_index": i,
                "chunk_text": f"Batch test chunk {i}",
                "content_embedding": [0.1] * 1536,
                "metadata": {
                    "page_number": i + 1,
                    "section": f"batch_section_{i}"
                }
            }
            for i in range(5)
        ]
        
        # Insert batch
        response = service_client.table("document_vectors").insert(batch_vectors).execute()
        assert len(response.data) == 5, "Batch insert failed"
        
        # Batch query
        batch_query = service_client.table("document_vectors").select("*").eq("document_id", test_document).execute()
        assert len(batch_query.data) == 5, "Batch query failed"

    def test_vector_deletion(self, service_client: Client, test_document: str):
        """Test vector deletion."""
        vector_data = {
            "document_id": test_document,
            "chunk_index": 0,
            "chunk_text": "Test chunk for deletion",
            "content_embedding": [0.1] * 1536,
            "metadata": {"page_number": 1}
        }
        
        response = service_client.table("document_vectors").insert(vector_data).execute()
        vector_id = response.data[0]["id"]
        
        # Delete vector
        delete_response = service_client.table("document_vectors").delete().eq("id", vector_id).execute()
        assert delete_response.data, "Vector deletion failed"
        
        # Verify deletion
        verify_query = service_client.table("document_vectors").select("*").eq("id", vector_id).execute()
        assert not verify_query.data, "Vector still exists after deletion" 