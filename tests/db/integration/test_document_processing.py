import pytest
import uuid
from datetime import datetime
from typing import Dict, List

from supabase.client import Client
from tests.db.helpers import get_test_client
from tests.config.test_config import get_test_config

class TestDocumentProcessing:
    @pytest.fixture(scope="class")
    def supabase(self) -> Client:
        return get_test_client()
    
    @pytest.fixture(scope="class")
    def config(self):
        return get_test_config()

    @pytest.fixture(scope="class")
    def test_user_id(self) -> str:
        """Create a test user ID that will be used across all tests."""
        return str(uuid.uuid4())

    def test_document_creation(self, supabase: Client, test_user_id: str):
        """Test creating a document in the unified schema."""
        doc_data = {
            "user_id": test_user_id,
            "original_filename": "test_document.pdf",
            "document_type": "user_uploaded",
            "content_type": "application/pdf",
            "storage_path": f"documents/{uuid.uuid4()}/test_document.pdf",
            "metadata": {
                "jurisdiction": "federal",
                "program": "medicare",
                "document_date": datetime.now().isoformat(),
                "tags": ["test", "integration"]
            },
            "status": "pending"
        }
        
        response = supabase.table("documents").insert(doc_data).execute()
        assert response.data, "Document creation failed"
        assert response.data[0]["id"], "No document ID returned"
        assert response.data[0]["document_type"] == "user_uploaded"
        
        # Clean up
        supabase.table("documents").delete().eq("id", response.data[0]["id"]).execute()

    def test_document_vector_processing(self, supabase: Client, test_user_id: str):
        """Test vector processing for a document."""
        # Create test document
        doc_data = {
            "user_id": test_user_id,
            "original_filename": "vector_test.pdf",
            "document_type": "regulatory",
            "content_type": "application/pdf",
            "storage_path": f"documents/{uuid.uuid4()}/vector_test.pdf",
            "metadata": {
                "jurisdiction": "state",
                "state": "CA",
                "program": "medicaid",
                "document_date": datetime.now().isoformat()
            },
            "status": "pending"
        }
        
        doc_response = supabase.table("documents").insert(doc_data).execute()
        doc_id = doc_response.data[0]["id"]
        
        # Create test vector
        vector_data = {
            "document_id": doc_id,
            "chunk_index": 0,
            "chunk_text": "This is a test chunk for vector processing",
            "content_embedding": [0.1] * 1536,  # Example embedding
            "metadata": {
                "page_number": 1,
                "section": "introduction"
            }
        }
        
        vector_response = supabase.table("document_vectors").insert(vector_data).execute()
        assert vector_response.data, "Vector creation failed"
        assert vector_response.data[0]["document_id"] == doc_id
        
        # Clean up
        supabase.table("document_vectors").delete().eq("document_id", doc_id).execute()
        supabase.table("documents").delete().eq("id", doc_id).execute()

    def test_document_search(self, supabase: Client, test_user_id: str):
        """Test document search functionality."""
        # Create test documents with different jurisdictions
        docs = [
            {
                "user_id": test_user_id,
                "original_filename": f"test_doc_{i}.pdf",
                "document_type": "regulatory",
                "content_type": "application/pdf",
                "storage_path": f"documents/{uuid.uuid4()}/test_doc_{i}.pdf",
                "metadata": {
                    "jurisdiction": jur,
                    "program": prog,
                    "document_date": datetime.now().isoformat()
                },
                "status": "active"
            }
            for i, (jur, prog) in enumerate([
                ("federal", "medicare"),
                ("state", "medicaid"),
                ("county", "dual_eligible")
            ])
        ]
        
        doc_ids = []
        for doc in docs:
            response = supabase.table("documents").insert(doc).execute()
            doc_ids.append(response.data[0]["id"])
        
        # Test search by jurisdiction
        fed_docs = supabase.table("documents").select("*").eq("metadata->jurisdiction", "federal").execute()
        assert len(fed_docs.data) == 1, "Federal document search failed"
        
        # Test search by program
        medicaid_docs = supabase.table("documents").select("*").eq("metadata->program", "medicaid").execute()
        assert len(medicaid_docs.data) == 1, "Medicaid document search failed"
        
        # Clean up
        for doc_id in doc_ids:
            supabase.table("documents").delete().eq("id", doc_id).execute()

    def test_document_metadata(self, supabase: Client, test_user_id: str):
        """Test document metadata handling."""
        doc_data = {
            "user_id": test_user_id,
            "original_filename": "metadata_test.pdf",
            "document_type": "user_uploaded",
            "content_type": "application/pdf",
            "storage_path": f"documents/{uuid.uuid4()}/metadata_test.pdf",
            "metadata": {
                "jurisdiction": "federal",
                "program": "medicare",
                "document_date": datetime.now().isoformat(),
                "tags": ["test", "metadata"],
                "custom_field": "test_value"
            },
            "status": "active"
        }
        
        response = supabase.table("documents").insert(doc_data).execute()
        doc_id = response.data[0]["id"]
        
        # Update metadata
        update_data = {
            "metadata": {
                **doc_data["metadata"],
                "updated_field": "new_value"
            }
        }
        
        update_response = supabase.table("documents").update(update_data).eq("id", doc_id).execute()
        assert update_response.data[0]["metadata"]["updated_field"] == "new_value"
        
        # Clean up
        supabase.table("documents").delete().eq("id", doc_id).execute()

    def test_document_status_transitions(self, supabase: Client, test_user_id: str):
        """Test document status transitions."""
        doc_data = {
            "user_id": test_user_id,
            "original_filename": "status_test.pdf",
            "document_type": "regulatory",
            "content_type": "application/pdf",
            "storage_path": f"documents/{uuid.uuid4()}/status_test.pdf",
            "metadata": {
                "jurisdiction": "federal",
                "program": "medicare"
            },
            "status": "pending"
        }
        
        response = supabase.table("documents").insert(doc_data).execute()
        doc_id = response.data[0]["id"]
        
        # Test status transitions
        statuses = ["processing", "processed", "active"]
        for status in statuses:
            update_response = supabase.table("documents").update({"status": status}).eq("id", doc_id).execute()
            assert update_response.data[0]["status"] == status
        
        # Clean up
        supabase.table("documents").delete().eq("id", doc_id).execute() 