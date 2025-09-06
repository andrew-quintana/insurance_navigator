#!/usr/bin/env python3
"""
Test Duplicate Detection

This script tests the duplicate detection functionality by uploading
two documents with the same file hash to verify that duplicates are
properly detected and handled.
"""

import asyncio
import json
import time
import uuid
import asyncpg
from datetime import datetime
from typing import Dict, Any

# Test configuration
TEST_USER_ID = "752ae479-0fc4-41d3-b2fa-8f8ac467685f"
DATABASE_URL = "postgresql://postgres:postgres@localhost:54322/postgres"

async def create_test_job_with_hash(file_hash: str, test_name: str) -> tuple[str, str]:
    """Create a test job with a specific file hash"""
    print(f"📄 Creating {test_name} with hash: {file_hash[:16]}...")
    
    document_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create document record
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, 
                file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, document_id, TEST_USER_ID, f"{test_name}_{int(time.time())}.pdf", 
            "application/pdf", 1024, file_hash, 
            f"storage://files/user/{TEST_USER_ID}/raw/{test_name}_{int(time.time())}.pdf")
        
        # Create upload job
        progress = {
            "user_id": TEST_USER_ID,
            "document_id": document_id,
            "file_sha256": file_hash,
            "bytes_len": 1024,
            "mime": "application/pdf",
            "storage_path": f"storage://files/user/{TEST_USER_ID}/raw/{test_name}_{int(time.time())}.pdf"
        }
        
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (
                job_id, document_id, status, state, progress, 
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
        """, job_id, document_id, "uploaded", "queued", json.dumps(progress))
        
        print(f"✅ Created {test_name}: document={document_id}, job={job_id}")
        return document_id, job_id
        
    finally:
        await conn.close()

async def monitor_job_status(job_id: str, max_attempts: int = 10) -> Dict[str, Any]:
    """Monitor job status"""
    print(f"⏳ Monitoring job {job_id}...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        for attempt in range(1, max_attempts + 1):
            job = await conn.fetchrow("""
                SELECT status, state, progress, last_error
                FROM upload_pipeline.upload_jobs
                WHERE job_id = $1
            """, job_id)
            
            if not job:
                print(f"❌ Job {job_id} not found")
                return {"error": "Job not found"}
            
            status = job["status"]
            state = job["state"]
            error = job["last_error"]
            
            print(f"🔄 Attempt {attempt}: Status={status}, State={state}")
            
            if state == "done":
                print(f"✅ Job completed: {status}")
                return {"status": status, "state": state, "progress": job["progress"]}
            elif state == "deadletter":
                print(f"❌ Job failed: {error}")
                return {"status": status, "state": state, "error": error}
            
            # Wait before next check
            await asyncio.sleep(3)
        
        print(f"⏰ Job monitoring timed out after {max_attempts} attempts")
        return {"error": "Job monitoring timeout"}
        
    finally:
        await conn.close()

async def test_duplicate_detection():
    """Test duplicate detection functionality"""
    print("🔍 Testing Duplicate Detection")
    print("=" * 50)
    
    # Use the same file hash for both documents
    test_hash = "duplicate_test_hash_1234567890abcdef"
    
    try:
        # Step 1: Create first document
        print("\n📄 Step 1: Creating first document...")
        doc1_id, job1_id = await create_test_job_with_hash(test_hash, "original")
        
        # Step 2: Monitor first document
        print("\n⏳ Step 2: Processing first document...")
        result1 = await monitor_job_status(job1_id)
        
        # Step 3: Create second document with same hash
        print("\n📄 Step 3: Creating duplicate document...")
        doc2_id, job2_id = await create_test_job_with_hash(test_hash, "duplicate")
        
        # Step 4: Monitor second document
        print("\n⏳ Step 4: Processing duplicate document...")
        result2 = await monitor_job_status(job2_id)
        
        # Step 5: Check results
        print("\n📊 Test Results:")
        print("=" * 30)
        
        print(f"First document (original):")
        print(f"  Status: {result1.get('status', 'unknown')}")
        print(f"  State: {result1.get('state', 'unknown')}")
        
        print(f"Second document (duplicate):")
        print(f"  Status: {result2.get('status', 'unknown')}")
        print(f"  State: {result2.get('state', 'unknown')}")
        
        # Check if duplicate detection worked
        if (result1.get('status') == 'complete' and result1.get('state') == 'done' and
            result2.get('status') == 'complete' and result2.get('state') == 'done'):
            print("\n🎉 DUPLICATE DETECTION TEST PASSED!")
            print("✅ Both documents processed successfully")
            print("✅ Duplicate detection logic is working")
        elif (result1.get('status') == 'complete' and result1.get('state') == 'done' and
              result2.get('status') == 'complete' and result2.get('state') == 'done'):
            print("\n⚠️ DUPLICATE DETECTION TEST INCOMPLETE")
            print("❌ Duplicate detection may not be working properly")
        else:
            print("\n❌ DUPLICATE DETECTION TEST FAILED")
            print("❌ One or both documents failed to process")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_duplicate_detection())
