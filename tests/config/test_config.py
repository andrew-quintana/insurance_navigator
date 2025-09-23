"""
Test configuration for unit testing.

Provides test configuration classes and utilities for consistent testing
across different environments.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class SupabaseConfig:
    """Supabase configuration for testing."""
    url: str
    anon_key: str
    service_role_key: str
    jwt_secret: str


@dataclass
class TestConfig:
    """Test configuration container."""
    supabase: SupabaseConfig
    environment: str = "test"
    debug: bool = True


def get_base_test_config() -> TestConfig:
    """Get base test configuration."""
    return TestConfig(
        supabase=SupabaseConfig(
            url=os.getenv("SUPABASE_URL", "https://test.supabase.co"),
            anon_key=os.getenv("SUPABASE_ANON_KEY", "test_anon_key"),
            service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", "test_service_key"),
            jwt_secret=os.getenv("SUPABASE_JWT_SECRET", "test_jwt_secret")
        ),
        environment="test",
        debug=True
    )
