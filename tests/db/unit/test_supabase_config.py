"""Unit tests for Supabase configuration."""
import os
import pytest
from unittest.mock import patch
from db.config import SupabaseConfig

# Test constants
TEST_URL = "https://test-project.supabase.co"
TEST_ANON_KEY = "test-anon-key"
TEST_SERVICE_KEY = "test-service-key"
TEST_BUCKET = "documents"
TEST_EXPIRY = 3600

@pytest.fixture
def valid_config():
    """Create a valid Supabase configuration for testing."""
    return SupabaseConfig(
        url=TEST_URL,
        anon_key=TEST_ANON_KEY,
        service_role_key=TEST_SERVICE_KEY,
        storage_bucket=TEST_BUCKET,
        signed_url_expiry=TEST_EXPIRY
    )

class TestSupabaseConfig:
    """Test cases for Supabase configuration validation."""

    def test_valid_config_creation(self, valid_config):
        """Test creating a valid configuration."""
        assert valid_config.url == TEST_URL
        assert valid_config.anon_key == TEST_ANON_KEY
        assert valid_config.service_role_key == TEST_SERVICE_KEY
        assert valid_config.storage_bucket == TEST_BUCKET
        assert valid_config.signed_url_expiry == TEST_EXPIRY

    def test_config_from_env(self):
        """Test loading configuration from environment variables."""
        test_env = {
            'SUPABASE_URL': TEST_URL,
            'SUPABASE_ANON_KEY': TEST_ANON_KEY,
            'SUPABASE_SERVICE_ROLE_KEY': TEST_SERVICE_KEY,
            'SUPABASE_STORAGE_BUCKET': TEST_BUCKET,
            'SUPABASE_SIGNED_URL_EXPIRY': str(TEST_EXPIRY)
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            config = SupabaseConfig.from_env()
            assert config.url == TEST_URL
            assert config.anon_key == TEST_ANON_KEY
            assert config.service_role_key == TEST_SERVICE_KEY
            assert config.storage_bucket == TEST_BUCKET
            assert config.signed_url_expiry == TEST_EXPIRY

    def test_missing_env_variables(self):
        """Test handling of missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                SupabaseConfig.from_env()
            assert "Missing required environment variable" in str(exc_info.value)

    def test_invalid_url(self):
        """Test validation of invalid URLs."""
        with pytest.raises(ValueError) as exc_info:
            SupabaseConfig(
                url="not-a-url",
                anon_key=TEST_ANON_KEY,
                service_role_key=TEST_SERVICE_KEY,
                storage_bucket=TEST_BUCKET,
                signed_url_expiry=TEST_EXPIRY
            )
        assert "Invalid Supabase URL" in str(exc_info.value)

    def test_invalid_expiry(self):
        """Test validation of invalid URL expiry times."""
        with pytest.raises(ValueError) as exc_info:
            SupabaseConfig(
                url=TEST_URL,
                anon_key=TEST_ANON_KEY,
                service_role_key=TEST_SERVICE_KEY,
                storage_bucket=TEST_BUCKET,
                signed_url_expiry=-1
            )
        assert "URL expiry time must be positive" in str(exc_info.value)

    def test_empty_keys(self):
        """Test validation of empty API keys."""
        for empty_key in ['', None, '   ']:
            with pytest.raises(ValueError) as exc_info:
                SupabaseConfig(
                    url=TEST_URL,
                    anon_key=empty_key,
                    service_role_key=TEST_SERVICE_KEY,
                    storage_bucket=TEST_BUCKET,
                    signed_url_expiry=TEST_EXPIRY
                )
            assert "API keys cannot be empty" in str(exc_info.value) 