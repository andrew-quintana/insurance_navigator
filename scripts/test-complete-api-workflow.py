import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone

import pytest
import asyncpg
from dotenv import load_dotenv

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from backend.workers.base_worker import BaseWorker
from shared.config import WorkerConfig
from config.database import get_async_database_url

# Load environment variables
load_dotenv(os.path.join(project_root, '.env.development'))

# Test constants
SMALL_TEST_FILE = 'examples/simulated_insurance_document.pdf'
LARGE_TEST_FILE = 'examples/scan_classic_hmo.pdf'
TEST_SCHEMA = 'upload_pipeline'
TEST_USER_ID = uuid.UUID('f47ac10b-58cc-4372-a567-0e02b2c3d479')  # Example UUID

# --- Test Setup and Teardown ---

@pytest.fixture(scope="function")
async def db_pool():
    """Create a database pool for the test module."""
    pool = await asyncpg.create_pool(get_async_database_url())
    yield pool
    await pool.close()

@pytest.fixture(autouse=True)
async def cleanup_test_data(db_pool):
    """Clean up test data before and after each test."""
    await clean_test_artifacts(db_pool)
    yield
    await clean_test_artifacts(db_pool)

async def clean_test_artifacts(pool):
    """Helper to remove test data from the database."""
    async with pool.acquire() as conn:
        # Get all document_ids for the test user
        document_ids = await conn.fetch(f"SELECT document_id FROM {TEST_SCHEMA}.documents WHERE user_id = $1;", TEST_USER_ID)
        if document_ids:
            # Delete from upload_jobs first
            await conn.execute(f"DELETE FROM {TEST_SCHEMA}.upload_jobs WHERE document_id = ANY($1);", [d['document_id'] for d in document_ids])
        # Then delete from documents
        await conn.execute(f"DELETE FROM {TEST_SCHEMA}.documents WHERE user_id = $1;", TEST_USER_ID)


# --- Test Helper Functions ---

async def create_test_document(pool, file_path, user_id):
    """
    Creates a test document and a corresponding upload job in the database.
    This function now correctly handles the initial state of a job.
    """
    file_name = os.path.basename(file_path)
    storage_path = f"test_uploads/{user_id}/{file_name}"
    parsed_path = f"parsed_output/{user_id}/{file_name}.json"
    document_id = uuid.uuid4()
    file_size = os.path.getsize(os.path.join(project_root, file_path))

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Create a document record
            await conn.execute(
                f"""
                INSERT INTO {TEST_SCHEMA}.documents
                (document_id, user_id, filename, raw_path, processing_status, parsed_path, mime, bytes_len, created_at, updated_at)
                VALUES ($1, $2, $3, $4, 'uploading', $5, 'application/pdf', $6, NOW(), NOW());
                """,
                document_id, user_id, file_name, storage_path, parsed_path, file_size
            )

            # Create an upload job record in 'parsed' stage
            job_id = await conn.fetchval(
                f"""
                INSERT INTO {TEST_SCHEMA}.upload_jobs
                (document_id, stage, created_at, updated_at)
                VALUES ($1, 'parsed', NOW(), NOW())
                RETURNING job_id;
                """,
                document_id
            )
    return document_id, job_id

# --- Test Cases ---

@pytest.mark.asyncio
async def test_external_api_connectivity(db_pool):
    """
    Tests basic connectivity to LlamaParse and OpenAI APIs.
    """
    # This test assumes the BaseWorker's constructor or a helper method
    # can be used to check service availability.
    config = WorkerConfig(
        database_url=os.getenv("DATABASE_URL"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_anon_key=os.getenv("ANON_KEY"),
        supabase_service_role_key=os.getenv("SERVICE_ROLE_KEY"),
        llamaparse_api_url=os.getenv("LLAMAPARSE_BASE_URL"),
        llamaparse_api_key=os.getenv("LLAMAPARSE_API_KEY"),
        openai_api_url=os.getenv("OPENAI_API_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model="text-embedding-3-small"
    )
    worker = BaseWorker(config)
    assert await worker.health_check(), "External services health check failed"

@pytest.mark.asyncio
async def test_worker_job_processing_small_file(db_pool):
    """
    Tests the complete worker pipeline with a small test file.
    """
    document_id, job_id = await create_test_document(db_pool, SMALL_TEST_FILE, TEST_USER_ID)

    config = WorkerConfig(
        database_url=os.getenv("DATABASE_URL"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_anon_key=os.getenv("ANON_KEY"),
        supabase_service_role_key=os.getenv("SERVICE_ROLE_KEY"),
        llamaparse_api_url=os.getenv("LLAMAPARSE_BASE_URL"),
        llamaparse_api_key=os.getenv("LLAMAPARSE_API_KEY"),
        openai_api_url=os.getenv("OPENAI_API_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model="text-embedding-3-small"
    )
    worker = BaseWorker(config)
    await worker.process_jobs()

    # Validate final state
    async with db_pool.acquire() as conn:
        final_job_stage = await conn.fetchval(
            f"SELECT stage FROM {TEST_SCHEMA}.upload_jobs WHERE job_id = $1;", job_id
        )
        assert final_job_stage == 'embedded', f"Job did not complete. Final stage: {final_job_stage}"

        chunk_count = await conn.fetchval(
            f"SELECT COUNT(*) FROM {TEST_SCHEMA}.document_chunks WHERE document_id = $1;", document_id
        )
        assert chunk_count > 0, "No document chunks were created."

@pytest.mark.asyncio
async def test_worker_job_processing_large_file(db_pool):
    """
    Tests the complete worker pipeline with a large test file.
    """
    document_id, job_id = await create_test_document(db_pool, LARGE_TEST_FILE, TEST_USER_ID)

    config = WorkerConfig(
        database_url=os.getenv("DATABASE_URL"),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_anon_key=os.getenv("ANON_KEY"),
        supabase_service_role_key=os.getenv("SERVICE_ROLE_KEY"),
        llamaparse_api_url=os.getenv("LLAMAPARSE_BASE_URL"),
        llamaparse_api_key=os.getenv("LLAMAPARSE_API_KEY"),
        openai_api_url=os.getenv("OPENAI_API_URL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model="text-embedding-3-small"
    )
    worker = BaseWorker(config)
    await worker.process_jobs()

    # Validate final state
    async with db_pool.acquire() as conn:
        final_job_stage = await conn.fetchval(
            f"SELECT stage FROM {TEST_SCHEMA}.upload_jobs WHERE job_id = $1;", job_id
        )
        assert final_job_stage == 'embedded', f"Job did not complete. Final stage: {final_job_stage}"

        chunk_count = await conn.fetchval(
            f"SELECT COUNT(*) FROM {TEST_SCHEMA}.document_chunks WHERE document_id = $1;", document_id
        )
        assert chunk_count > 0, "No document chunks were created."

# --- Main Execution ---

async def main():
    """Main function to run tests."""
    # Running tests with pytest
    # This script should be run with `pytest scripts/test-complete-api-workflow.py`
    print("This script is designed to be run with pytest.")
    print("Example: pytest scripts/test-complete-api-workflow.py")

if __name__ == "__main__":
    asyncio.run(main())