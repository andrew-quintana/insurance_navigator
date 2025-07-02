"""Shared fixtures for database tests."""
import os
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from datetime import datetime
from cryptography.fernet import Fernet

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from db.config import SupabaseConfig, JWTConfig

# Test configuration constants
TEST_URL = "http://127.0.0.1:54321"
TEST_SERVICE_KEY = "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
TEST_ANON_KEY = "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.OXBO4nlx4gE7qGF4e1-znHLBALmZtABh_Fd_Ai5-YNg"
TEST_JWT_EXPIRY = 3600
TEST_ENCRYPTION_KEY = "YourBase64EncodedKey=="

@pytest.fixture
def mock_db_session():
    """Create a mock database session with HIPAA compliance."""
    session = AsyncMock()
    
    # Mock collections with audit logging
    session.policy_documents = AsyncMock()
    session.policy_documents.insert_one = AsyncMock()
    session.policy_documents.find = AsyncMock()
    session.policy_documents.find_one = AsyncMock()
    session.policy_documents.delete_one = AsyncMock()
    session.policy_documents.update_one = AsyncMock()
    
    # Mock audit log collection
    session.audit_logs = AsyncMock()
    session.audit_logs.insert_one = AsyncMock()
    
    return session

@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client with HIPAA compliance."""
    client = MagicMock()
    
    # Mock auth operations with audit logging
    client.auth = MagicMock()
    client.auth.sign_up = AsyncMock()
    client.auth.sign_in = AsyncMock()
    client.auth.sign_out = AsyncMock()
    client.auth.get_session = AsyncMock()
    
    # Mock storage operations with encryption
    storage = MagicMock()
    storage.from_.return_value.upload = AsyncMock()
    storage.from_.return_value.download = AsyncMock()
    client.storage = storage
    
    # Mock table operations with RLS
    table_mock = AsyncMock()
    table_mock.select.return_value.execute.return_value.data = [{'count': 1}]
    table_mock.select.return_value.execute.return_value.error = None
    client.table.return_value = table_mock
    
    # Mock audit logging
    client.rpc = AsyncMock()
    client.rpc.return_value.execute = AsyncMock()
    
    return client

@pytest.fixture
def supabase_config():
    """Create a test Supabase configuration with HIPAA compliance."""
    return SupabaseConfig(
        url=TEST_URL,
        service_role_key=TEST_SERVICE_KEY,
        anon_key=TEST_ANON_KEY,
        jwt_secret=os.getenv("SUPABASE_JWT_SECRET"),  # Use JWT secret from environment
        jwt_expiry=TEST_JWT_EXPIRY,
        encryption_key=TEST_ENCRYPTION_KEY,
        audit_logging=True,
        data_retention_days=365
    )

@pytest.fixture
def jwt_config():
    """Create a test JWT configuration."""
    return JWTConfig(
        secret=os.getenv("SUPABASE_JWT_SECRET"),  # Use JWT secret from environment
        algorithm="HS256",
        access_token_expire_minutes=30
    )

@pytest.fixture
def sample_policy_id():
    """Create a sample policy ID."""
    return uuid.uuid4()

@pytest.fixture
def sample_file_data():
    """Create sample encrypted file data."""
    fernet = Fernet(TEST_ENCRYPTION_KEY.encode())
    return fernet.encrypt(b"Sample policy document content")

@pytest.fixture
def sample_metadata():
    """Create sample document metadata with audit fields."""
    return {
        'document_type': 'policy',
        'version': '1.0',
        'uploaded_by': 'test_user',
        'created_at': datetime.now().isoformat(),
        'encryption_version': '1.0',
        'last_accessed': datetime.now().isoformat(),
        'access_history': []
    } 