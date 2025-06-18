#!/usr/bin/env python3

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def fix_stuck_queue():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print('🔧 Fixing Stuck Queue Processing')
    print('=' * 50)
    
    # Find jobs stuck in 'running' status for > 5 minutes
    stuck_jobs = await conn.fetch('''
        SELECT id, document_id, job_type, created_at,
               EXTRACT(EPOCH FROM (NOW() - created_at))/60 as age_minutes
        FROM processing_jobs 
        WHERE status = 'running' 
        AND created_at < NOW() - INTERVAL '5 minutes'
        ORDER BY created_at
    ''')
    
    print(f'🚨 Found {len(stuck_jobs)} stuck jobs')
    
    if len(stuck_jobs) == 0:
        print('✅ No stuck jobs to fix')
        await conn.close()
        return
    
    for job in stuck_jobs:
        print(f'   🔄 {job["id"]} - {job["job_type"]} - {job["age_minutes"]:.1f} min old')
    
    # Reset stuck jobs to 'pending' status
    reset_count = await conn.execute('''
        UPDATE processing_jobs 
        SET status = 'pending',
            updated_at = NOW(),
            retry_count = retry_count + 1
        WHERE status = 'running' 
        AND created_at < NOW() - INTERVAL '5 minutes'
    ''')
    
    print(f'\n✅ Reset {reset_count.split()[-1]} stuck jobs to pending')
    
    # Verify the fix
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f'📋 get_pending_jobs() now returns: {len(pending_jobs)} jobs')
    
    # Update documents that were stuck in parsing
    doc_update_count = await conn.execute('''
        UPDATE documents 
        SET status = 'pending',
            progress_percentage = 0,
            updated_at = NOW()
        WHERE status = 'parsing'
        AND updated_at < NOW() - INTERVAL '5 minutes'
    ''')
    
    print(f'📄 Reset {doc_update_count.split()[-1]} documents from parsing to pending')
    
    print('\n🎉 Queue should now be processing! Test with the Edge Functions.')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_stuck_queue()) 

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def fix_stuck_queue():
    load_dotenv()
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    print('🔧 Fixing Stuck Queue Processing')
    print('=' * 50)
    
    # Find jobs stuck in 'running' status for > 5 minutes
    stuck_jobs = await conn.fetch('''
        SELECT id, document_id, job_type, created_at,
               EXTRACT(EPOCH FROM (NOW() - created_at))/60 as age_minutes
        FROM processing_jobs 
        WHERE status = 'running' 
        AND created_at < NOW() - INTERVAL '5 minutes'
        ORDER BY created_at
    ''')
    
    print(f'🚨 Found {len(stuck_jobs)} stuck jobs')
    
    if len(stuck_jobs) == 0:
        print('✅ No stuck jobs to fix')
        await conn.close()
        return
    
    for job in stuck_jobs:
        print(f'   🔄 {job["id"]} - {job["job_type"]} - {job["age_minutes"]:.1f} min old')
    
    # Reset stuck jobs to 'pending' status
    reset_count = await conn.execute('''
        UPDATE processing_jobs 
        SET status = 'pending',
            updated_at = NOW(),
            retry_count = retry_count + 1
        WHERE status = 'running' 
        AND created_at < NOW() - INTERVAL '5 minutes'
    ''')
    
    print(f'\n✅ Reset {reset_count.split()[-1]} stuck jobs to pending')
    
    # Verify the fix
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f'📋 get_pending_jobs() now returns: {len(pending_jobs)} jobs')
    
    # Update documents that were stuck in parsing
    doc_update_count = await conn.execute('''
        UPDATE documents 
        SET status = 'pending',
            progress_percentage = 0,
            updated_at = NOW()
        WHERE status = 'parsing'
        AND updated_at < NOW() - INTERVAL '5 minutes'
    ''')
    
    print(f'📄 Reset {doc_update_count.split()[-1]} documents from parsing to pending')
    
    print('\n🎉 Queue should now be processing! Test with the Edge Functions.')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_stuck_queue()) 