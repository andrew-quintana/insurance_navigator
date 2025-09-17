#!/usr/bin/env python3
"""
Reset failed jobs for testing and HITL scenarios
"""

import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv

load_dotenv('.env.development')

async def reset_failed_jobs(job_ids=None, status_filter=None, reset_retry_count=True):
    """Reset failed jobs to allow retry"""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Build query based on parameters
        if job_ids:
            # Reset specific job IDs
            placeholders = ','.join([f'${i+1}' for i in range(len(job_ids))])
            query = f"""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'parse_queued', 
                    last_error = NULL,
                    updated_at = now()
                    {', retry_count = 0' if reset_retry_count else ''}
                WHERE job_id IN ({placeholders})
            """
            result = await conn.execute(query, *job_ids)
            print(f"✅ Reset {len(job_ids)} specific jobs")
            
        elif status_filter:
            # Reset jobs by status
            query = f"""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'parse_queued', 
                    last_error = NULL,
                    updated_at = now()
                    {', retry_count = 0' if reset_retry_count else ''}
                WHERE status = $1
            """
            result = await conn.execute(query, status_filter)
            print(f"✅ Reset jobs with status '{status_filter}'")
            
        else:
            # Reset all failed_parse jobs
            query = f"""
                UPDATE upload_pipeline.upload_jobs 
                SET status = 'parse_queued', 
                    last_error = NULL,
                    updated_at = now()
                    {', retry_count = 0' if reset_retry_count else ''}
                WHERE status = 'failed_parse'
            """
            result = await conn.execute(query)
            print(f"✅ Reset all failed_parse jobs")
        
        # Show current job statuses
        jobs = await conn.fetch("""
            SELECT job_id, status, state, retry_count, created_at, updated_at
            FROM upload_pipeline.upload_jobs 
            ORDER BY created_at DESC
        """)
        
        print(f"\n📊 Current Job Statuses ({len(jobs)} total):")
        for job in jobs:
            print(f"  {job['job_id']} - {job['status']}/{job['state']} - Retries: {job['retry_count']} - Updated: {job['updated_at']}")
        
    except Exception as e:
        print(f"❌ Error resetting jobs: {e}")
        raise
    finally:
        await conn.close()

async def show_job_statuses():
    """Show current job statuses"""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        jobs = await conn.fetch("""
            SELECT job_id, status, state, retry_count, last_error, created_at, updated_at
            FROM upload_pipeline.upload_jobs 
            ORDER BY created_at DESC
        """)
        
        print(f"📊 Current Job Statuses ({len(jobs)} total):")
        for job in jobs:
            error_info = f" - Error: {job['last_error'][:100]}..." if job['last_error'] else ""
            print(f"  {job['job_id']} - {job['status']}/{job['state']} - Retries: {job['retry_count']}{error_info}")
        
    except Exception as e:
        print(f"❌ Error showing job statuses: {e}")
        raise
    finally:
        await conn.close()

async def main():
    """Main function with command line interface"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "show":
            await show_job_statuses()
        elif command == "reset-all":
            await reset_failed_jobs()
        elif command == "reset-status":
            if len(sys.argv) < 3:
                print("Usage: python reset_failed_jobs.py reset-status <status>")
                return
            status = sys.argv[2]
            await reset_failed_jobs(status_filter=status)
        elif command == "reset-jobs":
            if len(sys.argv) < 3:
                print("Usage: python reset_failed_jobs.py reset-jobs <job_id1,job_id2,...>")
                return
            job_ids = sys.argv[2].split(',')
            await reset_failed_jobs(job_ids=job_ids)
        else:
            print("Unknown command. Available commands:")
            print("  show - Show current job statuses")
            print("  reset-all - Reset all failed_parse jobs")
            print("  reset-status <status> - Reset jobs with specific status")
            print("  reset-jobs <job_id1,job_id2,...> - Reset specific jobs")
    else:
        # Default: show statuses
        await show_job_statuses()

if __name__ == "__main__":
    asyncio.run(main())
