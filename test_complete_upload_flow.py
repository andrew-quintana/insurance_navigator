#!/usr/bin/env python3
"""
Test complete upload flow from file upload to processing completion.
"""

import asyncio
import httpx
import hashlib
import json
import time
from pathlib import Path

async def test_complete_upload_flow():
    """Test the complete upload flow end-to-end."""
    
    # Test file
    test_file_path = Path("test_upload_pipeline.md")
    if not test_file_path.exists():
        print("❌ Test file not found")
        return False
    
    # Read file content
    with open(test_file_path, 'r') as f:
        file_content = f.read()
    
    # Calculate file metadata
    file_sha256 = hashlib.sha256(file_content.encode()).hexdigest()
    file_size = len(file_content.encode())
    
    print(f"📄 Test file: {test_file_path}")
    print(f"📊 File size: {file_size} bytes")
    print(f"🔐 SHA256: {file_sha256[:16]}...")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Create upload job
        print("\n🔄 Step 1: Creating upload job...")
        upload_response = await client.post(
            "http://localhost:8000/api/upload-pipeline/upload-test",
            json={
                "filename": "test_upload_pipeline.pdf",
                "bytes_len": file_size,
                "mime": "application/pdf",
                "sha256": file_sha256,
                "ocr": False
            }
        )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload job creation failed: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            return False
        
        upload_data = upload_response.json()
        job_id = upload_data["job_id"]
        document_id = upload_data["document_id"]
        signed_url = upload_data["signed_url"]
        
        print(f"✅ Upload job created")
        print(f"   Job ID: {job_id}")
        print(f"   Document ID: {document_id}")
        print(f"   Signed URL: {signed_url[:50]}...")
        
        # Step 2: Upload file to storage
        print("\n🔄 Step 2: Uploading file to storage...")
        upload_file_response = await client.put(
            signed_url,
            content=file_content,
            headers={
                "Content-Type": "application/pdf",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
            }
        )
        
        if upload_file_response.status_code not in [200, 201]:
            print(f"❌ File upload failed: {upload_file_response.status_code}")
            print(f"Response: {upload_file_response.text}")
            return False
        
        print(f"✅ File uploaded successfully")
        print(f"   Response: {upload_file_response.text}")
        
        # Step 3: Monitor job processing
        print("\n🔄 Step 3: Monitoring job processing...")
        max_wait_time = 60  # 60 seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check document status
            job_status_response = await client.get(
                f"http://localhost:8000/documents/{document_id}/status"
            )
            
            if job_status_response.status_code == 200:
                doc_data = job_status_response.json()
                status = doc_data.get("status", "unknown")
                progress = doc_data.get("progress", 0)
                
                print(f"   Document status: {status}, progress: {progress}%")
                
                if status == "processed":
                    print(f"✅ Document processing completed successfully!")
                    break
                elif status == "failed":
                    print(f"❌ Document processing failed")
                    return False
            else:
                print(f"   Status check failed: {job_status_response.status_code}")
            
            await asyncio.sleep(2)
        else:
            print(f"⏰ Job processing timed out after {max_wait_time} seconds")
            return False
        
        # Step 4: Check document status
        print("\n🔄 Step 4: Checking document status...")
        doc_status_response = await client.get(
            f"http://localhost:8000/api/upload-pipeline/documents/{document_id}/status"
        )
        
        if doc_status_response.status_code == 200:
            doc_data = doc_status_response.json()
            processing_status = doc_data.get("processing_status", "unknown")
            print(f"✅ Document status: {processing_status}")
        else:
            print(f"❌ Document status check failed: {doc_status_response.status_code}")
        
        # Step 5: Verify file exists in storage
        print("\n🔄 Step 5: Verifying file exists in storage...")
        verify_response = await client.get(signed_url)
        
        if verify_response.status_code == 200:
            stored_content = verify_response.text
            if stored_content == file_content:
                print(f"✅ File verified in storage - content matches")
            else:
                print(f"⚠️ File exists but content doesn't match")
        else:
            print(f"❌ File verification failed: {verify_response.status_code}")
        
        print(f"\n🎉 Complete upload flow test completed!")
        return True

if __name__ == "__main__":
    asyncio.run(test_complete_upload_flow())
