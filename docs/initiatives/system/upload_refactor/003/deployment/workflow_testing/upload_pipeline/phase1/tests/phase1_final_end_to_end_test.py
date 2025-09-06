#!/usr/bin/env python3
"""
Phase 1 Final End-to-End Pipeline Test

This test demonstrates the complete upload pipeline working end-to-end:
1. Creates a new document and job
2. Monitors the worker processing through all stages
3. Verifies the complete pipeline flow
"""

import asyncio
import httpx
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "752ae479-0fc4-41d3-b2fa-8f8ac467685f"

async def test_complete_pipeline():
    """Test the complete upload pipeline end-to-end"""
    print("🚀 Phase 1 Final End-to-End Pipeline Test")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Step 1: Create a new document
        print("📄 Creating new test document...")
        
        document_data = {
            "filename": f"test_pipeline_{int(time.time())}.pdf",
            "mime": "application/pdf",
            "bytes_len": 1024,
            "sha256": f"test_hash_{int(time.time())}",
            "raw_path": f"files/user/{TEST_USER_ID}/raw/test_{int(time.time())}.pdf"
        }
        
        # Create document
        doc_response = await client.post(
            f"{API_BASE_URL}/api/v2/documents",
            json=document_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        if doc_response.status_code != 201:
            print(f"❌ Failed to create document: {doc_response.status_code} - {doc_response.text}")
            return False
        
        document = doc_response.json()
        document_id = document["document_id"]
        print(f"✅ Created document: {document_id}")
        
        # Step 2: Create upload job
        print("🔧 Creating upload job...")
        
        job_data = {
            "document_id": document_id,
            "status": "uploaded",
            "state": "queued",
            "progress": {"test": True}
        }
        
        # Insert job directly into database (simulating API upload)
        import asyncpg
        conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:54322/postgres")
        
        job_id = f"test-job-{int(time.time())}"
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs 
            (job_id, document_id, status, state, progress, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
        """, job_id, document_id, "uploaded", "queued", json.dumps(job_data["progress"]))
        
        await conn.close()
        print(f"✅ Created job: {job_id}")
        
        # Step 3: Monitor job processing
        print("⏳ Monitoring job processing...")
        
        expected_stages = ["uploaded", "upload_validated", "parse_queued", "parsed", "parse_validated", "chunks_stored", "embedding_in_progress", "embedded", "complete"]
        current_stage = "uploaded"
        stage_index = 0
        
        for attempt in range(30):  # Monitor for up to 5 minutes
            try:
                # Check job status via API
                status_response = await client.get(
                    f"{API_BASE_URL}/api/v2/jobs/{job_id}",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                if status_response.status_code == 200:
                    job_status = status_response.json()
                    new_stage = job_status.get("stage", current_stage)
                    
                    if new_stage != current_stage:
                        print(f"🔄 Stage transition: {current_stage} → {new_stage}")
                        current_stage = new_stage
                        stage_index = expected_stages.index(new_stage) if new_stage in expected_stages else stage_index
                        
                        if new_stage == "complete":
                            print("🎉 Pipeline completed successfully!")
                            break
                    else:
                        print(f"⏳ Current stage: {current_stage} (attempt {attempt + 1})")
                else:
                    print(f"⚠️  Status check failed: {status_response.status_code} - {status_response.text}")
                
            except Exception as e:
                print(f"⚠️  Error checking status: {e}")
            
            await asyncio.sleep(10)  # Check every 10 seconds
        
        # Step 4: Verify final state
        print("\n📊 Final Verification:")
        print(f"   Final stage: {current_stage}")
        print(f"   Expected stages: {expected_stages}")
        print(f"   Pipeline complete: {'✅ YES' if current_stage == 'complete' else '❌ NO'}")
        
        return current_stage == "complete"

async def main():
    """Main test function"""
    try:
        success = await test_complete_pipeline()
        
        if success:
            print("\n🎉 PHASE 1 END-TO-END TEST: SUCCESS!")
            print("✅ Complete upload pipeline is working correctly")
            print("✅ All components are functioning as expected")
            print("✅ Ready for Phase 2 testing")
        else:
            print("\n❌ PHASE 1 END-TO-END TEST: FAILED")
            print("⚠️  Pipeline did not complete successfully")
            print("⚠️  Check logs for details")
        
        return success
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
