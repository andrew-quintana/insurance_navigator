#!/usr/bin/env python3
"""
End-to-End Document Processing Validation
Tests the complete document processing pipeline including:
1. Current status check
2. Queue management validation
3. Processing job triggers
4. Progress monitoring
"""

import asyncio
import asyncpg
import aiohttp
import json
import os
import tempfile
from datetime import datetime, timezone

# Configuration
DATABASE_URL = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
SUPABASE_URL = 'https://jhrespvvhbnloxrieycf.supabase.co'
SERVICE_ROLE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpocmVzcHZ2aGJubG94cmleeeWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDIyNDgzNiwiZXhwIjoyMDQ1ODAwODM2fQ.m4lgWEY6lUQ7O4_iHp5QYHY-nxRxNSMpWZJR4S7xCZo'

async def main():
    """Run complete end-to-end validation"""
    print("🔍 End-to-End Document Processing Validation")
    print("=" * 60)
    
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        # Step 1: Check current system status
        await check_current_status(conn)
        
        # Step 2: Validate queue management
        await validate_queue_management(conn)
        
        # Step 3: Check processing functions
        await check_processing_functions(conn)
        
        # Step 4: Test job processor
        await test_job_processor()
        
        # Step 5: Test manual job creation
        await test_manual_job_creation(conn)
        
        # Step 6: Monitor queue activity
        await monitor_queue_activity(conn)
        
        print("\n✅ End-to-end validation complete!")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    finally:
        if conn:
            await conn.close()

async def check_current_status(conn):
    """Check current status of documents and jobs"""
    print("\n🔍 Step 1: Current System Status")
    print("-" * 40)
    
    # Check documents by status
    doc_stats = await conn.fetch("""
        SELECT 
            status, 
            COUNT(*) as count,
            MIN(created_at) as oldest,
            MAX(created_at) as newest
        FROM documents 
        GROUP BY status
        ORDER BY count DESC
    """)
    
    print("📄 Document Status Distribution:")
    total_docs = sum(row['count'] for row in doc_stats)
    for row in doc_stats:
        percentage = (row['count'] / total_docs * 100) if total_docs > 0 else 0
        print(f"   {row['status']}: {row['count']} ({percentage:.1f}%)")
        if row['status'] == 'pending':
            print(f"      Oldest pending: {row['oldest']}")
    
    # Check processing jobs
    job_stats = await conn.fetch("""
        SELECT 
            job_type,
            status, 
            COUNT(*) as count,
            AVG(retry_count) as avg_retries
        FROM processing_jobs 
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY job_type, status
        ORDER BY job_type, status
    """)
    
    print("\n📋 Processing Jobs (24h):")
    if job_stats:
        for row in job_stats:
            print(f"   {row['job_type']} → {row['status']}: {row['count']} (avg retries: {row['avg_retries']:.1f})")
    else:
        print("   No processing jobs found in last 24 hours")
    
    # Check for stuck jobs
    stuck_jobs = await conn.fetch("""
        SELECT 
            pj.id, d.original_filename, pj.job_type, pj.status,
            EXTRACT(EPOCH FROM (NOW() - pj.created_at)) / 60 as age_minutes
        FROM processing_jobs pj
        JOIN documents d ON pj.document_id = d.id
        WHERE pj.status = 'running' AND pj.created_at < NOW() - INTERVAL '30 minutes'
        ORDER BY pj.created_at
    """)
    
    if stuck_jobs:
        print(f"\n⚠️  Stuck Jobs ({len(stuck_jobs)}):")
        for job in stuck_jobs:
            print(f"   {job['job_type']} for {job['original_filename']} (running {job['age_minutes']:.1f}m)")
    else:
        print("\n✅ No stuck jobs found")

