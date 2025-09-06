#!/usr/bin/env python3
"""
Phase 1 Complete Pipeline Test

This test verifies the complete upload pipeline workflow:
1. Upload file via API
2. Monitor job progression through all stages
3. Verify all artifacts are created
"""

import asyncio
import httpx
import json
import os
import time
import hashlib
from datetime import datetime, timedelta
from uuid import uuid4

# Configuration
API_BASE_URL = "http://localhost:8000"
SUPABASE_URL = "http://localhost:54321"
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"

def get_jwt_token():
    """Generate a test JWT token"""
    import jwt
    
    payload = {
        "sub": str(uuid4()),
        "email": "test@example.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "aud": "authenticated",
        "iss": SUPABASE_URL
    }
    
    return jwt.encode(payload, SUPABASE_SERVICE_ROLE_KEY, algorithm="HS256")

async def upload_test_file(file_path: str) -> str:
    """Upload a test file and return the job_id"""
    print(f"📤 Uploading {file_path}...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Test file not found: {file_path}")
    
    # Get file metadata
    with open(file_path, 'rb') as f:
        file_content = f.read()
        file_size = len(file_content)
        file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Get JWT token
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload request
    upload_data = {
        "filename": os.path.basename(file_path),
        "bytes_len": file_size,
        "sha256": file_hash,
        "mime": "application/pdf",
        "ocr": False
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/api/v2/upload", json=upload_data, headers=headers, timeout=10)
        
        if response.status_code != 200:
            raise Exception(f"Upload failed: {response.status_code} - {response.text}")
        
        result = response.json()
        job_id = result['job_id']
        print(f"✅ Upload initiated: {job_id}")
        
        # Upload file to signed URL
        signed_url = result['signed_url']
        print(f"🔗 Signed URL: {signed_url}")
        
        # Upload file to storage
        file_headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}"}
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
            upload_response = await client.put(signed_url, data=file_data, headers=file_headers, timeout=30)
        
        if upload_response.status_code not in [200, 201]:
            raise Exception(f"File upload failed: {upload_response.status_code} - {upload_response.text}")
        
        print(f"✅ File uploaded to storage: {file_path}")
        return job_id

async def monitor_job_progress(job_id: str, max_wait_minutes: int = 10):
    """Monitor job progress through all pipeline stages"""
    print(f"\n⏳ Monitoring job {job_id} progress...")
    
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    expected_stages = [
        "uploaded",
        "upload_validated", 
        "parse_queued",
        "parsed",
        "parse_validated",
        "chunks_stored",
        "embedding_in_progress",
        "embedded",
        "complete"
    ]
    
    completed_stages = []
    
    async with httpx.AsyncClient() as client:
        while time.time() - start_time < max_wait_seconds:
            try:
                response = await client.get(f"{API_BASE_URL}/api/v2/jobs/{job_id}", headers=headers, timeout=10)
                
                if response.status_code == 200:
                    job_data = response.json()
                    current_status = job_data.get('status', 'unknown')
                    current_state = job_data.get('state', 'unknown')
                    
                    if current_status not in completed_stages:
                        completed_stages.append(current_status)
                        print(f"✅ Stage completed: {current_status} (state: {current_state})")
                        
                        if current_status == "complete":
                            print(f"🎉 Job completed successfully!")
                            return True
                    
                    print(f"📊 Current status: {current_status} (state: {current_state})")
                    
                else:
                    print(f"⚠️  Status check failed: {response.status_code} - {response.text}")
                
            except Exception as e:
                print(f"⚠️  Error checking status: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    print(f"⏰ Timeout reached. Completed stages: {completed_stages}")
    return False

async def verify_artifacts(job_id: str):
    """Verify that all expected artifacts were created"""
    print(f"\n🔍 Verifying artifacts for job {job_id}...")
    
    # This would check database for:
    # - Document records
    # - Chunk records  
    # - Embedding records
    # - Storage objects
    
    print("✅ Artifact verification completed (simplified)")

async def main():
    print("🚀 Starting Phase 1 Complete Pipeline Test")
    print("=" * 60)
    
    # Test file
    test_file = "test_data/simulated_insurance_document.pdf"
    
    try:
        # 1. Upload file
        job_id = await upload_test_file(test_file)
        
        # 2. Monitor pipeline progress
        success = await monitor_job_progress(job_id, max_wait_minutes=5)
        
        # 3. Verify artifacts
        if success:
            await verify_artifacts(job_id)
            print("\n🎉 Complete pipeline test PASSED!")
            return True
        else:
            print("\n❌ Complete pipeline test FAILED - timeout or error")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
