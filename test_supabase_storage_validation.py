#!/usr/bin/env python3
"""
Test Supabase Storage API to validate the "Bucket not found" error
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def test_storage_api():
    """Test Supabase Storage API to understand the error"""
    
    print(f"Testing Supabase Storage API")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"Service Role Key Present: {bool(SUPABASE_SERVICE_ROLE_KEY)}")
    print(f"Service Role Key Length: {len(SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_SERVICE_ROLE_KEY else 0}")
    
    # Test 1: List buckets
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
        print(f"Response: {response.text}")
    
    # Test 2: Test the specific failing path
    print("\n=== Test 2: Test Failing Path ===")
    failing_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/af10bedc_5e4390c2.pdf"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/{failing_path}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Headers: {dict(response.headers)}")
    
    # Test 3: Test with a known existing file
    print("\n=== Test 3: Test Known Existing File ===")
    existing_path = "files/user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/a61afcc6_36d295c4.pdf"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/{existing_path}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        print(f"Headers: {dict(response.headers)}")
    
    # Test 4: Test bucket access
    print("\n=== Test 4: Test Bucket Access ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/list/files",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_storage_api())
