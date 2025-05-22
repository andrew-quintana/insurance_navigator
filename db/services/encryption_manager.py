from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import json
from supabase import create_client, Client
from ..config import config
from .encryption_service import EncryptionServiceFactory, EncryptionService

class EncryptionKeyManager:
    def __init__(self):
        self.supabase: Client = create_client(
            config.supabase.url,
            config.supabase.service_role_key
        )
        self._active_key_cache: Optional[Dict[str, Any]] = None
        self._cache_expiry: Optional[datetime] = None
        self.encryption_service: EncryptionService = EncryptionServiceFactory.create_service(
            config.encryption.provider
        )

    async def get_active_key(self) -> Dict[str, Any]:
        """
        Get the currently active encryption key.
        Uses caching to reduce database queries.
        """
        if self._is_cache_valid():
            return self._active_key_cache

        response = await self.supabase.table('encryption_keys') \
            .select('*') \
            .eq('key_status', 'active') \
            .single() \
            .execute()

        if not response.data:
            raise ValueError("No active encryption key found")

        self._active_key_cache = response.data
        self._cache_expiry = datetime.now() + timedelta(minutes=5)
        return response.data

    async def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt data using the active encryption key.
        """
        key = await self.get_active_key()
        return await self.encryption_service.encrypt(data, key['id'])

    async def decrypt_data(self, encrypted_data: bytes, key_id: uuid.UUID) -> bytes:
        """
        Decrypt data using the specified key.
        Validates the key status before decryption.
        """
        if not await self.validate_key_status(key_id):
            raise ValueError(f"Key {key_id} is not valid for decryption")
        
        return await self.encryption_service.decrypt(encrypted_data, key_id)

    async def rotate_key(self) -> Dict[str, Any]:
        """
        Rotate the encryption key by:
        1. Marking current active key as rotated
        2. Creating a new active key
        """
        # Get current active key
        current_key = await self.get_active_key()
        
        # Mark current key as rotated
        await self.supabase.table('encryption_keys') \
            .update({
                'key_status': 'rotated',
                'rotated_at': datetime.now().isoformat()
            }) \
            .eq('id', current_key['id']) \
            .execute()

        # Generate new key
        new_key_data = await self.encryption_service.generate_key()
        new_key = {
            'id': new_key_data['id'],
            'key_version': current_key['key_version'] + 1,
            'key_status': 'active',
            'created_at': datetime.now().isoformat(),
            'metadata': {
                **new_key_data['metadata'],
                'previous_key_id': current_key['id'],
                'rotation_interval': '30d'
            }
        }

        # Store new key
        response = await self.supabase.table('encryption_keys') \
            .insert(new_key) \
            .execute()

        # Invalidate cache
        self._active_key_cache = None
        self._cache_expiry = None

        return response.data[0]

    async def get_key_by_version(self, version: int) -> Dict[str, Any]:
        """Get an encryption key by its version number."""
        response = await self.supabase.table('encryption_keys') \
            .select('*') \
            .eq('key_version', version) \
            .single() \
            .execute()

        if not response.data:
            raise ValueError(f"No encryption key found for version {version}")

        return response.data

    def _is_cache_valid(self) -> bool:
        """Check if the cached key is still valid."""
        if not self._active_key_cache or not self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry

    async def validate_key_status(self, key_id: uuid.UUID) -> bool:
        """
        Validate that a key is still active or rotated (not retired).
        Used when decrypting data to ensure the key is still valid.
        """
        response = await self.supabase.table('encryption_keys') \
            .select('key_status') \
            .eq('id', key_id) \
            .single() \
            .execute()

        if not response.data:
            return False

        return response.data['key_status'] in ['active', 'rotated']

    async def retire_key(self, key_id: uuid.UUID) -> None:
        """
        Retire an encryption key.
        This should only be done after all data encrypted with this key
        has been re-encrypted with a newer key.
        """
        await self.supabase.table('encryption_keys') \
            .update({
                'key_status': 'retired',
                'retired_at': datetime.now().isoformat()
            }) \
            .eq('id', key_id) \
            .execute()

        # Invalidate cache if the retired key was cached
        if self._active_key_cache and self._active_key_cache['id'] == key_id:
            self._active_key_cache = None
            self._cache_expiry = None 