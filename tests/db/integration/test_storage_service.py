"""Integration tests for storage service with actual Supabase interactions."""
import pytest
import os
from uuid import uuid4
from datetime import datetime
import asyncio
from typing import AsyncGenerator, Dict, Any

from db.services.storage_service import StorageService
from db.config import config

# Integration test markers
pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio
]

@pytest.fixture
async def supabase_config():
    """Get Supabase configuration."""
    return config.supabase

@pytest.fixture
async def storage_service(supabase_config) -> StorageService:
    """Create a real storage service instance."""
    # Note: Using actual DB session in integration tests
    from db.database import get_db_session
    db_session = await get_db_session()
    service = StorageService(db_session)
    return service

@pytest.fixture
async def test_policy_id():
    """Create a unique policy ID for testing."""
    return uuid4()

@pytest.fixture
async def test_document_content():
    """Create test document content."""
    return b"Test document content for integration testing"

@pytest.fixture
async def uploaded_document(
    storage_service,
    test_policy_id,
    test_document_content
) -> AsyncGenerator[Dict[str, Any], None]:
    """Fixture to create and clean up a test document."""
    filename = f"test_doc_{test_policy_id}.pdf"
    metadata = {
        'document_type': 'test',
        'version': '1.0',
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Upload test document
    result = await storage_service.upload_policy_document(
        test_policy_id,
        test_document_content,
        filename,
        metadata
    )
    
    yield result
    
    # Cleanup after test
    try:
        await storage_service.delete_document(result['path'])
    except Exception as e:
        pytest.fail(f"Failed to cleanup test document: {e}")

class TestStorageServiceIntegration:
    """Integration tests for storage service."""

    async def test_document_upload_and_retrieval(
        self,
        storage_service,
        test_policy_id,
        test_document_content
    ):
        """Test complete document upload and retrieval flow."""
        # Upload document
        filename = f"test_doc_{test_policy_id}.pdf"
        upload_result = await storage_service.upload_policy_document(
            test_policy_id,
            test_document_content,
            filename
        )
        
        assert upload_result['path'].endswith(filename)
        
        # Get signed URL
        signed_url = await storage_service.get_signed_url(upload_result['path'])
        assert signed_url.startswith('https://')
        
        # List documents
        documents = await storage_service.list_policy_documents(test_policy_id)
        assert any(doc['path'] == upload_result['path'] for doc in documents)
        
        # Cleanup
        await storage_service.delete_document(upload_result['path'])

    async def test_document_metadata_operations(
        self,
        storage_service,
        uploaded_document
    ):
        """Test document metadata operations."""
        # Get metadata
        metadata = await storage_service.get_document_metadata(
            uploaded_document['path']
        )
        
        assert metadata['document_type'] == 'test'
        assert metadata['version'] == '1.0'
        assert 'created_at' in metadata

    async def test_document_move_operation(
        self,
        storage_service,
        uploaded_document,
        test_policy_id
    ):
        """Test moving a document between directories."""
        new_path = uploaded_document['path'].replace('raw', 'processed')
        
        # Move document
        move_result = await storage_service.move_document(
            uploaded_document['path'],
            new_path
        )
        assert move_result is True
        
        # Verify document in new location
        documents = await storage_service.list_policy_documents(test_policy_id)
        assert any(doc['path'] == new_path for doc in documents)

    async def test_concurrent_operations(
        self,
        storage_service,
        test_policy_id,
        test_document_content
    ):
        """Test concurrent document operations."""
        async def upload_and_process(index: int):
            filename = f"concurrent_doc_{index}.pdf"
            result = await storage_service.upload_policy_document(
                test_policy_id,
                test_document_content,
                filename
            )
            return result['path']
        
        # Upload multiple documents concurrently
        paths = await asyncio.gather(*[
            upload_and_process(i) for i in range(3)
        ])
        
        try:
            # List all documents
            documents = await storage_service.list_policy_documents(test_policy_id)
            assert len(documents) >= len(paths)
            
            # Clean up
            await asyncio.gather(*[
                storage_service.delete_document(path) for path in paths
            ])
        except Exception as e:
            pytest.fail(f"Concurrent operations failed: {e}")

    async def test_error_handling(
        self,
        storage_service,
        test_policy_id
    ):
        """Test error handling in storage operations."""
        # Test non-existent document
        with pytest.raises(ValueError):
            await storage_service.get_document_metadata(
                f"policies/{test_policy_id}/nonexistent.pdf"
            )
        
        # Test invalid move operation
        with pytest.raises(Exception):
            await storage_service.move_document(
                f"policies/{test_policy_id}/nonexistent.pdf",
                f"policies/{test_policy_id}/processed/nonexistent.pdf"
            )

    @pytest.mark.timeout(10)
    async def test_large_document_handling(
        self,
        storage_service,
        test_policy_id
    ):
        """Test handling of larger documents."""
        # Create a 5MB test document
        large_content = os.urandom(5 * 1024 * 1024)  # 5MB of random data
        filename = f"large_doc_{test_policy_id}.pdf"
        
        try:
            # Upload large document
            result = await storage_service.upload_policy_document(
                test_policy_id,
                large_content,
                filename
            )
            
            # Verify upload
            metadata = await storage_service.get_document_metadata(result['path'])
            assert metadata['size'] == len(large_content)
            
            # Clean up
            await storage_service.delete_document(result['path'])
        except Exception as e:
            pytest.fail(f"Large document handling failed: {e}")

    async def test_rate_limiting(
        self,
        storage_service,
        test_policy_id,
        test_document_content
    ):
        """Test handling of rate limiting."""
        # Attempt rapid sequential uploads
        for i in range(10):
            filename = f"rate_test_{i}.pdf"
            try:
                result = await storage_service.upload_policy_document(
                    test_policy_id,
                    test_document_content,
                    filename
                )
                # Add small delay to avoid rate limits
                await asyncio.sleep(0.1)
                # Clean up
                await storage_service.delete_document(result['path'])
            except Exception as e:
                if 'rate limit' in str(e).lower():
                    pytest.skip("Rate limit reached as expected")
                else:
                    pytest.fail(f"Unexpected error: {e}") 