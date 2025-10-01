#!/usr/bin/env python3
"""
Test the storage workaround to bypass RLS policy issues
"""

import httpx
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env.staging
load_dotenv('.env.staging')

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://dfgzeastcxnoqshgyotp.supabase.co")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

async def test_storage_workaround():
    """Test direct file access workaround"""
    print("🔧 Testing Storage Workaround - Direct File Access")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    print(f"Service Role Key Present: {bool(SUPABASE_SERVICE_ROLE_KEY)}")

    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
    }

    async with httpx.AsyncClient() as client:
        # Test 1: Direct file access (this is what blob_exists uses)
        print("\n=== Test 1: Direct File Access ===")
        test_file_path = "files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/af10bedc_5e4390c2.pdf"
        response = await client.get(f"{SUPABASE_URL}/storage/v1/object/{test_file_path}", headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
        if response.status_code == 200:
            print("✅ Direct file access works!")
        else:
            print(f"❌ Direct file access failed: {response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]}")

        # Test 2: Different file path structure
        print("\n=== Test 2: Different File Path Structure ===")
        simple_path = "files/test.pdf"
        response = await client.get(f"{SUPABASE_URL}/storage/v1/object/{simple_path}", headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Simple path works!")
        else:
            print(f"❌ Simple path failed: {response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]}")

        # Test 3: Check if it's a path encoding issue
        print("\n=== Test 3: Path Encoding Test ===")
        # Try with URL encoding
        import urllib.parse
        encoded_path = urllib.parse.quote(test_file_path, safe='/')
        response = await client.get(f"{SUPABASE_URL}/storage/v1/object/{encoded_path}", headers=headers)
        print(f"Encoded path: {encoded_path}")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ URL encoded path works!")
        else:
            print(f"❌ URL encoded path failed: {response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_storage_workaround())