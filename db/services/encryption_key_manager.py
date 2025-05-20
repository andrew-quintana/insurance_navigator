"""Encryption key management service."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
from uuid import uuid4

class EncryptionKeyManager:
    """Manages encryption keys for the system."""

    def __init__(self, db_session):
        """Initialize the encryption key manager.
        
        Args:
            db_session: Database session for key operations
        """
        self.db = db_session
        self._key_cache = {}

    async def get_active_key(self) -> Dict[str, Any]:
        """Get the currently active encryption key.
        
        Returns:
            Dict containing the active key information
        """
        # Check cache first
        if 'active_key' in self._key_cache:
            return self._key_cache['active_key']

        # Query database for active key
        key = await self.db.encryption_keys.find_one({
            'key_status': 'active'
        })

        if not key:
            # Create new key if none exists
            key = await self._create_new_key()

        self._key_cache['active_key'] = key
        return key

    async def get_key_by_version(self, version: int) -> Optional[Dict[str, Any]]:
        """Get a specific key version.
        
        Args:
            version: Key version number
            
        Returns:
            Dict containing the key information or None if not found
        """
        cache_key = f'key_v{version}'
        if cache_key in self._key_cache:
            return self._key_cache[cache_key]

        key = await self.db.encryption_keys.find_one({
            'key_version': version
        })

        if key:
            self._key_cache[cache_key] = key
        return key

    async def rotate_key(self) -> Dict[str, Any]:
        """Rotate the active encryption key.
        
        Returns:
            Dict containing the new active key information
        """
        # Get current active key
        current_key = await self.get_active_key()

        # Create new key
        new_key = await self._create_new_key(
            version=current_key['key_version'] + 1
        )

        # Update current key status
        await self.db.encryption_keys.update_one(
            {'id': current_key['id']},
            {
                '$set': {
                    'key_status': 'rotated',
                    'rotated_at': datetime.utcnow().isoformat()
                }
            }
        )

        # Clear cache
        self._key_cache.clear()
        return new_key

    async def retire_key(self, key_id: str) -> None:
        """Retire an encryption key.
        
        Args:
            key_id: ID of the key to retire
        """
        await self.db.encryption_keys.update_one(
            {'id': key_id},
            {
                '$set': {
                    'key_status': 'retired',
                    'retired_at': datetime.utcnow().isoformat()
                }
            }
        )
        self._key_cache.clear()

    async def encrypt_data(self, data: str) -> str:
        """Encrypt data using the active key.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data string
        """
        key = await self.get_active_key()
        # In a real implementation, this would use proper encryption
        # For now, we'll just simulate encryption
        return f"encrypted:{key['id']}:{data}"

    async def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using the appropriate key.
        
        Args:
            encrypted_data: Data to decrypt
            
        Returns:
            Decrypted data string
        """
        # In a real implementation, this would use proper decryption
        # For now, we'll just simulate decryption
        parts = encrypted_data.split(':', 2)
        if len(parts) != 3 or parts[0] != 'encrypted':
            raise ValueError("Invalid encrypted data format")
        
        key_id = parts[1]
        data = parts[2]
        return data

    async def _create_new_key(self, version: Optional[int] = None) -> Dict[str, Any]:
        """Create a new encryption key.
        
        Args:
            version: Optional version number for the new key
            
        Returns:
            Dict containing the new key information
        """
        if version is None:
            # Get highest version number
            latest_key = await self.db.encryption_keys.find_one(
                sort=[('key_version', -1)]
            )
            version = (latest_key['key_version'] + 1) if latest_key else 1

        key = {
            'id': str(uuid4()),
            'key_version': version,
            'key_status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'metadata': {
                'created_by': 'system',
                'rotation_interval': '30d'
            }
        }

        await self.db.encryption_keys.insert_one(key)
        return key 