#!/usr/bin/env python3
"""
Phase 1 Simple Pipeline Test
Tests the upload pipeline using existing infrastructure
"""

import requests
import time
import json
import os
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"

def get_jwt_token():
    """Generate a test JWT token"""
    import jwt
    from uuid import uuid4
    from datetime import datetime, timedelta
    
    # Create a test user ID
    test_user_id = str(uuid4())
    
    # Token payload
    payload = {
        "sub": test_user_id,  # Subject (user ID)
        "email": "test@example.com",
        "role": "user",
        "aud": "authenticated",
        "iss": "http://localhost:54321",
        "iat": datetime.utcnow().timestamp(),
        "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp(),
    }
    
    # Use the Supabase service role key as the secret
    secret = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
    return jwt.encode(payload, secret, algorithm="HS256")

def test_api_health():
    """Test API health"""
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy: {data['status']}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def upload_test_file(file_path):
    """Upload a test file"""
    print(f"📤 Uploading {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ Test file not found: {file_path}")
        return None
    
    # Get file info
    file_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # Calculate SHA256
    import hashlib
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
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/v2/upload", json=upload_data, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return None
        
        result = response.json()
        print(f"✅ Upload initiated: {result['job_id']}")
        
        # Upload file to signed URL
        signed_url = result['signed_url']
        print(f"🔗 Signed URL: {signed_url}")
        file_headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
        
        with open(file_path, 'rb') as f:
            upload_response = requests.put(signed_url, data=f, headers=file_headers, timeout=30)
        
        if upload_response.status_code not in [200, 201]:
            print(f"❌ File upload failed: {upload_response.status_code} - {upload_response.text}")
            return None
        
        print(f"✅ File uploaded successfully")
        return result['job_id']
        
    except Exception as e:
        print(f"❌ Upload failed with exception: {e}")
        return None

def check_job_status_via_api(job_id):
    """Check job status via API"""
    try:
        token = get_jwt_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{API_BASE_URL}/api/v2/jobs/{job_id}", headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Job status check failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Job status check failed: {e}")
        return None

def wait_for_job_completion(job_id, timeout=120):
    """Wait for a job to complete"""
    print(f"⏳ Waiting for job {job_id} to complete...")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        job_status = check_job_status_via_api(job_id)
        if not job_status:
            print(f"❌ Job {job_id} not found")
            return False
        
        current_status = job_status.get('status', 'unknown')
        current_progress = job_status.get('progress', 0)
        
        if current_status != last_status:
            print(f"📊 Job status: {current_status} (progress: {current_progress}%)")
            last_status = current_status
        
        # Check if job is complete
        if current_status in ['complete', 'failed_parse', 'failed_chunking', 'failed_embedding']:
            if current_status == 'complete':
                print(f"✅ Job completed successfully!")
                return True
            else:
                print(f"❌ Job failed with status: {current_status}")
                return False
        
        time.sleep(5)
    
    print(f"⏰ Timeout waiting for job completion")
    return False

def main():
    """Run the Phase 1 test"""
    print("🚀 Starting Phase 1 Simple Pipeline Test")
    print("=" * 50)
    
    # Test API health
    if not test_api_health():
        print("❌ API health check failed, aborting test")
        return False
    
    # Test files
    test_files = [
        "test_data/simulated_insurance_document.pdf",
        "test_data/scan_classic_hmo_parsed.pdf"
    ]
    
    # Upload test files
    job_ids = []
    for file_path in test_files:
        job_id = upload_test_file(file_path)
        if job_id:
            job_ids.append(job_id)
    
    if not job_ids:
        print("❌ No files uploaded successfully")
        return False
    
    print(f"📤 Uploaded {len(job_ids)} files")
    
    # Wait for jobs to complete
    successful_jobs = []
    for job_id in job_ids:
        if wait_for_job_completion(job_id):
            successful_jobs.append(job_id)
        else:
            print(f"❌ Job {job_id} did not complete successfully")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 PHASE 1 TEST SUMMARY")
    print("=" * 50)
    print(f"📤 Files uploaded: {len(job_ids)}")
    print(f"✅ Successful jobs: {len(successful_jobs)}")
    print(f"❌ Failed jobs: {len(job_ids) - len(successful_jobs)}")
    
    if successful_jobs:
        print("\n🎉 Phase 1 test PASSED!")
        print("✅ Upload pipeline is working correctly")
        return True
    else:
        print("\n💥 Phase 1 test FAILED!")
        print("❌ Upload pipeline has issues")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
