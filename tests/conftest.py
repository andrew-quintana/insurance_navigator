import pytest
from typing import Dict, Any
from supabase.client import Client

from .config.test_config import get_base_test_config, TestConfig
from .db.helpers import get_test_client, cleanup_test_data

@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Get test configuration."""
    return get_base_test_config()

@pytest.fixture(scope="session")
def supabase_client() -> Client:
    """Get Supabase client for testing."""
    return get_test_client("service_role")

@pytest.fixture(scope="session")
def anon_client() -> Client:
    """Get anonymous Supabase client for testing."""
    return get_test_client("anon")
