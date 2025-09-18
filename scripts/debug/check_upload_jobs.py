#!/usr/bin/env python3
"""
Check upload jobs in the database.
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.production')

async def check_upload_jobs():
    """Check upload jobs in the database."""
    try:
        # Connect to database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return
            
        conn = await asyncpg.connect(database_url)
        
        print("🔍 Checking upload jobs")
        print("=" * 50)
        
        # Check upload jobs table
        jobs_query = """
        SELECT job_id, document_id, status, state, progress, created_at, updated_at
        FROM upload_pipeline.upload_jobs 
        ORDER BY created_at DESC
        LIMIT 10
        """
        
        jobs = await conn.fetch(jobs_query)
        print(f"📊 Upload jobs found: {len(jobs)}")
        
        for job in jobs:
            job_id_str = str(job['job_id'])[:8]
            doc_id_str = str(job['document_id'])[:8]
            print(f"  - Job {job_id_str}... (Doc: {doc_id_str}..., Status: {job['status']}, State: {job['state']}, Created: {job['created_at']})")
        
        # Check if there are any pending jobs
        pending_query = """
        SELECT COUNT(*) as pending_count
        FROM upload_pipeline.upload_jobs 
        WHERE status = 'uploaded' AND state = 'queued'
        """
        
        pending_result = await conn.fetchrow(pending_query)
        print(f"\n⏳ Pending jobs: {pending_result['pending_count']}")
        
        # Check if there are any failed jobs
        failed_query = """
        SELECT COUNT(*) as failed_count
        FROM upload_pipeline.upload_jobs 
        WHERE status = 'failed'
        """
        
        failed_result = await conn.fetchrow(failed_query)
        print(f"❌ Failed jobs: {failed_result['failed_count']}")
        
        # Check if there are any completed jobs
        completed_query = """
        SELECT COUNT(*) as completed_count
        FROM upload_pipeline.upload_jobs 
        WHERE status = 'completed'
        """
        
        completed_result = await conn.fetchrow(completed_query)
        print(f"✅ Completed jobs: {completed_result['completed_count']}")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error checking upload jobs: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_upload_jobs())
