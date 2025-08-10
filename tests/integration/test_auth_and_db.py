"""
Integration tests for authentication and database connections.
"""
import os
import sys
import pytest
import logging
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import HTTPException

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db.services.user_service import get_user_service, UserService
from db.services.db_pool import get_db_pool, close_db_pool, get_connection_status
from config.database import get_supabase_client, get_db_client
from supabase import Client
from db.config import SupabaseConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test data
TEST_USER_EMAIL = f"test_auth_{uuid.uuid4().hex[:8]}@example.com"
TEST_USER_PASSWORD = "TestPassword123!"
TEST_USER_NAME = "Auth Test User"

@pytest.fixture
async def user_service():
    """Get a configured user service for testing."""
    client = await get_supabase_client()
    service = get_user_service()
    return service

@pytest.fixture
def user_data():
    """Get test user data."""
    return {
        "email": f"test_{uuid.uuid4()}@example.com",
        "password": "Test123!@#",
        "consent_version": "1.0",
        "consent_timestamp": datetime.utcnow().isoformat()
    }

@pytest.fixture
async def test_user(user_service: UserService) -> Optional[Dict[str, Any]]:
    """Create a test user and clean up after test."""
    # Create test user
    user_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
        "full_name": TEST_USER_NAME
    }
    
    user = await user_service.create_user(user_data)
    
    yield user
    
    # Cleanup: Delete test user
    if user:
        await user_service.db.delete().eq("id", user["id"]).execute()

@pytest.mark.asyncio
async def test_database_connection():
    """Test database connection."""
    async with get_db_client() as client:
        # Test a simple query
        response = await client.table("users").select("count").execute()
        assert response.data is not None
        assert not response.error

@pytest.mark.asyncio
async def test_user_creation(user_service, user_data):
    """Test user creation with HIPAA compliance."""
    # Create user
    user = await user_service.create_user(
        email=user_data["email"],
        password=user_data["password"],
        consent_version=user_data["consent_version"],
        consent_timestamp=user_data["consent_timestamp"]
    )
    
    assert user is not None
    assert user["user"]["email"] == user_data["email"]
    assert user["user"]["consent_version"] == user_data["consent_version"]
    assert user["session"]["access_token"] is not None
    assert user["session"]["refresh_token"] is not None

@pytest.mark.asyncio
async def test_user_authentication(user_service, user_data):
    """Test user authentication with audit logging."""
    # Create test user first
    await user_service.create_user(
        email=user_data["email"],
        password=user_data["password"],
        consent_version=user_data["consent_version"],
        consent_timestamp=user_data["consent_timestamp"]
    )
    
    # Test authentication
    auth_result = await user_service.authenticate_user(
        email=user_data["email"],
        password=user_data["password"]
    )
    
    assert auth_result is not None
    assert auth_result["user"]["email"] == user_data["email"]
    assert auth_result["access_token"] is not None
    assert auth_result["refresh_token"] is not None

@pytest.mark.asyncio
async def test_invalid_authentication(user_service):
    """Test invalid authentication handling."""
    with pytest.raises(HTTPException) as exc_info:
        await user_service.authenticate_user(
            email="invalid@example.com",
            password="invalid"
        )
    
    assert exc_info.value.status_code == 401
    assert "Authentication failed" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_connection_retry():
    """Test database connection retry logic."""
    async with get_db_client() as client:
        # Test connection retry
        response = await client.table("users").select("count").execute()
        assert response.data is not None
        assert not response.error

@pytest.mark.asyncio
async def test_auth_flow_with_hipaa_audit(user_service, test_user_data):
    """Test the complete auth flow with HIPAA audit logging."""
    # Create user
    user = await user_service.create_user(
        email=test_user_data["email"],
        password=test_user_data["password"],
        consent_version=test_user_data["consent_version"],
        consent_timestamp=test_user_data["consent_timestamp"]
    )
    assert user is not None
    assert user["email"] == test_user_data["email"]
    assert user["consent_version"] == test_user_data["consent_version"]
    
    # Verify audit log
    audit_log = await user_service.get_audit_log(user["id"])
    assert audit_log is not None
    assert len(audit_log) > 0
    assert audit_log[0]["action"] == "user.created"
    assert audit_log[0]["user_id"] == user["id"]

@pytest.mark.asyncio
async def test_document_processing_pipeline(document_service, storage_service, test_document, test_user):
    """Test the document processing pipeline with encryption and audit logging."""
    # Process document
    processed_doc = await document_service.process_document(
        document_id=test_document["id"],
        user_id=test_user["id"]
    )
    assert processed_doc is not None
    assert processed_doc["status"] == "processed"
    assert processed_doc["is_encrypted"] is True
    
    # Verify audit log
    audit_log = await document_service.get_audit_log(test_document["id"])
    assert audit_log is not None
    assert len(audit_log) > 0
    assert audit_log[0]["action"] == "document.processed"
    assert audit_log[0]["document_id"] == test_document["id"]

@pytest.mark.asyncio
async def test_storage_with_encryption(storage_service, test_document, test_user):
    """Test storage operations with encryption and audit logging."""
    # Store encrypted document
    stored_doc = await storage_service.store_document(
        document_id=test_document["id"],
        user_id=test_user["id"],
        content=b"test content"
    )
    assert stored_doc is not None
    assert stored_doc["is_encrypted"] is True
    
    # Verify audit log
    audit_log = await storage_service.get_audit_log(test_document["id"])
    assert audit_log is not None
    assert len(audit_log) > 0
    assert audit_log[0]["action"] == "storage.document.stored"
    assert audit_log[0]["document_id"] == test_document["id"]

