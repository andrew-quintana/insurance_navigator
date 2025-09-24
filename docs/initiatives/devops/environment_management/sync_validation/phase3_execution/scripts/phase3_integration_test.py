"""
Phase 3: Multi-User Data Integrity - Integration Test

This test validates the complete Phase 3 workflow:
1. User 1 uploads a document
2. User 2 uploads the same document content (different filename)
3. System detects cross-user duplicate and creates document duplication
4. Both users can access their own document entries
5. RAG queries work correctly for both users with proper isolation
"""

import pytest
import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List

# Test configuration
TEST_USER_1 = str(uuid.uuid4())
TEST_USER_2 = str(uuid.uuid4())
TEST_USER_3 = str(uuid.uuid4())

SAMPLE_DOCUMENT_HASH = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
SAMPLE_DOCUMENT_FILENAME_1 = "insurance_policy_user1.pdf"
SAMPLE_DOCUMENT_FILENAME_2 = "insurance_policy_user2.pdf"
SAMPLE_DOCUMENT_FILENAME_3 = "insurance_policy_user3.pdf"

# Sample document content for testing
SAMPLE_DOCUMENT_CONTENT = """
Insurance Policy Document

This is a comprehensive insurance policy that covers:
- Medical expenses
- Prescription drugs
- Emergency services
- Preventive care

Coverage Details:
- Annual deductible: $1,000
- Co-pay: $25 for primary care visits
- Co-pay: $50 for specialist visits
- Prescription coverage: 80% after deductible

This policy is effective from January 1, 2024 to December 31, 2024.
"""

# Sample chunks that would be generated from the document
SAMPLE_CHUNKS = [
    {
        "chunker_name": "semantic",
        "chunker_version": "1.0",
        "chunk_ord": 0,
        "text": "Insurance Policy Document\n\nThis is a comprehensive insurance policy that covers:\n- Medical expenses\n- Prescription drugs\n- Emergency services\n- Preventive care",
        "chunk_sha": "chunk_sha_1",
        "embed_model": "text-embedding-3-small",
        "embed_version": "1",
        "vector_dim": 1536,
        "embedding": [0.1] * 1536
    },
    {
        "chunker_name": "semantic",
        "chunker_version": "1.0",
        "chunk_ord": 1,
        "text": "Coverage Details:\n- Annual deductible: $1,000\n- Co-pay: $25 for primary care visits\n- Co-pay: $50 for specialist visits\n- Prescription coverage: 80% after deductible",
        "chunk_sha": "chunk_sha_2",
        "embed_model": "text-embedding-3-small",
        "embed_version": "1",
        "vector_dim": 1536,
        "embedding": [0.2] * 1536
    },
    {
        "chunker_name": "semantic",
        "chunker_version": "1.0",
        "chunk_ord": 2,
        "text": "This policy is effective from January 1, 2024 to December 31, 2024.",
        "chunk_sha": "chunk_sha_3",
        "embed_model": "text-embedding-3-small",
        "embed_version": "1",
        "vector_dim": 1536,
        "embedding": [0.3] * 1536
    }
]


