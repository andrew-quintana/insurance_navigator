#!/usr/bin/env python3

import asyncio
import os
import sys
import uuid
import hashlib
from dotenv import load_dotenv
import asyncpg

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.workers.base_worker import BaseWorker
from shared.config import WorkerConfig

# Load environment variables
load_dotenv('.env.development')

# Test constants
TEST_FILE = 'examples/scan_classic_hmo.pdf'
TEST_SCHEMA = 'upload_pipeline'
TEST_USER_ID = uuid.UUID('f47ac10b-58cc-4372-a567-0e02b2c3d479')

async def create_test_document(pool, file_path, user_id):
    """Creates a test document and job starting at 'parsed' stage."""
    file_name = os.path.basename(file_path)
    storage_path = f"storage://uploads/{user_id}/{file_name}"
    parsed_path = f"storage://parsed/{user_id}/{file_name}.json"
    document_id = uuid.uuid4()
    
    # Get actual file size and compute hash
    full_path = os.path.join(project_root, file_path)
    if os.path.exists(full_path):
        file_size = os.path.getsize(full_path)
        with open(full_path, 'rb') as f:
            file_sha256 = hashlib.sha256(f.read()).hexdigest()
    else:
        file_size = 2500000  # Default size if file doesn't exist
        file_sha256 = hashlib.sha256(b"test file content").hexdigest()

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Create document record
            await conn.execute(
                f"""
                INSERT INTO {TEST_SCHEMA}.documents
                (document_id, user_id, filename, raw_path, processing_status, parsed_path, mime, bytes_len, file_sha256, created_at, updated_at)
                VALUES ($1, $2, $3, $4, 'parsing', $5, 'application/pdf', $6, $7, NOW(), NOW());
                """,
                document_id, user_id, file_name, storage_path, parsed_path, file_size, file_sha256
            )

            # Create job at 'parsed' stage (start from where we can proceed)
            job_id = uuid.uuid4()
            await conn.execute(
                f"""
                INSERT INTO {TEST_SCHEMA}.upload_jobs
                (job_id, document_id, stage, state, created_at, updated_at)
                VALUES ($1, $2, 'parsed', 'queued', NOW(), NOW());
                """,
                job_id, document_id
            )
    
    print(f"Created test document: {document_id}")
    print(f"Created job: {job_id}")
    print(f"File: {file_name} ({file_size} bytes)")
    return document_id, job_id

async def test_end_to_end_pipeline():
    """Test complete end-to-end pipeline processing."""
    print("🚀 Starting End-to-End Pipeline Test")
    print(f"📁 Test file: {TEST_FILE}")
    
    # Connect to database
    pool = await asyncpg.create_pool('postgresql://postgres:postgres@127.0.0.1:54322/postgres')
    
    try:
        # Clean up existing test data
        print("🧹 Cleaning up existing test data...")
        async with pool.acquire() as conn:
            document_ids = await conn.fetch(f"SELECT document_id FROM {TEST_SCHEMA}.documents WHERE user_id = $1;", TEST_USER_ID)
            if document_ids:
                await conn.execute(f"DELETE FROM {TEST_SCHEMA}.upload_jobs WHERE document_id = ANY($1);", [d['document_id'] for d in document_ids])
            await conn.execute(f"DELETE FROM {TEST_SCHEMA}.documents WHERE user_id = $1;", TEST_USER_ID)
            print(f"   Cleaned up {len(document_ids)} existing documents")
        
        # Create test document
        print("📄 Creating test document...")
        document_id, job_id = await create_test_document(pool, TEST_FILE, TEST_USER_ID)
        
        # Configure worker
        print("⚙️  Configuring worker...")
        config = WorkerConfig(
            database_url='postgresql://postgres:postgres@127.0.0.1:54322/postgres',
            supabase_url=os.getenv('SUPABASE_URL', 'http://localhost:54321'),
            supabase_anon_key=os.getenv('SUPABASE_ANON_KEY'),
            supabase_service_role_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
            llamaparse_api_url=os.getenv('LLAMAPARSE_API_URL', 'http://localhost:8001'),
            llamaparse_api_key=os.getenv('LLAMAPARSE_API_KEY', 'test-key'),
            openai_api_url=os.getenv('OPENAI_API_URL', 'http://localhost:8002'),
            openai_api_key=os.getenv('OPENAI_API_KEY', 'test-key'),
            openai_model="text-embedding-3-small"
        )
        
        # Create worker and run processing
        print("🔄 Starting worker processing...")
        worker = BaseWorker(config)
        
        # Initialize the worker
        await worker._initialize_components()
        worker.running = True
        
        # Process a single job cycle with timeout
        try:
            # Try to process one job with a timeout
            job = await worker._get_next_job()
            if job:
                print(f"   📋 Retrieved job: {job['job_id']} at stage '{job['stage']}'")
                await worker._process_single_job_with_monitoring(job)
                print("   ✅ Job processed successfully")
            else:
                print("   ⚠️  No jobs found to process")
        finally:
            worker.running = False
            await worker._cleanup_components()
        
        # Check final results
        print("📊 Checking final results...")
        async with pool.acquire() as conn:
            # Get final job status
            job_status = await conn.fetchrow(
                f"SELECT stage, state, updated_at FROM {TEST_SCHEMA}.upload_jobs WHERE job_id = $1;", 
                job_id
            )
            
            # Get chunk count
            chunk_count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {TEST_SCHEMA}.document_chunks WHERE document_id = $1;", 
                document_id
            )
            
            # Get document status
            doc_status = await conn.fetchrow(
                f"SELECT processing_status, updated_at FROM {TEST_SCHEMA}.documents WHERE document_id = $1;",
                document_id
            )
        
        print(f"\n📋 FINAL RESULTS:")
        print(f"   Job Stage: {job_status['stage'] if job_status else 'NOT FOUND'}")
        print(f"   Job State: {job_status['state'] if job_status else 'NOT FOUND'}")
        print(f"   Document Status: {doc_status['processing_status'] if doc_status else 'NOT FOUND'}")
        print(f"   Chunk Count: {chunk_count}")
        print(f"   Last Updated: {job_status['updated_at'] if job_status else 'N/A'}")
        
        # Determine success
        if job_status and job_status['stage'] == 'embedded':
            print(f"\n✅ SUCCESS: End-to-end pipeline completed successfully!")
            print(f"   Document processed through all stages to 'embedded'")
            print(f"   Generated {chunk_count} chunks")
            return True
        else:
            print(f"\n⚠️  PARTIAL SUCCESS: Pipeline did not complete fully")
            print(f"   Final stage: {job_status['stage'] if job_status else 'UNKNOWN'}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await pool.close()

if __name__ == "__main__":
    success = asyncio.run(test_end_to_end_pipeline())
    sys.exit(0 if success else 1)