#!/usr/bin/env python3
"""
Fix Queue Processing Issues
1. Clean up stuck jobs
2. Create jobs for pending documents
3. Set up proper database triggers
4. Test the complete pipeline
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
    """Fix all queue processing issues"""
    print("🔧 Fixing Queue Processing Issues")
    print("=" * 50)
    
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        # Step 1: Clean up stuck jobs
        await cleanup_stuck_jobs(conn)
        
        # Step 2: Create jobs for pending documents
        await create_missing_jobs(conn)
        
        # Step 3: Set up database triggers
        await setup_triggers(conn)
        
        # Step 4: Test job processing
        await test_job_processing()
        
        # Step 5: Verify the fix
        await verify_fixes(conn)
        
        print("\n✅ Queue processing fixes complete!")
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await conn.close()

async def cleanup_stuck_jobs(conn):
    """Clean up stuck jobs that have been running too long"""
    print("\n🧹 Step 1: Cleaning Up Stuck Jobs")
    print("-" * 40)
    
    # Find stuck jobs (running > 30 minutes)
    stuck_jobs = await conn.fetch("""
        SELECT 
            pj.id, d.original_filename, pj.job_type,
            EXTRACT(EPOCH FROM (NOW() - pj.created_at)) / 60 as age_minutes
        FROM processing_jobs pj
        JOIN documents d ON pj.document_id = d.id
        WHERE pj.status = 'running' 
        AND pj.created_at < NOW() - INTERVAL '30 minutes'
    """)
    
    if stuck_jobs:
        print(f"🚨 Found {len(stuck_jobs)} stuck jobs:")
        
        for job in stuck_jobs:
            print(f"   📄 {job['original_filename']} ({job['age_minutes']:.1f}m)")
            
            # Mark as failed and allow retry
            await conn.execute("""
                UPDATE processing_jobs 
                SET 
                    status = 'failed',
                    error_message = 'Job stuck - marked as failed for retry',
                    updated_at = NOW()
                WHERE id = $1
            """, job['id'])
            
            print(f"      ✅ Marked as failed for retry")
    else:
        print("✅ No stuck jobs found")

async def create_missing_jobs(conn):
    """Create processing jobs for pending documents that don't have them"""
    print("\n📋 Step 2: Creating Missing Jobs")
    print("-" * 40)
    
    # Find pending documents without processing jobs
    pending_docs = await conn.fetch("""
        SELECT d.id, d.original_filename, d.storage_path
        FROM documents d
        LEFT JOIN processing_jobs pj ON d.id = pj.document_id
        WHERE d.status = 'pending' 
        AND pj.id IS NULL
        ORDER BY d.created_at ASC
    """)
    
    if pending_docs:
        print(f"📄 Found {len(pending_docs)} documents needing jobs:")
        
        for i, doc in enumerate(pending_docs):
            doc_id = doc['id']
            filename = doc['original_filename']
            
            print(f"   {i+1}. {filename}")
            
            try:
                # Create processing job
                job_id = await conn.fetchval("""
                    SELECT create_processing_job(
                        $1::UUID,     -- document_id
                        'parse',      -- job_type
                        $2::JSONB,    -- payload
                        5,            -- priority
                        3,            -- max_retries
                        2             -- schedule_delay_seconds
                    )
                """, doc_id, json.dumps({
                    'documentId': str(doc_id),
                    'storagePath': doc['storage_path']
                }))
                
                print(f"      ✅ Created job: {job_id}")
                
            except Exception as e:
                print(f"      ❌ Failed to create job: {e}")
    else:
        print("✅ All pending documents have processing jobs")

