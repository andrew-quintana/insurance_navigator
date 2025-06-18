#!/usr/bin/env python3

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def check_job_schema():
    load_dotenv()
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0, 
        server_settings={'jit': 'off'}
    )
    
    try:
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'processing_jobs' 
            ORDER BY ordinal_position
        """)
        
        print('Processing_jobs table schema:')
        for col in columns:
            nullable = 'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'
            default = f' DEFAULT {col["column_default"]}' if col['column_default'] else ''
            print(f'  {col["column_name"]}: {col["data_type"]} {nullable}{default}')
    except Exception as e:
        print(f'Error: {e}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_job_schema()) 

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

async def check_job_schema():
    load_dotenv()
    conn = await asyncpg.connect(
        os.getenv('DATABASE_URL'), 
        statement_cache_size=0, 
        server_settings={'jit': 'off'}
    )
    
    try:
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'processing_jobs' 
            ORDER BY ordinal_position
        """)
        
        print('Processing_jobs table schema:')
        for col in columns:
            nullable = 'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'
            default = f' DEFAULT {col["column_default"]}' if col['column_default'] else ''
            print(f'  {col["column_name"]}: {col["data_type"]} {nullable}{default}')
    except Exception as e:
        print(f'Error: {e}')
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_job_schema()) 