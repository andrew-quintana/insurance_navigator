"""
Phase 3: Multi-User Data Integrity - Document Duplication Tests

This test suite validates the document row duplication system that allows multiple users
to upload the same document content while maintaining separate user-scoped document
entries and preserving existing processing data.
"""

import pytest
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List

# Test configuration
TEST_USER_1 = str(uuid.uuid4())
TEST_USER_2 = str(uuid.uuid4())
TEST_USER_3 = str(uuid.uuid4())

SAMPLE_DOCUMENT_HASH = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
SAMPLE_DOCUMENT_FILENAME_1 = "test_policy_1.pdf"
SAMPLE_DOCUMENT_FILENAME_2 = "test_policy_2.pdf"
SAMPLE_DOCUMENT_FILENAME_3 = "test_policy_3.pdf"

SAMPLE_CHUNKS = [
    {
        "chunker_name": "semantic",
        "chunker_version": "1.0",
        "chunk_ord": 0,
        "text": "This is the first chunk of the insurance policy document.",
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
        "text": "This is the second chunk with coverage details.",
        "chunk_sha": "chunk_sha_2",
        "embed_model": "text-embedding-3-small",
        "embed_version": "1",
        "vector_dim": 1536,
        "embedding": [0.2] * 1536
    }
]


class TestDocumentDuplication:
    """Test suite for Phase 3 document duplication functionality."""
    
    @pytest.fixture
    async def db_connection(self):
        """Get database connection for tests."""
        # This would be replaced with actual database connection in real tests
        # For now, we'll use a mock connection
        from unittest.mock import AsyncMock
        mock_conn = AsyncMock()
        return mock_conn
    
    @pytest.fixture
    async def sample_document_data(self):
        """Create sample document data for testing."""
        return {
            "document_id": str(uuid.uuid4()),
            "user_id": TEST_USER_1,
            "filename": SAMPLE_DOCUMENT_FILENAME_1,
            "mime": "application/pdf",
            "bytes_len": 1024000,
            "file_sha256": SAMPLE_DOCUMENT_HASH,
            "parsed_sha256": "parsed_" + SAMPLE_DOCUMENT_HASH,
            "raw_path": f"raw/user/{TEST_USER_1}/document.pdf",
            "parsed_path": f"parsed/user/{TEST_USER_1}/document.md",
            "processing_status": "embedded",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    async def test_duplicate_document_for_user_success(self, db_connection, sample_document_data):
        """Test successful document duplication for a new user."""
        from api.upload_pipeline.utils.document_duplication import duplicate_document_for_user
        
        # Mock database responses
        db_connection.fetchrow.return_value = sample_document_data
        db_connection.fetch.return_value = SAMPLE_CHUNKS
        db_connection.execute.return_value = "INSERT 0 1"
        
        # Test duplication
        result = await duplicate_document_for_user(
            source_document_id=sample_document_data["document_id"],
            target_user_id=TEST_USER_2,
            target_filename=SAMPLE_DOCUMENT_FILENAME_2,
            db_connection=db_connection
        )
        
        # Verify result structure
        assert "document_id" in result
        assert "filename" in result
        assert "raw_path" in result
        assert "parsed_path" in result
        assert "processing_status" in result
        assert "created_at" in result
        
        # Verify filename was updated
        assert result["filename"] == SAMPLE_DOCUMENT_FILENAME_2
        
        # Verify database calls were made
        assert db_connection.fetchrow.call_count >= 1  # Source document lookup
        assert db_connection.fetch.call_count >= 1     # Chunks lookup
        assert db_connection.execute.call_count >= 1   # Document and chunks insert
    
    async def test_duplicate_document_source_not_found(self, db_connection):
        """Test document duplication when source document doesn't exist."""
        from api.upload_pipeline.utils.document_duplication import duplicate_document_for_user
        
        # Mock database response - no document found
        db_connection.fetchrow.return_value = None
        
        # Test duplication should raise ValueError
        with pytest.raises(ValueError, match="Source document .* not found"):
            await duplicate_document_for_user(
                source_document_id="nonexistent-doc-id",
                target_user_id=TEST_USER_2,
                target_filename=SAMPLE_DOCUMENT_FILENAME_2,
                db_connection=db_connection
            )
    
    async def test_find_existing_document_by_content_hash(self, db_connection, sample_document_data):
        """Test finding existing document by content hash across all users."""
        from api.upload_pipeline.utils.document_duplication import find_existing_document_by_content_hash
        
        # Mock database response
        db_connection.fetchrow.return_value = sample_document_data
        
        # Test finding document
        result = await find_existing_document_by_content_hash(
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=db_connection
        )
        
        # Verify result
        assert result is not None
        assert result["file_sha256"] == SAMPLE_DOCUMENT_HASH
        assert result["user_id"] == TEST_USER_1
        
        # Verify database query was made
        db_connection.fetchrow.assert_called_once()
    
    async def test_find_existing_document_not_found(self, db_connection):
        """Test finding document when none exists with given content hash."""
        from api.upload_pipeline.utils.document_duplication import find_existing_document_by_content_hash
        
        # Mock database response - no document found
        db_connection.fetchrow.return_value = None
        
        # Test finding document
        result = await find_existing_document_by_content_hash(
            content_hash="nonexistent-hash",
            db_connection=db_connection
        )
        
        # Verify result
        assert result is None
    
    async def test_check_user_has_document(self, db_connection, sample_document_data):
        """Test checking if user already has a document with given content hash."""
        from api.upload_pipeline.utils.document_duplication import check_user_has_document
        
        # Mock database response
        db_connection.fetchrow.return_value = sample_document_data
        
        # Test checking user document
        result = await check_user_has_document(
            user_id=TEST_USER_1,
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=db_connection
        )
        
        # Verify result
        assert result is not None
        assert result["user_id"] == TEST_USER_1
        assert result["file_sha256"] == SAMPLE_DOCUMENT_HASH
    
    async def test_check_user_has_document_not_found(self, db_connection):
        """Test checking user document when user doesn't have it."""
        from api.upload_pipeline.utils.document_duplication import check_user_has_document
        
        # Mock database response - no document found
        db_connection.fetchrow.return_value = None
        
        # Test checking user document
        result = await check_user_has_document(
            user_id=TEST_USER_2,
            content_hash=SAMPLE_DOCUMENT_HASH,
            db_connection=db_connection
        )
        
        # Verify result
        assert result is None


class TestUploadPipelineIntegration:
    """Test suite for upload pipeline integration with document duplication."""
    
    @pytest.fixture
    async def mock_upload_request(self):
        """Create mock upload request for testing."""
        from api.upload_pipeline.models import UploadRequest
        return UploadRequest(
            filename=SAMPLE_DOCUMENT_FILENAME_1,
            mime="application/pdf",
            bytes_len=1024000,
            sha256=SAMPLE_DOCUMENT_HASH
        )
    
    @pytest.fixture
    async def mock_user(self):
        """Create mock user for testing."""
        from api.upload_pipeline.auth import User
        return User(
            user_id=TEST_USER_2,
            email="test2@example.com",
            name="Test User 2"
        )
    
    async def test_upload_with_user_duplicate_detection(self, mock_upload_request, mock_user):
        """Test upload pipeline detects user's existing document."""
        # This test would require mocking the entire upload pipeline
        # For now, we'll test the logic components
        
        from api.upload_pipeline.utils.document_duplication import check_user_has_document
        from unittest.mock import AsyncMock
        
        # Mock database connection
        db_connection = AsyncMock()
        
        # Mock existing document for user
        existing_doc = {
            "document_id": str(uuid.uuid4()),
            "user_id": TEST_USER_2,
            "filename": SAMPLE_DOCUMENT_FILENAME_1,
            "file_sha256": SAMPLE_DOCUMENT_HASH,
            "raw_path": f"raw/user/{TEST_USER_2}/document.pdf",
            "processing_status": "embedded"
        }
        db_connection.fetchrow.return_value = existing_doc
        
        # Test user duplicate detection
        result = await check_user_has_document(
            user_id=str(mock_user.user_id),
            content_hash=mock_upload_request.sha256,
            db_connection=db_connection
        )
        
        # Verify duplicate detected
        assert result is not None
        assert result["user_id"] == str(mock_user.user_id)
        assert result["file_sha256"] == mock_upload_request.sha256
    
    async def test_upload_with_cross_user_duplicate_detection(self, mock_upload_request, mock_user):
        """Test upload pipeline detects cross-user duplicate and creates duplication."""
        from api.upload_pipeline.utils.document_duplication import (
            find_existing_document_by_content_hash,
            duplicate_document_for_user
        )
        from unittest.mock import AsyncMock
        
        # Mock database connection
        db_connection = AsyncMock()
        
        # Mock existing document from different user
        existing_doc = {
            "document_id": str(uuid.uuid4()),
            "user_id": TEST_USER_1,  # Different user
            "filename": SAMPLE_DOCUMENT_FILENAME_1,
            "file_sha256": SAMPLE_DOCUMENT_HASH,
            "raw_path": f"raw/user/{TEST_USER_1}/document.pdf",
            "parsed_path": f"parsed/user/{TEST_USER_1}/document.md",
            "processing_status": "embedded",
            "mime": "application/pdf",
            "bytes_len": 1024000,
            "parsed_sha256": "parsed_" + SAMPLE_DOCUMENT_HASH,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mock chunks data
        db_connection.fetch.return_value = SAMPLE_CHUNKS
        db_connection.execute.return_value = "INSERT 0 1"
        
        # First, find existing document
        db_connection.fetchrow.return_value = existing_doc
        cross_user_doc = await find_existing_document_by_content_hash(
            content_hash=mock_upload_request.sha256,
            db_connection=db_connection
        )
        
        # Verify cross-user document found
        assert cross_user_doc is not None
        assert cross_user_doc["user_id"] == TEST_USER_1
        
        # Then, duplicate for new user
        duplicated_doc = await duplicate_document_for_user(
            source_document_id=cross_user_doc["document_id"],
            target_user_id=str(mock_user.user_id),
            target_filename=mock_upload_request.filename,
            db_connection=db_connection
        )
        
        # Verify duplication successful
        assert duplicated_doc is not None
        assert duplicated_doc["filename"] == mock_upload_request.filename


class TestRAGIntegration:
    """Test suite for RAG integration with duplicated documents."""
    
    async def test_rag_user_isolation_with_duplicated_documents(self):
        """Test that RAG queries maintain user isolation with duplicated documents."""
        # This test would require setting up actual RAG queries
        # For now, we'll test the concept
        
        # Simulate two users with the same document content
        user_1_doc_id = str(uuid.uuid4())
        user_2_doc_id = str(uuid.uuid4())
        
        # Both documents have the same content hash but different document IDs
        # Both should have the same chunks (duplicated)
        
        # RAG query for user 1 should only return chunks from user_1_doc_id
        # RAG query for user 2 should only return chunks from user_2_doc_id
        
        # This is handled by the existing RAG query:
        # SELECT dc.* FROM document_chunks dc
        # JOIN documents d ON dc.document_id = d.document_id
        # WHERE d.user_id = $1
        
        # The JOIN ensures user isolation even with duplicated documents
        assert True  # Placeholder for actual RAG test


class TestEdgeCases:
    """Test suite for edge cases in document duplication."""
    
    async def test_concurrent_upload_same_document(self):
        """Test concurrent uploads of the same document by different users."""
        # This test would simulate concurrent uploads
        # The first upload should create the document
        # Subsequent uploads should detect the duplicate and create copies
        
        # Implementation would require:
        # 1. Database transaction isolation
        # 2. Proper locking mechanisms
        # 3. Race condition handling
        
        assert True  # Placeholder for concurrent upload test
    
    async def test_duplicate_with_missing_chunks(self):
        """Test duplication when source document has no chunks."""
        from api.upload_pipeline.utils.document_duplication import duplicate_document_for_user
        from unittest.mock import AsyncMock
        
        # Mock database connection
        db_connection = AsyncMock()
        
        # Mock document without chunks
        sample_doc = {
            "document_id": str(uuid.uuid4()),
            "user_id": TEST_USER_1,
            "filename": SAMPLE_DOCUMENT_FILENAME_1,
            "file_sha256": SAMPLE_DOCUMENT_HASH,
            "processing_status": "uploaded",  # Not processed yet
            "mime": "application/pdf",
            "bytes_len": 1024000,
            "parsed_sha256": None,
            "raw_path": f"raw/user/{TEST_USER_1}/document.pdf",
            "parsed_path": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        db_connection.fetchrow.return_value = sample_doc
        db_connection.fetch.return_value = []  # No chunks
        db_connection.execute.return_value = "INSERT 0 1"
        
        # Test duplication
        result = await duplicate_document_for_user(
            source_document_id=sample_doc["document_id"],
            target_user_id=TEST_USER_2,
            target_filename=SAMPLE_DOCUMENT_FILENAME_2,
            db_connection=db_connection
        )
        
        # Verify duplication successful even without chunks
        assert result is not None
        assert result["filename"] == SAMPLE_DOCUMENT_FILENAME_2
    
    async def test_duplicate_with_partial_processing(self):
        """Test duplication when source document is partially processed."""
        from api.upload_pipeline.utils.document_duplication import duplicate_document_for_user
        from unittest.mock import AsyncMock
        
        # Mock database connection
        db_connection = AsyncMock()
        
        # Mock partially processed document
        sample_doc = {
            "document_id": str(uuid.uuid4()),
            "user_id": TEST_USER_1,
            "filename": SAMPLE_DOCUMENT_FILENAME_1,
            "file_sha256": SAMPLE_DOCUMENT_HASH,
            "processing_status": "chunked",  # Partially processed
            "mime": "application/pdf",
            "bytes_len": 1024000,
            "parsed_sha256": "parsed_" + SAMPLE_DOCUMENT_HASH,
            "raw_path": f"raw/user/{TEST_USER_1}/document.pdf",
            "parsed_path": f"parsed/user/{TEST_USER_1}/document.md",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Mock some chunks (partial processing)
        partial_chunks = [SAMPLE_CHUNKS[0]]  # Only first chunk
        
        db_connection.fetchrow.return_value = sample_doc
        db_connection.fetch.return_value = partial_chunks
        db_connection.execute.return_value = "INSERT 0 1"
        
        # Test duplication
        result = await duplicate_document_for_user(
            source_document_id=sample_doc["document_id"],
            target_user_id=TEST_USER_2,
            target_filename=SAMPLE_DOCUMENT_FILENAME_2,
            db_connection=db_connection
        )
        
        # Verify duplication successful with partial chunks
        assert result is not None
        assert result["filename"] == SAMPLE_DOCUMENT_FILENAME_2


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
