#!/usr/bin/env python3
"""
Doc Parser Diagnostic
Tests the doc-parser edge function directly to diagnose why jobs are stuck in running state
"""

import asyncio
import asyncpg
import aiohttp
import json
from datetime import datetime, timezone

# Configuration
DATABASE_URL = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
SUPABASE_URL = 'https://jhrespvvhbnloxrieycf.supabase.co'
SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpocmVzcHZ2aGJubG94cmleeeWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDIyNDgzNiwiZXhwIjoyMDQ1ODAwODM2fQ.m4lgWEY6lUQ7O4_iHp5QYHY-nxRxNSMpWZJR4S7xCZo'

async def main():
    """Diagnose doc-parser functionality"""
    print("🔍 Doc Parser Diagnostic")
    print("=" * 50)
    
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        # Step 1: Check running jobs
        await check_running_jobs(conn)
        
        # Step 2: Test doc-parser directly
        await test_doc_parser_directly(conn)
        
        # Step 3: Check environment variables in doc-parser
        await check_doc_parser_environment()
        
        # Step 4: Manual job completion test
        await test_manual_job_completion(conn)
        
        print("\n✅ Doc parser diagnostic completed!")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await conn.close()

async def check_running_jobs(conn):
    """Check currently running jobs"""
    print("\n📋 Step 1: Checking Running Jobs")
    print("-" * 40)
    
    running_jobs = await conn.fetch("""
        SELECT 
            pj.id, pj.document_id, pj.job_type, pj.status,
            pj.created_at, pj.started_at, pj.payload,
            d.original_filename, d.storage_path,
            EXTRACT(EPOCH FROM (NOW() - pj.created_at)) / 60 as age_minutes
        FROM processing_jobs pj
        JOIN documents d ON pj.document_id = d.id
        WHERE pj.status = 'running'
        ORDER BY pj.created_at DESC
    """)
    
    if running_jobs:
        print(f"🔄 Found {len(running_jobs)} running jobs:")
        for job in running_jobs:
            print(f"\n   📄 {job['original_filename']}")
            print(f"      Job ID: {job['id']}")
            print(f"      Status: {job['status']} (running {job['age_minutes']:.1f}m)")
            print(f"      Storage: {job['storage_path']}")
            if job['payload']:
                print(f"      Payload: {job['payload']}")
        
        # Select one for testing
        test_job = running_jobs[0]
        return test_job
    else:
        print("✅ No running jobs found")
        return None

async def test_doc_parser_directly(conn):
    """Test the doc-parser edge function directly"""
    print("\n🧪 Step 2: Testing Doc-Parser Directly")
    print("-" * 40)
    
    # Get a document to test with
    test_doc = await conn.fetchrow("""
        SELECT id, original_filename, storage_path
        FROM documents 
        WHERE status = 'parsing'
        AND storage_path IS NOT NULL
        LIMIT 1
    """)
    
    if not test_doc:
        print("❌ No suitable test document found")
        return
    
    print(f"📄 Testing with: {test_doc['original_filename']}")
    print(f"   Document ID: {test_doc['id']}")
    print(f"   Storage Path: {test_doc['storage_path']}")
    
    timeout = aiohttp.ClientTimeout(total=120)  # 2 minutes
    headers = {
        'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'apikey': SERVICE_ROLE_KEY
    }
    
    payload = {
        'documentId': str(test_doc['id']),
        'storagePath': test_doc['storage_path']
    }
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            doc_parser_url = f"{SUPABASE_URL}/functions/v1/doc-parser"
            
            print(f"📞 Calling doc-parser...")
            print(f"   URL: {doc_parser_url}")
            print(f"   Payload: {payload}")
            
            async with session.post(doc_parser_url, headers=headers, json=payload) as response:
                status = response.status
                
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                print(f"\n📋 Doc-Parser Response:")
                print(f"   Status: {status}")
                print(f"   Response: {response_data}")
                
                if status == 200:
                    print("   ✅ Doc-parser responded successfully")
                    
                    # Check if document status changed
                    updated_doc = await conn.fetchrow("""
                        SELECT status, progress_percentage, error_message
                        FROM documents
                        WHERE id = $1
                    """, test_doc['id'])
                    
                    print(f"   📄 Document status after call: {updated_doc['status']}")
                    
                elif status == 500:
                    print("   ❌ Doc-parser internal error")
                elif status == 404:
                    print("   ❌ Doc-parser not found or document not accessible")
                else:
                    print(f"   ⚠️  Unexpected status: {status}")
                    
    except Exception as e:
        print(f"   ❌ Doc-parser call failed: {e}")

