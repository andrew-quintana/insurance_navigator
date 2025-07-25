import pytest
from typing import Dict, Any
from supabase.client import Client
import os
from supabase import create_client
from dotenv import dotenv_values

# Load environment variables from .env.development
env_vars = dotenv_values(".env.development")
os.environ.update(env_vars)

# Map legacy .env keys to expected SUPABASE_* keys for tests
if "URL" in os.environ:
    os.environ["SUPABASE_URL"] = os.environ["URL"]
if "ANON_KEY" in os.environ:
    os.environ["SUPABASE_ANON_KEY"] = os.environ["ANON_KEY"]
if "SERVICE_ROLE_KEY" in os.environ:
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = os.environ["SERVICE_ROLE_KEY"]
if "JWT_SECRET" in os.environ:
    os.environ["SUPABASE_JWT_SECRET"] = os.environ["JWT_SECRET"]

from .config.test_config import get_base_test_config, TestConfig
# from .db.helpers import clear_test_data, test_supabase

@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Get test configuration."""
    return get_base_test_config()

# @pytest.fixture(scope="session")
# async def supabase_client(test_supabase: Client) -> Client:
#     """Get Supabase client for testing."""
#     return test_supabase

# @pytest.fixture(scope="session")
# async def anon_client(test_supabase: Client) -> Client:
#     """Get anonymous Supabase client for testing."""
#     # Assuming anon client can be derived from the test_supabase client or created similarly
#     # For now, returning the same client, but this might need adjustment based on actual anon client setup
#     return test_supabase

@pytest.fixture
def test_user_factory(test_config: TestConfig):
    """Factory fixture to create test users, optionally as admin."""
    def _create_user(is_admin: bool = False) -> Dict[str, Any]:
        client = create_client(
            test_config.supabase.url,
            test_config.supabase.service_role_key
        )

        email = f"test_{'admin' if is_admin else 'user'}_{os.urandom(4).hex()}@example.com"
        password = "test-password-123"

        # Try to sign up first
        auth = client.auth.sign_up({
            "email": email,
            "password": password
        })

        if auth.user:
            user_data = {"email": email}
            if is_admin:
                user_data["role"] = "admin" # This is for the user_metadata
            
            # Update user metadata
            client.auth.update_user({
                "data": user_data
            })
            
            return {
                "user": auth.user,
                "token": auth.session.access_token,
                "user_id": auth.user.id
            }
        else:
            # If signup fails, try to sign in (shouldn't happen with unique email)
            auth = client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if auth.user:
                user_data = {"email": email}
                if is_admin:
                    user_data["role"] = "admin"
                client.auth.update_user({
                    "data": user_data
                })
                return {
                    "user": auth.user,
                    "token": auth.session.access_token,
                    "user_id": auth.user.id
                }
            else:
                raise Exception("Failed to create or sign in test user.")

    yield _create_user

# Keep the original test_user fixture for backward compatibility, but make it a non-admin user
@pytest.fixture
def test_user(test_user_factory):
    return test_user_factory(is_admin=False)

@pytest.fixture
def admin_user(test_user_factory):
    return test_user_factory(is_admin=True)