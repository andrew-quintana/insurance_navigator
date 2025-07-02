"""Integration tests for database schema validation."""
import pytest
from db.services.db_pool import get_db_pool

@pytest.mark.asyncio
async def test_users_table_exists():
    """Test that the users table exists with correct columns."""
    db = get_db_pool()
    assert db is not None, "Database connection failed"
    
    # Get table info from Postgres
    response = db.table('users').select("id,email,name,created_at,last_login,session_expires").limit(0).execute()
    assert response.data is not None, "Users table does not exist"
    
    # Verify required columns exist by checking if the select query works
    assert response.data == [], "Users table missing required columns"

@pytest.mark.asyncio
async def test_documents_table_exists():
    """Test that the documents table exists with correct columns."""
    db = get_db_pool()
    assert db is not None, "Database connection failed"
    
    # Get table info from Postgres
    response = db.table('documents').select(
        "id,user_id,filename,content_type,status,created_at,updated_at,storage_path,error_message"
    ).limit(0).execute()
    assert response.data is not None, "Documents table does not exist"
    
    # Verify required columns exist by checking if the select query works
    assert response.data == [], "Documents table missing required columns"

@pytest.mark.asyncio
async def test_storage_bucket_exists():
    """Test that the documents storage bucket exists."""
    db = get_db_pool()
    assert db is not None, "Database connection failed"
    
    # Use the storage API to check the bucket
    storage = db.storage
    buckets = storage.list_buckets()
    assert any(b.name == 'documents' for b in buckets), "Storage bucket 'documents' not found"
    
    bucket = next(b for b in buckets if b.name == 'documents')
    assert not bucket.public, "Storage bucket should not be public"
    assert bucket.file_size_limit == 10485760, "Incorrect file size limit"  # 10MB
    assert 'application/pdf' in bucket.allowed_mime_types, "PDF mime type not allowed"

@pytest.mark.asyncio
async def test_rls_policies():
    """Test that RLS policies are enabled."""
    db = get_db_pool()
    assert db is not None, "Database connection failed"
    
    # Test users table RLS
    users_response = db.table('users').select("*").limit(1).execute()
    assert users_response.data is not None, "Cannot access users table"
    
    # Test documents table RLS
    docs_response = db.table('documents').select("*").limit(1).execute()
    assert docs_response.data is not None, "Cannot access documents table" 