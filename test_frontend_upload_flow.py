#!/usr/bin/env python3
"""
Test the complete frontend upload flow to ensure files are stored correctly
"""

import asyncio
import asyncpg
import os
import requests
import time
from dotenv import load_dotenv

async def test_frontend_upload_flow():
    """Test the complete frontend upload flow with file verification"""
    load_dotenv('.env.development')
    
    print("🧪 Testing Complete Frontend Upload Flow")
    print("=" * 60)
    
    try:
        # Step 1: Get authentication token
        print("🔐 Step 1: Getting authentication token...")
        login_response = requests.post(
            "http://localhost:8000/login",
            json={"email": "upload_test@example.com", "password": "UploadTest123!"}
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        print(f"✅ Authentication successful")
        
        # Step 2: Upload file via frontend endpoint (simulating frontend)
        print(f"📤 Step 2: Uploading file via frontend endpoint...")
        
        with open('examples/scan_classic_hmo.pdf', 'rb') as f:
            files = {'file': ('test_frontend_upload.pdf', f, 'application/pdf')}
            data = {'policy_id': f'frontend_test_{int(time.time())}'}
            
            upload_response = requests.post(
                "http://localhost:8000/upload-document-backend",
                headers={'Authorization': f'Bearer {token}'},
                files=files,
                data=data
            )
        
        print(f"   Response: {upload_response.status_code}")
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"   Error: {upload_response.text}")
            return False
        
        result = upload_response.json()
        document_id = result.get('document_id')
        job_id = result.get('job_id')
        
        print(f"✅ Upload successful")
        print(f"   Document ID: {document_id}")
        print(f"   Job ID: {job_id}")
        
        # Step 3: Verify database records
        print(f"📊 Step 3: Verifying database records...")
        
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        try:
            # Check document record
            doc_info = await conn.fetchrow("""
                SELECT raw_path, processing_status, filename, bytes_len, file_sha256
                FROM upload_pipeline.documents 
                WHERE document_id = $1
            """, document_id)
            
            if not doc_info:
                print(f"❌ Document record not found")
                return False
            
            raw_path = doc_info['raw_path']
            processing_status = doc_info['processing_status']
            filename = doc_info['filename']
            bytes_len = doc_info['bytes_len']
            file_sha256 = doc_info['file_sha256']
            
            print(f"✅ Document record found")
            print(f"   Filename: {filename}")
            print(f"   Raw path: {raw_path}")
            print(f"   Processing status: {processing_status}")
            print(f"   File size: {bytes_len} bytes")
            print(f"   SHA256: {file_sha256[:16]}...")
            
            # Verify path structure
            if raw_path.startswith('files/user/') and '/raw/' in raw_path:
                print(f"   ✅ Path structure correct: files/user/{{user_id}}/raw/{{filename}}")
            else:
                print(f"   ❌ Path structure incorrect: {raw_path}")
            
            # Check job record
            job_info = await conn.fetchrow("""
                SELECT status, state, created_at
                FROM upload_pipeline.upload_jobs 
                WHERE job_id = $1
            """, job_id)
            
            if job_info:
                print(f"✅ Job record found")
                print(f"   Status: {job_info['status']}")
                print(f"   State: {job_info['state']}")
                print(f"   Created: {job_info['created_at']}")
            
            # Step 4: Verify file exists in blob storage
            print(f"🗄️  Step 4: Verifying file in blob storage...")
            
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
            storage_response = requests.get(
                f"http://127.0.0.1:54321/storage/v1/object/{raw_path}",
                headers={"Authorization": f"Bearer {service_role_key}"}
            )
            
            print(f"   Storage response: {storage_response.status_code}")
            
            if storage_response.status_code == 200:
                stored_size = len(storage_response.content)
                print(f"✅ File exists in blob storage!")
                print(f"   Stored size: {stored_size} bytes")
                print(f"   Size matches database: {stored_size == bytes_len}")
                
                # Verify it's real PDF content
                if storage_response.content.startswith(b'%PDF'):
                    print(f"   ✅ Real PDF content confirmed")
                else:
                    print(f"   ❌ Not valid PDF content")
                
                # Step 5: Check if enhanced worker will process it
                print(f"🤖 Step 5: Enhanced worker processing...")
                
                if job_info['status'] == 'uploaded':
                    print(f"   ✅ Job ready for enhanced worker processing")
                    print(f"   🔄 Enhanced worker should pick this up automatically")
                    return True
                else:
                    print(f"   ℹ️  Job status: {job_info['status']} - may already be processed")
                    return True
            else:
                print(f"❌ File not found in storage")
                print(f"   Error: {storage_response.text}")
                return False
                
        finally:
            await conn.close()
    
    except Exception as e:
        print(f"💥 Exception: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_frontend_upload_flow())
    print(f"\n🎯 Frontend Upload Flow Test: {'SUCCESS' if result else 'FAILED'}")
