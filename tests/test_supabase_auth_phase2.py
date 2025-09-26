"""
Test suite for Phase 2 Supabase Authentication implementation.
Tests the simplified authentication system using only Supabase auth.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
import json

# Import the auth components
from db.services.auth_adapter import auth_adapter, SupabaseAuthBackend
from db.services.supabase_auth_service import supabase_auth_service


class TestSupabaseAuthService:
    """Test the Supabase authentication service."""
    
    def test_auth_service_initialization(self):
        """Test that the auth service initializes correctly."""
        assert supabase_auth_service is not None
        assert hasattr(supabase_auth_service, 'create_user')
        assert hasattr(supabase_auth_service, 'authenticate_user')
        assert hasattr(supabase_auth_service, 'validate_token')
        assert hasattr(supabase_auth_service, 'get_user_by_id')
    
    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Test successful user creation."""
        # Mock the Supabase client
        mock_client = Mock()
        mock_auth_response = Mock()
        mock_auth_response.user = Mock()
        mock_auth_response.user.id = "test-user-id"
        mock_auth_response.user.email = "test@example.com"
        mock_auth_response.user.user_metadata = {"name": "Test User"}
        
        mock_client.auth.admin.create_user.return_value = mock_auth_response
        
        with patch.object(supabase_auth_service, '_get_service_client', return_value=mock_client):
            result = await supabase_auth_service.create_user(
                email="test@example.com",
                password="testpassword",
                name="Test User"
            )
            
            assert result is not None
            assert "user" in result
            assert result["user"]["id"] == "test-user-id"
            assert result["user"]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful user authentication."""
        # Mock the Supabase client
        mock_client = Mock()
        mock_auth_response = Mock()
        mock_auth_response.user = Mock()
        mock_auth_response.user.id = "test-user-id"
        mock_auth_response.user.email = "test@example.com"
        mock_auth_response.user.user_metadata = {"name": "Test User"}
        mock_auth_response.user.email_confirmed_at = "2025-01-01T00:00:00Z"
        
        mock_session = Mock()
        mock_session.access_token = "test-access-token"
        mock_session.refresh_token = "test-refresh-token"
        mock_session.expires_at = 1234567890
        
        mock_auth_response.session = mock_session
        mock_client.auth.sign_in_with_password.return_value = mock_auth_response
        
        with patch.object(supabase_auth_service, '_get_client', return_value=mock_client):
            result = await supabase_auth_service.authenticate_user(
                email="test@example.com",
                password="testpassword"
            )
            
            assert result is not None
            assert "user" in result
            assert "session" in result
            assert result["user"]["id"] == "test-user-id"
            assert result["session"]["access_token"] == "test-access-token"
    
    def test_validate_token_success(self):
        """Test successful token validation."""
        # Mock JWT decode
        mock_payload = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "exp": 9999999999,  # Future timestamp
            "iat": 1234567890
        }
        
        with patch('jwt.decode', return_value=mock_payload):
            result = supabase_auth_service.validate_token("test-token")
            
            assert result is not None
            assert result["id"] == "test-user-id"
            assert result["email"] == "test@example.com"
    
    def test_validate_token_expired(self):
        """Test token validation with expired token."""
        # Mock JWT decode with expired token
        mock_payload = {
            "sub": "test-user-id",
            "email": "test@example.com",
            "exp": 1234567890,  # Past timestamp
            "iat": 1234567890
        }
        
        with patch('jwt.decode', return_value=mock_payload):
            result = supabase_auth_service.validate_token("test-token")
            
            assert result is None


class TestAuthAdapter:
    """Test the authentication adapter."""
    
    def test_auth_adapter_initialization(self):
        """Test that the auth adapter initializes correctly."""
        assert auth_adapter is not None
        assert auth_adapter.backend_type == "supabase"
        assert isinstance(auth_adapter.backend, SupabaseAuthBackend)
    
    @pytest.mark.asyncio
    async def test_create_user(self):
        """Test user creation through auth adapter."""
        # Mock the auth service
        mock_result = {
            "user": {"id": "test-id", "email": "test@example.com"},
            "session": {"access_token": "test-token"}
        }
        
        with patch.object(auth_adapter.backend.auth_service, 'create_user', return_value=mock_result):
            result = await auth_adapter.create_user(
                email="test@example.com",
                password="testpassword",
                name="Test User"
            )
            
            assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self):
        """Test user authentication through auth adapter."""
        # Mock the auth service
        mock_result = {
            "user": {"id": "test-id", "email": "test@example.com"},
            "session": {"access_token": "test-token"}
        }
        
        with patch.object(auth_adapter.backend.auth_service, 'authenticate_user', return_value=mock_result):
            result = await auth_adapter.authenticate_user(
                email="test@example.com",
                password="testpassword"
            )
            
            assert result == mock_result
    
    def test_validate_token(self):
        """Test token validation through auth adapter."""
        # Mock the auth service
        mock_result = {"id": "test-id", "email": "test@example.com"}
        
        with patch.object(auth_adapter.backend.auth_service, 'validate_token', return_value=mock_result):
            result = auth_adapter.validate_token("test-token")
            
            assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_get_user_info(self):
        """Test getting user info through auth adapter."""
        # Mock the auth service
        mock_result = {"id": "test-id", "email": "test@example.com", "name": "Test User"}
        
        with patch.object(auth_adapter.backend.auth_service, 'get_user_by_id', return_value=mock_result):
            result = await auth_adapter.get_user_info("test-id")
            
            assert result == mock_result


class TestAPIEndpoints:
    """Test the API endpoints with Supabase authentication."""
    
    @pytest.fixture
    def app(self):
        """Create a test FastAPI app."""
        from main import app
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create a test client."""
        return TestClient(app)
    
    def test_register_endpoint_success(self, client):
        """Test successful user registration."""
        # Mock the auth adapter
        mock_result = {
            "user": {"id": "test-id", "email": "test@example.com"},
            "session": {"access_token": "test-token"}
        }
        
        with patch.object(auth_adapter, 'create_user', return_value=mock_result):
            response = client.post("/register", json={
                "email": "test@example.com",
                "password": "testpassword",
                "name": "Test User"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user" in data
    
    def test_login_endpoint_success(self, client):
        """Test successful user login."""
        # Mock the auth adapter
        mock_result = {
            "user": {"id": "test-id", "email": "test@example.com"},
            "session": {"access_token": "test-token"}
        }
        
        with patch.object(auth_adapter, 'authenticate_user', return_value=mock_result):
            response = client.post("/login", json={
                "email": "test@example.com",
                "password": "testpassword"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "user" in data
    
    def test_me_endpoint_success(self, client):
        """Test successful user info retrieval."""
        # Mock token validation
        mock_user_data = {"id": "test-id", "email": "test@example.com"}
        
        with patch.object(auth_adapter, 'validate_token', return_value=mock_user_data):
            response = client.get("/me", headers={
                "Authorization": "Bearer test-token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert "email" in data
    
    def test_me_endpoint_invalid_token(self, client):
        """Test user info retrieval with invalid token."""
        # Mock token validation failure
        with patch.object(auth_adapter, 'validate_token', return_value=None):
            response = client.get("/me", headers={
                "Authorization": "Bearer invalid-token"
            })
            
            assert response.status_code == 401


class TestUploadPipelineAuth:
    """Test the upload pipeline authentication."""
    
    def test_upload_pipeline_auth_import(self):
        """Test that upload pipeline auth can be imported."""
        from api.upload_pipeline.auth import get_current_user, validate_jwt_token, User
        
        assert get_current_user is not None
        assert validate_jwt_token is not None
        assert User is not None
    
    def test_user_model(self):
        """Test the User model."""
        from api.upload_pipeline.auth import User
        from uuid import uuid4
        
        user_id = uuid4()
        user = User(user_id=user_id, email="test@example.com", role="user")
        
        assert user.user_id == user_id
        assert user.email == "test@example.com"
        assert user.role == "user"


class TestConfiguration:
    """Test the authentication configuration."""
    
    def test_auth_config_import(self):
        """Test that auth config can be imported."""
        from config.auth_config import get_auth_backend, is_supabase_auth, get_auth_config
        
        assert get_auth_backend is not None
        assert is_supabase_auth is not None
        assert get_auth_config is not None
    
    def test_auth_backend_default(self):
        """Test that auth backend defaults to supabase."""
        from config.auth_config import get_auth_backend
        
        # Should default to supabase
        backend = get_auth_backend()
        assert backend == "supabase"
    
    def test_is_supabase_auth(self):
        """Test that is_supabase_auth always returns True."""
        from config.auth_config import is_supabase_auth
        
        assert is_supabase_auth() == True
    
    def test_auth_config(self):
        """Test that auth config returns supabase config."""
        from config.auth_config import get_auth_config
        
        config = get_auth_config()
        assert config["description"] == "Full Supabase authentication for all environments"
        assert "Full Supabase auth integration" in config["features"]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])


