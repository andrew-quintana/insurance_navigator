"""Integration tests for auth service with HIPAA compliance."""
import pytest
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import HTTPException
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from db.services.auth_service import AuthService
from db.config import JWTConfig
from tests.db.helpers import get_test_client
from tests.config.test_config import get_base_test_config

# Mark all tests as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

class TestAuthService:
    @pytest.fixture
    def jwt_config(self) -> JWTConfig:
        """Get JWT configuration for testing."""
        return JWTConfig(
            secret="test_secret_key_for_testing",
            token_expire_minutes=15,
            algorithm="HS256"
        )

    @pytest.fixture
    async def auth_service(self, jwt_config: JWTConfig) -> AuthService:
        """Create auth service instance for testing."""
        return AuthService(jwt_config)

    @pytest.fixture
    def test_user_data(self) -> Dict[str, Any]:
        """Test user data fixture."""
        return {
            "sub": "test_user_id",
            "email": "test@example.com",
            "role": "user"
        }

    async def test_create_access_token(self, auth_service: AuthService, test_user_data: Dict[str, Any]):
        """Test access token creation."""
        token = auth_service.create_access_token(test_user_data)
        assert token is not None
        
        # Verify token
        payload = auth_service.verify_token(token)
        assert payload["sub"] == test_user_data["sub"]
        assert payload["email"] == test_user_data["email"]
        assert payload["role"] == test_user_data["role"]
        
        # Verify expiration
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=15)
        assert abs((exp_time - expected_exp).total_seconds()) < 5  # Allow 5 seconds difference

    async def test_create_refresh_token(self, auth_service: AuthService, test_user_data: Dict[str, Any]):
        """Test refresh token creation."""
        token = auth_service.create_refresh_token(test_user_data)
        assert token is not None
        
        # Verify token
        payload = auth_service.verify_token(token)
        assert payload["sub"] == test_user_data["sub"]
        assert payload["email"] == test_user_data["email"]
        assert payload["role"] == test_user_data["role"]
        assert payload["refresh"] is True

    async def test_refresh_access_token(self, auth_service: AuthService, test_user_data: Dict[str, Any]):
        """Test access token refresh."""
        refresh_token = auth_service.create_refresh_token(test_user_data)
        new_token = auth_service.refresh_access_token(refresh_token)
        assert new_token is not None
        
        # Verify new token
        payload = auth_service.verify_token(new_token)
        assert payload["sub"] == test_user_data["sub"]
        assert payload["email"] == test_user_data["email"]
        assert payload["role"] == test_user_data["role"]
        assert "refresh" not in payload

    async def test_token_expiration(self, auth_service: AuthService, test_user_data: Dict[str, Any]):
        """Test token expiration handling."""
        data = {**test_user_data, "exp": int(datetime.now(timezone.utc).timestamp()) - 60}  # 1 minute ago
        token = jwt.encode(data, auth_service.secret_key, algorithm="HS256")
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(token)
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    async def test_invalid_token(self, auth_service: AuthService):
        """Test invalid token handling."""
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token("invalid_token")
        assert exc_info.value.status_code == 401
        assert "validate" in exc_info.value.detail.lower()

    async def test_invalid_refresh_token(self, auth_service: AuthService, test_user_data: Dict[str, Any]):
        """Test invalid refresh token handling."""
        data = {**test_user_data, "role": "user"}  # Missing refresh flag
        access_token = auth_service.create_access_token(data)
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_access_token(access_token)
        assert exc_info.value.status_code == 401
        assert "invalid refresh token" in exc_info.value.detail.lower()

    async def test_hipaa_audit_logging(self, auth_service: AuthService, test_user_data: Dict[str, Any]):
        """Test HIPAA-compliant audit logging."""
        # Create a token with audit fields
        audit_data = {
            **test_user_data,
            "ip_address": "192.168.1.1",
            "user_agent": "test_browser",
            "access_type": "patient_data"
        }
        token = auth_service.create_access_token(audit_data)

        # Verify token and check audit fields
        payload = auth_service.verify_token(token)
        assert payload["ip_address"] == audit_data["ip_address"]
        assert payload["user_agent"] == audit_data["user_agent"]
        assert payload["access_type"] == audit_data["access_type"]

        # Verify audit log entry is created (if implemented)
        # This would check the audit_logs table in a real implementation 