#!/usr/bin/env python3
"""
Phase 1 Worker Pipeline Test

This test focuses on verifying the worker can process jobs through the complete pipeline
by manually creating jobs for existing files and monitoring their progression.
"""

import asyncio
import httpx
import json
import os
import time
from datetime import datetime
from uuid import uuid4

# Configuration
API_BASE_URL = "http://localhost:8000"
SUPABASE_URL = "http://localhost:54321"
SUPABASE_SERVICE_ROLE_KEY = "${SUPABASE_JWT_TOKEN}"

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

async def create_test_job_for_existing_file():
    """Create a job for an existing file to test the pipeline"""
    print("🔧 Creating test job for existing file...")
    
    # Use an existing document from the database
    # We'll create a job with status 'uploaded' to start the pipeline
    job_id = str(uuid4())
    document_id = "226ec0b0-73a4-409b-9c01-8c10222c84c5"  # From previous tests
    user_id = "766e8693-7fd5-465e-9ee4-4a9b3a696480"  # From previous tests
    
    # Connect to database and create job
    import asyncpg
    
    db_url = "postgresql://postgres:postgres@localhost:54322/postgres"
    conn = await asyncpg.connect(db_url)
    
    try:
        # Create a new job with status 'uploaded'
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (
                job_id, document_id, status, state, progress, created_at, updated_at
            ) VALUES (
                $1, $2, 'uploaded', 'queued', '{}', NOW(), NOW()
            )
        """, job_id, document_id)
        
        print(f"✅ Created job {job_id} for document {document_id}")
        return job_id
        
    finally:
        await conn.close()

async def monitor_job_progress(job_id: str, max_wait_minutes: int = 10):
    """Monitor job progress through all pipeline stages"""
    print(f"\n⏳ Monitoring job {job_id} progress...")
    
    token = get_jwt_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    expected_stages = [
        "uploaded",
        "parse_queued",
        "parsed",
        "parse_validated",
        "chunking",
        "chunks_stored",
        "embedding_queued",
        "embedding_in_progress",
        "embeddings_stored",
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

async def check_worker_logs():
    """Check worker logs for processing activity"""
    print("\n📋 Checking worker logs...")
    
    import subprocess
    result = subprocess.run(
        ["docker-compose", "logs", "enhanced-base-worker", "--tail=20"],
        capture_output=True,
        text=True
    )
    
    print("Worker logs (last 20 lines):")
    print(result.stdout)

async def main():
    print("🚀 Starting Phase 1 Worker Pipeline Test")
    print("=" * 60)
    
    try:
        # 1. Create test job
        job_id = await create_test_job_for_existing_file()
        
        # 2. Monitor pipeline progress
        success = await monitor_job_progress(job_id, max_wait_minutes=5)
        
        # 3. Check worker logs
        await check_worker_logs()
        
        if success:
            print("\n🎉 Worker pipeline test PASSED!")
            return True
        else:
            print("\n❌ Worker pipeline test FAILED - timeout or error")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
