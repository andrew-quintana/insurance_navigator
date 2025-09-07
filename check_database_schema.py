#!/usr/bin/env python3
"""
Check database schema for upload pipeline
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def check_schema():
    load_dotenv('.env.production')
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Check upload_pipeline schema
        schema_check = await conn.fetchval(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = $1", 
            'upload_pipeline'
        )
        print(f'✅ upload_pipeline schema exists: {schema_check is not None}')
        
        # Check tables
        tables = await conn.fetch('''
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'upload_pipeline'
            ORDER BY table_name
        ''')
        print(f'📋 Tables in upload_pipeline schema:')
        for table in tables:
            print(f'  - {table["table_name"]}')
        
        # Check upload_jobs constraint
        constraint_check = await conn.fetchval('''
            SELECT constraint_name 
            FROM information_schema.check_constraints 
            WHERE constraint_name = 'ck_upload_jobs_status'
        ''')
        print(f'✅ ck_upload_jobs_status constraint exists: {constraint_check is not None}')
        
        # Check allowed statuses
        if constraint_check:
            allowed_statuses = await conn.fetchval('''
                SELECT check_clause 
                FROM information_schema.check_constraints 
                WHERE constraint_name = 'ck_upload_jobs_status'
            ''')
            print(f'📋 Allowed statuses: {allowed_statuses}')
        
        # Check recent jobs
        recent_jobs = await conn.fetch('''
            SELECT job_id, status, state, created_at 
            FROM upload_pipeline.upload_jobs 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        print(f'📊 Recent jobs:')
        for job in recent_jobs:
            print(f'  - {job["job_id"]}: {job["status"]} ({job["state"]}) at {job["created_at"]}')
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_schema())
