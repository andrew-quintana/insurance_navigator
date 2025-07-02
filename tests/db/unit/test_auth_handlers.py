"""Unit tests for authentication handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import jwt
from datetime import datetime, timedelta
import uuid

# Import the auth handlers (adjust path as needed)
from db.services.auth_service import AuthService
from db.config import JWTConfig

@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client."""
    client = MagicMock()
    client.auth = MagicMock()
    client.auth.sign_up = AsyncMock()
    client.auth.sign_in = AsyncMock()
    client.auth.sign_out = AsyncMock()
    client.auth.get_session = AsyncMock()
    client.auth.get_user = AsyncMock()
    return client

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.users = AsyncMock()
    session.users.insert_one = AsyncMock()
    session.users.find_one = AsyncMock()
    session.users.update_one = AsyncMock()
    return session

@pytest.fixture
def jwt_config():
    """Create a test JWT configuration."""
    return JWTConfig(
        secret="test_secret",
        algorithm="HS256",
        access_token_expire_minutes=30
    )

@pytest.fixture
def auth_service(mock_db_session, mock_supabase, jwt_config):
    """Create an auth service instance with mocked dependencies."""
    with patch('db.services.auth_service.get_db_pool', return_value=mock_supabase):
        service = AuthService(jwt_config)
        return service

@pytest.fixture
def sample_user_data():
    """Create sample user registration data."""
    return {
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'full_name': 'Test User'
    }

class TestAuthService:
    """Test cases for the authentication service."""

    @pytest.mark.asyncio
    async def test_user_registration(self, auth_service, mock_supabase):
        """Test user registration."""
        # Setup
        email = "test@example.com"
        password = "Test123!"
        mock_supabase.auth.sign_up.return_value = {
            "user": {"id": "test_id", "email": email},
            "session": {"access_token": "test_token"}
        }

        # Test successful registration
        result = await auth_service.register_user(email, password)
        assert result["user"]["email"] == email
        assert result["session"]["access_token"] == "test_token"
        mock_supabase.auth.sign_up.assert_called_with({
            "email": email,
            "password": password
        })

        # Test invalid email
        with pytest.raises(ValueError) as exc_info:
            await auth_service.register_user("invalid_email", password)
        assert "Invalid email format" in str(exc_info.value)

        # Test invalid password
        with pytest.raises(ValueError) as exc_info:
            await auth_service.register_user(email, "weak")
        assert "Invalid password format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_user_login(self, auth_service, mock_supabase):
        """Test user login."""
        # Setup
        email = "test@example.com"
        password = "Test123!"
        mock_supabase.auth.sign_in.return_value = {
            "user": {"id": "test_id", "email": email},
            "session": {"access_token": "test_login_token"}
        }

        # Test successful login
        result = await auth_service.login_user(email, password)
        assert result["user"]["email"] == email
        assert result["session"]["access_token"] == "test_login_token"
        mock_supabase.auth.sign_in.assert_called_with({
            "email": email,
            "password": password
        })

        # Test login failure
        mock_supabase.auth.sign_in.side_effect = Exception("Invalid credentials")
        with pytest.raises(Exception) as exc_info:
            await auth_service.login_user(email, "wrong_password")
        assert "Invalid credentials" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_current_user(self, auth_service, mock_supabase):
        """Test getting current user."""
        # Setup
        user_id = "test_id"
        mock_token = jwt.encode(
            {"sub": user_id, "exp": datetime.utcnow() + timedelta(minutes=30)},
            auth_service.jwt_config.secret,
            algorithm=auth_service.jwt_config.algorithm
        )
        mock_supabase.auth.get_user.return_value = {
            "id": user_id,
            "email": "test@example.com"
        }

        # Test valid token
        result = await auth_service.get_current_user(mock_token)
        assert result["id"] == user_id
        mock_supabase.auth.get_user.assert_called_with(user_id)

    @pytest.mark.asyncio
    async def test_invalid_token(self, auth_service):
        """Test handling invalid token."""
        result = await auth_service.get_current_user("invalid_token")
        assert result is None

    @pytest.mark.asyncio
    async def test_expired_token(self, auth_service):
        """Test handling expired token."""
        # Create expired token
        expired_token = jwt.encode(
            {"sub": "test_id", "exp": datetime.utcnow() - timedelta(minutes=30)},
            auth_service.jwt_config.secret,
            algorithm=auth_service.jwt_config.algorithm
        )
        result = await auth_service.get_current_user(expired_token)
        assert result is None

    @pytest.mark.asyncio
    async def test_user_logout(self, auth_service, mock_supabase):
        """Test user logout."""
        # Test successful logout
        success = await auth_service.logout_user()
        assert success is True
        mock_supabase.auth.sign_out.assert_called_once()

        # Test logout failure
        mock_supabase.auth.sign_out.side_effect = Exception("Logout failed")
        success = await auth_service.logout_user()
        assert success is False

    @pytest.mark.asyncio
    async def test_password_validation(self, auth_service):
        """Test password validation."""
        # Test valid password
        email = "test@example.com"
        valid_password = "Test123!"
        assert auth_service.validate_password(valid_password) is True

        # Test invalid passwords
        invalid_passwords = [
            "short",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoSpecialChar123",  # No special character
            "NoNumber!",  # No number
            "",  # Empty
            None  # None
        ]
        for password in invalid_passwords:
            assert auth_service.validate_password(password) is False

    @pytest.mark.asyncio
    async def test_email_validation(self, auth_service):
        """Test email validation."""
        # Test valid email
        valid_email = "test@example.com"
        assert auth_service.validate_email(valid_email) is True

        # Test invalid emails
        invalid_emails = [
            "invalid_email",  # No @ symbol
            "@nodomain",  # No local part
            "no_domain@",  # No domain part
            "no_tld@domain",  # No TLD
            "",  # Empty
            None  # None
        ]
        for email in invalid_emails:
            assert auth_service.validate_email(email) is False

    @pytest.mark.asyncio
    async def test_duplicate_registration(self, auth_service, mock_supabase):
        """Test handling duplicate registration."""
        # Setup
        email = "test@example.com"
        password = "Test123!"
        mock_supabase.auth.sign_up.side_effect = Exception("User already exists")

        # Test duplicate registration
        with pytest.raises(Exception) as exc_info:
            await auth_service.register_user(email, password)
        assert "User already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_session_refresh(self, auth_service, mock_supabase):
        """Test session refresh."""
        # Setup
        mock_supabase.auth.get_session.return_value = {
            "access_token": "new_token",
            "expires_at": datetime.utcnow() + timedelta(minutes=30)
        }

        # Test successful refresh
        result = await auth_service.refresh_session()
        assert result["access_token"] == "new_token"
        mock_supabase.auth.get_session.assert_called_once()

        # Test refresh failure
        mock_supabase.auth.get_session.side_effect = Exception("Session expired")
        result = await auth_service.refresh_session()
        assert result is None 