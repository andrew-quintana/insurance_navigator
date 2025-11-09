#!/usr/bin/env python3
"""
Test script to replicate the upload failure by bypassing authentication
"""
import asyncio
import httpx
import json
import uuid
import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/Users/aq_home/1Projects/accessa/insurance_navigator')

# Test data
TEST_USER_ID = "74a635ac-4bfe-4b6e-87d2-c0f54a366fbe"
TEST_FILENAME = "simulated_insurance_document.pdf"
TEST_SHA256 = "a" * 64  # Mock SHA256
TEST_BYTES_LEN = 1024

async def test_upload_directly():
    """Test the upload functionality directly by calling the function"""
    print("🧪 Testing Upload Function Directly (Bypassing Auth)")
    print(f"📝 Test User ID: {TEST_USER_ID}")
    print(f"📄 Test Filename: {TEST_FILENAME}")
    print()
    
    try:
        # Import the upload function directly
        from api.upload_pipeline.endpoints.upload import _create_upload_job, _generate_signed_url
        from api.upload_pipeline.models import UploadRequest, JobPayloadJobValidated
        from api.upload_pipeline.database import get_database
        from config.database import get_supabase_client
        import uuid
        
        # Create test data
        job_id = uuid.uuid4()
        document_id = uuid.uuid4()
        user_id = uuid.UUID(TEST_USER_ID)
        
        payload = JobPayloadJobValidated(
            user_id=user_id,
            document_id=document_id,
            file_sha256=TEST_SHA256,
            bytes_len=TEST_BYTES_LEN,
            mime="application/pdf",
            storage_path=f"files/{TEST_USER_ID}/raw/{TEST_FILENAME}"
        )
        
        print("🚀 Testing database job creation...")
        
        # Test database job creation (this should work now with our fix)
        db = await get_database()
        await _create_upload_job(db, job_id, document_id, payload)
        print("✅ Database job creation successful!")
        
        print("🚀 Testing signed URL generation...")
        
        # Test signed URL generation (this should fail with storage auth error)
        try:
            signed_url = await _generate_signed_url(f"files/{TEST_USER_ID}/raw/{TEST_FILENAME}", 3600)
            print(f"✅ Signed URL generated: {signed_url[:100]}...")
            return False  # This shouldn't succeed
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Signed URL generation failed: {error_msg}")
            
            # Check if this is the storage authentication error we're looking for
            if "signature verification failed" in error_msg or "StorageApiError" in error_msg or "403" in error_msg:
                print("✅ SUCCESS: Replicated the Supabase storage authentication error!")
                return True
            else:
                print(f"❌ Different error: {error_msg}")
                return False
                
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
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
    print("🔬 UPLOAD FAILURE REPLICATION TEST (DIRECT FUNCTION CALL)")
    print("=" * 60)
    print()
    
    # First check if API is healthy
    is_healthy = await test_health_check()
    print()
    
    if not is_healthy:
        print("❌ API is not healthy, stopping test")
        return
    
    # Test the upload functionality directly
    success = await test_upload_directly()
    
    print()
    print("=" * 60)
    if success:
        print("✅ SUCCESS: Replicated the storage authentication error!")
    else:
        print("❌ FAILED: Could not replicate the error")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
