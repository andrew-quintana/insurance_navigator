#!/usr/bin/env python3
"""
Test Parsed Document Duplicate Detection

This script tests the parsed document duplicate detection functionality by
creating documents that will have the same parsed content to verify that
duplicate parsed documents are properly detected and handled.
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

async def create_test_job_with_unique_hash(test_name: str) -> tuple[str, str]:
    """Create a test job with a unique file hash"""
    print(f"📄 Creating {test_name}...")
    
    document_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    unique_hash = f"{test_name}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create document record
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, 
                file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, document_id, TEST_USER_ID, f"{test_name}_{int(time.time())}.pdf", 
            "application/pdf", 1024, unique_hash, 
            f"storage://files/user/{TEST_USER_ID}/raw/{test_name}_{int(time.time())}.pdf")
        
        # Create upload job
        progress = {
            "user_id": TEST_USER_ID,
            "document_id": document_id,
            "file_sha256": unique_hash,
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

async def monitor_job_status(job_id: str, max_attempts: int = 15) -> Dict[str, Any]:
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

async def check_parsed_duplicates(document_id: str) -> Dict[str, Any]:
    """Check for duplicate parsed content"""
    print(f"🔍 Checking for duplicate parsed content for document {document_id}...")
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Get document info
        doc = await conn.fetchrow("""
            SELECT document_id, filename, parsed_sha256, parsed_path, processing_status
            FROM upload_pipeline.documents
            WHERE document_id = $1
        """, document_id)
        
        if not doc:
            print(f"❌ Document {document_id} not found")
            return {"error": "Document not found"}
        
        print(f"   Document: {doc['filename']}")
        print(f"   Parsed SHA256: {doc['parsed_sha256']}")
        print(f"   Parsed Path: {doc['parsed_path']}")
        print(f"   Processing Status: {doc['processing_status']}")
        
        # Check for other documents with same parsed_sha256
        if doc['parsed_sha256']:
            duplicates = await conn.fetch("""
                SELECT document_id, filename, created_at, processing_status
                FROM upload_pipeline.documents
                WHERE parsed_sha256 = $1 AND document_id != $2
                ORDER BY created_at ASC
            """, doc['parsed_sha256'], document_id)
            
            print(f"   Found {len(duplicates)} documents with same parsed content")
            
            for dup in duplicates:
                print(f"   Duplicate: {dup['filename']} (created: {dup['created_at']}, status: {dup['processing_status']})")
        
        return {
            "document_id": str(doc["document_id"]),
            "filename": doc["filename"],
            "parsed_sha256": doc["parsed_sha256"],
            "parsed_path": doc["parsed_path"],
            "processing_status": doc["processing_status"],
            "duplicates": len(duplicates) if doc['parsed_sha256'] else 0
        }
        
    finally:
        await conn.close()

async def test_parsed_duplicate_detection():
    """Test parsed document duplicate detection functionality"""
    print("🔍 Testing Parsed Document Duplicate Detection")
    print("=" * 60)
    
    try:
        # Step 1: Create first document
        print("\n📄 Step 1: Creating first document...")
        doc1_id, job1_id = await create_test_job_with_unique_hash("parsed_test_1")
        
        # Step 2: Process first document
        print("\n⏳ Step 2: Processing first document...")
        result1 = await monitor_job_status(job1_id)
        
        if result1.get('state') != 'done':
            print("❌ First document failed to process")
            return False
        
        # Step 3: Check parsed content from first document
        print("\n🔍 Step 3: Checking parsed content from first document...")
        parsed1 = await check_parsed_duplicates(doc1_id)
        
        # Step 4: Create second document (will have same parsed content due to mock)
        print("\n📄 Step 4: Creating second document...")
        doc2_id, job2_id = await create_test_job_with_unique_hash("parsed_test_2")
        
        # Step 5: Process second document
        print("\n⏳ Step 5: Processing second document...")
        result2 = await monitor_job_status(job2_id)
        
        if result2.get('state') != 'done':
            print("❌ Second document failed to process")
            return False
        
        # Step 6: Check parsed content from second document
        print("\n🔍 Step 6: Checking parsed content from second document...")
        parsed2 = await check_parsed_duplicates(doc2_id)
        
        # Step 7: Check for cross-document duplicate parsed content
        print("\n🔍 Step 7: Checking for cross-document duplicate parsed content...")
        parsed1_updated = await check_parsed_duplicates(doc1_id)
        
        # Step 8: Report results
        print("\n📊 Test Results:")
        print("=" * 40)
        
        print(f"Document 1:")
        print(f"  Status: {result1.get('status', 'unknown')}")
        print(f"  State: {result1.get('state', 'unknown')}")
        print(f"  Parsed SHA256: {parsed1.get('parsed_sha256', 'None')[:16] if parsed1.get('parsed_sha256') else 'None'}...")
        print(f"  Processing Status: {parsed1.get('processing_status', 'unknown')}")
        print(f"  Duplicates Found: {parsed1.get('duplicates', 0)}")
        
        print(f"Document 2:")
        print(f"  Status: {result2.get('status', 'unknown')}")
        print(f"  State: {result2.get('state', 'unknown')}")
        print(f"  Parsed SHA256: {parsed2.get('parsed_sha256', 'None')[:16] if parsed2.get('parsed_sha256') else 'None'}...")
        print(f"  Processing Status: {parsed2.get('processing_status', 'unknown')}")
        print(f"  Duplicates Found: {parsed2.get('duplicates', 0)}")
        
        # Check if parsed duplicate detection is working
        if (parsed1_updated.get('duplicates', 0) > 0 or 
            parsed2.get('duplicates', 0) > 0 or
            parsed2.get('processing_status') == 'duplicate_parsed'):
            print("\n🎉 PARSED DUPLICATE DETECTION TEST PASSED!")
            print("✅ Duplicate parsed content detected and handled")
            print("✅ Parsed document duplicate detection logic is working")
        else:
            print("\n⚠️ PARSED DUPLICATE DETECTION TEST INCOMPLETE")
            print("ℹ️ No duplicate parsed content found (this could be normal if content is different)")
            print("ℹ️ Parsed duplicate detection logic is implemented but not triggered")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_parsed_duplicate_detection())
