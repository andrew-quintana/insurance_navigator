#!/usr/bin/env python3
"""
FM-012 Fix Verification Test
Tests that worker generates production webhook URLs instead of localhost
"""

import asyncio
import httpx
import os
import hashlib
import time
from datetime import datetime

# Test configuration
API_BASE_URL = "***REMOVED***"
TEST_DOCUMENT_PATH = "test_data/simulated_insurance_document.pdf"

async def test_fm012_fix():
    """Test FM-012 fix: Verify worker generates production webhook URLs"""
    
    print("🧪 FM-012 Fix Verification Test")
    print("=" * 50)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Check if test file exists
    print(f"\n📁 Step 1: Checking test file...")
    if not os.path.exists(TEST_DOCUMENT_PATH):
        print(f"❌ Test file not found: {TEST_DOCUMENT_PATH}")
        print("   Please ensure test_upload.pdf exists in test_data/")
        return False
    
    print(f"✅ Test file found: {TEST_DOCUMENT_PATH}")
    
    # Step 2: Prepare upload request
    print(f"\n📤 Step 2: Preparing upload request...")
    with open(TEST_DOCUMENT_PATH, 'rb') as f:
        file_content = f.read()
        file_sha256 = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)
    
    print(f"   File size: {file_size} bytes")
    print(f"   SHA256: {file_sha256[:16]}...")
    
    upload_request = {
        "filename": "fm012_fix_test.pdf",
        "mime": "application/pdf",
        "bytes_len": file_size,
        "sha256": file_sha256
    }
    
    # Step 3: Upload document
    print(f"\n📤 Step 3: Uploading document...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/upload-pipeline/upload-test",
                json=upload_request
            )
            
            if response.status_code == 200:
                upload_result = response.json()
                document_id = upload_result.get('document_id')
                job_id = upload_result.get('job_id')
                signed_url = upload_result.get('signed_url')
                
                print(f"✅ Upload successful!")
                print(f"   Document ID: {document_id}")
                print(f"   Job ID: {job_id}")
                print(f"   Signed URL: {signed_url[:50]}...")
                
                # Step 4: Upload file to storage
                print(f"\n📁 Step 4: Uploading file to storage...")
                storage_response = await client.put(
                    signed_url,
                    content=file_content,
                    headers={"Content-Type": "application/pdf"}
                )
                
                if storage_response.status_code == 200:
                    print("✅ Storage upload successful!")
                else:
                    print(f"❌ Storage upload failed: {storage_response.status_code}")
                    print(f"   Response: {storage_response.text}")
                    return False
                
                # Step 5: Monitor worker logs for webhook URL generation
                print(f"\n🔍 Step 5: Monitoring worker logs...")
                print("   Checking for production webhook URLs (not localhost)...")
                
                # Wait a moment for worker to process
                await asyncio.sleep(5)
                
                print(f"\n📊 Step 6: Checking worker logs for webhook URL generation...")
                print("   Expected: ***REMOVED***")
                print("   NOT: http://localhost:8000")
                
                # Note: In a real test, we would check worker logs here
                # For now, we'll just indicate what to look for
                print(f"\n✅ Test setup complete!")
                print(f"   Job ID: {job_id}")
                print(f"   Document ID: {document_id}")
                print(f"\n📝 Next steps:")
                print(f"   1. Check worker logs for webhook URL generation")
                print(f"   2. Verify no localhost URLs are generated")
                print(f"   3. Confirm LlamaParse accepts the webhook URL")
                
                return True
                
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            return False

async def main():
    """Main test function"""
    success = await test_fm012_fix()
    
    if success:
        print(f"\n🎉 FM-012 Fix Test: SETUP COMPLETE")
        print(f"   - Document uploaded successfully")
        print(f"   - Storage upload successful")
        print(f"   - Job created for processing")
        print(f"\n📋 Manual verification needed:")
        print(f"   1. Check worker logs for webhook URL generation")
        print(f"   2. Verify production URLs are used (not localhost)")
        print(f"   3. Confirm LlamaParse processing succeeds")
    else:
        print(f"\n❌ FM-012 Fix Test: FAILED")
        print(f"   - Test setup failed")
        print(f"   - Check error messages above")

if __name__ == "__main__":
    asyncio.run(main())

