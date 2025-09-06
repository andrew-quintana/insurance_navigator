#!/usr/bin/env python3
"""
Phase 1 Real API Direct Test

This script tests the upload pipeline with real LlamaParse and OpenAI APIs
by directly inserting jobs into the database, bypassing API authentication.
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

async def create_test_job_directly() -> tuple[str, str]:
    """Create a test job directly in the database"""
    print("📄 Creating test job directly in database...")
    
    document_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    unique_hash = f"real_api_test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create document record
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, 
                file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, document_id, TEST_USER_ID, f"real_api_test_{int(time.time())}.pdf", 
            "application/pdf", 1024, unique_hash, 
            f"storage://files/user/{TEST_USER_ID}/raw/real_api_test_{int(time.time())}.pdf")
        
        # Create upload job
        progress = {
            "user_id": TEST_USER_ID,
            "document_id": document_id,
            "file_sha256": unique_hash,
            "bytes_len": 1024,
            "mime": "application/pdf",
            "storage_path": f"storage://files/user/{TEST_USER_ID}/raw/real_api_test_{int(time.time())}.pdf"
        }
        
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (
                job_id, document_id, status, state, progress, 
                created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
        """, job_id, document_id, "uploaded", "queued", json.dumps(progress))
        
        print(f"✅ Created document: {document_id}")
        print(f"✅ Created job: {job_id}")
        return document_id, job_id
        
    finally:
        await conn.close()

async def monitor_pipeline_progress(job_id: str, max_attempts: int = 30) -> Dict[str, Any]:
    """Monitor the pipeline progress by checking the database"""
    print("⏳ Monitoring pipeline progress with REAL APIs...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        for attempt in range(1, max_attempts + 1):
            # Get job status from database
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
                print("🎉 Pipeline completed successfully!")
                return {"status": status, "state": state, "progress": job["progress"]}
            elif state == "deadletter":
                print(f"❌ Pipeline failed: {error}")
                return {"status": status, "state": state, "error": error}
            
            # Wait before next check
            await asyncio.sleep(5)
        
        print(f"⏰ Pipeline monitoring timed out after {max_attempts} attempts")
        return {"error": "Pipeline monitoring timeout"}
        
    finally:
        await conn.close()

async def verify_database_records(document_id: str):
    """Verify that database records were created"""
    print("🗄️ Verifying database records...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Check document chunks
        chunk_count = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.document_chunks
            WHERE document_id = $1
        """, document_id)
        
        # Check job status
        job_status = await conn.fetchval("""
            SELECT status FROM upload_pipeline.upload_jobs
            WHERE document_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, document_id)
        
        # Check for embeddings
        embedding_count = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.document_chunks
            WHERE document_id = $1 AND embedding IS NOT NULL
        """, document_id)
        
        print(f"   Document chunks: {chunk_count}")
        print(f"   Chunks with embeddings: {embedding_count}")
        print(f"   Final job status: {job_status}")
        
        return {
            "chunks": chunk_count,
            "embeddings": embedding_count,
            "final_status": job_status
        }
        
    finally:
        await conn.close()

async def test_real_api_integration():
    """Test the complete pipeline with real APIs"""
    print("🔍 Phase 1 Real API Direct Integration Test")
    print("=" * 60)
    
    try:
        # Step 1: Create test job directly in database
        document_id, job_id = await create_test_job_directly()
        
        # Step 2: Monitor pipeline progress
        result = await monitor_pipeline_progress(job_id)
        
        # Step 3: Verify database records
        db_records = await verify_database_records(document_id)
        
        # Step 4: Report results
        print("\n📊 Final Test Results:")
        print("=" * 40)
        
        if "error" in result:
            print(f"❌ Pipeline failed: {result['error']}")
            success = False
        else:
            print("✅ Pipeline completed successfully!")
            print(f"   Final status: {result.get('status', 'unknown')}")
            print(f"   Final state: {result.get('state', 'unknown')}")
            success = True
        
        print(f"   Document chunks created: {db_records['chunks']}")
        print(f"   Chunks with embeddings: {db_records['embeddings']}")
        print(f"   Final job status: {db_records['final_status']}")
        
        if success and db_records['chunks'] > 0 and db_records['embeddings'] > 0:
            print("\n🎉 REAL API INTEGRATION TEST PASSED!")
            print("✅ LlamaParse API integration working")
            print("✅ OpenAI API integration working")
            print("✅ End-to-end pipeline with real services confirmed")
        else:
            print("\n⚠️ REAL API INTEGRATION TEST INCOMPLETE")
            print("❌ Some components may not be working with real APIs")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_real_api_integration())
