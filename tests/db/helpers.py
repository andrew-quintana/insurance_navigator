"""Helper utilities for database testing."""

import os
import pytest
from typing import AsyncGenerator, Optional
from unittest.mock import MagicMock
from supabase import create_client, Client

async def setup_test_database():
    """Set up a clean test database state."""
    # Create Supabase client with test credentials
    supabase = create_client(
        os.getenv('SUPABASE_URL', 'https://test.supabase.co'),
        os.getenv('SUPABASE_SERVICE_ROLE_KEY', 'test-service-role-key')
    )
    
    # Clear existing test data
    await clear_test_data(supabase)
    
    # Apply test migrations
    await apply_test_migrations(supabase)
    
    return supabase

async def clear_test_data(supabase: Client):
    """Clear all test data from the database."""
    # List of tables to clear in order (respecting foreign key constraints)
    tables = [
        'user_roles',
        'users',
        'roles',
        'encryption_keys',
        'system_metadata'
    ]
    
    for table in tables:
        await supabase.table(table).delete().execute()

async def apply_test_migrations(supabase: Client):
    """Apply test migrations to set up the database schema."""
    # Execute initial schema migration
    with open('db/migrations/001_initial_schema.sql', 'r') as f:
        schema_sql = f.read()
        await supabase.rpc('exec_sql', {'sql': schema_sql}).execute()
    
    # Execute seed data migration
    with open('db/migrations/002_initial_seed.sql', 'r') as f:
        seed_sql = f.read()
        await supabase.rpc('exec_sql', {'sql': seed_sql}).execute()

@pytest.fixture
async def test_supabase() -> AsyncGenerator[Client, None]:
    """Fixture to provide a test Supabase client with clean database state."""
    supabase = await setup_test_database()
    yield supabase
    await clear_test_data(supabase)

@pytest.fixture
def mock_storage_service():
    """Create a mock storage service for testing."""
    mock = MagicMock()
    mock.upload_file.return_value = "test-file-path"
    mock.get_signed_url.return_value = "https://test-signed-url"
    return mock

@pytest.fixture
def mock_encryption_service():
    """Create a mock encryption service for testing."""
    mock = MagicMock()
    mock.encrypt.return_value = b"encrypted-data"
    mock.decrypt.return_value = b"decrypted-data"
    return mock 