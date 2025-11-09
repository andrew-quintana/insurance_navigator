#!/usr/bin/env python3
"""
Test script to replicate the upload failure locally
"""
import asyncio
import httpx
import json
import uuid
from pathlib import Path

# Test data
TEST_USER_ID = "74a635ac-4bfe-4b6e-87d2-c0f54a366fbe"
TEST_FILENAME = "simulated_insurance_document.pdf"
TEST_SHA256 = "a" * 64  # Mock SHA256
TEST_BYTES_LEN = 1024

async def test_upload_failure():
    """Test the upload endpoint to replicate the failure"""
    
    # Upload request payload
    upload_payload = {
        "filename": TEST_FILENAME,
        "bytes_len": TEST_BYTES_LEN,
        "mime": "application/pdf",
        "sha256": TEST_SHA256,
        "ocr": False
    }
    
    print("🧪 Testing Upload Failure Replication")
    print(f"📝 Test User ID: {TEST_USER_ID}")
    print(f"📄 Test Filename: {TEST_FILENAME}")
    print(f"🔗 API Endpoint: http://localhost:8000/api/upload-pipeline/upload")
    print()
    
    async with httpx.AsyncClient() as client:
        try:
            # Test upload endpoint
            print("🚀 Sending upload request...")
            response = await client.post(
                "http://localhost:8000/api/upload-pipeline/upload",
                json=upload_payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {TEST_USER_ID}"  # Mock auth
                },
                timeout=30.0
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📋 Response Headers: {dict(response.headers)}")
            
            try:
                response_json = response.json()
                print(f"📄 Response Body: {json.dumps(response_json, indent=2)}")
            except:
                print(f"📄 Response Text: {response.text}")
                
        except httpx.TimeoutException:
            print("⏰ Request timed out")
        except httpx.ConnectError:
            print("🔌 Connection error - is the API server running?")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

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
    print("🔬 UPLOAD FAILURE REPLICATION TEST")
    print("=" * 60)
    print()
    
    # First check if API is healthy
    is_healthy = await test_health_check()
    print()
    
    if not is_healthy:
        print("❌ API is not healthy, stopping test")
        return
    
    # Test the upload endpoint
    await test_upload_failure()
    
    print()
    print("=" * 60)
    print("🏁 Test completed")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
