#!/usr/bin/env python3
"""
Direct database check to see if there are any existing chunks.
This bypasses the API and checks the database directly.
"""

import asyncio
import asyncpg
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_database_directly():
    """Check the database directly for existing chunks and documents."""
    
    # Use the production database URL from the example
    DATABASE_URL = "postgresql://postgres:password@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres"
    
    try:
        # Connect to database
        logger.info("Connecting to production database...")
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("✅ Connected to database successfully")
        
        # Check documents table
        logger.info("Checking documents table...")
        documents = await conn.fetch("""
            SELECT document_id, user_id, filename, created_at, processing_status
            FROM upload_pipeline.documents 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        logger.info(f"Found {len(documents)} documents:")
        for doc in documents:
            logger.info(f"  - {doc['document_id']}: {doc['filename']} (status: {doc['processing_status']}, user: {doc['user_id']})")
        
        # Check chunks table
        logger.info("Checking chunks table...")
        chunks = await conn.fetch("""
            SELECT chunk_id, document_id, user_id, chunk_index, text_preview, created_at
            FROM upload_pipeline.document_chunks 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        logger.info(f"Found {len(chunks)} chunks:")
        for chunk in chunks:
            text_preview = chunk['text_preview'][:100] + "..." if chunk['text_preview'] and len(chunk['text_preview']) > 100 else chunk['text_preview']
            logger.info(f"  - {chunk['chunk_id']}: doc={chunk['document_id']}, index={chunk['chunk_index']}, text='{text_preview}'")
        
        # Check upload jobs table
        logger.info("Checking upload jobs table...")
        jobs = await conn.fetch("""
            SELECT job_id, document_id, status, state, progress, retry_count, last_error, created_at
            FROM upload_pipeline.upload_jobs 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        logger.info(f"Found {len(jobs)} jobs:")
        for job in jobs:
            logger.info(f"  - {job['job_id']}: doc={job['document_id']}, status={job['status']}, state={job['state']}, progress={job['progress']}")
            if job['last_error']:
                logger.info(f"    Error: {job['last_error']}")
        
        # Check embeddings table
        logger.info("Checking embeddings table...")
        embeddings = await conn.fetch("""
            SELECT embedding_id, chunk_id, document_id, user_id, created_at
            FROM upload_pipeline.embeddings 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        logger.info(f"Found {len(embeddings)} embeddings:")
        for emb in embeddings:
            logger.info(f"  - {emb['embedding_id']}: chunk={emb['chunk_id']}, doc={emb['document_id']}")
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 DATABASE SUMMARY")
        logger.info("=" * 60)
        logger.info(f"📄 Documents: {len(documents)}")
        logger.info(f"🧩 Chunks: {len(chunks)}")
        logger.info(f"⚙️  Jobs: {len(jobs)}")
        logger.info(f"🔢 Embeddings: {len(embeddings)}")
        logger.info("=" * 60)
        
        if len(chunks) > 0:
            logger.info("🎉 CHUNKS FOUND! The system is working and has processed documents.")
        else:
            logger.info("❌ NO CHUNKS FOUND. The system hasn't successfully processed any documents yet.")
        
        await conn.close()
        logger.info("Database connection closed.")
        
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(check_database_directly())