async def validate_queue_management(conn):
    """Validate queue management functions and triggers"""
    print("\n🔧 Step 2: Queue Management Validation")
    print("-" * 40)
    
    # Check if required functions exist
    functions_to_check = [
        'get_pending_jobs',
        'create_processing_job',
        'start_processing_job',
        'complete_processing_job',
        'fail_processing_job'
    ]
    
    for func_name in functions_to_check:
        try:
            exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_proc 
                    WHERE proname = $1
                )
            """, func_name)
            
            status = "✅" if exists else "❌"
            print(f"   {status} Function: {func_name}")
            
        except Exception as e:
            print(f"   ❌ Error checking {func_name}: {e}")
    
    # Test get_pending_jobs function
    try:
        pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(5)')
        print(f"\n📥 Pending Jobs: {len(pending_jobs)} ready for processing")
        
        if pending_jobs:
            for i, job in enumerate(pending_jobs[:3]):  # Show first 3
                print(f"   Job {i+1}: {job['job_type']} for document {job['document_id']}")
        
    except Exception as e:
        print(f"   ❌ Error getting pending jobs: {e}")

async def check_processing_functions(conn):
    """Check processing functions and edge functions"""
    print("\n⚙️  Step 3: Processing Functions Check")
    print("-" * 40)
    
    # Check if we have the required environment in edge functions
    edge_functions = [
        'doc-parser',
        'job-processor', 
        'link-assigner',
        'upload-handler'
    ]
    
    print("📡 Edge Functions Status:")
    for func in edge_functions:
        print(f"   {func}: Should be deployed")
    
    # Check database triggers
    triggers = await conn.fetch("""
        SELECT 
            trigger_name, 
            event_object_table,
            action_timing,
            event_manipulation
        FROM information_schema.triggers 
        WHERE trigger_schema = 'public'
        AND trigger_name LIKE '%document%' OR trigger_name LIKE '%job%'
    """)
    
    print(f"\n🔗 Database Triggers ({len(triggers)}):")
    for trigger in triggers:
        print(f"   {trigger['trigger_name']} on {trigger['event_object_table']}")

async def test_job_processor():
    """Test the job processor edge function"""
    print("\n🎯 Step 4: Testing Job Processor")
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
            
            async with session.post(job_processor_url, headers=headers, json={}) as response:
                status = response.status
                try:
                    response_data = await response.json()
                except:
                    response_data = await response.text()
                
                print(f"📞 Job Processor Response:")
                print(f"   Status: {status}")
                print(f"   Response: {response_data}")
                
                if status == 200:
                    print("   ✅ Job processor is accessible")
                else:
                    print("   ⚠️  Job processor may have issues")
                    
    except Exception as e:
        print(f"   ❌ Job processor test failed: {e}")

async def test_manual_job_creation(conn):
    """Test manual job creation for pending documents"""
    print("\n🔨 Step 5: Testing Manual Job Creation")
    print("-" * 40)
    
    # Find a pending document without jobs
    pending_doc = await conn.fetchrow("""
        SELECT d.id, d.original_filename
        FROM documents d
        LEFT JOIN processing_jobs pj ON d.id = pj.document_id
        WHERE d.status = 'pending' 
        AND pj.id IS NULL
        LIMIT 1
    """)
    
    if pending_doc:
        doc_id = pending_doc['id']
        filename = pending_doc['original_filename']
        
        print(f"📄 Found pending document: {filename}")
        print(f"   Creating manual processing job...")
        
        try:
            # Create a manual job
            job_id = await conn.fetchval("""
                SELECT create_processing_job(
                    $1::UUID,     -- document_id
                    'parse',      -- job_type
                    '{}'::JSONB,  -- payload
                    5,            -- priority
                    3,            -- max_retries
                    5             -- schedule_delay_seconds
                )
            """, doc_id)
            
            print(f"   ✅ Created job: {job_id}")
            
            # Verify job was created
            job_info = await conn.fetchrow("""
                SELECT status, created_at, scheduled_at
                FROM processing_jobs
                WHERE id = $1
            """, job_id)
            
            if job_info:
                print(f"   Status: {job_info['status']}")
                print(f"   Scheduled for: {job_info['scheduled_at']}")
            
        except Exception as e:
            print(f"   ❌ Manual job creation failed: {e}")
    else:
        print("📄 No pending documents found without jobs")

async def monitor_queue_activity(conn):
    """Monitor queue activity for a short period"""
    print("\n📊 Step 6: Queue Activity Monitoring")
    print("-" * 40)
    
    print("🔍 Monitoring for 30 seconds...")
    
    initial_stats = await get_queue_stats(conn)
    print(f"Initial state: {initial_stats}")
    
    # Wait and check again
    await asyncio.sleep(30)
    
    final_stats = await get_queue_stats(conn)
    print(f"After 30s: {final_stats}")
    
    # Calculate changes
    changes = {}
    for status in ['pending', 'running', 'completed', 'failed']:
        initial = initial_stats.get(status, 0)
        final = final_stats.get(status, 0)
        change = final - initial
        if change != 0:
            changes[status] = change
    
    if changes:
        print("\n📈 Changes detected:")
        for status, change in changes.items():
            direction = "+" if change > 0 else ""
            print(f"   {status}: {direction}{change}")
    else:
        print("\n📊 No queue activity detected")

async def get_queue_stats(conn):
    """Get current queue statistics"""
    stats = await conn.fetch("""
        SELECT status, COUNT(*) as count
        FROM processing_jobs
        WHERE created_at > NOW() - INTERVAL '1 hour'
        GROUP BY status
    """)
    
    return {row['status']: row['count'] for row in stats}

if __name__ == "__main__":
    asyncio.run(main()) 