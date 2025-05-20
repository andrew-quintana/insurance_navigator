"""Test fixtures for the database infrastructure."""

import asyncio
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uuid import uuid4

from db.services.encryption_key_manager import EncryptionKeyManager
from db.services.storage_service import StorageService
from db.services.policy_access_evaluator import PolicyAccessEvaluator
from db.services.policy_operations import PolicyOperations
from db.services.access_logging_service import AccessLoggingService

@pytest.fixture
def app() -> FastAPI:
    """Create a FastAPI test application."""
    from db.api.error_handler import setup_error_handlers
    app = FastAPI()
    setup_error_handlers(app)
    return app

@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
async def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    return AsyncMock()

@pytest.fixture
async def mock_access_logger() -> AsyncMock:
    """Create a mock access logger."""
    return AsyncMock(spec=AccessLoggingService)

@pytest.fixture
async def encryption_manager(mock_db_session: AsyncMock) -> EncryptionKeyManager:
    """Create an encryption key manager instance."""
    manager = EncryptionKeyManager(mock_db_session)
    # Mock the get_active_key method
    manager.get_active_key = AsyncMock(return_value={
        'id': str(uuid4()),
        'key_version': 1,
        'key_status': 'active'
    })
    # Mock other methods
    manager.encrypt_data = AsyncMock(return_value='encrypted_data')
    manager.decrypt_data = AsyncMock(return_value='decrypted_data')
    manager.rotate_key = AsyncMock(return_value={
        'id': str(uuid4()),
        'key_version': 2,
        'key_status': 'active'
    })
    return manager

@pytest.fixture
async def storage_service(mock_db_session: AsyncMock) -> StorageService:
    """Create a storage service instance."""
    service = StorageService(mock_db_session)
    # Mock methods
    service.upload_policy_document = AsyncMock(return_value={
        'path': f'policies/{uuid4()}/raw/test.pdf',
        'metadata': {}
    })
    service.get_signed_url = AsyncMock(return_value='https://test-signed-url.com')
    service.list_policy_documents = AsyncMock(return_value=[])
    service.get_document_metadata = AsyncMock(return_value={})
    service.delete_document = AsyncMock(return_value=True)
    service.move_document = AsyncMock(return_value=True)
    return service

@pytest.fixture
def sample_user_id() -> str:
    """Generate a sample user ID."""
    return str(uuid4())

@pytest.fixture
def sample_resource_id() -> str:
    """Generate a sample resource ID."""
    return str(uuid4())

@pytest.fixture
def admin_user_roles() -> Dict[str, Any]:
    """Create admin user roles fixture."""
    return {
        'permissions': ['read', 'write', 'delete'],
        'roles': ['admin']
    }

@pytest.fixture
def reader_user_roles() -> Dict[str, Any]:
    """Create reader user roles fixture."""
    return {
        'permissions': ['read'],
        'roles': ['reader']
    }

@pytest.fixture
def sample_policy_id() -> str:
    """Generate a sample policy ID."""
    return str(uuid4())

@pytest.fixture
def sample_file_data() -> bytes:
    """Create sample file data."""
    return b'Sample policy document content'

@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """Create sample metadata."""
    return {
        'document_type': 'policy',
        'uploaded_by': 'test_user',
        'version': '1.0'
    } 