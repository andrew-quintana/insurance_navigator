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
from backend.shared.config.worker_config import WorkerConfig

# Load ACTUAL development environment variables
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

            # Create job at 'parsed' stage
            job_id = uuid.uuid4()
            await conn.execute(
                f"""
                INSERT INTO {TEST_SCHEMA}.upload_jobs
                (job_id, document_id, stage, state, created_at, updated_at)
                VALUES ($1, $2, 'parsed', 'queued', NOW(), NOW());
                """,
                job_id, document_id
            )
    
    return document_id, job_id

async def test_with_development_config():
    """Test pipeline processing using actual development configuration."""
    print("🔧 DEVELOPMENT CONFIGURATION VALIDATION")
    print("="*60)
    
    # Load configuration from environment (development)
    print("📋 Loading development configuration from .env.development...")
    config = WorkerConfig.from_environment()
    
    print(f"   Database URL: {config.database_url}")
    print(f"   Supabase URL: {config.supabase_url}")
    print(f"   OpenAI API URL: {config.openai_api_url}")
    print(f"   LlamaParse API URL: {config.llamaparse_api_url}")
    print(f"   Terminal Stage: {config.terminal_stage}")
    print(f"   Mock Storage: {config.use_mock_storage}")
    
    # Validate development-specific settings
    if config.database_url != "postgresql://postgres:postgres@127.0.0.1:54322/postgres":
        print(f"⚠️  WARNING: Database URL doesn't match expected development URL")
    
    if config.supabase_url != "http://127.0.0.1:54321":
        print(f"⚠️  WARNING: Supabase URL doesn't match expected development URL")
    
    # Connect to the development database
    print(f"\n🔗 Connecting to development database...")
    pool = await asyncpg.create_pool(config.database_url)
    
    try:
        # Clean up existing test data
        print("🧹 Cleaning up existing test data...")
        async with pool.acquire() as conn:
            document_ids = await conn.fetch(f"SELECT document_id FROM {TEST_SCHEMA}.documents WHERE user_id = $1;", TEST_USER_ID)
            if document_ids:
                await conn.execute(f"DELETE FROM {TEST_SCHEMA}.document_chunks WHERE document_id = ANY($1);", [d['document_id'] for d in document_ids])
                await conn.execute(f"DELETE FROM {TEST_SCHEMA}.upload_jobs WHERE document_id = ANY($1);", [d['document_id'] for d in document_ids])
                await conn.execute(f"DELETE FROM {TEST_SCHEMA}.documents WHERE user_id = $1;", TEST_USER_ID)
            print(f"   Cleaned up {len(document_ids)} existing documents")
        
        # Create test document
        print("📄 Creating test document...")
        document_id, job_id = await create_test_document(pool, TEST_FILE, TEST_USER_ID)
        
        print(f"\n🚀 Testing with development configuration...")
        print(f"   Terminal stage: {config.terminal_stage}")
        print(f"   Using {'mock' if config.use_mock_storage else 'real'} storage")
        
        # Create worker with development configuration
        worker = BaseWorker(config)
        
        # Initialize the worker
        await worker._initialize_components()
        worker.running = True
        
        # Process through multiple stages to terminal
        try:
            max_iterations = 10
            for i in range(max_iterations):
                print(f"\n--- Processing Iteration {i+1} ---")
                
                # Check current job status
                async with pool.acquire() as conn:
                    current_job = await conn.fetchrow(
                        f"SELECT stage, state FROM {TEST_SCHEMA}.upload_jobs WHERE job_id = $1;",
                        job_id
                    )
                
                if not current_job:
                    print("   ❌ Job not found")
                    break
                    
                print(f"   Current job: stage='{current_job['stage']}', state='{current_job['state']}'")
                
                # Check if we've reached terminal stage with done state
                if current_job['stage'] == config.terminal_stage and current_job['state'] == 'done':
                    print(f"   🎉 Job reached terminal stage '{config.terminal_stage}' with state 'done'!")
                    break
                
                # Try to get and process a job
                job = await worker._get_next_job()
                if job and str(job['job_id']) == str(job_id):
                    print(f"   📋 Processing job at stage '{job['stage']}'")
                    await worker._process_single_job_with_monitoring(job)
                    print(f"   ✅ Processed successfully")
                elif job:
                    print(f"   ⚠️  Found different job: {job['job_id']} (processing it)")
                    await worker._process_single_job_with_monitoring(job)
                else:
                    print("   ⏳ No jobs available")
                    break
                    
            else:
                print(f"   ⚠️  Reached max iterations ({max_iterations})")
        
        finally:
            worker.running = False
            await worker._cleanup_components()
        
        # Check final results
        print("\n📊 FINAL DEVELOPMENT TEST RESULTS:")
        async with pool.acquire() as conn:
            # Get final job status
            final_job = await conn.fetchrow(
                f"SELECT stage, state, updated_at FROM {TEST_SCHEMA}.upload_jobs WHERE job_id = $1;",
                job_id
            )
            
            # Get document status
            final_doc = await conn.fetchrow(
                f"SELECT processing_status FROM {TEST_SCHEMA}.documents WHERE document_id = $1;",
                document_id
            )
            
            # Get chunk count
            chunk_count = await conn.fetchval(
                f"SELECT COUNT(*) FROM {TEST_SCHEMA}.document_chunks WHERE document_id = $1;",
                document_id
            )
        
        print(f"   Job: stage='{final_job['stage'] if final_job else 'NONE'}', state='{final_job['state'] if final_job else 'NONE'}'")
        print(f"   Document: status='{final_doc['processing_status'] if final_doc else 'NONE'}'")
        print(f"   Chunks: {chunk_count}")
        print(f"   Last Updated: {final_job['updated_at'] if final_job else 'N/A'}")
        
        # Determine success for development environment
        success = (final_job and 
                  final_job['stage'] == config.terminal_stage and 
                  final_job['state'] == 'done' and
                  final_doc and 
                  final_doc['processing_status'] == 'completed')
        
        print("\n" + "="*60)
        if success:
            print("✅ DEVELOPMENT CONFIGURATION VALIDATION PASSED")
            print("   All closeout requirements met with dev config")
            return True
        else:
            print("❌ DEVELOPMENT CONFIGURATION VALIDATION FAILED")
            print("   Terminal stage finalization not working properly")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR during development validation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await pool.close()

if __name__ == "__main__":
    success = asyncio.run(test_with_development_config())
    print(f"\nDevelopment config validation: {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)