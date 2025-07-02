"""Unit tests for Supabase configuration."""
import pytest
from unittest.mock import patch
from db.config import SupabaseConfig

TEST_URL = "http://localhost:54321"
TEST_SERVICE_KEY = "test_service_key"
TEST_ANON_KEY = "test_anon_key"
TEST_JWT_SECRET = "test_jwt_secret"
TEST_JWT_EXPIRY = 3600

@pytest.fixture
def valid_config():
    """Create a valid Supabase configuration."""
    return SupabaseConfig(
        url=TEST_URL,
        service_role_key=TEST_SERVICE_KEY,
        anon_key=TEST_ANON_KEY,
        jwt_secret=TEST_JWT_SECRET,
        jwt_expiry=TEST_JWT_EXPIRY
    )

def test_valid_config_creation(valid_config):
    """Test creating a valid configuration."""
    assert valid_config.url == TEST_URL
    assert valid_config.service_role_key == TEST_SERVICE_KEY
    assert valid_config.anon_key == TEST_ANON_KEY
    assert valid_config.jwt_secret == TEST_JWT_SECRET
    assert valid_config.jwt_expiry == TEST_JWT_EXPIRY

def test_config_from_env():
    """Test creating configuration from environment variables."""
    with patch.dict('os.environ', {
        'SUPABASE_DB_URL': TEST_URL,
        'SUPABASE_SERVICE_ROLE_KEY': TEST_SERVICE_KEY,
        'SUPABASE_ANON_KEY': TEST_ANON_KEY,
        'JWT_SECRET': TEST_JWT_SECRET,
        'JWT_EXPIRY': str(TEST_JWT_EXPIRY)
    }):
        config = SupabaseConfig.from_env()
        assert config.url == TEST_URL
        assert config.service_role_key == TEST_SERVICE_KEY
        assert config.anon_key == TEST_ANON_KEY
        assert config.jwt_secret == TEST_JWT_SECRET
        assert config.jwt_expiry == TEST_JWT_EXPIRY

def test_missing_env_variables():
    """Test handling missing environment variables."""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            SupabaseConfig.from_env()
        assert "SUPABASE_DB_URL environment variable is required" in str(exc_info.value)

def test_invalid_url():
    """Test handling invalid URL."""
    with pytest.raises(ValueError) as exc_info:
        SupabaseConfig(
            url="",
            service_role_key=TEST_SERVICE_KEY,
            anon_key=TEST_ANON_KEY
        )
    assert "Invalid Supabase URL" in str(exc_info.value)

def test_invalid_expiry():
    """Test handling invalid JWT expiry."""
    with pytest.raises(ValueError) as exc_info:
        SupabaseConfig(
            url=TEST_URL,
            service_role_key=TEST_SERVICE_KEY,
            anon_key=TEST_ANON_KEY,
            jwt_expiry=-1
        )
    assert "JWT expiry must be positive" in str(exc_info.value)

def test_empty_keys():
    """Test handling empty API keys."""
    with pytest.raises(ValueError) as exc_info:
        SupabaseConfig(
            url=TEST_URL,
            service_role_key="",
            anon_key=""
        )
    assert "Service role key and anon key cannot be empty" in str(exc_info.value) 