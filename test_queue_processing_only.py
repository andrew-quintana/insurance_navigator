#!/usr/bin/env python3
"""
Queue Processing Test
Tests the queue processing pipeline with existing documents:
1. Check existing pending documents
2. Trigger job processing manually
3. Monitor job execution
4. Validate queue management
"""

import asyncio
import asyncpg
import aiohttp
import json
from datetime import datetime, timezone

# Configuration
DATABASE_URL = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
SUPABASE_URL = 'https://jhrespvvhbnloxrieycf.supabase.co'
SERVICE_ROLE_KEY = '***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpocmVzcHZ2aGJubG94cmleeeWNmIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczMDIyNDgzNiwiZXhwIjoyMDQ1ODAwODM2fQ.m4lgWEY6lUQ7O4_iHp5QYHY-nxRxNSMpWZJR4S7xCZo'

async def main():
    """Test queue processing with existing documents"""
    print("🔄 Queue Processing Test")
    print("=" * 50)
    
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        # Step 1: Check current queue state
        await check_current_queue_state(conn)
        
        # Step 2: Manually trigger job processing multiple times
        await trigger_multiple_job_processing()
        
        # Step 3: Monitor processing activity
        await monitor_processing_activity(conn)
        
        # Step 4: Analyze results
        await analyze_processing_results(conn)
        
        print("\n✅ Queue processing test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await conn.close()

async def check_current_queue_state(conn):
    """Check the current state of documents and jobs"""
    print("\n📊 Step 1: Current Queue State")
    print("-" * 40)
    
    # Check pending jobs ready for processing
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f"📥 Pending jobs ready: {len(pending_jobs)}")
    
    if pending_jobs:
        print("   Ready jobs:")
        for i, job in enumerate(pending_jobs[:5]):  # Show first 5
            print(f"   {i+1}. {job['job_type']} for document {job['document_id']}")
    
    # Check job status distribution
    job_stats = await conn.fetch("""
        SELECT 
            status, 
            COUNT(*) as count,
            MIN(created_at) as oldest,
            MAX(updated_at) as newest
        FROM processing_jobs 
        WHERE created_at > NOW() - INTERVAL '6 hours'
        GROUP BY status
        ORDER BY count DESC
    """)
    
    print(f"\n📋 Job Status Distribution (6h):")
    for stat in job_stats:
        print(f"   {stat['status']}: {stat['count']} jobs")
        if stat['status'] == 'failed':
            print(f"      Oldest: {stat['oldest']}")
    
    # Check document status
    doc_stats = await conn.fetch("""
        SELECT status, COUNT(*) as count
        FROM documents 
        GROUP BY status
        ORDER BY count DESC
    """)
    
    print(f"\n📄 Document Status Distribution:")
    for stat in doc_stats:
        print(f"   {stat['status']}: {stat['count']} documents")

async def trigger_multiple_job_processing():
    """Trigger job processing multiple times to see activity"""
    print("\n🔄 Step 2: Triggering Job Processing")
    print("-" * 40)
    
    timeout = aiohttp.ClientTimeout(total=60)
    headers = {
        'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json',
        'apikey': SERVICE_ROLE_KEY
    }
    
    print("📞 Calling job processor multiple times...")
    
    results = []
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        job_processor_url = f"{SUPABASE_URL}/functions/v1/job-processor"
        
        for attempt in range(3):  # Try 3 times
            print(f"\n   Attempt {attempt + 1}:")
            
            try:
                async with session.post(job_processor_url, headers=headers, json={}) as response:
                    status = response.status
                    try:
                        response_data = await response.json()
                    except:
                        response_data = await response.text()
                    
                    print(f"   Status: {status}")
                    print(f"   Response: {response_data}")
                    
                    results.append({
                        'attempt': attempt + 1,
                        'status': status,
                        'response': response_data
                    })
                    
                    if status == 200:
                        processed = response_data.get('processed', 0) if isinstance(response_data, dict) else 0
                        if processed > 0:
                            print(f"   ✅ Processed {processed} jobs")
                        else:
                            print(f"   ℹ️  No jobs processed")
                    else:
                        print(f"   ⚠️  Unexpected status: {status}")
                        
            except Exception as e:
                print(f"   ❌ Request failed: {e}")
                results.append({
                    'attempt': attempt + 1,
                    'status': 'error',
                    'response': str(e)
                })
            
            # Wait between attempts
            if attempt < 2:
                await asyncio.sleep(5)
    
    return results

