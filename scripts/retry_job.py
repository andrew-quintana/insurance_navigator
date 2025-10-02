#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv('.env.staging')

async def retry_failed_job():
    database_url = os.getenv('DATABASE_URL')
    
    conn = await asyncpg.connect(database_url)
    
    try:
        # Retry the failed job
        job_id = '44903e5e-3def-4f6c-81ab-c0383a8c9f05'
        
        # Reset the job to uploaded status so it gets picked up by the worker
        await conn.execute('''
            UPDATE upload_pipeline.upload_jobs
            SET status = 'uploaded', last_error = NULL, updated_at = NOW()
            WHERE job_id = $1
        ''', job_id)
        
        print(f'Reset job {job_id} to uploaded status - worker should pick it up now')
        
        # Check the job status
        job = await conn.fetchrow('''
            SELECT job_id, status, created_at, updated_at
            FROM upload_pipeline.upload_jobs
            WHERE job_id = $1
        ''', job_id)
        
        if job:
            print(f'Job status: {job["status"]} (updated: {job["updated_at"]})')
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(retry_failed_job())
