#!/usr/bin/env python3
"""
Phase 1 Real API Integration Test

This script tests the upload pipeline with real LlamaParse and OpenAI APIs
instead of mock services to ensure end-to-end functionality.
"""

import asyncio
import json
import time
import uuid
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any
import jwt

# Test configuration
TEST_USER_ID = "752ae479-0fc4-41d3-b2fa-8f8ac467685f"
API_BASE_URL = "http://localhost:8000"
DATABASE_URL = "postgresql://postgres:postgres@localhost:54322/postgres"

# JWT configuration for testing
# The API is using the service role key as the JWT secret
JWT_SECRET = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
SUPABASE_URL = "http://127.0.0.1:54321"

def create_test_jwt_token(user_id: str) -> str:
    """Use the Supabase anon key as a test JWT token"""
    # The anon key is already a valid JWT token from Supabase
    # We'll use it directly instead of creating our own
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"

async def create_test_document() -> str:
    """Create a test document via upload endpoint"""
    print("📄 Creating test document via upload endpoint...")
    
    unique_hash = f"real_api_test_{int(time.time())}_{uuid.uuid4().hex[:8]}"
    
    # Create JWT token for authentication
    token = create_test_jwt_token(TEST_USER_ID)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create upload request
    upload_request = {
        "filename": f"real_api_test_{int(time.time())}.pdf",
        "mime": "application/pdf",
        "bytes_len": 1024,
        "sha256": unique_hash
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/api/v2/upload", json=upload_request, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to create upload request: {response.text}")
        
        upload_response = response.json()
        document_id = upload_response["document_id"]
        job_id = upload_response["job_id"]
        
        print(f"✅ Created document: {document_id}")
        print(f"✅ Created job: {job_id}")
        return document_id, job_id

async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get job status from the API"""
    # Create JWT token for authentication
    token = create_test_jwt_token(TEST_USER_ID)
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/v2/jobs/{job_id}", headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get job status: {response.text}")
        
        return response.json()

async def monitor_pipeline_progress(job_id: str, max_attempts: int = 20) -> Dict[str, Any]:
    """Monitor the pipeline progress"""
    print("⏳ Monitoring pipeline progress with REAL APIs...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            job_data = await get_job_status(job_id)
            status = job_data.get("status", "unknown")
            state = job_data.get("state", "unknown")
            
            print(f"🔄 Attempt {attempt}: Status={status}, State={state}")
            
            if state == "done":
                print("🎉 Pipeline completed successfully!")
                return job_data
            elif state == "deadletter":
                error_info = job_data.get("error", "Unknown error")
                print(f"❌ Pipeline failed: {error_info}")
                return job_data
            
            # Wait before next check
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"❌ Failed to get job status: {e}")
            return {"error": f"Failed to get job status: {e}"}
    
    print(f"⏰ Pipeline monitoring timed out after {max_attempts} attempts")
    return {"error": "Pipeline monitoring timeout"}

async def verify_database_records(document_id: str):
    """Verify that database records were created"""
    print("🗄️ Verifying database records...")
    
    import asyncpg
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Check document chunks
        chunk_count = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.document_chunks
            WHERE document_id = $1
        """, document_id)
        
        # Check job status
        job_status = await conn.fetchval("""
            SELECT status FROM upload_pipeline.upload_jobs
            WHERE document_id = $1
            ORDER BY created_at DESC
            LIMIT 1
        """, document_id)
        
        print(f"   Document chunks: {chunk_count}")
        print(f"   Final job status: {job_status}")
        
        return {
            "chunks": chunk_count,
            "final_status": job_status
        }
        
    finally:
        await conn.close()

async def test_real_api_integration():
    """Test the complete pipeline with real APIs"""
    print("🔍 Phase 1 Real API Integration Test")
    print("=" * 60)
    
    try:
        # Step 1: Create test document and job
        document_id, job_id = await create_test_document()
        
        # Step 2: Monitor pipeline progress
        result = await monitor_pipeline_progress(job_id)
        
        # Step 3: Verify database records
        db_records = await verify_database_records(document_id)
        
        # Step 4: Report results
        print("\n📊 Final Test Results:")
        print("=" * 40)
        
        if "error" in result:
            print(f"❌ Pipeline failed: {result['error']}")
            success = False
        else:
            print("✅ Pipeline completed successfully!")
            print(f"   Final status: {result.get('status', 'unknown')}")
            print(f"   Final state: {result.get('state', 'unknown')}")
            success = True
        
        print(f"   Document chunks created: {db_records['chunks']}")
        print(f"   Final job status: {db_records['final_status']}")
        
        if success and db_records['chunks'] > 0:
            print("\n🎉 REAL API INTEGRATION TEST PASSED!")
            print("✅ LlamaParse API integration working")
            print("✅ OpenAI API integration working")
            print("✅ End-to-end pipeline with real services confirmed")
        else:
            print("\n⚠️ REAL API INTEGRATION TEST INCOMPLETE")
            print("❌ Some components may not be working with real APIs")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_real_api_integration())
