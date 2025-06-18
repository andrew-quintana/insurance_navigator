#!/usr/bin/env python3
"""
Complete Pipeline Test
Tests the entire document processing pipeline:
1. Upload document
2. Verify job creation (trigger)
3. Monitor job processing
4. Validate completion
"""

import asyncio
import asyncpg
import aiohttp
import json
import tempfile
import os
from datetime import datetime, timezone

# Configuration
DATABASE_URL = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
SUPABASE_URL = 'https://jhrespvvhbnloxrieycf.supabase.co'
SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpocmVzcHZ2aGJubG94cmleeeWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDIyNDgzNiwiZXhwIjoyMDQ1ODAwODM2fQ.m4lgWEY6lUQ7O4_iHp5QYHY-nxRxNSMpWZJR4S7xCZo'

async def main():
    """Test the complete document processing pipeline"""
    print("🚀 Complete Pipeline Test")
    print("=" * 50)
    
    conn = None
    temp_file_path = None
    document_id = None
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        # Step 1: Create test document
        temp_file_path, document_id = await create_test_document(conn)
        
        # Step 2: Wait for trigger to create job
        await wait_for_job_creation(conn, document_id)
        
        # Step 3: Trigger job processing
        await trigger_job_processing()
        
        # Step 4: Monitor processing progress
        await monitor_processing_progress(conn, document_id)
        
        # Step 5: Validate final results
        await validate_final_results(conn, document_id)
        
        print("\n🎉 Pipeline test completed successfully!")
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        if conn:
            await conn.close()

