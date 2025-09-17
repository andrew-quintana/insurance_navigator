#!/usr/bin/env python3
"""
Test complete pipeline with real user authentication (no hardcoded UUIDs)
"""

import asyncio
import asyncpg
import os
import requests
import hashlib
import time
from dotenv import load_dotenv

async def test_pipeline_with_auth():
    """Test complete pipeline with real user authentication"""
    load_dotenv('.env.development')
    
    print("🧪 Testing Pipeline with Real User Authentication")
    print("=" * 60)
    
    try:
        # Step 1: Register a new user (to avoid hardcoded UUIDs)
        print("👤 Step 1: Registering new test user...")
        
        test_email = f"test_user_{int(time.time())}@example.com"
        register_response = requests.post(
            "http://localhost:8000/register",
            json={
                "email": test_email,
                "password": "TestPassword123!"
            }
        )
        
        print(f"   Registration: {register_response.status_code}")
        
        if register_response.status_code not in [200, 201]:
            print(f"❌ Registration failed: {register_response.text}")
            return False
        
        # Step 2: Login with the new user
        print(f"🔐 Step 2: Logging in as new user...")
        
        login_response = requests.post(
            "http://localhost:8000/login",
            json={
                "email": test_email,
                "password": "TestPassword123!"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
        
        token = login_response.json()["access_token"]
        print(f"✅ Authentication successful with real user")
        
        # Step 3: Test upload with real user
        print(f"📤 Step 3: Testing upload with real user...")
        
        with open('examples/scan_classic_hmo.pdf', 'rb') as f:
            files = {'file': ('test_real_user.pdf', f, 'application/pdf')}
            data = {'policy_id': f'real_user_test_{int(time.time())}'}
            
            upload_response = requests.post(
                "http://localhost:8000/upload-document-backend",
                headers={'Authorization': f'Bearer {token}'},
                files=files,
                data=data
            )
        
        print(f"   Upload response: {upload_response.status_code}")
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(f"   Error: {upload_response.text}")
            return False
        
        result = upload_response.json()
        document_id = result.get('document_id')
        job_id = result.get('job_id')
        
        print(f"✅ Upload successful with real user")
        print(f"   Document ID: {document_id}")
        print(f"   Job ID: {job_id}")
        
        # Step 4: Verify database records with real user ID
        print(f"📊 Step 4: Verifying database records...")
        
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        try:
            # Check document record
            doc_info = await conn.fetchrow("""
                SELECT user_id::text, raw_path, processing_status, filename
                FROM upload_pipeline.documents 
                WHERE document_id = $1
            """, document_id)
            
            if not doc_info:
                print(f"❌ Document record not found")
                return False
            
            user_id = doc_info['user_id']
            raw_path = doc_info['raw_path']
            processing_status = doc_info['processing_status']
            filename = doc_info['filename']
            
            print(f"✅ Document record found")
            print(f"   User ID: {user_id} (no longer hardcoded!)")
            print(f"   Raw path: {raw_path}")
            print(f"   Processing status: {processing_status}")
            print(f"   Filename: {filename}")
            
            # Verify path structure uses real user ID
            if f"files/user/{user_id}/raw/" in raw_path:
                print(f"   ✅ Path uses real user ID (not hardcoded)")
            else:
                print(f"   ❌ Path structure incorrect")
            
            # Step 5: Verify file in storage
            print(f"🗄️  Step 5: Verifying file in blob storage...")
            
            service_role_key = os.getenv("SERVICE_ROLE_KEY", "")
            storage_response = requests.get(
                f"http://127.0.0.1:54321/storage/v1/object/{raw_path}",
                headers={"Authorization": f"Bearer {service_role_key}"}
            )
            
            print(f"   Storage check: {storage_response.status_code}")
            
            if storage_response.status_code == 200:
                print(f"✅ File exists in storage: {len(storage_response.content)} bytes")
                
                # Step 6: Check enhanced worker processing
                print(f"🤖 Step 6: Checking enhanced worker processing...")
                
                job_info = await conn.fetchrow("""
                    SELECT status, state, updated_at
                    FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1
                """, job_id)
                
                if job_info:
                    print(f"   Job status: {job_info['status']}/{job_info['state']}")
                    print(f"   Updated: {job_info['updated_at']}")
                    
                    if job_info['status'] == 'uploaded':
                        print(f"   🔄 Enhanced worker should process this job")
                    elif job_info['status'] == 'parse_queued':
                        print(f"   ⏳ Enhanced worker submitted to LlamaParse")
                        print(f"   📋 Next: Debug webhook for parsed file saving")
                    else:
                        print(f"   ℹ️  Job status: {job_info['status']}")
                
                return True
            else:
                print(f"❌ File not in storage: {storage_response.text}")
                return False
                
        finally:
            await conn.close()
    
    except Exception as e:
        print(f"💥 Exception: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_pipeline_with_auth())
    print(f"\n🎯 Pipeline Test with Real Auth: {'SUCCESS' if result else 'FAILED'}")
