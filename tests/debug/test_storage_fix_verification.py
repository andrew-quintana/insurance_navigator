#!/usr/bin/env python3
"""
Test the storage fix by simulating the correct API calls
Based on the RLS policy analysis
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def test_storage_fix():
    """Test storage access with the identified RLS policy requirements"""
    
    print(f"🔧 Testing Storage Fix - RLS Policy Requirements")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    
    # Test 1: Verify bucket listing works (this should work now)
    print("\n=== Test 1: List Buckets (should work) ===")
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
    
    # Test 2: Test object listing with different approaches
    print("\n=== Test 2: Object Listing Approaches ===")
    
    # Approach 2a: Direct object listing (this is what was failing)
    print("\n2a. Direct object listing:")
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
    
    # Approach 2b: Using query parameters
    print("\n2b. Object listing with query params:")
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
            print("✅ Object listing with params works!")
            print(f"Response: {response.text}")
        else:
            print(f"❌ Object listing with params failed: {response.text}")
    
    # Test 3: Test individual file access
    print("\n=== Test 3: Individual File Access ===")
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
            print(f"Content-Length: {response.headers.get('content-length')}")
        else:
            print(f"❌ File access failed: {response.text}")
    
    # Test 4: Test the specific failing file from the worker
    print("\n=== Test 4: Worker Failing File ===")
    failing_file_path = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/af10bedc_5e4390c2.pdf"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/files/{failing_file_path}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Worker failing file now works!")
        else:
            print(f"❌ Worker failing file still fails: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_storage_fix())
