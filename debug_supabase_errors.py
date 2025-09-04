#!/usr/bin/env python3
"""
Debug script to test Supabase email sending and identify specific error modes.
"""

import asyncio
import os
import sys
from supabase import create_client
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_supabase_email_errors():
    """Test different Supabase email scenarios to identify failure modes."""
    
    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print(f"Supabase URL: {supabase_url}")
    print(f"Anon Key (first 20 chars): {supabase_anon_key[:20] if supabase_anon_key else 'None'}...")
    print(f"Service Key (first 20 chars): {supabase_service_key[:20] if supabase_service_key else 'None'}...")
    
    if not all([supabase_url, supabase_anon_key, supabase_service_key]):
        print("❌ Missing required environment variables")
        return
    
    # Test 1: Regular client signup
    print("\n=== Test 1: Regular Client Signup ===")
    try:
        client = create_client(supabase_url, supabase_anon_key)
        result = client.auth.sign_up({
            "email": "test1@example.com",
            "password": "testpassword123"
        })
        print(f"✅ Regular signup successful: {result.user.id}")
    except Exception as e:
        print(f"❌ Regular signup failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
    
    # Test 2: Service client admin create user
    print("\n=== Test 2: Service Client Admin Create User ===")
    try:
        service_client = create_client(supabase_url, supabase_service_key)
        result = service_client.auth.admin.create_user({
            "email": "test2@example.com",
            "password": "testpassword123",
            "email_confirm": True
        })
        print(f"✅ Service admin create user successful: {result.user.id}")
    except Exception as e:
        print(f"❌ Service admin create user failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
    
    # Test 3: Service client admin create user with email confirmation
    print("\n=== Test 3: Service Client Admin Create User (No Auto-confirm) ===")
    try:
        service_client = create_client(supabase_url, supabase_service_key)
        result = service_client.auth.admin.create_user({
            "email": "test3@example.com",
            "password": "testpassword123",
            "email_confirm": False
        })
        print(f"✅ Service admin create user (no auto-confirm) successful: {result.user.id}")
    except Exception as e:
        print(f"❌ Service admin create user (no auto-confirm) failed: {str(e)}")
        print(f"Error type: {type(e).__name__}")
    
    # Test 4: Check SMTP configuration
    print("\n=== Test 4: Check SMTP Configuration ===")
    try:
        service_client = create_client(supabase_url, supabase_service_key)
        # Try to get project settings to see SMTP config
        print("✅ Service client created successfully")
        print("Note: SMTP configuration is managed in Supabase dashboard")
    except Exception as e:
        print(f"❌ Service client creation failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_supabase_email_errors())
