#!/usr/bin/env python3
"""
Phase 1 Test Jobs - Create jobs for existing documents and add second document.
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime

async def create_test_jobs():
    """Create jobs for existing documents and add second document."""
    
    # Connect to Supabase database
    conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:54322/postgres")
    
    try:
        # Test user ID
        user_id = "766e8693-7fd5-465e-9ee4-4a9b3a696480"
        
        # Get existing document
        doc1 = await conn.fetchrow("""
            SELECT document_id, filename FROM upload_pipeline.documents 
            WHERE filename = 'Simulated Insurance Document.pdf' 
            ORDER BY created_at DESC LIMIT 1
        """)
        
        if doc1:
            doc1_id = doc1['document_id']
            print(f"Found existing document 1: {doc1_id}")
            
            # Create job for document 1
            job1_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO upload_pipeline.upload_jobs (
                    job_id, document_id, status, state, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, NOW(), NOW())
            """, job1_id, doc1_id, "uploaded", "queued")
            print(f"Created job 1: {job1_id}")
        
        # Create document 2: Scan Classic HMO.pdf
        doc2_id = str(uuid.uuid4())
        job2_id = str(uuid.uuid4())
        
        print(f"Creating document 2: {doc2_id}")
        
        # Insert document 2
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, doc2_id, user_id, "Scan Classic HMO.pdf", "application/pdf", 2544678, 
            "8df483896c19e6d1e20d627b19838da4e7d911cd90afad64cf5098138e50afe5",
            "files/user/766e8693-7fd5-465e-9ee4-4a9b3a696480/raw/04d067ab_c67cd788.pdf")
        
        # Insert job 2
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (
                job_id, document_id, status, state, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, NOW(), NOW())
        """, job2_id, doc2_id, "uploaded", "queued")
        
        print(f"Created job 2: {job2_id}")
        
        print("✅ Test jobs created successfully!")
        
        # Show all jobs
        jobs = await conn.fetch("""
            SELECT job_id, document_id, status, state, created_at 
            FROM upload_pipeline.upload_jobs 
            ORDER BY created_at DESC
        """)
        
        print("\nAll jobs:")
        for job in jobs:
            print(f"  Job {job['job_id']}: {job['status']} ({job['state']})")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_jobs())

