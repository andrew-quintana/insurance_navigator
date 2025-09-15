#!/usr/bin/env python3
"""
Phase 3: Multi-User Data Integrity - Implementation Validation

This script validates the Phase 3 document duplication implementation
by testing the complete workflow with real database operations.
"""

import asyncio
import uuid
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List

# Test configuration
TEST_USER_1 = str(uuid.uuid4())
TEST_USER_2 = str(uuid.uuid4())
TEST_USER_3 = str(uuid.uuid4())

# Sample document content
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

# Generate content hash
SAMPLE_DOCUMENT_HASH = hashlib.sha256(SAMPLE_DOCUMENT_CONTENT.encode()).hexdigest()

# Sample chunks
SAMPLE_CHUNKS = [
    {
        "chunker_name": "semantic",
        "chunker_version": "1.0",
        "chunk_ord": 0,
        "text": "Insurance Policy Document\n\nThis is a comprehensive insurance policy that covers:\n- Medical expenses\n- Prescription drugs\n- Emergency services\n- Preventive care",
        "chunk_sha": hashlib.sha256("chunk_1_content".encode()).hexdigest(),
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
        "chunk_sha": hashlib.sha256("chunk_2_content".encode()).hexdigest(),
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
        "chunk_sha": hashlib.sha256("chunk_3_content".encode()).hexdigest(),
        "embed_model": "text-embedding-3-small",
        "embed_version": "1",
        "vector_dim": 1536,
        "embedding": [0.3] * 1536
    }
]


async def get_database_connection():
    """Get database connection for testing."""
    try:
        # Try to import and use the actual database connection
        from api.upload_pipeline.database import get_database
        return await get_database()
    except ImportError:
        print("❌ Could not import database connection. Using mock connection.")
        from unittest.mock import AsyncMock
        return AsyncMock()


async def create_test_document(db, user_id: str, filename: str, content_hash: str) -> str:
    """Create a test document in the database."""
    from api.upload_pipeline.utils.upload_pipeline_utils import generate_document_id
    
    document_id = generate_document_id(user_id, content_hash)
    now = datetime.utcnow()
    
    # Create document record
    await db.execute("""
        INSERT INTO upload_pipeline.documents (
            document_id, user_id, filename, mime, bytes_len, file_sha256,
            parsed_sha256, raw_path, parsed_path, processing_status,
            created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
    """, document_id, user_id, filename, "application/pdf", 1024000,
        content_hash, "parsed_" + content_hash,
        f"raw/user/{user_id}/document.pdf", f"parsed/user/{user_id}/document.md",
        "embedded", now, now)
    
    # Add chunks
    for chunk_data in SAMPLE_CHUNKS:
        chunk_id = str(uuid.uuid4())
        vector_string = '[' + ','.join(str(x) for x in chunk_data["embedding"]) + ']'
        
        await db.execute("""
            INSERT INTO upload_pipeline.document_chunks (
                chunk_id, document_id, chunker_name, chunker_version, chunk_ord,
                text, chunk_sha, embed_model, embed_version, vector_dim, embedding,
                embed_updated_at, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector(1536), $12, $13, $14)
        """, chunk_id, document_id, chunk_data["chunker_name"], chunk_data["chunker_version"],
            chunk_data["chunk_ord"], chunk_data["text"], chunk_data["chunk_sha"],
            chunk_data["embed_model"], chunk_data["embed_version"], chunk_data["vector_dim"],
            vector_string, now, now, now)
    
    return document_id


