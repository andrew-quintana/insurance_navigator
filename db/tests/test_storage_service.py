import pytest
import uuid
from datetime import datetime
from ..services.storage_service import StorageService

@pytest.fixture
async def storage_service():
    return StorageService()

@pytest.fixture
def sample_policy_id():
    return uuid.uuid4()

@pytest.fixture
def sample_file_data():
    return b"Sample policy document content"

@pytest.fixture
def sample_metadata():
    return {
        'document_type': 'policy',
        'version': '1.0',
        'uploaded_by': 'test_user'
    }

@pytest.mark.asyncio
async def test_upload_policy_document(
    storage_service,
    sample_policy_id,
    sample_file_data,
    sample_metadata
):
    """Test uploading a policy document."""
    result = await storage_service.upload_policy_document(
        sample_policy_id,
        sample_file_data,
        'test_policy.pdf',
        sample_metadata
    )
    
    assert 'path' in result
    assert 'metadata_path' in result
    assert 'metadata' in result
    assert result['metadata']['policy_id'] == str(sample_policy_id)
    assert result['metadata']['type'] == 'policy'

@pytest.mark.asyncio
async def test_get_signed_url(storage_service, sample_policy_id):
    """Test generating a signed URL."""
    path = f"policies/{sample_policy_id}/raw/test.pdf"
    signed_url = await storage_service.get_signed_url(path)
    
    assert signed_url.startswith('http')
    assert 'signature=' in signed_url

@pytest.mark.asyncio
async def test_list_policy_documents(
    storage_service,
    sample_policy_id,
    sample_file_data
):
    """Test listing policy documents."""
    # Upload a document first
    await storage_service.upload_policy_document(
        sample_policy_id,
        sample_file_data,
        'test_policy.pdf'
    )
    
    # List documents
    documents = await storage_service.list_policy_documents(sample_policy_id)
    assert len(documents) > 0

@pytest.mark.asyncio
async def test_get_document_metadata(
    storage_service,
    sample_policy_id,
    sample_file_data,
    sample_metadata
):
    """Test retrieving document metadata."""
    # Upload a document with metadata
    await storage_service.upload_policy_document(
        sample_policy_id,
        sample_file_data,
        'test_policy.pdf',
        sample_metadata
    )
    
    # Get metadata
    metadata = await storage_service.get_document_metadata(sample_policy_id)
    assert metadata['policy_id'] == str(sample_policy_id)
    assert metadata['type'] == 'policy'
    assert metadata['metadata'] == sample_metadata

@pytest.mark.asyncio
async def test_delete_document(
    storage_service,
    sample_policy_id,
    sample_file_data
):
    """Test deleting a document."""
    # Upload a document
    result = await storage_service.upload_policy_document(
        sample_policy_id,
        sample_file_data,
        'test_policy.pdf'
    )
    
    # Delete the document
    await storage_service.delete_document(result['path'])
    
    # Verify deletion
    with pytest.raises(Exception):
        await storage_service.get_document_metadata(sample_policy_id)

@pytest.mark.asyncio
async def test_move_document(
    storage_service,
    sample_policy_id,
    sample_file_data
):
    """Test moving a document."""
    # Upload a document
    result = await storage_service.upload_policy_document(
        sample_policy_id,
        sample_file_data,
        'test_policy.pdf'
    )
    
    # Move the document
    new_path = f"policies/{sample_policy_id}/processed/test_policy.pdf"
    move_result = await storage_service.move_document(
        result['path'],
        new_path
    )
    
    assert move_result['new_path'] == new_path
    assert move_result['metadata_updated'] is True

@pytest.mark.asyncio
async def test_create_processed_version(
    storage_service,
    sample_policy_id,
    sample_file_data,
    sample_metadata
):
    """Test creating a processed version of a document."""
    # Upload original document
    await storage_service.upload_policy_document(
        sample_policy_id,
        sample_file_data,
        'test_policy.pdf'
    )
    
    # Create processed version
    result = await storage_service.create_processed_version(
        sample_policy_id,
        sample_file_data,
        'processed_policy.pdf',
        sample_metadata
    )
    
    assert 'path' in result
    assert 'metadata' in result
    assert 'processed_version' in result['metadata']
    assert result['metadata']['processed_version']['path'] == result['path'] 