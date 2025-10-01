#!/usr/bin/env python3
"""
Test staging storage access to identify missing policies
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load staging environment variables
load_dotenv('.env.staging')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def test_staging_storage():
    """Test staging storage access to identify what policies are missing"""
    
    print("🔍 Staging Storage Access Analysis")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"Service Role Key Present: {bool(SUPABASE_SERVICE_ROLE_KEY)}")
    
    # Test 1: List buckets (should work)
    print("\n=== Test 1: List Buckets ===")
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
            print("✅ Bucket listing works!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Bucket listing failed: {response.text}")
    
    # Test 2: List objects in files bucket (this is what's failing)
    print("\n=== Test 2: List Objects in Files Bucket ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/list/files",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Object listing works!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Object listing failed: {response.text}")
            print("This is the root cause of the 400 'Bucket not found' error")
    
    # Test 3: Access specific file (this should work)
    print("\n=== Test 3: Access Specific File ===")
    file_path = "user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/a61afcc6_36d295c4.pdf"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/files/{file_path}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ File access works!")
            print(f"Content-Type: {response.headers.get('content-type')}")
        else:
            print(f"❌ File access failed: {response.text}")
    
    # Test 4: Test different API endpoints for object listing
    print("\n=== Test 4: Alternative Object Listing Endpoints ===")
    
    # Test 4a: Using query parameters
    print("\n4a. Object listing with query params:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/list",
            params={"bucket": "files"},
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Query param listing works!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Query param listing failed: {response.text}")
    
    # Test 4b: Using admin endpoint
    print("\n4b. Admin endpoint:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/admin/bucket/files/objects",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Admin endpoint works!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Admin endpoint failed: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_staging_storage())