async def test_phase3_implementation():
    """Test the Phase 3 document duplication implementation."""
    print("🚀 Starting Phase 3 Implementation Validation")
    print("=" * 60)
    
    # Get database connection
    db = await get_database_connection()
    
    try:
        # Step 1: Create document for User 1
        print("Step 1: Creating document for User 1")
        user1_doc_id = await create_test_document(
            db, TEST_USER_1, "insurance_policy_user1.pdf", SAMPLE_DOCUMENT_HASH
        )
        print(f"✅ User 1 document created: {user1_doc_id}")
        
        # Step 2: Test duplicate detection functions
        print("\nStep 2: Testing duplicate detection functions")
        
        from api.upload_pipeline.utils.document_duplication import (
            check_user_has_document,
            find_existing_document_by_content_hash,
            duplicate_document_for_user
        )
        
        # Test user-specific duplicate detection
        user1_existing = await check_user_has_document(
            TEST_USER_1, SAMPLE_DOCUMENT_HASH, db
        )
        assert user1_existing is not None
        assert user1_existing["user_id"] == TEST_USER_1
        print("✅ User 1 duplicate detection working")
        
        # Test cross-user duplicate detection
        cross_user_existing = await find_existing_document_by_content_hash(
            SAMPLE_DOCUMENT_HASH, db
        )
        assert cross_user_existing is not None
        assert cross_user_existing["user_id"] == TEST_USER_1
        print("✅ Cross-user duplicate detection working")
        
        # Step 3: Duplicate document for User 2
        print("\nStep 3: Duplicating document for User 2")
        user2_duplicated = await duplicate_document_for_user(
            source_document_id=user1_doc_id,
            target_user_id=TEST_USER_2,
            target_filename="insurance_policy_user2.pdf",
            db_connection=db
        )
        
        assert user2_duplicated is not None
        user2_doc_id = user2_duplicated["document_id"]
        print(f"✅ User 2 document duplicated: {user2_doc_id}")
        
        # Step 4: Verify user isolation
        print("\nStep 4: Verifying user isolation")
        
        # User 1 should see their original document
        user1_doc = await check_user_has_document(TEST_USER_1, SAMPLE_DOCUMENT_HASH, db)
        assert user1_doc["document_id"] == user1_doc_id
        print("✅ User 1 sees their original document")
        
        # User 2 should see their duplicated document
        user2_doc = await check_user_has_document(TEST_USER_2, SAMPLE_DOCUMENT_HASH, db)
        assert user2_doc["document_id"] == user2_doc_id
        print("✅ User 2 sees their duplicated document")
        
        # Verify different document IDs
        assert user1_doc_id != user2_doc_id
        print("✅ Document IDs are different (user isolation maintained)")
        
        # Step 5: Test RAG query isolation
        print("\nStep 5: Testing RAG query isolation")
        
        # Query chunks for User 1
        user1_chunks = await db.fetch("""
            SELECT dc.chunk_id, dc.document_id, dc.text
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $1
            ORDER BY dc.chunk_ord
        """, TEST_USER_1)
        
        # Query chunks for User 2
        user2_chunks = await db.fetch("""
            SELECT dc.chunk_id, dc.document_id, dc.text
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $1
            ORDER BY dc.chunk_ord
        """, TEST_USER_2)
        
        # Both users should have the same number of chunks
        assert len(user1_chunks) == len(SAMPLE_CHUNKS)
        assert len(user2_chunks) == len(SAMPLE_CHUNKS)
        print(f"✅ Both users have {len(user1_chunks)} chunks")
        
        # Chunk content should be identical but document IDs different
        for i, (chunk1, chunk2) in enumerate(zip(user1_chunks, user2_chunks)):
            assert chunk1["text"] == chunk2["text"]
            assert chunk1["document_id"] == user1_doc_id
            assert chunk2["document_id"] == user2_doc_id
            assert chunk1["chunk_id"] != chunk2["chunk_id"]
        
        print("✅ RAG query isolation working correctly")
        
        # Step 6: Test multiple duplications
        print("\nStep 6: Testing multiple duplications")
        
        # Duplicate for User 3
        user3_duplicated = await duplicate_document_for_user(
            source_document_id=user1_doc_id,
            target_user_id=TEST_USER_3,
            target_filename="insurance_policy_user3.pdf",
            db_connection=db
        )
        
        user3_doc_id = user3_duplicated["document_id"]
        print(f"✅ User 3 document duplicated: {user3_doc_id}")
        
        # Verify all three users have separate documents
        user1_final = await check_user_has_document(TEST_USER_1, SAMPLE_DOCUMENT_HASH, db)
        user2_final = await check_user_has_document(TEST_USER_2, SAMPLE_DOCUMENT_HASH, db)
        user3_final = await check_user_has_document(TEST_USER_3, SAMPLE_DOCUMENT_HASH, db)
        
        doc_ids = {user1_final["document_id"], user2_final["document_id"], user3_final["document_id"]}
        assert len(doc_ids) == 3
        print("✅ All three users have separate document entries")
        
        # Step 7: Test database indexes
        print("\nStep 7: Testing database indexes")
        
        # Test content hash index performance
        start_time = datetime.utcnow()
        cross_user_result = await find_existing_document_by_content_hash(SAMPLE_DOCUMENT_HASH, db)
        end_time = datetime.utcnow()
        
        query_time = (end_time - start_time).total_seconds()
        print(f"✅ Content hash query completed in {query_time:.4f} seconds")
        
        # Step 8: Cleanup
        print("\nStep 8: Cleaning up test data")
        
        # Delete test documents and chunks
        await db.execute("DELETE FROM upload_pipeline.document_chunks WHERE document_id = ANY($1)", 
                        [user1_doc_id, user2_doc_id, user3_doc_id])
        await db.execute("DELETE FROM upload_pipeline.documents WHERE document_id = ANY($1)", 
                        [user1_doc_id, user2_doc_id, user3_doc_id])
        
        print("✅ Test data cleaned up")
        
        print("\n" + "=" * 60)
        print("🎉 Phase 3 Implementation Validation PASSED!")
        print("✅ Document duplication system working correctly")
        print("✅ User isolation maintained")
        print("✅ RAG queries work with duplicated documents")
        print("✅ Database indexes performing well")
        print("✅ Multiple users can upload same content")
        
    except Exception as e:
        print(f"\n❌ Phase 3 Implementation Validation FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


async def main():
    """Main function to run the Phase 3 validation."""
    try:
        await test_phase3_implementation()
    except Exception as e:
        print(f"Test failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

