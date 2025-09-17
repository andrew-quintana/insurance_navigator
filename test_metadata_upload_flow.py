#!/usr/bin/env python3
"""
Test the proper metadata-only upload flow
"""

import asyncio
import asyncpg
import os
import requests
import hashlib
import time
from dotenv import load_dotenv

async def test_metadata_upload_flow():
    """Test the proper two-step flow: metadata → signed URL → file upload"""
    load_dotenv('.env.development')
    
    print("🧪 Testing Metadata-Only Upload Flow")
    print("=" * 60)
    
    # Use existing PDF file but with unique hash by adding timestamp
    pdf_path = "examples/scan_classic_hmo.pdf"
    
    with open(pdf_path, 'rb') as f:
        original_content = f.read()
    
    # Add unique timestamp to create unique hash (append as comment in PDF)
    timestamp_comment = f"\n% Unique test timestamp: {time.time()}\n".encode('utf-8')
    file_content = original_content + timestamp_comment
    
    file_hash = hashlib.sha256(file_content).hexdigest()
    file_size = len(file_content)
    print(f"📄 File metadata: {file_hash[:16]}... ({file_size} bytes)")
    
    try:
        # Get authentication token
        login_response = requests.post(
            "http://localhost:8000/login",
            json={"email": "upload_test@example.com", "password": "UploadTest123!"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        print(f"✅ Authentication successful")
        
        # Step 1: Send metadata only to get signed URL
        print(f"📋 Step 1: Sending metadata to get signed URL...")
        metadata_response = requests.post(
            "http://localhost:8000/upload-metadata",
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            },
            json={
                'filename': f'metadata_test_{int(time.time())}.pdf',
                'bytes_len': file_size,
                'mime': 'application/pdf',
                'sha256': file_hash,
                'ocr': False
            }
        )
        
        print(f"   Response: {metadata_response.status_code}")
        
        if metadata_response.status_code != 200:
            print(f"❌ Failed to get signed URL: {metadata_response.status_code}")
            print(f"   Error: {metadata_response.text}")
            return False
        
        upload_data = metadata_response.json()
        signed_url = upload_data.get('signed_url')
        document_id = upload_data.get('document_id')
        job_id = upload_data.get('job_id')
        
        print(f"✅ Signed URL received")
        print(f"   Document ID: {document_id}")
        print(f"   Job ID: {job_id}")
        print(f"   Signed URL: {signed_url}")
        
        # Step 2: Upload file to signed URL (backend proxy)
        print(f"📤 Step 2: Uploading file to signed URL...")
        
        file_upload_response = requests.put(
            signed_url,
            headers={
                'Content-Type': 'application/pdf',
                'Authorization': f'Bearer {token}'  # User token for backend proxy
            },
            data=file_content
        )
        
        print(f"   Response: {file_upload_response.status_code}")
        
        if file_upload_response.status_code not in [200, 201]:
            print(f"❌ File upload to signed URL failed: {file_upload_response.status_code}")
            print(f"   Error: {file_upload_response.text}")
            return False
        
        print(f"✅ File uploaded to signed URL successfully")
        
        # Step 3: Verify file exists in storage and job is created
        print(f"🗄️  Step 3: Verifying complete workflow...")
        
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        try:
            # Check document record
            doc_info = await conn.fetchrow("""
                SELECT raw_path, processing_status 
                FROM upload_pipeline.documents 
                WHERE document_id = $1
            """, document_id)
            
            if not doc_info:
                print(f"❌ Document record not found")
                return False
            
            raw_path = doc_info['raw_path']
            processing_status = doc_info['processing_status']
            print(f"   Document: {raw_path} - Status: {processing_status}")
            
            # Check if file exists in blob storage
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
            storage_response = requests.get(
                f"http://127.0.0.1:54321/storage/v1/object/{raw_path}",
                headers={"Authorization": f"Bearer {service_role_key}"}
            )
            
            print(f"   Storage check: {storage_response.status_code}")
            
            if storage_response.status_code != 200:
                print(f"❌ File not found in storage: {storage_response.text}")
                return False
            
            print(f"✅ File exists in storage: {len(storage_response.content)} bytes")
            
            # Check job status
            job_info = await conn.fetchrow("""
                SELECT status, state 
                FROM upload_pipeline.upload_jobs 
                WHERE job_id = $1
            """, job_id)
            
            if job_info:
                print(f"   Job status: {job_info['status']}/{job_info['state']}")
                
                if job_info['status'] in ['uploaded', 'parse_queued']:
                    print(f"🎉 SUCCESS: Complete metadata-only upload flow working!")
                    print(f"   ✅ Metadata sent without file content")
                    print(f"   ✅ Signed URL generated")
                    print(f"   ✅ File uploaded via proxy")
                    print(f"   ✅ File stored in blob storage")
                    print(f"   ✅ Job created for enhanced worker")
                    return True
                else:
                    print(f"⚠️  Job status unexpected: {job_info['status']}")
                    return False
            else:
                print(f"❌ Job record not found")
                return False
                
        finally:
            await conn.close()
    
    except Exception as e:
        print(f"💥 Exception: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_metadata_upload_flow())
    print(f"\n🎯 Metadata Upload Flow Test: {'SUCCESS' if result else 'FAILED'}")