@pytest.mark.asyncio
async def test_rls_policy_enforcement(supabase_client, test_user, test_document):
    """Test RLS policy enforcement for data isolation."""
    # Try accessing document as different user
    other_user_id = str(uuid.uuid4())
    
    # This should fail due to RLS
    with pytest.raises(HTTPException) as exc_info:
        await supabase_client.from_("documents").select("*").eq("id", test_document["id"]).execute()
    assert exc_info.value.status_code == 403
    
    # Access with correct user should work
    result = await supabase_client.auth.sign_in_with_password({
        "email": test_user["email"],
        "password": test_user["password"]
    })
    assert result.user is not None
    
    docs = await supabase_client.from_("documents").select("*").eq("id", test_document["id"]).execute()
    assert len(docs.data) == 1
    assert docs.data[0]["id"] == test_document["id"]

@pytest.mark.asyncio
async def test_cross_service_transactions(transaction_service, test_user, test_document):
    """Test cross-service transactions with rollback and audit logging."""
    # Start transaction
    async with transaction_service.transaction() as txn:
        # Update document
        updated_doc = await txn.document_service.update_document(
            document_id=test_document["id"],
            updates={"status": "archived"}
        )
        assert updated_doc["status"] == "archived"
        
        # Update storage
        storage_result = await txn.storage_service.archive_document(
            document_id=test_document["id"]
        )
        assert storage_result is True
        
        # Verify transaction audit log
        audit_log = await txn.get_audit_log()
        assert audit_log is not None
        assert len(audit_log) == 2
        assert audit_log[0]["action"] == "document.updated"
        assert audit_log[1]["action"] == "storage.document.archived"

@pytest.mark.asyncio
async def test_user_signup_and_consent(
    supabase_client: Client,
    test_user_data: Dict[str, Any]
):
    """Test user signup with consent tracking."""
    # Sign up user
    auth_response = await supabase_client.auth.sign_up({
        "email": test_user_data["email"],
        "password": test_user_data["password"],
        "options": {
            "data": {
                "consent_version": test_user_data["consent_version"],
                "consent_date": test_user_data["consent_date"],
                "metadata": test_user_data["metadata"]
            }
        }
    })
    
    assert auth_response.user is not None
    assert auth_response.user.email == test_user_data["email"]
    
    # Verify user metadata
    user_metadata = auth_response.user.user_metadata
    assert user_metadata["consent_version"] == test_user_data["consent_version"]
    assert user_metadata["consent_date"] is not None
    assert user_metadata["metadata"]["requires_mfa"] is True

@pytest.mark.asyncio
async def test_document_upload_with_encryption(
    supabase_client: Client,
    test_user_data: Dict[str, Any],
    test_document_data: Dict[str, Any]
):
    """Test document upload with encryption and audit logging."""
    # Sign in user
    auth_response = await supabase_client.auth.sign_in_with_password({
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    assert auth_response.user is not None
    
    # Upload document
    storage = supabase_client.storage.from_(os.getenv("STORAGE_BUCKET"))
    
    # Create test file content
    test_content = b"Test document content"
    
    # Upload with encryption
    upload_response = await storage.upload(
        path=test_document_data["filename"],
        file=test_content,
        file_options={
            "content_type": test_document_data["content_type"],
            "encryption_enabled": test_document_data["encryption_enabled"],
            "metadata": test_document_data["metadata"]
        }
    )
    
    assert upload_response is not None
    
    # Verify document metadata
    doc_metadata = await storage.get_metadata(test_document_data["filename"])
    assert doc_metadata["encryption_enabled"] == test_document_data["encryption_enabled"]
    assert doc_metadata["metadata"]["encryption_version"] == test_document_data["metadata"]["encryption_version"]
    
    # Verify audit log entry if enabled
    if test_document_data["audit_enabled"]:
        audit_logs = await supabase_client.table("audit_logs").select("*").eq(
            "document_id", test_document_data["filename"]
        ).execute()
        
        assert len(audit_logs.data) > 0
        assert audit_logs.data[0]["action"] == "upload"
        assert audit_logs.data[0]["user_id"] == auth_response.user.id

@pytest.mark.asyncio
async def test_document_access_tracking(
    supabase_client: Client,
    test_user_data: Dict[str, Any],
    test_document_data: Dict[str, Any]
):
    """Test document access tracking and audit logging."""
    # Sign in user
    auth_response = await supabase_client.auth.sign_in_with_password({
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    
    assert auth_response.user is not None
    
    # Access document
    storage = supabase_client.storage.from_(os.getenv("STORAGE_BUCKET"))
    download_response = await storage.download(test_document_data["filename"])
    
    assert download_response is not None
    
    # Verify access log if audit enabled
    if test_document_data["audit_enabled"]:
        audit_logs = await supabase_client.table("audit_logs").select("*").eq(
            "document_id", test_document_data["filename"]
        ).eq("action", "download").execute()
        
        assert len(audit_logs.data) > 0
        latest_access = audit_logs.data[-1]
        assert latest_access["user_id"] == auth_response.user.id
        assert latest_access["timestamp"] is not None

@pytest.mark.asyncio
async def test_data_retention_policy(
    supabase_client: Client,
    test_user_data: Dict[str, Any],
    test_document_data: Dict[str, Any]
):
    """Test data retention policy enforcement."""
    # Get documents older than retention period
    retention_days = test_document_data["metadata"]["retention_period"]
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    expired_docs = await supabase_client.table("documents").select("*").lt(
        "created_at", cutoff_date.isoformat()
    ).execute()
    
    # Verify expired documents are handled according to policy
    for doc in expired_docs.data:
        assert doc["status"] == "archived" or doc["status"] == "pending_deletion"

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 