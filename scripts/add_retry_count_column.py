#!/usr/bin/env python3
"""
Add retry_count column to upload_jobs table
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv('.env.development')

async def add_retry_count_column():
    """Add retry_count column to upload_jobs table"""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Check if column already exists
        result = await conn.fetchval("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'upload_pipeline' 
            AND table_name = 'upload_jobs' 
            AND column_name = 'retry_count'
        """)
        
        if result:
            print("✅ retry_count column already exists")
            return
        
        # Add retry_count column
        await conn.execute("""
            ALTER TABLE upload_pipeline.upload_jobs 
            ADD COLUMN retry_count INTEGER DEFAULT 0
        """)
        
        print("✅ Added retry_count column to upload_jobs table")
        
        # Update existing failed_parse jobs to have retry_count = 0
        await conn.execute("""
            UPDATE upload_pipeline.upload_jobs 
            SET retry_count = 0 
            WHERE status = 'failed_parse' AND retry_count IS NULL
        """)
        
        print("✅ Updated existing failed_parse jobs with retry_count = 0")
        
    except Exception as e:
        print(f"❌ Error adding retry_count column: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_retry_count_column())
