import pytest
import uuid
from datetime import datetime
from typing import Dict, List

from supabase.client import Client
from tests.db.helpers import get_test_client
from tests.config.test_config import get_base_test_config

class TestDocumentMetadata:
    @pytest.fixture(scope="class")
    def supabase(self) -> Client:
        return get_test_client()
    
    @pytest.fixture(scope="class")
    def config(self):
        return get_base_test_config()
    
    @pytest.fixture(scope="function")
    def test_documents(self, supabase: Client) -> List[str]:
        """Create test documents with different metadata and clean them up after the test."""
        docs = [
            {
                "original_filename": f"metadata_test_{i}.pdf",
                "document_type": "regulatory",
                "content_type": "application/pdf",
                "storage_path": f"documents/{uuid.uuid4()}/metadata_test_{i}.pdf",
                "metadata": {
                    "jurisdiction": jur,
                    "program": prog,
                    "document_date": datetime.now().isoformat(),
                    "tags": tags
                },
                "status": "active"
            }
            for i, (jur, prog, tags) in enumerate([
                ("federal", "medicare", ["policy", "coverage"]),
                ("state", "medicaid", ["eligibility", "benefits"]),
                ("county", "dual_eligible", ["coordination", "enrollment"])
            ])
        ]
        
        doc_ids = []
        for doc in docs:
            response = supabase.table("documents").insert(doc).execute()
            doc_ids.append(response.data[0]["id"])
        
        yield doc_ids
        
        # Clean up
        for doc_id in doc_ids:
            supabase.table("documents").delete().eq("id", doc_id).execute()

    def test_metadata_crud(self, supabase: Client, test_documents: List[str]):
        """Test CRUD operations on document metadata."""
        doc_id = test_documents[0]
        
        # Read initial metadata
        doc = supabase.table("documents").select("*").eq("id", doc_id).single().execute()
        initial_metadata = doc.data["metadata"]
        assert initial_metadata["jurisdiction"] == "federal"
        
        # Update metadata
        updated_metadata = {
            **initial_metadata,
            "last_reviewed": datetime.now().isoformat(),
            "reviewer": "test_user"
        }
        
        update_response = supabase.table("documents").update({"metadata": updated_metadata}).eq("id", doc_id).execute()
        assert update_response.data[0]["metadata"]["reviewer"] == "test_user"
        
        # Patch metadata (partial update)
        patch_data = {
            "metadata": {
                **updated_metadata,
                "status_note": "Metadata updated successfully"
            }
        }
        
        patch_response = supabase.table("documents").update(patch_data).eq("id", doc_id).execute()
        assert patch_response.data[0]["metadata"]["status_note"] == "Metadata updated successfully"

    def test_jurisdiction_hierarchy(self, supabase: Client, test_documents: List[str]):
        """Test jurisdiction-based document relationships."""
        # Query federal documents
        federal_docs = supabase.table("documents").select("*").eq("metadata->jurisdiction", "federal").execute()
        assert len(federal_docs.data) == 1
        
        # Query state documents
        state_docs = supabase.table("documents").select("*").eq("metadata->jurisdiction", "state").execute()
        assert len(state_docs.data) == 1
        
        # Query county documents
        county_docs = supabase.table("documents").select("*").eq("metadata->jurisdiction", "county").execute()
        assert len(county_docs.data) == 1

    def test_program_relationships(self, supabase: Client, test_documents: List[str]):
        """Test program-based document relationships."""
        # Query Medicare documents
        medicare_docs = supabase.table("documents").select("*").eq("metadata->program", "medicare").execute()
        assert len(medicare_docs.data) == 1
        
        # Query Medicaid documents
        medicaid_docs = supabase.table("documents").select("*").eq("metadata->program", "medicaid").execute()
        assert len(medicaid_docs.data) == 1
        
        # Query dual-eligible documents
        dual_docs = supabase.table("documents").select("*").eq("metadata->program", "dual_eligible").execute()
        assert len(dual_docs.data) == 1

    def test_tag_operations(self, supabase: Client, test_documents: List[str]):
        """Test document tag operations."""
        doc_id = test_documents[0]
        
        # Read initial tags
        doc = supabase.table("documents").select("*").eq("id", doc_id).single().execute()
        initial_tags = doc.data["metadata"]["tags"]
        assert "policy" in initial_tags
        
        # Add new tag
        updated_tags = [*initial_tags, "new_tag"]
        update_response = supabase.table("documents").update({
            "metadata": {
                **doc.data["metadata"],
                "tags": updated_tags
            }
        }).eq("id", doc_id).execute()
        
        assert "new_tag" in update_response.data[0]["metadata"]["tags"]
        
        # Remove tag
        updated_tags.remove("new_tag")
        remove_response = supabase.table("documents").update({
            "metadata": {
                **doc.data["metadata"],
                "tags": updated_tags
            }
        }).eq("id", doc_id).execute()
        
        assert "new_tag" not in remove_response.data[0]["metadata"]["tags"]

    def test_document_linking(self, supabase: Client, test_documents: List[str]):
        """Test document linking functionality."""
        doc_id = test_documents[0]
        related_doc_id = test_documents[1]
        
        # Create document link
        link_data = {
            "metadata": {
                "linked_documents": [
                    {
                        "document_id": str(related_doc_id),
                        "relationship_type": "references",
                        "link_date": datetime.now().isoformat()
                    }
                ]
            }
        }
        
        link_response = supabase.table("documents").update(link_data).eq("id", doc_id).execute()
        assert len(link_response.data[0]["metadata"]["linked_documents"]) == 1
        
        # Query linked documents
        linked_doc = supabase.table("documents").select("*").eq("id", related_doc_id).single().execute()
        assert linked_doc.data["id"] == related_doc_id

    def test_metadata_validation(self, supabase: Client):
        """Test metadata validation rules."""
        # Test invalid jurisdiction
        with pytest.raises(Exception):
            doc_data = {
                "original_filename": "invalid_jurisdiction.pdf",
                "document_type": "regulatory",
                "content_type": "application/pdf",
                "storage_path": f"documents/{uuid.uuid4()}/invalid_jurisdiction.pdf",
                "metadata": {
                    "jurisdiction": "invalid",  # Should fail
                    "program": "medicare"
                },
                "status": "active"
            }
            supabase.table("documents").insert(doc_data).execute()
        
        # Test invalid program
        with pytest.raises(Exception):
            doc_data = {
                "original_filename": "invalid_program.pdf",
                "document_type": "regulatory",
                "content_type": "application/pdf",
                "storage_path": f"documents/{uuid.uuid4()}/invalid_program.pdf",
                "metadata": {
                    "jurisdiction": "federal",
                    "program": "invalid"  # Should fail
                },
                "status": "active"
            }
            supabase.table("documents").insert(doc_data).execute() 