class TestPhase3Integration:
    """Integration test for Phase 3 document duplication workflow."""
    
    @pytest.fixture
    async def mock_database(self):
        """Create mock database with realistic data."""
        from unittest.mock import AsyncMock
        
        # Mock database connection
        db = AsyncMock()
        
        # Track documents and chunks
        self.documents = {}
        self.chunks = {}
        self.upload_jobs = {}
        
        # Mock database operations
        async def mock_fetchrow(query, *args):
            if "SELECT" in query and "documents" in query:
                if "user_id" in query and "file_sha256" in query:
                    # User-specific document lookup
                    user_id, file_sha256 = args[0], args[1]
                    for doc in self.documents.values():
                        if doc["user_id"] == user_id and doc["file_sha256"] == file_sha256:
                            return doc
                elif "file_sha256" in query:
                    # Cross-user document lookup
                    file_sha256 = args[0]
                    for doc in self.documents.values():
                        if doc["file_sha256"] == file_sha256:
                            return doc
                elif "document_id" in query:
                    # Document by ID lookup
                    doc_id = args[0]
                    return self.documents.get(doc_id)
            return None
        
        async def mock_fetch(query, *args):
            if "document_chunks" in query and "document_id" in query:
                doc_id = args[0]
                return [chunk for chunk in self.chunks.values() if chunk["document_id"] == doc_id]
            return []
        
        async def mock_execute(query, *args):
            if "INSERT INTO upload_pipeline.documents" in query:
                # Extract document data from query
                doc_id = args[0]
                user_id = args[1]
                filename = args[2]
                file_sha256 = args[5]
                
                self.documents[doc_id] = {
                    "document_id": doc_id,
                    "user_id": user_id,
                    "filename": filename,
                    "file_sha256": file_sha256,
                    "mime": args[3],
                    "bytes_len": args[4],
                    "parsed_sha256": args[6],
                    "raw_path": args[7],
                    "parsed_path": args[8],
                    "processing_status": args[9],
                    "created_at": args[10],
                    "updated_at": args[11]
                }
                return "INSERT 0 1"
            
            elif "INSERT INTO upload_pipeline.document_chunks" in query:
                # Extract chunk data from query
                chunk_id = args[0]
                document_id = args[1]
                
                self.chunks[chunk_id] = {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "chunker_name": args[2],
                    "chunker_version": args[3],
                    "chunk_ord": args[4],
                    "text": args[5],
                    "chunk_sha": args[6],
                    "embed_model": args[7],
                    "embed_version": args[8],
                    "vector_dim": args[9],
                    "embedding": args[10],
                    "embed_updated_at": args[11],
                    "created_at": args[12],
                    "updated_at": args[13]
                }
                return "INSERT 0 1"
            
            return "INSERT 0 1"
        
        db.fetchrow = mock_fetchrow
        db.fetch = mock_fetch
        db.execute = mock_execute
        
        return db
    
    async def test_complete_phase3_workflow(self, mock_database):
        """Test the complete Phase 3 workflow with multiple users."""
        from api.upload_pipeline.utils.document_duplication import (
            check_user_has_document,
            find_existing_document_by_content_hash,
            duplicate_document_for_user
        )
        from api.upload_pipeline.utils.upload_pipeline_utils import generate_document_id
        
        # Step 1: User 1 uploads a document
        print("Step 1: User 1 uploads document")
        
        # Check if user 1 already has this document (should be None)
        user1_existing = await check_user_has_document(
            user_id=TEST_USER_1,
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=mock_database
        )
        assert user1_existing is None
        
        # Check if any user has this document (should be None)
        cross_user_existing = await find_existing_document_by_content_hash(
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=mock_database
        )
        assert cross_user_existing is None
        
        # Create document for user 1
        user1_doc_id = generate_document_id(TEST_USER_1, SAMPLE_DOCUMENT_HASH)
        
        # Simulate document creation (normally done by upload pipeline)
        await mock_database.execute(
            "INSERT INTO upload_pipeline.documents (document_id, user_id, filename, mime, bytes_len, file_sha256, parsed_sha256, raw_path, parsed_path, processing_status, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)",
            user1_doc_id, TEST_USER_1, SAMPLE_DOCUMENT_FILENAME_1, "application/pdf", 1024000,
            SAMPLE_DOCUMENT_HASH, "parsed_" + SAMPLE_DOCUMENT_HASH,
            f"raw/user/{TEST_USER_1}/document.pdf", f"parsed/user/{TEST_USER_1}/document.md",
            "embedded", datetime.utcnow(), datetime.utcnow()
        )
        
        # Add chunks for user 1's document
        for i, chunk_data in enumerate(SAMPLE_CHUNKS):
            chunk_id = str(uuid.uuid4())
            await mock_database.execute(
                "INSERT INTO upload_pipeline.document_chunks (chunk_id, document_id, chunker_name, chunker_version, chunk_ord, text, chunk_sha, embed_model, embed_version, vector_dim, embedding, embed_updated_at, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)",
                chunk_id, user1_doc_id, chunk_data["chunker_name"], chunk_data["chunker_version"],
                chunk_data["chunk_ord"], chunk_data["text"], chunk_data["chunk_sha"],
                chunk_data["embed_model"], chunk_data["embed_version"], chunk_data["vector_dim"],
                chunk_data["embedding"], datetime.utcnow(), datetime.utcnow(), datetime.utcnow()
            )
        
        print(f"✅ User 1 document created: {user1_doc_id}")
        
        # Step 2: User 2 uploads the same document content
        print("Step 2: User 2 uploads same document content")
        
        # Check if user 2 already has this document (should be None)
        user2_existing = await check_user_has_document(
            user_id=TEST_USER_2,
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=mock_database
        )
        assert user2_existing is None
        
        # Check if any user has this document (should find user 1's document)
        cross_user_existing = await find_existing_document_by_content_hash(
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=mock_database
        )
        assert cross_user_existing is not None
        assert cross_user_existing["user_id"] == TEST_USER_1
        assert cross_user_existing["document_id"] == user1_doc_id
        
        # Duplicate the document for user 2
        user2_duplicated = await duplicate_document_for_user(
            source_document_id=user1_doc_id,
            target_user_id=TEST_USER_2,
            target_filename=SAMPLE_DOCUMENT_FILENAME_2,
            db_connection=mock_database
        )
        
        assert user2_duplicated is not None
        assert user2_duplicated["filename"] == SAMPLE_DOCUMENT_FILENAME_2
        user2_doc_id = user2_duplicated["document_id"]
        
        print(f"✅ User 2 document duplicated: {user2_doc_id}")
        
        # Step 3: Verify both users have their own document entries
        print("Step 3: Verify user isolation")
        
        # User 1 should see their original document
        user1_doc = await check_user_has_document(
            user_id=TEST_USER_1,
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=mock_database
        )
        assert user1_doc is not None
        assert user1_doc["user_id"] == TEST_USER_1
        assert user1_doc["document_id"] == user1_doc_id
        
        # User 2 should see their duplicated document
        user2_doc = await check_user_has_document(
            user_id=TEST_USER_2,
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=mock_database
        )
        assert user2_doc is not None
        assert user2_doc["user_id"] == TEST_USER_2
        assert user2_doc["document_id"] == user2_doc_id
        
        # Verify different document IDs
        assert user1_doc_id != user2_doc_id
        
        print("✅ User isolation verified")
        
        # Step 4: Verify both documents have the same chunks
        print("Step 4: Verify chunk duplication")
        
        # Get chunks for user 1's document
        user1_chunks = await mock_database.fetch(
            "SELECT * FROM upload_pipeline.document_chunks WHERE document_id = $1",
            user1_doc_id
        )
        
        # Get chunks for user 2's document
        user2_chunks = await mock_database.fetch(
            "SELECT * FROM upload_pipeline.document_chunks WHERE document_id = $1",
            user2_doc_id
        )
        
        # Both should have the same number of chunks
        assert len(user1_chunks) == len(SAMPLE_CHUNKS)
        assert len(user2_chunks) == len(SAMPLE_CHUNKS)
        
        # Chunk content should be identical (but different chunk IDs)
        for i, (chunk1, chunk2) in enumerate(zip(user1_chunks, user2_chunks)):
            assert chunk1["text"] == chunk2["text"]
            assert chunk1["chunk_ord"] == chunk2["chunk_ord"]
            assert chunk1["chunk_id"] != chunk2["chunk_id"]  # Different IDs
            assert chunk1["document_id"] == user1_doc_id
            assert chunk2["document_id"] == user2_doc_id
        
        print("✅ Chunk duplication verified")
        
        # Step 5: Test RAG query isolation
        print("Step 5: Test RAG query isolation")
        
        # Simulate RAG query for user 1
        user1_rag_chunks = await mock_database.fetch(
            """
            SELECT dc.chunk_id, dc.document_id, dc.text, dc.embedding
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $1
            """,
            TEST_USER_1
        )
        
        # Simulate RAG query for user 2
        user2_rag_chunks = await mock_database.fetch(
            """
            SELECT dc.chunk_id, dc.document_id, dc.text, dc.embedding
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $1
            """,
            TEST_USER_2
        )
        
        # Both users should get their own chunks
        assert len(user1_rag_chunks) == len(SAMPLE_CHUNKS)
        assert len(user2_rag_chunks) == len(SAMPLE_CHUNKS)
        
        # Chunk content should be identical
        for chunk1, chunk2 in zip(user1_rag_chunks, user2_rag_chunks):
            assert chunk1["text"] == chunk2["text"]
            assert chunk1["document_id"] == user1_doc_id
            assert chunk2["document_id"] == user2_doc_id
        
        print("✅ RAG query isolation verified")
        
        # Step 6: User 3 uploads the same document content
        print("Step 6: User 3 uploads same document content")
        
        # Check if user 3 already has this document (should be None)
        user3_existing = await check_user_has_document(
            user_id=TEST_USER_3,
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=mock_database
        )
        assert user3_existing is None
        
        # Check if any user has this document (should find user 1's document)
        cross_user_existing = await find_existing_document_by_content_hash(
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=mock_database
        )
        assert cross_user_existing is not None
        
        # Duplicate the document for user 3
        user3_duplicated = await duplicate_document_for_user(
            source_document_id=user1_doc_id,  # Use original document as source
            target_user_id=TEST_USER_3,
            target_filename=SAMPLE_DOCUMENT_FILENAME_3,
            db_connection=mock_database
        )
        
        assert user3_duplicated is not None
        assert user3_duplicated["filename"] == SAMPLE_DOCUMENT_FILENAME_3
        user3_doc_id = user3_duplicated["document_id"]
        
        print(f"✅ User 3 document duplicated: {user3_doc_id}")
        
        # Step 7: Verify all three users have separate document entries
        print("Step 7: Verify all users have separate entries")
        
        # All users should have their own documents
        user1_final = await check_user_has_document(TEST_USER_1, SAMPLE_DOCUMENT_HASH, mock_database)
        user2_final = await check_user_has_document(TEST_USER_2, SAMPLE_DOCUMENT_HASH, mock_database)
        user3_final = await check_user_has_document(TEST_USER_3, SAMPLE_DOCUMENT_HASH, mock_database)
        
        assert user1_final is not None
        assert user2_final is not None
        assert user3_final is not None
        
        # All should have different document IDs
        doc_ids = {user1_final["document_id"], user2_final["document_id"], user3_final["document_id"]}
        assert len(doc_ids) == 3  # All unique
        
        # All should have the same content hash
        assert user1_final["file_sha256"] == SAMPLE_DOCUMENT_HASH
        assert user2_final["file_sha256"] == SAMPLE_DOCUMENT_HASH
        assert user3_final["file_sha256"] == SAMPLE_DOCUMENT_HASH
        
        print("✅ All users have separate document entries")
        
        print("\n🎉 Phase 3 Integration Test PASSED!")
        print("✅ Document duplication system working correctly")
        print("✅ User isolation maintained")
        print("✅ RAG queries work with duplicated documents")
        print("✅ Multiple users can upload same content")


if __name__ == "__main__":
    # Run the integration test
    async def run_test():
        test_instance = TestPhase3Integration()
        await test_instance.test_complete_phase3_workflow(None)
    
    asyncio.run(run_test())

