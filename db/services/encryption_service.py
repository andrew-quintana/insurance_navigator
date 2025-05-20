from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import uuid
from datetime import datetime
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionService(ABC):
    """Abstract base class for encryption services."""
    
    @abstractmethod
    async def encrypt(self, data: bytes, key_id: uuid.UUID) -> bytes:
        """Encrypt data using the specified key."""
        pass
    
    @abstractmethod
    async def decrypt(self, encrypted_data: bytes, key_id: uuid.UUID) -> bytes:
        """Decrypt data using the specified key."""
        pass
    
    @abstractmethod
    async def generate_key(self) -> Dict[str, Any]:
        """Generate a new encryption key."""
        pass

class MockEncryptionService(EncryptionService):
    """Mock implementation of encryption service for development and testing."""
    
    def __init__(self):
        self._keys: Dict[uuid.UUID, bytes] = {}
        self._salt = b'mock_salt'  # In production, this would be unique per key
    
    def _derive_key(self, key_id: uuid.UUID) -> bytes:
        """Derive a key from the key ID for mock encryption."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(str(key_id).encode()))
    
    async def encrypt(self, data: bytes, key_id: uuid.UUID) -> bytes:
        """Mock encryption using Fernet."""
        key = self._derive_key(key_id)
        f = Fernet(key)
        return f.encrypt(data)
    
    async def decrypt(self, encrypted_data: bytes, key_id: uuid.UUID) -> bytes:
        """Mock decryption using Fernet."""
        key = self._derive_key(key_id)
        f = Fernet(key)
        return f.decrypt(encrypted_data)
    
    async def generate_key(self) -> Dict[str, Any]:
        """Generate a mock encryption key."""
        key_id = uuid.uuid4()
        key = Fernet.generate_key()
        self._keys[key_id] = key
        
        return {
            'id': key_id,
            'key_version': 1,
            'key_status': 'active',
            'created_at': datetime.now().isoformat(),
            'metadata': {
                'provider': 'mock',
                'algorithm': 'fernet',
                'created_by': 'system'
            }
        }

class EncryptionServiceFactory:
    """Factory for creating encryption service instances."""
    
    @staticmethod
    def create_service(provider: str) -> EncryptionService:
        """
        Create an encryption service instance based on the provider.
        
        Args:
            provider: The encryption provider to use ('mock' for development)
        
        Returns:
            An instance of EncryptionService
        """
        if provider == 'mock':
            return MockEncryptionService()
        else:
            raise ValueError(f"Unsupported encryption provider: {provider}") 