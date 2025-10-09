#!/usr/bin/env python3
"""
Quick script to check if user has chunks in the database.
This will help verify if the zero-chunk issue is due to missing data.
"""

import asyncio
import asyncpg
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env.production
load_dotenv('.env.production')

# Production Supabase configuration
# Note: There are TWO Supabase projects:
# 1. Frontend (UI): https://znvwzkdblknkkztqyfnu.supabase.co
# 2. Backend/API: https://mrbigmtnadjtyepxqefa.supabase.co
# The backend uses the second one for RAG operations

PRODUCTION_CONFIG = {
    "host": "db.mrbigmtnadjtyepxqefa.supabase.co",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": os.getenv("DATABASE_URL", "").split("@")[0].split(":")[-1] if os.getenv("DATABASE_URL") else "",  # Extract password from DATABASE_URL
    "ssl": "require"
}

TEST_USER_ID = "cae3b3ec-b355-4509-bd4e-0f7da8cb2858"

async def check_user_chunks():
    """Check if the test user has chunks in the database."""
    conn = None
    try:
        # Create connection string
        conn_str = f"postgresql://{PRODUCTION_CONFIG['user']}:{PRODUCTION_CONFIG['password']}@{PRODUCTION_CONFIG['host']}:{PRODUCTION_CONFIG['port']}/{PRODUCTION_CONFIG['database']}?sslmode=require"
        
        print(f"Connecting to database: {PRODUCTION_CONFIG['host']}")
        conn = await asyncpg.connect(conn_str)
        
        # Check if user has any documents
        print(f"\n=== Checking documents for user: {TEST_USER_ID} ===")
        doc_count_query = """
            SELECT COUNT(*) as document_count 
            FROM upload_pipeline.documents 
            WHERE user_id = $1
        """
        doc_result = await conn.fetchrow(doc_count_query, TEST_USER_ID)
        doc_count = doc_result['document_count']
        print(f"Documents found: {doc_count}")
        
        # Check if user has any chunks with embeddings
        print(f"\n=== Checking chunks with embeddings ===")
        chunk_count_query = """
            SELECT COUNT(*) as chunk_count 
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $1
            AND dc.embedding IS NOT NULL
        """
        chunk_result = await conn.fetchrow(chunk_count_query, TEST_USER_ID)
        chunk_count = chunk_result['chunk_count']
        print(f"Chunks with embeddings: {chunk_count}")
        
        # Check total chunks (with and without embeddings)
        print(f"\n=== Checking total chunks ===")
        total_chunks_query = """
            SELECT 
                COUNT(*) as total_chunks,
                COUNT(CASE WHEN dc.embedding IS NOT NULL THEN 1 END) as chunks_with_embeddings,
                COUNT(CASE WHEN dc.embedding IS NULL THEN 1 END) as chunks_without_embeddings
            FROM upload_pipeline.document_chunks dc
            JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
            WHERE d.user_id = $1
        """
        total_result = await conn.fetchrow(total_chunks_query, TEST_USER_ID)
        print(f"Total chunks: {total_result['total_chunks']}")
        print(f"Chunks with embeddings: {total_result['chunks_with_embeddings']}")
        print(f"Chunks without embeddings: {total_result['chunks_without_embeddings']}")
        
        # Check document details
        print(f"\n=== Checking document details ===")
        doc_details_query = """
            SELECT 
                d.document_id,
                d.filename,
                d.created_at,
                COUNT(dc.chunk_id) as chunk_count
            FROM upload_pipeline.documents d
            LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
            WHERE d.user_id = $1
            GROUP BY d.document_id, d.filename, d.created_at
            ORDER BY d.created_at DESC
        """
        doc_details = await conn.fetch(doc_details_query, TEST_USER_ID)
        print("Document details:")
        for row in doc_details:
            print(f"  {row['filename']}: {row['chunk_count']} chunks, created {row['created_at']}")
        
        # Check recent upload jobs
        print(f"\n=== Checking recent upload jobs ===")
        upload_jobs_query = """
            SELECT 
                uj.job_id,
                uj.status,
                uj.created_at,
                d.filename,
                d.document_type
            FROM upload_pipeline.upload_jobs uj
            JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
            WHERE d.user_id = $1
            ORDER BY uj.created_at DESC
            LIMIT 10
        """
        upload_jobs = await conn.fetch(upload_jobs_query, TEST_USER_ID)
        print("Recent upload jobs:")
        for row in upload_jobs:
            print(f"  {row['created_at']}: {row['filename']} ({row['document_type']}) - Status: {row['status']}")
        
        # Summary
        print(f"\n=== SUMMARY ===")
        if doc_count == 0:
            print("❌ NO DOCUMENTS found for this user")
            print("   → This explains the zero-chunk issue")
            print("   → Need to investigate upload pipeline")
        elif chunk_count == 0:
            print("❌ NO CHUNKS WITH EMBEDDINGS found")
            print("   → Documents exist but no chunks/embeddings")
            print("   → Need to investigate chunk generation process")
        else:
            print(f"✅ FOUND {chunk_count} chunks with embeddings")
            print("   → Data exists, issue is likely in retrieval logic")
            print("   → Focus on embedding generation or database query issues")
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   → Check database credentials and network connectivity")
        return False
    finally:
        if conn:
            await conn.close()
    
    return True

if __name__ == "__main__":
    print("FM-038 Database Chunk Verification")
    print("=" * 50)
    asyncio.run(check_user_chunks())
