#!/usr/bin/env python3
"""
Debug RLS policies and service role access
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def test_rls_debug():
    """Debug RLS policies and service role access"""
    
    print("🔍 RLS Policy Debug")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"Service Role Key Present: {bool(SUPABASE_SERVICE_ROLE_KEY)}")
    print(f"Service Role Key Length: {len(SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_SERVICE_ROLE_KEY else 0}")
    
    # Test 1: Check if we can access the storage API at all
    print("\n=== Test 1: Basic Storage API Access ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/bucket",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Basic storage API access works!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Basic storage API access failed: {response.text}")
    
    # Test 2: Try with different header combinations
    print("\n=== Test 2: Different Header Combinations ===")
    
    # Test 2a: Only apikey header
    print("\n2a. Only apikey header:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/files/user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/a61afcc6_36d295c4.pdf",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ apikey only works!")
        else:
            print(f"❌ apikey only failed: {response.text}")
    
    # Test 2b: Only Authorization header
    print("\n2b. Only Authorization header:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/files/user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/a61afcc6_36d295c4.pdf",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Authorization only works!")
        else:
            print(f"❌ Authorization only failed: {response.text}")
    
    # Test 3: Check if the issue is with the specific file path
    print("\n=== Test 3: Different File Paths ===")
    
    # Test 3a: Try a simpler path
    print("\n3a. Simpler path test:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/files/test.txt",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Simple path works!")
        else:
            print(f"❌ Simple path failed: {response.text}")
    
    # Test 4: Check if we can access the storage objects table directly
    print("\n=== Test 4: Direct Database Access ===")
    print("This would require a different approach - checking if the issue is with the API layer")

if __name__ == "__main__":
    asyncio.run(test_rls_debug())
