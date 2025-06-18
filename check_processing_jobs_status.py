#!/usr/bin/env python3
"""
Check Processing Jobs Status
Monitors the processing jobs to see where they might be stuck
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

async def check_processing_status():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔍 Processing Jobs Status Check")
        print("=" * 50)
        
        # Check current processing jobs
        jobs = await conn.fetch("""
            SELECT 
                pj.id, pj.document_id, pj.job_type, pj.status, 
                pj.created_at, pj.started_at, pj.error_message,
                pj.retry_count, pj.max_retries,
                d.original_filename,
                EXTRACT(EPOCH FROM (NOW() - pj.created_at)) / 60 as age_minutes,
                EXTRACT(EPOCH FROM (NOW() - COALESCE(pj.started_at, pj.created_at))) / 60 as running_minutes
            FROM processing_jobs pj
            JOIN documents d ON pj.document_id = d.id
            WHERE pj.created_at > NOW() - INTERVAL '2 hours'
            ORDER BY pj.created_at DESC
            LIMIT 10
        """)
        
        if jobs:
            print(f"📋 Recent Processing Jobs ({len(jobs)}):")
            for job in jobs:
                status = job['status']
                age = job['age_minutes']
                running = job['running_minutes']
                
                status_emoji = {
                    'pending': '⏳',
                    'running': '🔄', 
                    'completed': '✅',
                    'failed': '❌',
                    'retrying': '🔁'
                }.get(status, '❓')
                
                print(f"\n   {status_emoji} Job {job['id']}")
                print(f"      📄 Document: {job['original_filename']}")
                print(f"      🔧 Type: {job['job_type']} | Status: {status}")
                print(f"      ⏱️  Age: {age:.1f}m | Running: {running:.1f}m")
                
                if job['retry_count'] and job['retry_count'] > 0:
                    print(f"      🔁 Retries: {job['retry_count']}/{job['max_retries'] or 3}")
                
                if job['error_message']:
                    print(f"      ❌ Error: {job['error_message']}")
        else:
            print("📋 No recent processing jobs found")
        
        # Check overall document status distribution
        print(f"\n📊 Document Status Distribution:")
        status_counts = await conn.fetch("""
            SELECT status, COUNT(*) as count
            FROM documents 
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY status
            ORDER BY count DESC
        """)
        
        for status in status_counts:
            print(f"   {status['status']}: {status['count']} documents")
        
        # Check if we need environment variables for processing
        print(f"\n🔍 Environment Variables Check:")
        required_env_vars = [
            'OPENAI_API_KEY',
            'LLAMAPARSE_API_KEY', 
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        # Check Edge Function secrets
        print(f"   📍 These should be set in Supabase Edge Functions:")
        for var in required_env_vars:
            print(f"   - {var}")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Check Supabase Edge Functions → Environment Variables")
        print(f"   2. Ensure OPENAI_API_KEY is set (for embeddings)")
        print(f"   3. Check Edge Function logs for detailed errors")
        print(f"   4. Monitor processing jobs for completion")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_processing_status()) 
"""
Check Processing Jobs Status
Monitors the processing jobs to see where they might be stuck
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

async def check_processing_status():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔍 Processing Jobs Status Check")
        print("=" * 50)
        
        # Check current processing jobs
        jobs = await conn.fetch("""
            SELECT 
                pj.id, pj.document_id, pj.job_type, pj.status, 
                pj.created_at, pj.started_at, pj.error_message,
                pj.retry_count, pj.max_retries,
                d.original_filename,
                EXTRACT(EPOCH FROM (NOW() - pj.created_at)) / 60 as age_minutes,
                EXTRACT(EPOCH FROM (NOW() - COALESCE(pj.started_at, pj.created_at))) / 60 as running_minutes
            FROM processing_jobs pj
            JOIN documents d ON pj.document_id = d.id
            WHERE pj.created_at > NOW() - INTERVAL '2 hours'
            ORDER BY pj.created_at DESC
            LIMIT 10
        """)
        
        if jobs:
            print(f"📋 Recent Processing Jobs ({len(jobs)}):")
            for job in jobs:
                status = job['status']
                age = job['age_minutes']
                running = job['running_minutes']
                
                status_emoji = {
                    'pending': '⏳',
                    'running': '🔄', 
                    'completed': '✅',
                    'failed': '❌',
                    'retrying': '🔁'
                }.get(status, '❓')
                
                print(f"\n   {status_emoji} Job {job['id']}")
                print(f"      📄 Document: {job['original_filename']}")
                print(f"      🔧 Type: {job['job_type']} | Status: {status}")
                print(f"      ⏱️  Age: {age:.1f}m | Running: {running:.1f}m")
                
                if job['retry_count'] and job['retry_count'] > 0:
                    print(f"      🔁 Retries: {job['retry_count']}/{job['max_retries'] or 3}")
                
                if job['error_message']:
                    print(f"      ❌ Error: {job['error_message']}")
        else:
            print("📋 No recent processing jobs found")
        
        # Check overall document status distribution
        print(f"\n📊 Document Status Distribution:")
        status_counts = await conn.fetch("""
            SELECT status, COUNT(*) as count
            FROM documents 
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY status
            ORDER BY count DESC
        """)
        
        for status in status_counts:
            print(f"   {status['status']}: {status['count']} documents")
        
        # Check if we need environment variables for processing
        print(f"\n🔍 Environment Variables Check:")
        required_env_vars = [
            'OPENAI_API_KEY',
            'LLAMAPARSE_API_KEY', 
            'SUPABASE_SERVICE_ROLE_KEY'
        ]
        
        # Check Edge Function secrets
        print(f"   📍 These should be set in Supabase Edge Functions:")
        for var in required_env_vars:
            print(f"   - {var}")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Check Supabase Edge Functions → Environment Variables")
        print(f"   2. Ensure OPENAI_API_KEY is set (for embeddings)")
        print(f"   3. Check Edge Function logs for detailed errors")
        print(f"   4. Monitor processing jobs for completion")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_processing_status()) 