"""
Authentication Helper for Phase 3 Testing

Provides utilities for creating and authenticating test users.
"""

import asyncio
import httpx
import logging
from typing import Dict, Any, Optional
import uuid
import time

logger = logging.getLogger(__name__)

async def create_test_user(username_prefix: str = "test_user") -> Dict[str, Any]:
    """Create a test user for validation testing."""
    timestamp = str(int(time.time()))
    test_user = {
        "email": f"{username_prefix}_{timestamp}@example.com",
        "password": "TestPassword123!",
        "name": f"Test User {timestamp}"
    }
    
    return test_user

async def authenticate_test_user(email: str, password: str, base_url: str = "http://localhost:8000") -> Optional[str]:
    """Authenticate test user and return access token."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try to register the user first (might fail if exists)
            register_response = await client.post(
                f"{base_url}/register",
                json={
                    "email": email,
                    "password": password,
                    "name": email.split("@")[0]
                }
            )
            
            # Whether registration succeeds or fails, try to login
            login_response = await client.post(
                f"{base_url}/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                return login_data.get("access_token")
            else:
                logger.error(f"Login failed: {login_response.status_code} - {login_response.text}")
                return None
                
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return None

async def validate_token(token: str, base_url: str = "http://localhost:8000") -> bool:
    """Validate an access token."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{base_url}/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return False
