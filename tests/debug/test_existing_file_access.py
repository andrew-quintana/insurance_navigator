#!/usr/bin/env python3
"""
Test access to the file that actually exists in production
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.staging')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

async def test_existing_file_access():
    """Test access to the file that actually exists in production"""
    
    print("🔍 Testing Access to Existing File in Production")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    
    # Test with the file that actually exists in production
    file_path = "user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/a61afcc6_36d295c4.pdf"
    
    print(f"\n=== Testing File: {file_path} ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/files/{file_path}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        if response.status_code == 200:
            print("✅ File access works!")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Length: {response.headers.get('content-length')}")
            print(f"Response preview: {response.text[:100] if response.text else 'Binary content'}...")
        else:
            print(f"❌ File access failed: {response.text}")
    
    # Test the parsed file too
    parsed_file_path = "user/be18f14d-4815-422f-8ebd-bfa044c33953/parsed/d37eadde-2ea1-5a66-91d9-1d5474b6ba23.md"
    
    print(f"\n=== Testing Parsed File: {parsed_file_path} ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SUPABASE_URL}/storage/v1/object/files/{parsed_file_path}",
            headers={
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"
            }
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Parsed file access works!")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Response preview: {response.text[:200]}...")
        else:
            print(f"❌ Parsed file access failed: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_existing_file_access())