async def monitor_processing_activity(conn):
    """Monitor processing activity for a period"""
    print("\n📊 Step 3: Monitoring Processing Activity")
    print("-" * 40)
    
    print("🔍 Taking baseline measurement...")
    
    # Get baseline
    baseline = await get_processing_stats(conn)
    print(f"Baseline: {baseline}")
    
    print("\n⏱️  Waiting 60 seconds for processing activity...")
    await asyncio.sleep(60)
    
    # Get final measurement
    final = await get_processing_stats(conn)
    print(f"After 60s: {final}")
    
    # Calculate changes
    changes = {}
    for status in ['pending', 'running', 'completed', 'failed']:
        baseline_count = baseline.get(status, 0)
        final_count = final.get(status, 0)
        change = final_count - baseline_count
        if change != 0:
            changes[status] = change
    
    print(f"\n📈 Activity detected:")
    if changes:
        for status, change in changes.items():
            direction = "+" if change > 0 else ""
            print(f"   {status}: {direction}{change}")
        
        # Analyze activity
        completed_increase = changes.get('completed', 0)
        failed_increase = changes.get('failed', 0)
        running_change = changes.get('running', 0)
        
        if completed_increase > 0:
            print(f"   ✅ Progress: {completed_increase} jobs completed")
        
        if failed_increase > 0:
            print(f"   ❌ Issues: {failed_increase} jobs failed")
        
        if running_change > 0:
            print(f"   🔄 Activity: {running_change} new jobs started")
        elif running_change < 0:
            print(f"   📉 Completion: {abs(running_change)} jobs finished")
            
    else:
        print("   📊 No processing activity detected")

async def analyze_processing_results(conn):
    """Analyze the processing results"""
    print("\n🔬 Step 4: Analyzing Processing Results")
    print("-" * 40)
    
    # Check recent job activity
    recent_jobs = await conn.fetch("""
        SELECT 
            pj.id, pj.job_type, pj.status, 
            pj.created_at, pj.started_at, pj.completed_at,
            pj.error_message, d.original_filename,
            EXTRACT(EPOCH FROM (COALESCE(pj.completed_at, pj.updated_at) - pj.created_at)) as duration_seconds
        FROM processing_jobs pj
        JOIN documents d ON pj.document_id = d.id
        WHERE pj.updated_at > NOW() - INTERVAL '30 minutes'
        ORDER BY pj.updated_at DESC
        LIMIT 10
    """)
    
    if recent_jobs:
        print(f"📋 Recent Job Activity ({len(recent_jobs)} jobs):")
        for job in recent_jobs:
            status_emoji = {
                'pending': '⏳', 'running': '🔄', 'completed': '✅', 
                'failed': '❌', 'retrying': '🔁'
            }.get(job['status'], '❓')
            
            duration = f"{job['duration_seconds']:.1f}s" if job['duration_seconds'] else "N/A"
            
            print(f"\n   {status_emoji} {job['job_type']} - {job['original_filename']}")
            print(f"      Status: {job['status']} | Duration: {duration}")
            
            if job['error_message']:
                print(f"      Error: {job['error_message']}")
    else:
        print("📋 No recent job activity found")
    
    # Check for documents that completed processing
    completed_docs = await conn.fetch("""
        SELECT 
            d.id, d.original_filename, d.status, d.progress_percentage,
            d.processing_completed_at, d.extracted_text_length
        FROM documents d
        WHERE d.updated_at > NOW() - INTERVAL '30 minutes'
        AND d.status IN ('completed', 'failed')
        ORDER BY d.updated_at DESC
        LIMIT 5
    """)
    
    if completed_docs:
        print(f"\n📄 Recently Processed Documents ({len(completed_docs)}):")
        for doc in completed_docs:
            status_emoji = "✅" if doc['status'] == 'completed' else "❌"
            text_length = doc['extracted_text_length'] or 0
            
            print(f"   {status_emoji} {doc['original_filename']}")
            print(f"      Status: {doc['status']} ({doc['progress_percentage']}%)")
            print(f"      Text extracted: {text_length} chars")
    else:
        print(f"\n📄 No documents completed processing recently")
    
    # Overall health assessment
    print(f"\n🏥 Queue Health Assessment:")
    
    # Check if jobs are being processed
    processing_activity = len(recent_jobs) > 0
    successful_completions = len([j for j in recent_jobs if j['status'] == 'completed']) > 0
    
    if processing_activity:
        print("   ✅ Queue is active - jobs are being processed")
    else:
        print("   ⚠️  No recent job activity detected")
    
    if successful_completions:
        print("   ✅ Jobs are completing successfully")
    else:
        print("   ⚠️  No successful job completions recently")
    
    # Check for stuck or failed jobs
    stuck_jobs = await conn.fetchval("""
        SELECT COUNT(*)
        FROM processing_jobs
        WHERE status = 'running' 
        AND created_at < NOW() - INTERVAL '30 minutes'
    """)
    
    if stuck_jobs == 0:
        print("   ✅ No stuck jobs detected")
    else:
        print(f"   ⚠️  {stuck_jobs} stuck jobs found")

async def get_processing_stats(conn):
    """Get current processing statistics"""
    stats = await conn.fetch("""
        SELECT status, COUNT(*) as count
        FROM processing_jobs
        WHERE created_at > NOW() - INTERVAL '2 hours'
        GROUP BY status
    """)
    
    return {row['status']: row['count'] for row in stats}

if __name__ == "__main__":
    asyncio.run(main()) 