async def setup_triggers(conn):
    """Set up database triggers for automatic job creation"""
    print("\n🔗 Step 3: Setting Up Database Triggers")
    print("-" * 40)
    
    try:
        # Create trigger function for automatic job creation
        await conn.execute("""
            CREATE OR REPLACE FUNCTION auto_create_processing_job()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Only create job for newly uploaded documents
                IF NEW.status = 'pending' AND (OLD IS NULL OR OLD.status != 'pending') THEN
                    -- Create a parse job
                    INSERT INTO processing_jobs (
                        document_id, job_type, status, priority, 
                        max_retries, retry_count, created_at, scheduled_at
                    ) VALUES (
                        NEW.id, 'parse', 'pending', 5,
                        3, 0, NOW(), NOW() + INTERVAL '5 seconds'
                    );
                    
                    RAISE LOG 'Auto-created processing job for document %', NEW.original_filename;
                END IF;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        print("✅ Created trigger function: auto_create_processing_job")
        
        # Create the trigger
        await conn.execute("""
            DROP TRIGGER IF EXISTS auto_job_creation_trigger ON documents;
            
            CREATE TRIGGER auto_job_creation_trigger
                AFTER INSERT OR UPDATE ON documents
                FOR EACH ROW
                EXECUTE FUNCTION auto_create_processing_job();
        """)
        
        print("✅ Created trigger: auto_job_creation_trigger")
        
    except Exception as e:
        print(f"❌ Trigger setup failed: {e}")

async def test_job_processing():
    """Test the job processor to ensure it's working"""
    print("\n🎯 Step 4: Testing Job Processing")
    print("-" * 40)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'apikey': SERVICE_ROLE_KEY
    }
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            job_processor_url = f"{SUPABASE_URL}/functions/v1/job-processor"
            
            print("📞 Calling job processor...")
            async with session.post(job_processor_url, headers=headers, json={}) as response:
                status = response.status
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                print(f"Status: {status}")
                print(f"Response: {response_data}")
                
                if status == 200:
                    processed = response_data.get('processed', 0)
                    if processed > 0:
                        print(f"✅ Successfully processed {processed} jobs")
                    else:
                        print("ℹ️  No jobs to process (this is normal)")
                else:
                    print(f"⚠️  Job processor returned status {status}")
                    
    except Exception as e:
        print(f"❌ Job processor test failed: {e}")

async def verify_fixes(conn):
    """Verify that our fixes worked"""
    print("\n✅ Step 5: Verifying Fixes")
    print("-" * 40)
    
    # Check for stuck jobs
    stuck_count = await conn.fetchval("""
        SELECT COUNT(*)
        FROM processing_jobs
        WHERE status = 'running' 
        AND created_at < NOW() - INTERVAL '30 minutes'
    """)
    
    print(f"🚨 Stuck jobs: {stuck_count}")
    
    # Check pending jobs ready for processing
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f"📥 Pending jobs ready: {len(pending_jobs)}")
    
    # Check documents without jobs
    docs_without_jobs = await conn.fetchval("""
        SELECT COUNT(*)
        FROM documents d
        LEFT JOIN processing_jobs pj ON d.id = pj.document_id
        WHERE d.status = 'pending' AND pj.id IS NULL
    """)
    
    print(f"📄 Documents without jobs: {docs_without_jobs}")
    
    # Check trigger existence
    trigger_exists = await conn.fetchval("""
        SELECT EXISTS(
            SELECT 1 FROM information_schema.triggers
            WHERE trigger_name = 'auto_job_creation_trigger'
            AND event_object_table = 'documents'
        )
    """)
    
    print(f"🔗 Auto-creation trigger: {'✅ Active' if trigger_exists else '❌ Missing'}")
    
    # Summary
    print(f"\n📊 Fix Summary:")
    if stuck_count == 0 and docs_without_jobs == 0 and trigger_exists:
        print("✅ All issues resolved!")
        print("🚀 Queue processing should now work automatically")
    else:
        print("⚠️  Some issues remain:")
        if stuck_count > 0:
            print(f"   - {stuck_count} stuck jobs need manual intervention")
        if docs_without_jobs > 0:
            print(f"   - {docs_without_jobs} documents still need jobs")
        if not trigger_exists:
            print("   - Auto-creation trigger is missing")

if __name__ == "__main__":
    asyncio.run(main()) 