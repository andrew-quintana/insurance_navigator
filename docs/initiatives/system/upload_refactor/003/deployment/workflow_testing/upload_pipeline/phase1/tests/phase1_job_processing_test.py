#!/usr/bin/env python3
"""
Phase 1 Job Processing Test
Tests the job processing pipeline with existing files in storage
"""

import requests
import time
import json
import os
from datetime import datetime
import psycopg2

# Configuration
API_BASE_URL = "http://localhost:8000"
DATABASE_URL = "postgresql://postgres:postgres@localhost:54322/postgres"

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
    secret = "${SUPABASE_JWT_TOKEN}"
    return jwt.encode(payload, secret, algorithm="HS256"), test_user_id

def create_test_jobs():
    """Create test jobs for existing files in storage"""
    print("🔧 Creating test jobs for existing files...")
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Get existing files from storage (we know they exist from the CLI)
    test_files = [
        {
            "filename": "simulated_insurance_document.pdf",
            "file_size": 1782,
            "file_hash": "0331f3c86b9de0f8ff372c486bed5572e843c4b6d5f5502e283e1a9483f4635d",
            "storage_path": "files/user/766e8693-7fd5-465e-9ee4-4a9b3a696480/raw/04d067ab_c67cd788.pdf"
        },
        {
            "filename": "scan_classic_hmo_parsed.pdf", 
            "file_size": 2544678,
            "file_hash": "8df483896c19e6d1e20d627b19838da4e7d911cd90afad64cf5098138e50afe5",
            "storage_path": "files/user/766e8693-7fd5-465e-9ee4-4a9b3a696480/raw/6112f766_307def27.pdf"
        }
    ]
    
    job_ids = []
    
    for file_info in test_files:
        # Create document record
        document_id = str(uuid4())
        user_id = "766e8693-7fd5-465e-9ee4-4a9b3a696480"  # Use existing user ID
        
        cur.execute("""
            INSERT INTO upload_pipeline.documents 
            (document_id, user_id, filename, file_size, file_hash, raw_path, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (document_id) DO NOTHING
        """, (
            document_id,
            user_id,
            file_info["filename"],
            file_info["file_size"],
            file_info["file_hash"],
            file_info["storage_path"],
            "uploaded",
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        # Create job record
        job_id = str(uuid4())
        cur.execute("""
            INSERT INTO upload_pipeline.upload_jobs
            (job_id, document_id, user_id, status, state, progress, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO NOTHING
        """, (
            job_id,
            document_id,
            user_id,
            "uploaded",
            "queued",
            json.dumps({}),
            datetime.utcnow(),
            datetime.utcnow()
        ))
        
        job_ids.append(job_id)
        print(f"✅ Created job {job_id} for {file_info['filename']}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    return job_ids

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

def wait_for_job_completion(job_id, timeout=300):
    """Wait for a job to complete"""
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
    """Run the Phase 1 job processing test"""
    print("🚀 Starting Phase 1 Job Processing Test")
    print("=" * 50)
    
    # Test API health
    print("🔍 Testing API health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy: {data['status']}")
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False
    
    # Create test jobs
    job_ids = create_test_jobs()
    
    if not job_ids:
        print("❌ No jobs created")
        return False
    
    print(f"📤 Created {len(job_ids)} jobs")
    
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
    print("📊 PHASE 1 JOB PROCESSING TEST SUMMARY")
    print("=" * 50)
    print(f"📤 Jobs created: {len(job_ids)}")
    print(f"✅ Successful jobs: {len(successful_jobs)}")
    print(f"❌ Failed jobs: {len(job_ids) - len(successful_jobs)}")
    
    if successful_jobs:
        print("\n🎉 Phase 1 job processing test PASSED!")
        print("✅ Upload pipeline job processing is working correctly")
        return True
    else:
        print("\n💥 Phase 1 job processing test FAILED!")
        print("❌ Upload pipeline job processing has issues")
        return False

if __name__ == "__main__":
    import uuid
    success = main()
    exit(0 if success else 1)

