"""Shared fixtures for database tests."""
import os
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.config import SupabaseConfig
from tests.db.unit.test_supabase_config import (
    TEST_URL,
    TEST_ANON_KEY,
    TEST_SERVICE_KEY,
    TEST_BUCKET,
    TEST_EXPIRY
)

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
    
    # Mock storage operations
    storage = MagicMock()
    storage.from_.return_value.upload = AsyncMock()
    storage.from_.return_value.download = AsyncMock()
    client.storage = storage
    
    # Mock table operations
    table_mock = AsyncMock()
    table_mock.select.return_value.execute.return_value.data = [{'count': 1}]
    table_mock.select.return_value.execute.return_value.error = None
    client.table.return_value = table_mock
    
    return client

@pytest.fixture
def test_config():
    """Create a test Supabase configuration."""
    return SupabaseConfig(
        url=TEST_URL,
        anon_key=TEST_ANON_KEY,
        service_role_key=TEST_SERVICE_KEY,
        storage_bucket=TEST_BUCKET,
        signed_url_expiry=TEST_EXPIRY
    )

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
        'uploaded_by': 'test_user',
        'created_at': datetime.now().isoformat()
    } 