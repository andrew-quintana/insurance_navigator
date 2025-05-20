import pytest
import uuid
from datetime import datetime, timedelta
from ..services.encryption_manager import EncryptionKeyManager
from ..config import config

@pytest.fixture
async def encryption_manager():
    return EncryptionKeyManager()

@pytest.fixture
def sample_data():
    return b"Sample sensitive data for encryption testing"

@pytest.mark.asyncio
async def test_get_active_key(encryption_manager):
    """Test retrieving the active encryption key."""
    key = await encryption_manager.get_active_key()
    assert key is not None
    assert key['key_status'] == 'active'
    assert 'key_version' in key
    assert 'metadata' in key

@pytest.mark.asyncio
async def test_encrypt_decrypt_data(encryption_manager, sample_data):
    """Test encrypting and decrypting data."""
    # Get active key
    key = await encryption_manager.get_active_key()
    
    # Encrypt data
    encrypted_data = await encryption_manager.encrypt_data(sample_data)
    assert encrypted_data != sample_data  # Ensure data is actually encrypted
    
    # Decrypt data
    decrypted_data = await encryption_manager.decrypt_data(encrypted_data, key['id'])
    assert decrypted_data == sample_data  # Ensure data is correctly decrypted

@pytest.mark.asyncio
async def test_key_rotation(encryption_manager):
    """Test key rotation process."""
    # Get current active key
    current_key = await encryption_manager.get_active_key()
    current_version = current_key['key_version']

    # Rotate key
    new_key = await encryption_manager.rotate_key()
    
    assert new_key['key_version'] == current_version + 1
    assert new_key['key_status'] == 'active'
    assert new_key['metadata']['previous_key_id'] == current_key['id']

    # Verify old key is marked as rotated
    old_key = await encryption_manager.get_key_by_version(current_version)
    assert old_key['key_status'] == 'rotated'
    assert old_key['rotated_at'] is not None

@pytest.mark.asyncio
async def test_get_key_by_version(encryption_manager):
    """Test retrieving a key by version number."""
    # Get active key to know its version
    active_key = await encryption_manager.get_active_key()
    version = active_key['key_version']

    # Get key by version
    key = await encryption_manager.get_key_by_version(version)
    assert key['key_version'] == version

    # Test non-existent version
    with pytest.raises(ValueError):
        await encryption_manager.get_key_by_version(999999)

@pytest.mark.asyncio
async def test_validate_key_status(encryption_manager):
    """Test key status validation."""
    # Get active key
    active_key = await encryption_manager.get_active_key()
    
    # Validate active key
    assert await encryption_manager.validate_key_status(active_key['id']) is True

    # Test with invalid UUID
    assert await encryption_manager.validate_key_status(uuid.uuid4()) is False

@pytest.mark.asyncio
async def test_retire_key(encryption_manager):
    """Test key retirement process."""
    # Create a new key to retire
    new_key = await encryption_manager.rotate_key()
    
    # Retire the key
    await encryption_manager.retire_key(new_key['id'])
    
    # Verify key is retired
    retired_key = await encryption_manager.get_key_by_version(new_key['key_version'])
    assert retired_key['key_status'] == 'retired'
    assert retired_key['retired_at'] is not None

@pytest.mark.asyncio
async def test_key_cache(encryption_manager):
    """Test key caching mechanism."""
    # First call should hit the database
    key1 = await encryption_manager.get_active_key()
    
    # Second call should use cache
    key2 = await encryption_manager.get_active_key()
    
    assert key1 == key2  # Should be the same object from cache
    
    # Force cache expiry
    encryption_manager._cache_expiry = datetime.now() - timedelta(minutes=1)
    
    # This call should hit the database again
    key3 = await encryption_manager.get_active_key()
    assert key3['id'] == key1['id']  # Should be the same key, but from fresh DB query

@pytest.mark.asyncio
async def test_encryption_with_rotated_key(encryption_manager, sample_data):
    """Test encryption/decryption with rotated keys."""
    # Get initial active key
    initial_key = await encryption_manager.get_active_key()
    
    # Encrypt data with initial key
    encrypted_data = await encryption_manager.encrypt_data(sample_data)
    
    # Rotate the key
    new_key = await encryption_manager.rotate_key()
    
    # Should still be able to decrypt with old key
    decrypted_data = await encryption_manager.decrypt_data(encrypted_data, initial_key['id'])
    assert decrypted_data == sample_data
    
    # Encrypt new data with new key
    new_encrypted_data = await encryption_manager.encrypt_data(sample_data)
    assert new_encrypted_data != encrypted_data  # Should be different due to different keys
    
    # Decrypt new data with new key
    new_decrypted_data = await encryption_manager.decrypt_data(new_encrypted_data, new_key['id'])
    assert new_decrypted_data == sample_data 