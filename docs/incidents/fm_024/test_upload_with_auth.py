#!/usr/bin/env python3
"""
Test script to replicate the upload failure with proper authentication
"""
import asyncio
import httpx
import json
import uuid
import jwt
from datetime import datetime, timedelta

# Test data
TEST_USER_ID = "74a635ac-4bfe-4b6e-87d2-c0f54a366fbe"
TEST_FILENAME = "simulated_insurance_document.pdf"
TEST_SHA256 = "a" * 64  # Mock SHA256
TEST_BYTES_LEN = 1024

# JWT secret from development environment
JWT_SECRET = "-DmnwJD8pSuFyGv00YASxZufzB4NdBYCl9FzwyFxMep_07cEPPOp_EC8Q8_iEnozziSMdAPh5gZDcrwE4MQp9A"

def create_test_jwt_token(user_id: str) -> str:
    """Create a test JWT token for local development"""
    payload = {
        "sub": user_id,
        "email": "test@example.com",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "role": "user"
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

async def test_upload_with_auth():
    """Test the upload endpoint with proper authentication"""
    
    # Create a valid JWT token
    token = create_test_jwt_token(TEST_USER_ID)
    
    # Upload request payload
    upload_payload = {
        "filename": TEST_FILENAME,
        "bytes_len": TEST_BYTES_LEN,
        "mime": "application/pdf",
        "sha256": TEST_SHA256,
        "ocr": False
    }
    
    print("🧪 Testing Upload with Authentication")
    print(f"📝 Test User ID: {TEST_USER_ID}")
    print(f"📄 Test Filename: {TEST_FILENAME}")
    print(f"🔑 JWT Token: {token[:50]}...")
    print(f"🔗 API Endpoint: http://localhost:8000/api/upload-pipeline/upload")
    print()
    
    async with httpx.AsyncClient() as client:
        try:
            # Test upload endpoint with authentication
            print("🚀 Sending authenticated upload request...")
            response = await client.post(
                "http://localhost:8000/api/upload-pipeline/upload",
                json=upload_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}"
                },
                timeout=30.0
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📋 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📄 Response Body: {json.dumps(response_json, indent=2)}")
                
                # Check if we get the storage authentication error
                if response.status_code == 500:
                    error_detail = response_json.get("detail", "")
                    if "signature verification failed" in error_detail or "StorageApiError" in error_detail:
                        print("✅ SUCCESS: Replicated the Supabase storage authentication error!")
                        return True
                    else:
                        print(f"❌ Different error: {error_detail}")
                        return False
                else:
                    print(f"ℹ️  Unexpected status code: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"📄 Response Text: {response.text}")
                print(f"❌ Error parsing response: {e}")
                return False
                
        except httpx.TimeoutException:
            print("⏰ Request timed out")
            return False
        except httpx.ConnectError:
            print("🔌 Connection error - is the API server running?")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

async def test_health_check():
    """Test health endpoint first"""
    print("🏥 Testing health endpoint...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health", timeout=10.0)
            print(f"✅ Health check: {response.status_code}")
            if response.status_code == 200:
                health_data = response.json()
                print(f"📊 Services: {health_data.get('services', {})}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("🔬 UPLOAD FAILURE REPLICATION TEST (WITH AUTH)")
    print("=" * 60)
    print()
    
    # First check if API is healthy
    is_healthy = await test_health_check()
    print()
    
    if not is_healthy:
        print("❌ API is not healthy, stopping test")
        return
    
    # Test the upload endpoint with authentication
    success = await test_upload_with_auth()
    
    print()
    print("=" * 60)
    if success:
        print("✅ SUCCESS: Replicated the storage authentication error!")
    else:
        print("❌ FAILED: Could not replicate the error")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
