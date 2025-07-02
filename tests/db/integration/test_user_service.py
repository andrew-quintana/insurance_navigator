"""Integration tests for user service with HIPAA compliance."""
import pytest
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import HTTPException
from db.services.user_service import UserService
from tests.db.helpers import get_test_client
from tests.config.test_config import get_base_test_config

# Mark all tests as integration tests
pytestmark = [pytest.mark.integration]

class TestUserService:
    @pytest.fixture
    def supabase_client(self):
        """Get Supabase client for testing."""
        client = get_test_client(use_service_role=True)  # Use service role key for tests
        yield client
        # Cleanup test data after each test
        try:
            data = client.table("users").select("id").execute()
            if data and data.data:
                for user in data.data:
                    client.table("users").delete().eq("id", user["id"]).execute()
        except Exception as e:
            print(f"Warning: Failed to cleanup test data: {str(e)}")

    @pytest.fixture
    def user_service(self, supabase_client) -> UserService:
        """Create user service instance for testing."""
        return UserService(supabase_client)

    @pytest.fixture
    def test_user(self, user_service: UserService) -> Dict[str, Any]:
        """Create a test user."""
        email = f"test_{uuid.uuid4()}@example.com"
        password = "Test123!@#"
        name = f"Test User {uuid.uuid4()}"
        consent_version = "1.0"
        consent_timestamp = datetime.utcnow().isoformat()
        
        try:
            user = user_service.create_user(
                email=email,
                password=password,
                name=name,
                consent_version=consent_version,
                consent_timestamp=consent_timestamp
            )
            
            return {
                "id": user.user.id,
                "email": email,
                "name": name,
                "password": password,
                "consent_version": consent_version,
                "consent_timestamp": consent_timestamp
            }
        except Exception as e:
            pytest.fail(f"Failed to create test user: {str(e)}")

    def test_create_user(self, user_service: UserService):
        """Test user creation with HIPAA compliance fields."""
        email = f"test_{uuid.uuid4()}@example.com"
        password = "Test123!@#"
        name = f"Test User {uuid.uuid4()}"
        consent_version = "1.0"
        consent_timestamp = datetime.utcnow().isoformat()
        
        # Create user
        user = user_service.create_user(
            email=email,
            password=password,
            name=name,
            consent_version=consent_version,
            consent_timestamp=consent_timestamp
        )
        
        assert user is not None
        assert user.user.email == email
        assert user.user.id is not None
        
        # Verify HIPAA compliance fields
        user_data = user_service.get_user_by_id(user.user.id)
        assert user_data["name"] == name
        assert user_data["consent_version"] == consent_version
        assert user_data["consent_timestamp"] is not None
        assert user_data["is_active"] is True

    def test_get_user_by_id(self, user_service: UserService, test_user: Dict[str, Any]):
        """Test retrieving user by ID."""
        user = user_service.get_user_by_id(test_user["id"])
        assert user is not None
        assert user["email"] == test_user["email"]
        assert user["name"] == test_user["name"]
        assert user["consent_version"] == test_user["consent_version"]
        
        # Test non-existent user
        non_existent_id = str(uuid.uuid4())
        user = user_service.get_user_by_id(non_existent_id)
        assert user is None

    def test_update_user(self, user_service: UserService, test_user: Dict[str, Any]):
        """Test updating user data."""
        # Update user data
        updated = user_service.update_user(
            user_id=test_user["id"],
            update_data={
                "name": "Updated Name",
                "consent_version": "2.0"
            }
        )
        
        assert updated is not None
        assert updated["name"] == "Updated Name"
        assert updated["consent_version"] == "2.0"
        
        # Verify audit log
        audit_logs = user_service.db.table("audit_logs").select("*").eq("user_id", test_user["id"]).execute()
        update_log = next(log for log in audit_logs.data if log["action"] == "user_update")
        assert update_log is not None
        assert update_log["details"]["success"] is True
        assert "name" in update_log["details"]["fields_updated"]
        assert "consent_version" in update_log["details"]["fields_updated"]

    def test_deactivate_user(self, user_service: UserService, test_user: Dict[str, Any]):
        """Test deactivating a user."""
        # Deactivate user
        deactivated = user_service.deactivate_user(test_user["id"])
        assert deactivated is True
        
        # Verify deactivation
        user = user_service.get_user_by_id(test_user["id"])
        assert user["is_active"] is False
        
        # Test deactivating non-existent user
        non_existent_id = str(uuid.uuid4())
        deactivated = user_service.deactivate_user(non_existent_id)
        assert deactivated is False

    def test_authenticate_user(self, user_service: UserService, test_user: Dict[str, Any]):
        """Test user authentication."""
        # Test valid credentials
        auth_response = user_service.authenticate_user(
            email=test_user["email"],
            password=test_user["password"]
        )
        
        assert auth_response is not None
        assert auth_response["user"]["email"] == test_user["email"]
        assert auth_response["session"]["access_token"] is not None
        assert auth_response["session"]["refresh_token"] is not None
        assert auth_response["session"]["expires_at"] is not None
        
        # Verify audit log
        audit_logs = user_service.db.table("audit_logs").select("*").eq("user_id", test_user["id"]).execute()
        assert len(audit_logs.data) > 0
        
        # Verify login audit log
        login_log = next(log for log in audit_logs.data if log["action"] == "user_login")
        assert login_log is not None
        assert login_log["details"]["success"] is True

    def test_get_user_from_token(self, user_service: UserService, test_user: Dict[str, Any]):
        """Test retrieving user from token."""
        # First authenticate to get token
        auth_response = user_service.authenticate_user(
            email=test_user["email"],
            password=test_user["password"]
        )
        
        assert auth_response["session"]["access_token"] is not None
        assert auth_response["session"]["refresh_token"] is not None
        assert auth_response["session"]["expires_at"] is not None
        access_token = auth_response["session"]["access_token"]
        refresh_token = auth_response["session"]["refresh_token"]
        expires_at = auth_response["session"]["expires_at"]
        
        # Test with full session data
        user = user_service.get_user_from_token(
            token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        assert user is not None
        assert user["id"] == test_user["id"]
        
        # Test with just access token (should work but with limited functionality)
        user_limited = user_service.get_user_from_token(access_token)
        assert user_limited is not None
        assert user_limited["id"] == test_user["id"]
        
        # Test with access token and expires_at
        user_with_expiry = user_service.get_user_from_token(
            token=access_token,
            expires_at=expires_at
        )
        assert user_with_expiry is not None
        assert user_with_expiry["id"] == test_user["id"]
        
        # Verify audit log
        audit_logs = user_service.db.table("audit_logs").select("*").eq("user_id", test_user["id"]).execute()
        token_logs = [log for log in audit_logs.data if log["action"] == "token_access"]
        assert len(token_logs) >= 3  # Should have at least 3 logs (one for each token test)
        
        # Verify session types in audit logs
        session_types = [log["details"]["session_type"] for log in token_logs]
        assert "full" in session_types
        assert "access_only" in session_types

    def test_invalid_credentials(self, user_service: UserService):
        """Test authentication with invalid credentials."""
        with pytest.raises(HTTPException) as exc_info:
            user_service.authenticate_user(
                email="nonexistent@example.com",
                password="wrongpassword"
            )
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in exc_info.value.detail

    def test_hipaa_audit_logging(self, user_service: UserService, test_user: Dict[str, Any]):
        """Test HIPAA-compliant audit logging."""
        # Update user data
        user_service.update_user(
            user_id=test_user["id"],
            update_data={
                "consent_version": "2.0",
                "consent_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # Verify audit logs
        audit_logs = user_service.db.table("audit_logs").select("*").eq("user_id", test_user["id"]).execute()
        assert len(audit_logs.data) > 0
        
        # Verify update log
        update_log = next(log for log in audit_logs.data if log["action"] == "user_update")
        assert update_log is not None
        assert update_log["details"]["success"] is True
        assert "consent_version" in update_log["details"]["fields_updated"]
        assert "consent_timestamp" in update_log["details"]["fields_updated"] 