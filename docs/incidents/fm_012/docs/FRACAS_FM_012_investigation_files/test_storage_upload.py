#!/usr/bin/env python3
"""
Test Storage Upload
Test uploading a file to storage to see the exact error
"""

import asyncio
import httpx
import os
import io
from dotenv import load_dotenv

# Load staging environment variables
load_dotenv('.env.staging')

async def test_storage_upload():
    """Test uploading a file to storage"""
    client = httpx.AsyncClient(timeout=30.0)
    
    staging_url = os.getenv("SUPABASE_URL", "https://dfgzeastcxnoqshgyotp.supabase.co")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
    
    print("🔍 TESTING STORAGE UPLOAD")
    print("=" * 50)
    print(f"Staging URL: {staging_url}")
    print(f"Service Role Key: {service_role_key[:20]}...")
    
    # Create a test file content
    test_content = b"This is a test document for storage upload testing."
    import time
    test_filename = f"test_upload_document_{int(time.time())}.txt"
    test_path = f"files/user/test-user-123/raw/{test_filename}"
    
    try:
        # Test upload
        print(f"\n📤 Uploading test file: {test_path}")
        
        response = await client.post(
            f"{staging_url}/storage/v1/object/{test_path}",
            headers={
                "Authorization": f"Bearer {service_role_key}",
                "apikey": service_role_key,
                "Content-Type": "text/plain"
            },
            content=test_content
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
        else:
            print("❌ Upload failed!")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
    
    await client.aclose()

if __name__ == "__main__":
    asyncio.run(test_storage_upload())
