#!/usr/bin/env python3
"""
Test script to verify worker job processing functionality
"""

import asyncio
import asyncpg
import json
from datetime import datetime

async def test_worker_job_processing():
    """Test worker job processing functionality"""
    print("🧪 Testing Worker Job Processing")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = await asyncpg.connect('postgresql://postgres:postgres@postgres:5432/postgres')
        print("✅ Connected to database")
        
        # Check current job state
        print("\n📊 Current Job State:")
        jobs = await conn.fetch("""
            SELECT job_id, document_id, stage, state, created_at, updated_at
            FROM upload_pipeline.upload_jobs
            ORDER BY created_at DESC
        """)
        
        for job in jobs:
            print(f"  Job {str(job['job_id'])[:8]}... - Stage: {job['stage']}, State: {job['state']}")
        
        # Check if there are any queued jobs
        queued_jobs = await conn.fetch("""
            SELECT COUNT(*) as count
            FROM upload_pipeline.upload_jobs
            WHERE stage = 'queued' AND state = 'queued'
        """)
        
        queued_count = queued_jobs[0]['count']
        print(f"\n📋 Queued Jobs: {queued_count}")
        
        if queued_count > 0:
            print("\n🔍 Testing Job Query (what worker should see):")
            
            # Test the exact query the worker uses
            test_job = await conn.fetchrow("""
                WITH next_job AS (
                    SELECT uj.job_id, uj.document_id, d.user_id, uj.stage, uj.state,
                           uj.payload, uj.retry_count, uj.last_error, uj.created_at
                    FROM upload_pipeline.upload_jobs uj
                    JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                    WHERE uj.stage IN (
                        'queued', 'job_validated', 'parsed', 'parse_validated', 'chunking', 'chunks_buffered',
                        'embedding', 'embeddings_buffered'
                    )
                    AND uj.state IN ('queued', 'working', 'retryable')
                    AND (
                        uj.last_error IS NULL 
                        OR (uj.last_error->>'retry_at')::timestamp <= now()
                    )
                    ORDER BY uj.created_at
                    LIMIT 1
                )
                SELECT * FROM next_job
            """)
            
            if test_job:
                print(f"  ✅ Found job: {str(test_job['job_id'])[:8]}...")
                print(f"     Stage: {test_job['stage']}")
                print(f"     State: {test_job['state']}")
                print(f"     Document: {str(test_job['document_id'])[:8]}...")
                
                # Test stage advancement
                print(f"\n🔄 Testing Stage Advancement:")
                print(f"  Current stage: {test_job['stage']}")
                
                if test_job['stage'] == 'queued':
                    new_stage = 'job_validated'
                    print(f"  Advancing to: {new_stage}")
                    
                    # Update the job stage
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs 
                        SET stage = $1, state = 'queued', updated_at = now()
                        WHERE job_id = $2
                    """, new_stage, test_job['job_id'])
                    
                    print(f"  ✅ Stage advanced to {new_stage}")
                    
                    # Verify the change
                    updated_job = await conn.fetchrow("""
                        SELECT stage, state, updated_at
                        FROM upload_pipeline.upload_jobs
                        WHERE job_id = $1
                    """, test_job['job_id'])
                    
                    print(f"  Verified: stage={updated_job['stage']}, state={updated_job['state']}")
                    
            else:
                print("  ❌ No jobs found matching worker criteria")
        
        # Check final state
        print(f"\n📊 Final Job State:")
        final_jobs = await conn.fetch("""
            SELECT job_id, document_id, stage, state, updated_at
            FROM upload_pipeline.upload_jobs
            ORDER BY updated_at DESC
        """)
        
        for job in final_jobs:
            print(f"  Job {str(job['job_id'])[:8]}... - Stage: {job['stage']}, State: {job['state']}")
        
        await conn.close()
        print("\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_worker_job_processing())
