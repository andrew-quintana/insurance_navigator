#!/usr/bin/env python3
"""
Cleanup script to remove duplicate data from production database
that could cause conflicts when testing uploads from frontend UI.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

async def cleanup_duplicates():
    """Clean up duplicate data from production database."""
    
    # Connect to production database with proper SSL and pgbouncer settings
    conn = await asyncpg.connect(
        'postgresql://postgres.znvwzkdblknkkztqyfnu:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres?sslmode=require',
        statement_cache_size=0  # Fix pgbouncer prepared statement issue
    )
    
    try:
        print("🧹 Starting database cleanup...")
        
        # First, let's check what data exists
        print("\n📊 Checking existing data...")
        
        # Check documents table
        docs_result = await conn.fetch('''
            SELECT document_id, filename, created_at 
            FROM upload_pipeline.documents 
            WHERE filename IN ('scan_classic_hmo.pdf', 'simulated_insurance_document.pdf')
            ORDER BY created_at DESC
        ''')
        
        print(f"📄 Found {len(docs_result)} documents to clean up:")
        for doc in docs_result:
            print(f"  - {doc['document_id']}: {doc['filename']} ({doc['created_at']})")
        
        # Check upload_jobs table
        jobs_result = await conn.fetch('''
            SELECT job_id, document_id, status, created_at 
            FROM upload_pipeline.upload_jobs 
            WHERE document_id IN (
                SELECT document_id FROM upload_pipeline.documents 
                WHERE filename IN ('scan_classic_hmo.pdf', 'simulated_insurance_document.pdf')
            )
            ORDER BY created_at DESC
        ''')
        
        print(f"📋 Found {len(jobs_result)} upload jobs to clean up:")
        for job in jobs_result:
            print(f"  - {job['job_id']}: {job['status']} ({job['created_at']})")
        
        if len(docs_result) == 0 and len(jobs_result) == 0:
            print("✅ No duplicate data found - database is clean!")
            return
        
        # Clean up in correct order (foreign key constraints)
        print("\n🗑️ Cleaning up data...")
        
        # 1. Delete document_chunks first (references documents)
        chunks_result = await conn.execute('''
            DELETE FROM upload_pipeline.document_chunks 
            WHERE document_id IN (
                SELECT document_id FROM upload_pipeline.documents 
                WHERE filename IN ('scan_classic_hmo.pdf', 'simulated_insurance_document.pdf')
            )
        ''')
        print(f"✅ Deleted {chunks_result} document_chunks rows")
        
        # 2. Delete upload_jobs (references documents)
        jobs_result = await conn.execute('''
            DELETE FROM upload_pipeline.upload_jobs 
            WHERE document_id IN (
                SELECT document_id FROM upload_pipeline.documents 
                WHERE filename IN ('scan_classic_hmo.pdf', 'simulated_insurance_document.pdf')
            )
        ''')
        print(f"✅ Deleted {jobs_result} upload_jobs rows")
        
        # 3. Delete documents last
        docs_result = await conn.execute('''
            DELETE FROM upload_pipeline.documents 
            WHERE filename IN ('scan_classic_hmo.pdf', 'simulated_insurance_document.pdf')
        ''')
        print(f"✅ Deleted {docs_result} documents rows")
        
        print("\n🎉 Database cleanup completed successfully!")
        print("✅ Ready for frontend UI testing without duplicates")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())
