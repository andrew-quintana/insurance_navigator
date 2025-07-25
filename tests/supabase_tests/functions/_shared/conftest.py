"""Shared test fixtures for Supabase Edge Functions."""
import os
import pytest
from typing import Dict, Any
from supabase.client import Client
from supabase import create_client

@pytest.fixture
def supabase_config() -> Dict[str, str]:
    """Get Supabase configuration."""
    return {
        "url": os.getenv("URL", ""),
        "anon_key": os.getenv("ANON_KEY", ""),
        "service_role_key": os.getenv("SERVICE_ROLE_KEY", "")
    }

@pytest.fixture
def test_user(supabase_config: Dict[str, str]) -> Dict[str, Any]:
    """Create or get test user."""
    client = create_client(
        supabase_config["url"],
        supabase_config["service_role_key"]
    )
    
    email = "test@example.com"
    password = "test-password-123"
    
    # Try to sign up first (may fail if user exists)
    try:
        auth = client.auth.sign_up({
            "email": email,
            "password": password
        })
        if auth.user:
            return {
                "user": auth.user,
                "token": auth.session.access_token,
                "user_id": auth.user.id
            }
    except Exception:
        pass
        
    # If signup fails, try to sign in
    auth = client.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    
    return {
        "user": auth.user,
        "token": auth.session.access_token,
        "user_id": auth.user.id
    }