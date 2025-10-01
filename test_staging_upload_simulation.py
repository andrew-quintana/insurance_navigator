#!/usr/bin/env python3
"""
FM-027: Staging Upload Simulation
Test our fix by simulating a new upload in the staging environment
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime
from io import BytesIO

# Staging configuration
API_BASE_URL = "http://localhost:8000"  # Assuming local API
SUPABASE_URL = "https://dfgzeastcxnoqshgyotp.supabase.co"
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

async def test_staging_upload():
    """Test upload process in staging environment"""
    
    print("🚀 FM-027: Staging Upload Test")
    print("=" * 50)
    
    # Test data
    test_user_id = "be18f14d-4815-422f-8ebd-bfa044c33953"  # Use existing user
    test_document_id = str(uuid.uuid4())  # New document
    test_filename = "test_fm027_fix.pdf"
    
    print(f"Test User ID: {test_user_id}")
    print(f"Test Document ID: {test_document_id}")
    print(f"Test Filename: {test_filename}")
    
    # Step 1: Test our path generation
    print("\n1️⃣ PATH GENERATION TEST")
    print("-" * 40)
    
    import sys
    sys.path.append('.')
    from api.upload_pipeline.utils.upload_pipeline_utils import generate_storage_path
    
    generated_path = generate_storage_path(test_user_id, test_document_id, test_filename)
    print(f"Generated path: {generated_path}")
    
    # Test multiple calls for deterministic behavior
    paths = [generate_storage_path(test_user_id, test_document_id, test_filename) for _ in range(3)]
    unique_paths = set(paths)
    print(f"Multiple calls result: {len(unique_paths)} unique paths")
    print(f"Deterministic: {len(unique_paths) == 1}")
    
    # Step 2: Test file upload to storage
    print("\n2️⃣ STORAGE UPLOAD TEST")
    print("-" * 40)
    
    async with httpx.AsyncClient() as client:
        # Create test content
        test_content = b"This is a test file for FM-027 staging test"
        
        # Extract key from generated path
        file_key = generated_path.split('files/')[1]
        print(f"Uploading to key: {file_key}")
        
        # Upload to Supabase storage
        upload_response = await client.post(
            f"{SUPABASE_URL}/storage/v1/object/files/{file_key}",
            headers={
                "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
                "Content-Type": "application/pdf"
            },
            content=test_content
        )
        
        print(f"Upload status: {upload_response.status_code}")
        if upload_response.status_code in [200, 201, 204]:
            print("✅ File uploaded successfully")
            
            # Step 3: Verify file exists
            print("\n3️⃣ FILE VERIFICATION")
            print("-" * 40)
            
            verify_response = await client.get(
                f"{SUPABASE_URL}/storage/v1/object/files/{file_key}",
                headers={
                    "Authorization": f"Bearer {SERVICE_ROLE_KEY}"
                }
            )
            
            print(f"Verification status: {verify_response.status_code}")
            if verify_response.status_code == 200:
                print("✅ File verified - accessible with generated path")
                print(f"File size: {len(verify_response.content)} bytes")
                
                # Step 4: Test file access with our path generation
                print("\n4️⃣ PATH CONSISTENCY TEST")
                print("-" * 40)
                
                # Generate path again and test access
                new_generated_path = generate_storage_path(test_user_id, test_document_id, test_filename)
                new_file_key = new_generated_path.split('files/')[1]
                
                print(f"New generated path: {new_generated_path}")
                print(f"New file key: {new_file_key}")
                print(f"Keys match: {file_key == new_file_key}")
                
                if file_key == new_file_key:
                    print("✅ Path generation is consistent!")
                    
                    # Test access with new path
                    access_response = await client.get(
                        f"{SUPABASE_URL}/storage/v1/object/files/{new_file_key}",
                        headers={
                            "Authorization": f"Bearer {SERVICE_ROLE_KEY}"
                        }
                    )
                    
                    print(f"Access with new path status: {access_response.status_code}")
                    if access_response.status_code == 200:
                        print("✅ File accessible with regenerated path")
                        print("🎉 FIX IS WORKING CORRECTLY!")
                    else:
                        print("❌ File not accessible with regenerated path")
                else:
                    print("❌ Path generation is not consistent!")
            else:
                print(f"❌ File verification failed: {verify_response.text}")
        else:
            print(f"❌ Upload failed: {upload_response.text}")
    
    print("\n" + "=" * 50)
    print("🎯 STAGING TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_staging_upload())
