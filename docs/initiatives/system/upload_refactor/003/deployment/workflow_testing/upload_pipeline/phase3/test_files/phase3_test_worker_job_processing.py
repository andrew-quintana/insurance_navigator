#!/usr/bin/env python3
"""
Phase 3 Test: Worker Job Processing
Test if the worker service can now process jobs successfully after fixes.
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

async def test_worker_job_processing():
    """Test if worker service can process jobs"""
    
    # Database connection
    database_url = os.getenv('POOLER_URL', 'postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require')
    
    print("🔍 Testing worker job processing...")
    print(f"📊 Database URL: {database_url[:50]}...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url, statement_cache_size=0)
        print("✅ Connected to database successfully")
        
        # Create a test document record
        document_id = str(uuid.uuid4())
        user_id = "e6114f0c-df44-41e6-a5df-33d69f95bab1"  # Existing user ID
        
        print(f"📄 Creating test document: {document_id}")
        
        # Insert document record
        file_hash = f"test_hash_{uuid.uuid4().hex[:8]}"
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, processing_status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, document_id, user_id, "test_worker_processing.pdf", "application/pdf", 1024, file_hash, "files/test/worker_test.pdf", "uploaded", datetime.utcnow(), datetime.utcnow())
        
        # Insert upload job record
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (job_id, document_id, state, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, str(uuid.uuid4()), document_id, "queued", "uploaded", datetime.utcnow(), datetime.utcnow())
        
        print("✅ Test job created successfully")
        
        # Monitor job status changes
        print("⏳ Monitoring job status changes...")
        for i in range(30):  # Monitor for 5 minutes
            result = await conn.fetchrow("""
                SELECT state, status, updated_at FROM upload_pipeline.upload_jobs 
                WHERE document_id = $1 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, document_id)
            
            if result:
                state = result['state']
                status = result['status']
                updated_at = result['updated_at']
                print(f"📊 Job state: {state}, status: {status} (updated: {updated_at})")
                
                if state != "queued":
                    print(f"🎉 Job state changed from 'queued' to '{state}'!")
                    break
            else:
                print("❌ No job found")
                break
                
            await asyncio.sleep(10)  # Check every 10 seconds
        
        # Check final status
        final_result = await conn.fetchrow("""
            SELECT state, status, updated_at FROM upload_pipeline.upload_jobs 
            WHERE document_id = $1 
            ORDER BY updated_at DESC 
            LIMIT 1
        """, document_id)
        
        if final_result:
            final_state = final_result['state']
            final_status = final_result['status']
            print(f"🏁 Final job state: {final_state}, status: {final_status}")
            
            if final_state != "queued":
                print("✅ Worker service is processing jobs successfully!")
                return True
            else:
                print("❌ Worker service is not processing jobs")
                return False
        else:
            print("❌ No job found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    success = asyncio.run(test_worker_job_processing())
    if success:
        print("\n🎉 PHASE 3 WORKER TEST: SUCCESS!")
    else:
        print("\n❌ PHASE 3 WORKER TEST: FAILED!")
