#!/usr/bin/env python3
"""
FM-027 Final Root Cause Test
Test the specific header combination that fails
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

async def test_api_key_only():
    """Test the specific failing case: API Key Only"""
    load_dotenv('.env.staging')
    
    base_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    test_file_path = "user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/c04117ab_5e4390c2.pdf"
    
    url = f"{base_url}/storage/v1/object/files/{test_file_path}"
    
    # Test 1: API Key Only (fails with 400)
    print("🧪 Testing API Key Only (Expected to fail with 400)")
    headers = {"apikey": service_role_key}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.head(url, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        if response.text:
            print(f"   Response: {response.text[:200]}")
    
    # Test 2: Authorization Only (should work)
    print("\n🧪 Testing Authorization Only (Expected to work)")
    headers = {"Authorization": f"Bearer {service_role_key}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.head(url, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
    
    # Test 3: Both headers (should work)
    print("\n🧪 Testing Both Headers (Expected to work)")
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.head(url, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")

if __name__ == "__main__":
    asyncio.run(test_api_key_only())
