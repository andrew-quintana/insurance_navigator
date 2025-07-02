"""
Tests for Supabase connection verification.
"""

import os
import pytest
from tests.db.helpers import verify_supabase_connection, get_supabase_client, SupabaseVerificationError

def test_supabase_connection_verification():
    """Test comprehensive Supabase connection verification."""
    # Get environment variables
    url = os.getenv("SUPABASE_TEST_URL") or os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_TEST_KEY") or os.getenv("SUPABASE_ANON_KEY")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    db_password = os.getenv("DB_PASSWORD", "postgres")
    
    # Skip test if environment variables are not set
    if not all([url, anon_key, service_role_key]):
        pytest.skip("Required environment variables not set")
    
    # Run verification
    success, status, message = verify_supabase_connection(
        url=url,
        anon_key=anon_key,
        service_role_key=service_role_key,
        db_password=db_password
    )
    
    # Print detailed status for debugging
    print("\nSupabase Connection Verification Results:")
    print(message)
    
    # Assert overall success
    assert success, f"Supabase connection verification failed:\n{message}"
    
    # Assert individual components
    assert status["env_vars_present"], "Environment variables check failed"
    assert status["url_valid"], "URL validation failed"
    assert status["api_anon_access"], "Anonymous API access failed"
    assert status["api_service_access"], "Service role API access failed"
    assert status["db_direct_access"], "Direct database access failed"

def test_supabase_client_creation():
    """Test Supabase client creation with both anon and service role keys."""
    # Get environment variables
    url = os.getenv("SUPABASE_TEST_URL") or os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_TEST_KEY") or os.getenv("SUPABASE_ANON_KEY")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # Skip test if environment variables are not set
    if not all([url, anon_key, service_role_key]):
        pytest.skip("Required environment variables not set")
    
    # Test anon client creation
    anon_client = get_supabase_client(url=url, key=anon_key)
    assert anon_client is not None, "Failed to create anonymous client"
    
    # Test service role client creation
    service_client = get_supabase_client(
        url=url,
        key=service_role_key,
        use_service_role=True
    )
    assert service_client is not None, "Failed to create service role client"
    
    # Test basic query with both clients
    try:
        # Anonymous client should be able to read public data
        anon_result = anon_client.table("users").select("count").execute()
        assert anon_result is not None, "Anonymous client query failed"
        
        # Service role client should be able to read all data
        service_result = service_client.table("users").select("*").execute()
        assert service_result is not None, "Service role client query failed"
    except Exception as e:
        pytest.fail(f"Client query tests failed: {str(e)}")

def test_invalid_credentials():
    """Test error handling with invalid credentials."""
    # Test verify_supabase_connection with invalid credentials
    with pytest.raises(SupabaseVerificationError) as exc_info:
        verify_supabase_connection(
            url="http://invalid-url",
            anon_key="invalid-key",
            service_role_key="invalid-service-key",
            db_password="invalid-password"
        )
    assert "Failed to access Supabase URL" in str(exc_info.value)
    
    # Test get_supabase_client with invalid credentials
    with pytest.raises(SupabaseVerificationError) as exc_info:
        get_supabase_client(
            url="http://invalid-url",
            key="invalid-key"
        )
    assert "Failed to access Supabase URL" in str(exc_info.value) 