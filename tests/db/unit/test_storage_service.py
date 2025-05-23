"""Unit tests for the storage service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime
from db.services.storage_service import StorageService

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    
    # Mock collections
    session.policy_documents = AsyncMock()
    session.policy_documents.insert_one = AsyncMock()
    session.policy_documents.find = AsyncMock()
    session.policy_documents.find_one = AsyncMock()
    session.policy_documents.delete_one = AsyncMock()
    session.policy_documents.update_one = AsyncMock()
    
    return session

@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    client = MagicMock()
    storage = MagicMock()
    storage.from_.return_value.upload = AsyncMock()
    storage.from_.return_value.download = AsyncMock()
    client.storage = storage
    return client

@pytest.fixture
def storage_service(mock_db_session, mock_supabase):
    """Create a storage service instance with mocked dependencies."""
    with patch('db.services.storage_service.create_client', return_value=mock_supabase):
        service = StorageService(mock_db_session)
        return service

@pytest.fixture
def sample_policy_id():
    """Create a sample policy ID."""
    return uuid.uuid4()

@pytest.fixture
def sample_file_data():
    """Create sample file data."""
    return b"Sample policy document content"

@pytest.fixture
def sample_metadata():
    """Create sample document metadata."""
    return {
        'document_type': 'policy',
        'version': '1.0',
        'uploaded_by': 'test_user'
    }

class TestStorageService:
    """Test cases for the storage service."""

    @pytest.mark.asyncio
    async def test_upload_policy_document(
        self,
        storage_service,
        sample_policy_id,
        sample_file_data,
        sample_metadata,
        mock_db_session
    ):
        """Test uploading a policy document."""
        filename = "test_policy.pdf"
        
        # Configure mock
        mock_db_session.policy_documents.insert_one.return_value = AsyncMock()
        
        # Upload document
        result = await storage_service.upload_policy_document(
            sample_policy_id,
            sample_file_data,
            filename,
            sample_metadata
        )
        
        # Verify result
        assert 'path' in result
        assert 'metadata' in result
        assert result['path'].startswith(f"policies/{sample_policy_id}/raw/")
        assert result['path'].endswith(filename)
        
        # Verify metadata
        assert result['metadata']['filename'] == filename
        assert result['metadata']['size'] == len(sample_file_data)
        assert result['metadata']['content_type'] == 'application/pdf'
        assert result['metadata']['document_type'] == sample_metadata['document_type']
        
        # Verify database call
        mock_db_session.policy_documents.insert_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_signed_url(self, storage_service, sample_policy_id):
        """Test getting a signed URL."""
        path = f"policies/{sample_policy_id}/raw/test.pdf"
        url = await storage_service.get_signed_url(path)
        
        assert url.startswith('https://')
        assert path in url
        assert 'token=' in url

    @pytest.mark.asyncio
    async def test_list_policy_documents(
        self,
        storage_service,
        sample_policy_id,
        mock_db_session
    ):
        """Test listing policy documents."""
        # Configure mock
        mock_documents = [
            {'path': f"policies/{sample_policy_id}/raw/doc1.pdf"},
            {'path': f"policies/{sample_policy_id}/raw/doc2.pdf"}
        ]
        mock_db_session.policy_documents.find.return_value.to_list.return_value = mock_documents
        
        # List documents
        documents = await storage_service.list_policy_documents(sample_policy_id)
        
        assert len(documents) == 2
        assert all(doc['path'].startswith(f"policies/{sample_policy_id}/") for doc in documents)
        
        # Verify query
        mock_db_session.policy_documents.find.assert_called_once_with(
            {'policy_id': str(sample_policy_id)}
        )

    @pytest.mark.asyncio
    async def test_get_document_metadata(
        self,
        storage_service,
        sample_policy_id,
        mock_db_session
    ):
        """Test getting document metadata."""
        path = f"policies/{sample_policy_id}/raw/test.pdf"
        mock_metadata = {'filename': 'test.pdf', 'size': 1000}
        mock_db_session.policy_documents.find_one.return_value = {
            'metadata': mock_metadata
        }
        
        metadata = await storage_service.get_document_metadata(path)
        
        assert metadata == mock_metadata
        mock_db_session.policy_documents.find_one.assert_called_once_with(
            {'path': path}
        )

    @pytest.mark.asyncio
    async def test_delete_document(
        self,
        storage_service,
        sample_policy_id,
        mock_db_session
    ):
        """Test deleting a document."""
        path = f"policies/{sample_policy_id}/raw/test.pdf"
        mock_db_session.policy_documents.delete_one.return_value.deleted_count = 1
        
        result = await storage_service.delete_document(path)
        
        assert result is True
        mock_db_session.policy_documents.delete_one.assert_called_once_with(
            {'path': path}
        )

    @pytest.mark.asyncio
    async def test_move_document(
        self,
        storage_service,
        sample_policy_id,
        mock_db_session
    ):
        """Test moving a document."""
        old_path = f"policies/{sample_policy_id}/raw/test.pdf"
        new_path = f"policies/{sample_policy_id}/processed/test.pdf"
        mock_db_session.policy_documents.update_one.return_value.modified_count = 1
        
        result = await storage_service.move_document(old_path, new_path)
        
        assert result is True
        mock_db_session.policy_documents.update_one.assert_called_once_with(
            {'path': old_path},
            {'$set': {'path': new_path}}
        )

    def test_get_content_type(self, storage_service):
        """Test content type detection."""
        test_cases = [
            ('test.pdf', 'application/pdf'),
            ('test.doc', 'application/msword'),
            ('test.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
            ('test.jpg', 'image/jpeg'),
            ('test.png', 'image/png'),
            ('test.unknown', 'application/octet-stream')
        ]
        
        for filename, expected_type in test_cases:
            assert storage_service._get_content_type(filename) == expected_type 