#!/usr/bin/env python3
"""
Phase 1 Full Pipeline Test
Tests the complete upload pipeline from upload to completion
"""

import asyncio
import json
import time
import requests
import psycopg2
from datetime import datetime
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
SUPABASE_URL = "http://localhost:54321"
SUPABASE_SERVICE_KEY = "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsg3W5XoXU8dI"
DATABASE_URL = "postgresql://postgres:postgres@localhost:54322/postgres"

# Test files
TEST_FILES = [
    "test_data/simulated_insurance_document.pdf",
    "test_data/scan_classic_hmo.pdf"
]

def get_jwt_token():
    """Generate a test JWT token"""
    import jwt
    payload = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    secret = "test-secret-key"
    return jwt.encode(payload, secret, algorithm="HS256")

def upload_file(file_path):
    """Upload a file through the API"""
    print(f"📤 Uploading {file_path}...")
    
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
        "file_size": file_size,
        "file_hash": file_hash,
        "content_type": "application/pdf"
    }
    
    response = requests.post(f"{API_BASE_URL}/api/v2/upload", json=upload_data, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return None
    
    result = response.json()
    print(f"✅ Upload initiated: {result['job_id']}")
    
    # Upload file to signed URL
    signed_url = result['signed_url']
    file_headers = {"Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
    
    with open(file_path, 'rb') as f:
        upload_response = requests.put(signed_url, data=f, headers=file_headers)
    
    if upload_response.status_code not in [200, 201]:
        print(f"❌ File upload failed: {upload_response.status_code} - {upload_response.text}")
        return None
    
    print(f"✅ File uploaded successfully")
    return result['job_id']

def check_job_status(job_id):
    """Check the status of a job"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT job_id, status, state, progress, created_at, updated_at
        FROM upload_pipeline.upload_jobs 
        WHERE job_id = %s
    """, (job_id,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        return {
            "job_id": result[0],
            "status": result[1],
            "state": result[2],
            "progress": result[3],
            "created_at": result[4],
            "updated_at": result[5]
        }
    return None

def check_document_status(document_id):
    """Check the status of a document"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT document_id, filename, file_size, file_hash, status, created_at, updated_at
        FROM upload_pipeline.documents 
        WHERE document_id = %s
    """, (document_id,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        return {
            "document_id": result[0],
            "filename": result[1],
            "file_size": result[2],
            "file_hash": result[3],
            "status": result[4],
            "created_at": result[5],
            "updated_at": result[6]
        }
    return None

def get_job_document_id(job_id):
    """Get the document ID for a job"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT document_id FROM upload_pipeline.upload_jobs WHERE job_id = %s
    """, (job_id,))
    
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    return result[0] if result else None

def wait_for_job_completion(job_id, timeout=300):
    """Wait for a job to complete or fail"""
    print(f"⏳ Waiting for job {job_id} to complete...")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        job_status = check_job_status(job_id)
        if not job_status:
            print(f"❌ Job {job_id} not found")
            return False
        
        current_status = job_status['status']
        current_state = job_status['state']
        
        if current_status != last_status:
            print(f"📊 Job status: {current_status} (state: {current_state})")
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

def check_pipeline_artifacts(job_id):
    """Check what artifacts were created during pipeline processing"""
    print(f"🔍 Checking pipeline artifacts for job {job_id}...")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Get job details
    cur.execute("""
        SELECT job_id, document_id, status, state, progress
        FROM upload_pipeline.upload_jobs 
        WHERE job_id = %s
    """, (job_id,))
    
    job = cur.fetchone()
    if not job:
        print("❌ Job not found")
        return
    
    document_id = job[1]
    status = job[2]
    progress = job[4] if job[4] else {}
    
    print(f"📋 Job Status: {status}")
    print(f"📋 Progress: {json.dumps(progress, indent=2)}")
    
    # Check document
    cur.execute("""
        SELECT document_id, filename, file_size, file_hash, status
        FROM upload_pipeline.documents 
        WHERE document_id = %s
    """, (document_id,))
    
    doc = cur.fetchone()
    if doc:
        print(f"📄 Document: {doc[1]} ({doc[2]} bytes, status: {doc[4]})")
    
    # Check for chunks
    cur.execute("""
        SELECT COUNT(*) FROM upload_pipeline.document_chunks 
        WHERE document_id = %s
    """, (document_id,))
    
    chunk_count = cur.fetchone()[0]
    print(f"📝 Chunks created: {chunk_count}")
    
    # Check for embeddings
    cur.execute("""
        SELECT COUNT(*) FROM upload_pipeline.document_embeddings 
        WHERE document_id = %s
    """, (document_id,))
    
    embedding_count = cur.fetchone()[0]
    print(f"🧠 Embeddings created: {embedding_count}")
    
    cur.close()
    conn.close()

def main():
    """Run the full pipeline test"""
    print("🚀 Starting Phase 1 Full Pipeline Test")
    print("=" * 50)
    
    # Test API health
    print("🔍 Checking API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return
    
    # Upload test files
    job_ids = []
    for file_path in TEST_FILES:
        if not os.path.exists(file_path):
            print(f"❌ Test file not found: {file_path}")
            continue
        
        job_id = upload_file(file_path)
        if job_id:
            job_ids.append(job_id)
    
    if not job_ids:
        print("❌ No files uploaded successfully")
        return
    
    print(f"📤 Uploaded {len(job_ids)} files")
    
    # Wait for jobs to complete
    successful_jobs = []
    for job_id in job_ids:
        if wait_for_job_completion(job_id):
            successful_jobs.append(job_id)
            check_pipeline_artifacts(job_id)
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
    else:
        print("\n💥 Phase 1 test FAILED!")
        print("❌ Upload pipeline has issues")

if __name__ == "__main__":
    main()