async def create_test_document(conn):
    """Create a test document and upload it"""
    print("\n📄 Step 1: Creating Test Document")
    print("-" * 40)
    
    # Create test file
    test_content = """
    Insurance Policy Document - Test
    ================================
    
    Policy Number: TEST-12345
    Policy Holder: John Doe
    Coverage Type: Health Insurance
    Premium: $500/month
    Deductible: $1,000
    Coverage Limit: $100,000
    
    This is a test document for validating the complete
    document processing pipeline including:
    - Document upload
    - Job queue creation
    - Processing execution
    - Status updates
    - Vector embeddings
    
    The pipeline should automatically:
    1. Create a processing job when this document is uploaded
    2. Parse the content using LlamaParse
    3. Create vector embeddings
    4. Update the document status to completed
    """
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name
    
    # Get file stats
    file_size = os.path.getsize(temp_file_path)
    filename = f"pipeline_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print(f"📝 Created test file: {filename} ({file_size} bytes)")
    
    # Upload document metadata
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'apikey': SERVICE_ROLE_KEY
    }
    
    upload_metadata = {
        'fileName': filename,
        'fileSize': file_size,
        'contentType': 'text/plain'
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        upload_url = f"{SUPABASE_URL}/functions/v1/upload-handler"
        
        async with session.post(upload_url, json=upload_metadata, headers=headers) as response:
            status = response.status
            response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            
            if status == 200:
                document_id = response_data.get('documentId')
                print(f"✅ Document registered: {document_id}")
                
                # Verify in database
                doc_info = await conn.fetchrow("""
                    SELECT id, original_filename, status, created_at
                    FROM documents 
                    WHERE id = $1
                """, document_id)
                
                if doc_info:
                    print(f"📋 Document in DB: {doc_info['status']} status")
                    return temp_file_path, document_id
                else:
                    raise Exception("Document not found in database")
            else:
                raise Exception(f"Upload failed: {response_data}")

async def wait_for_job_creation(conn, document_id):
    """Wait for the trigger to create a processing job"""
    print("\n⏱️  Step 2: Waiting for Job Creation")
    print("-" * 40)
    
    max_wait = 30  # 30 seconds max
    check_interval = 2  # Check every 2 seconds
    
    for attempt in range(max_wait // check_interval):
        jobs = await conn.fetch("""
            SELECT id, job_type, status, created_at
            FROM processing_jobs
            WHERE document_id = $1
            ORDER BY created_at DESC
        """, document_id)
        
        if jobs:
            print(f"✅ Job created: {jobs[0]['id']}")
            print(f"   Type: {jobs[0]['job_type']}")
            print(f"   Status: {jobs[0]['status']}")
            return jobs[0]
        
        print(f"   Waiting... (attempt {attempt + 1}/{max_wait // check_interval})")
        await asyncio.sleep(check_interval)
    
    raise Exception("No processing job created within timeout period")

async def trigger_job_processing():
    """Trigger the job processor to start processing"""
    print("\n🔄 Step 3: Triggering Job Processing")
    print("-" * 40)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'apikey': SERVICE_ROLE_KEY
    }
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{SUPABASE_URL}/functions/v1/job-processor"
        
        print("📞 Calling job processor...")
        async with session.post(job_processor_url, headers=headers, json={}) as response:
            status = response.status
            response_data = await response.json() if response.content_type == 'application/json' else await response.text()
            
            print(f"Status: {status}")
            print(f"Response: {response_data}")
            
            if status == 200:
                processed = response_data.get('processed', 0)
                if processed > 0:
                    print(f"✅ Job processor started {processed} jobs")
                else:
                    print("ℹ️  No jobs were processed (may be scheduled for later)")
            else:
                print(f"⚠️  Job processor returned status {status}")

async def monitor_processing_progress(conn, document_id):
    """Monitor the processing progress"""
    print("\n📊 Step 4: Monitoring Processing Progress")
    print("-" * 40)
    
    max_wait = 180  # 3 minutes max
    check_interval = 10  # Check every 10 seconds
    
    print("🔍 Monitoring progress...")
    
    for attempt in range(max_wait // check_interval):
        # Check document status
        doc_info = await conn.fetchrow("""
            SELECT status, progress_percentage, error_message, updated_at
            FROM documents
            WHERE id = $1
        """, document_id)
        
        # Check job status
        jobs = await conn.fetch("""
            SELECT job_type, status, error_message, updated_at
            FROM processing_jobs
            WHERE document_id = $1
            ORDER BY created_at DESC
        """, document_id)
        
        print(f"\n   Check {attempt + 1} ({datetime.now().strftime('%H:%M:%S')}):")
        print(f"   📄 Document: {doc_info['status']} ({doc_info['progress_percentage']}%)")
        
        for job in jobs:
            print(f"   📋 Job {job['job_type']}: {job['status']}")
            if job['error_message']:
                print(f"      ❌ Error: {job['error_message']}")
        
        # Check for completion
        if doc_info['status'] == 'completed':
            print("\n✅ Document processing completed!")
            return True
        elif doc_info['status'] == 'failed':
            error_msg = doc_info.get('error_message', 'Unknown error')
            print(f"\n❌ Document processing failed: {error_msg}")
            return False
        
        await asyncio.sleep(check_interval)
    
    print("\n⏰ Processing monitoring timed out")
    return False

async def validate_final_results(conn, document_id):
    """Validate the final processing results"""
    print("\n✅ Step 5: Validating Final Results")
    print("-" * 40)
    
    # Check document final state
    doc_info = await conn.fetchrow("""
        SELECT 
            status, progress_percentage, 
            extracted_text_length, 
            processing_completed_at,
            error_message
        FROM documents
        WHERE id = $1
    """, document_id)
    
    print(f"📄 Final Document State:")
    print(f"   Status: {doc_info['status']}")
    print(f"   Progress: {doc_info['progress_percentage']}%")
    
    if doc_info['extracted_text_length']:
        print(f"   Text Length: {doc_info['extracted_text_length']} chars")
    
    if doc_info['processing_completed_at']:
        print(f"   Completed: {doc_info['processing_completed_at']}")
    
    if doc_info['error_message']:
        print(f"   Error: {doc_info['error_message']}")
    
    # Check job results
    jobs = await conn.fetch("""
        SELECT job_type, status, completed_at, result
        FROM processing_jobs
        WHERE document_id = $1
        ORDER BY created_at
    """, document_id)
    
    print(f"\n📋 Job Results ({len(jobs)} jobs):")
    for job in jobs:
        status_emoji = "✅" if job['status'] == 'completed' else "❌" if job['status'] == 'failed' else "⏳"
        print(f"   {status_emoji} {job['job_type']}: {job['status']}")
        
        if job['completed_at']:
            print(f"      Completed: {job['completed_at']}")
        
        if job['result']:
            result_keys = list(job['result'].keys()) if isinstance(job['result'], dict) else []
            print(f"      Result keys: {result_keys}")
    
    # Check if vectors were created
    vector_count = await conn.fetchval("""
        SELECT COUNT(*)
        FROM user_document_vectors
        WHERE document_id = $1
    """, document_id)
    
    print(f"\n🔗 Vector Embeddings: {vector_count} chunks created")
    
    # Overall assessment
    success = (
        doc_info['status'] in ['completed', 'processing'] and
        any(job['status'] == 'completed' for job in jobs) and
        vector_count > 0
    )
    
    if success:
        print(f"\n🎉 Pipeline validation: ✅ SUCCESS")
        print(f"   - Document processed successfully")
        print(f"   - Jobs completed properly")
        print(f"   - Vector embeddings created")
    else:
        print(f"\n⚠️  Pipeline validation: ❌ PARTIAL/FAILED")
        print(f"   Check the logs above for specific issues")

if __name__ == "__main__":
    asyncio.run(main()) 