async def check_doc_parser_environment():
    """Check if doc-parser has required environment variables"""
    print("\n🔧 Step 3: Checking Doc-Parser Environment")
    print("-" * 40)
    
    # The doc-parser needs these environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'LLAMAPARSE_API_KEY',
        'CUSTOM_SERVICE_ROLE_KEY'
    ]
    
    print("📍 Required environment variables for doc-parser:")
    for var in required_vars:
        print(f"   - {var}")
    
    print("\n💡 These should be set in:")
    print("   1. Supabase Dashboard → Edge Functions → doc-parser → Settings")
    print("   2. Or verify they're accessible in the function code")
    
    # Test a simple edge function call to see basic connectivity
    timeout = aiohttp.ClientTimeout(total=30)
    headers = {
        'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'apikey': SERVICE_ROLE_KEY
    }
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Test with minimal payload
            test_payload = {'test': 'connectivity'}
            doc_parser_url = f"{SUPABASE_URL}/functions/v1/doc-parser"
            
            async with session.post(doc_parser_url, headers=headers, json=test_payload) as response:
                status = response.status
                print(f"\n🔗 Basic connectivity test: Status {status}")
                
                if status == 200:
                    print("   ✅ Doc-parser is reachable")
                elif status == 500:
                    print("   ⚠️  Doc-parser has internal errors (likely env vars)")
                elif status == 404:
                    print("   ❌ Doc-parser not deployed")
                else:
                    print(f"   ❓ Unexpected response: {status}")
                    
    except Exception as e:
        print(f"   ❌ Connectivity test failed: {e}")

async def test_manual_job_completion(conn):
    """Test manually completing a stuck job"""
    print("\n🔧 Step 4: Manual Job Completion Test")
    print("-" * 40)
    
    # Find a running job to manually complete
    stuck_job = await conn.fetchrow("""
        SELECT id, document_id, job_type
        FROM processing_jobs
        WHERE status = 'running'
        AND created_at < NOW() - INTERVAL '2 minutes'
        LIMIT 1
    """)
    
    if stuck_job:
        job_id = stuck_job['id']
        doc_id = stuck_job['document_id']
        
        print(f"🔧 Found stuck job: {job_id}")
        print(f"   Document: {doc_id}")
        print(f"   Type: {stuck_job['job_type']}")
        
        # Option 1: Mark as failed to allow retry
        print(f"\n🔄 Option 1: Mark as failed for retry...")
        try:
            await conn.execute("""
                UPDATE processing_jobs 
                SET 
                    status = 'failed',
                    error_message = 'Manual intervention - marked for retry',
                    updated_at = NOW()
                WHERE id = $1
            """, job_id)
            
            print(f"   ✅ Job marked as failed")
            
            # Wait a moment and check if it gets retried
            await asyncio.sleep(5)
            
            retry_job = await conn.fetchrow("""
                SELECT status, retry_count
                FROM processing_jobs
                WHERE id = $1
            """, job_id)
            
            print(f"   📋 Job status after 5s: {retry_job['status']}")
            print(f"   🔁 Retry count: {retry_job['retry_count']}")
            
        except Exception as e:
            print(f"   ❌ Failed to update job: {e}")
            
    else:
        print("✅ No stuck jobs found for testing")

if __name__ == "__main__":
    asyncio.run(main()) 