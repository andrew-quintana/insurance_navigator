#!/usr/bin/env python3
"""
Test Supabase Storage API with RLS analysis
Based on web search results about RLS policies and bucket access
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def test_storage_with_rls_analysis():
    """Test Supabase Storage API with RLS policy analysis"""
    
    print(f"🔍 Supabase Storage RLS Analysis")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"Service Role Key Present: {bool(SUPABASE_SERVICE_ROLE_KEY)}")
    
    # Test 1: List buckets (should work with service role)
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
    
    # Test 2: List objects in files bucket (this is where the issue is)
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
        print(f"Response: {response.text}")
        print(f"Headers: {dict(response.headers)}")
    
    # Test 3: Access specific file (this works)
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
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {response.headers.get('content-length')}")
        print(f"Response preview: {response.text[:100] if response.text else 'Binary content'}...")
    
    # Test 4: Test with different API endpoints
    print("\n=== Test 4: Alternative API Endpoints ===")
    
    # Test 4a: Using the objects endpoint
    print("\n4a. Using /storage/v1/object endpoint:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object",
            params={"bucket": "files"},
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test 4b: Using the admin endpoint
    print("\n4b. Using /storage/v1/admin endpoint:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/admin/bucket/files/objects",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test 5: Check if we need different headers
    print("\n=== Test 5: Different Header Combinations ===")
    
    # Test 5a: With Content-Type header
    print("\n5a. With Content-Type header:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/list/files",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test 5b: With Accept header
    print("\n5b. With Accept header:")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/list/files",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Accept": "application/json"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_storage_with_rls_analysis())
