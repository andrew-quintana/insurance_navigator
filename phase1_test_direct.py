#!/usr/bin/env python3
"""
Phase 1 Direct Test - Create documents and jobs directly in database to test worker processing.
"""

import asyncio
import asyncpg
import uuid
from datetime import datetime

async def create_test_documents():
    """Create test documents and jobs directly in the database."""
    
    # Connect to Supabase database
    conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:54322/postgres")
    
    try:
        # Test user ID
        user_id = "766e8693-7fd5-465e-9ee4-4a9b3a696480"
        
        # Test document 1: Simulated Insurance Document.pdf
        doc1_id = str(uuid.uuid4())
        job1_id = str(uuid.uuid4())
        
        print(f"Creating document 1: {doc1_id}")
        
        # Insert document
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, doc1_id, user_id, "Simulated Insurance Document.pdf", "application/pdf", 1782, 
            "0331f3c86b9de0f8ff372c486bed5572e843c4b6d5f5502e283e1a9483f4635d",
            "files/user/766e8693-7fd5-465e-9ee4-4a9b3a696480/raw/6112f766_307def27.pdf")
        
        # Insert job
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (
                job_id, document_id, status, state, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, NOW(), NOW())
        """, job1_id, doc1_id, "uploaded", "queued")
        
        print(f"Created job 1: {job1_id}")
        
        # Test document 2: Scan Classic HMO.pdf
        doc2_id = str(uuid.uuid4())
        job2_id = str(uuid.uuid4())
        
        print(f"Creating document 2: {doc2_id}")
        
        # Insert document
        await conn.execute("""
            INSERT INTO upload_pipeline.documents (
                document_id, user_id, filename, mime, bytes_len, file_sha256, raw_path, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, NOW(), NOW())
        """, doc2_id, user_id, "Scan Classic HMO.pdf", "application/pdf", 2544678, 
            "8df483896c19e6d1e20d627b19838da4e7d911cd90afad64cf5098138e50afe5",
            "files/user/766e8693-7fd5-465e-9ee4-4a9b3a696480/raw/04d067ab_c67cd788.pdf")
        
        # Insert job
        await conn.execute("""
            INSERT INTO upload_pipeline.upload_jobs (
                job_id, document_id, status, state, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, NOW(), NOW())
        """, job2_id, doc2_id, "uploaded", "queued")
        
        print(f"Created job 2: {job2_id}")
        
        print("✅ Test documents and jobs created successfully!")
        print(f"Document 1 ID: {doc1_id}")
        print(f"Job 1 ID: {job1_id}")
        print(f"Document 2 ID: {doc2_id}")
        print(f"Job 2 ID: {job2_id}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_documents())
