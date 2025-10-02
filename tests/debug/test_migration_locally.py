#!/usr/bin/env python3
"""
Test the storage buckets RLS policy migration locally
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def test_storage_before_migration():
    """Test storage access before applying the migration"""
    
    print("🔍 Testing Storage Access BEFORE Migration")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    
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
        else:
            print(f"❌ Bucket listing failed: {response.text}")
    
    # Test 2: List objects in files bucket (this should fail)
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

if __name__ == "__main__":
    asyncio.run(test_storage_before_migration())
