#!/usr/bin/env python3
"""
Test API Upload
Test the API service upload endpoint to verify the fix
"""

import asyncio
import httpx
import os
import io
from dotenv import load_dotenv

# Load staging environment variables
load_dotenv('.env.staging')

async def test_api_upload():
    """Test the API service upload endpoint"""
    client = httpx.AsyncClient(timeout=30.0)
    
    api_url = "https://insurance-navigator-staging-api.onrender.com"
    
    print("🔍 TESTING API UPLOAD ENDPOINT")
    print("=" * 50)
    print(f"API URL: {api_url}")
    
    # Create a test file
    test_content = b"This is a test document for API upload testing."
    test_filename = f"test_api_upload_{int(time.time())}.pdf"
    
    # Create upload request data
    upload_request = {
        "filename": test_filename,
        "bytes_len": len(test_content),
        "mime": "application/pdf",
        "sha256": "test_sha256_hash",
        "ocr": False
    }
    
    try:
        print(f"\n📤 Testing API upload: {test_filename}")
        
        response = await client.post(
            f"{api_url}/upload-test",
            json=upload_request
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ API upload successful!")
            return True
        else:
            print("❌ API upload failed!")
            return False
            
    except Exception as e:
        print(f"❌ API upload error: {e}")
        return False
    finally:
        await client.aclose()

if __name__ == "__main__":
    import time
    success = asyncio.run(test_api_upload())
    exit(0 if success else 1)
