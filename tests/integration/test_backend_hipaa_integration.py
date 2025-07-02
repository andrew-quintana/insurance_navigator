import pytest
import os
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict

from fastapi import FastAPI
from httpx import AsyncClient
from supabase import create_client, Client

from config.database import get_supabase_client
from tests.config.eval_config import EnvironmentConfig
from tests.db.helpers import cleanup_test_data

pytestmark = pytest.mark.asyncio

@pytest.fixture(scope="function")
async def supabase_test_client() -> AsyncGenerator[Client, None]:
    """Create a real Supabase client for integration testing with proper cleanup."""
    # Use test configuration
    supabase_url = os.getenv("SUPABASE_TEST_URL")
    supabase_key = os.getenv("SUPABASE_TEST_KEY")
    
    if not supabase_url or not supabase_key:
        pytest.skip("Supabase test credentials not configured")
    
    client = create_client(supabase_url, supabase_key)
    
    # Setup test data and state
    test_data = {
        "user_ids": [],
        "document_ids": [],
        "storage_paths": []
    }
    
    yield client
    
    # Cleanup after tests
    await cleanup_test_data(client, test_data)

@pytest.fixture
async def test_app(supabase_test_client: Client) -> AsyncGenerator[FastAPI, None]:
    """Create test FastAPI application with dependencies."""
    from main import app  # Import here to avoid circular imports
    
    # Override dependencies for testing
    app.dependency_overrides[get_supabase_client] = lambda: supabase_test_client
    
    yield app
    
    # Clear overrides after tests
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
class TestBackendHIPAAIntegration:
    """Test suite for HIPAA-compliant backend integration."""

    async def test_auth_flow_with_hipaa_audit(self, async_client: AsyncClient):
        """Test user authentication flow with HIPAA audit requirements."""
        # Test user signup with consent tracking
        test_email = f"test_{uuid.uuid4()}@example.com"
        test_password = "SecureTest123!"
        consent_version = "1.0"
        consent_timestamp = datetime.utcnow().isoformat()

        signup_response = await async_client.post(
            "/auth/signup",
            json={
                "email": test_email,
                "password": test_password,
                "consent_version": consent_version,
                "consent_timestamp": consent_timestamp
            }
        )
        assert signup_response.status_code == 201
        signup_data = signup_response.json()
        assert signup_data["user_id"]
        assert signup_data["email"] == test_email
        assert signup_data.get("access_token")

        # Test user login
        login_response = await async_client.post(
            "/auth/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["user"]["email"] == test_email
        assert login_data["access_token"]
        assert login_data["refresh_token"]
        assert login_data["expires_at"]

    async def test_document_processing_pipeline(self, async_client: AsyncClient):
        """Test document processing with encryption and audit trail."""
        auth_token = await self._get_auth_token(async_client)
        
        # Upload document with encryption
        test_document = {
            "content": "Test medical record",
            "patient_id": str(uuid.uuid4()),
            "document_type": "medical_record",
            "encryption_level": "AES-256"
        }
        
        upload_response = await async_client.post(
            "/documents/upload",
            json=test_document,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["document_id"]
        
        # Verify document encryption and audit trail
        document_response = await async_client.get(
            f"/documents/{document_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert document_response.status_code == 200
        document_data = document_response.json()
        assert document_data["encryption_status"] == "encrypted"
        assert document_data["audit_trail"]

    async def test_storage_with_encryption(self, async_client: AsyncClient):
        """Test storage operations with encryption."""
        auth_token = await self._get_auth_token(async_client)
        
        # Test encrypted file upload
        test_file = {
            "content": "Sensitive medical data",
            "encryption_key": str(uuid.uuid4())
        }
        
        upload_response = await async_client.post(
            "/storage/upload",
            json=test_file,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert upload_response.status_code == 201
        file_id = upload_response.json()["file_id"]
        
        # Verify encryption
        file_response = await async_client.get(
            f"/storage/{file_id}/metadata",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert file_response.status_code == 200
        assert file_response.json()["is_encrypted"] == True

    async def test_rls_policy_enforcement(self, async_client: AsyncClient):
        """Test Row Level Security policy enforcement."""
        # Create two test users
        user1_token = await self._get_auth_token(async_client)
        user2_token = await self._get_auth_token(async_client)
        
        # Create a protected resource
        resource = {
            "name": "Protected Health Record",
            "content": "Confidential data"
        }
        
        create_response = await async_client.post(
            "/resources",
            json=resource,
            headers={"Authorization": f"Bearer {user1_token}"}
        )
        assert create_response.status_code == 201
        resource_id = create_response.json()["resource_id"]
        
        # Verify user2 cannot access user1's resource
        access_response = await async_client.get(
            f"/resources/{resource_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert access_response.status_code == 403

    async def test_cross_service_transactions(self, async_client: AsyncClient):
        """Test transactions across multiple services."""
        auth_token = await self._get_auth_token(async_client)
        
        # Create a document with associated metadata
        transaction_data = {
            "document": {
                "content": "Medical report",
                "type": "report"
            },
            "metadata": {
                "patient_id": str(uuid.uuid4()),
                "doctor_id": str(uuid.uuid4())
            },
            "audit": {
                "action": "create",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        response = await async_client.post(
            "/transactions/document",
            json=transaction_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
        result = response.json()
        
        # Verify all related records were created
        assert result["document_id"]
        assert result["metadata_id"]
        assert result["audit_id"]

    async def _get_auth_token(self, async_client: AsyncClient) -> str:
        """Helper to get auth token for testing."""
        test_email = f"test_{uuid.uuid4()}@example.com"
        test_password = "SecureTest123!"
        
        # Sign up
        await async_client.post(
            "/auth/signup",
            json={
                "email": test_email,
                "password": test_password,
                "consent_version": "1.0",
                "consent_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Login
        login_response = await async_client.post(
            "/auth/login",
            json={
                "email": test_email,
                "password": test_password
            }
        )
        
        return login_response.json()["access_token"] 