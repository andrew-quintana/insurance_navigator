#!/usr/bin/env python3
"""
Check chunks for a specific user in both tables.
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.production')

async def check_user_chunks():
    """Check chunks for a specific user."""
    try:
        # Connect to database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return
            
        conn = await asyncpg.connect(database_url)
        
        # Test user ID
        user_id = "b4b0c962-fd49-49b8-993b-4b14c8edc37b"
        
        print(f"🔍 Checking chunks for user: {user_id}")
        print("=" * 50)
        
        # Check upload_pipeline.document_chunks
        print("\n📊 Checking upload_pipeline.document_chunks:")
        upload_chunks_query = """
        SELECT COUNT(*) as chunk_count,
               MIN(c.created_at) as first_chunk,
               MAX(c.created_at) as last_chunk
        FROM upload_pipeline.document_chunks c
        JOIN upload_pipeline.documents d ON c.document_id = d.document_id
        WHERE d.user_id = $1
        """
        
        upload_chunks = await conn.fetchrow(upload_chunks_query, user_id)
        print(f"  - Chunks: {upload_chunks['chunk_count']}")
        print(f"  - First chunk: {upload_chunks['first_chunk']}")
        print(f"  - Last chunk: {upload_chunks['last_chunk']}")
        
        # Check documents.document_chunks
        print("\n📊 Checking documents.document_chunks:")
        docs_chunks_query = """
        SELECT COUNT(*) as chunk_count,
               MIN(c.created_at) as first_chunk,
               MAX(c.created_at) as last_chunk
        FROM documents.document_chunks c
        JOIN documents.documents d ON c.document_id = d.document_id
        WHERE d.user_id = $1
        """
        
        docs_chunks = await conn.fetchrow(docs_chunks_query, user_id)
        print(f"  - Chunks: {docs_chunks['chunk_count']}")
        print(f"  - First chunk: {docs_chunks['first_chunk']}")
        print(f"  - Last chunk: {docs_chunks['last_chunk']}")
        
        # Check all users with chunks in upload_pipeline
        print("\n👥 All users with chunks in upload_pipeline:")
        all_upload_chunks_query = """
        SELECT d.user_id, COUNT(c.chunk_id) as chunk_count
        FROM upload_pipeline.documents d
        LEFT JOIN upload_pipeline.document_chunks c ON d.document_id = c.document_id
        GROUP BY d.user_id
        ORDER BY chunk_count DESC
        """
        
        all_upload_chunks = await conn.fetch(all_upload_chunks_query)
        for user in all_upload_chunks:
            print(f"  - {user['user_id']}: {user['chunk_count']} chunks")
        
        # Check all users with chunks in documents
        print("\n👥 All users with chunks in documents:")
        all_docs_chunks_query = """
        SELECT d.user_id, COUNT(c.chunk_id) as chunk_count
        FROM documents.documents d
        LEFT JOIN documents.document_chunks c ON d.document_id = c.document_id
        GROUP BY d.user_id
        ORDER BY chunk_count DESC
        """
        
        all_docs_chunks = await conn.fetch(all_docs_chunks_query)
        for user in all_docs_chunks:
            print(f"  - {user['user_id']}: {user['chunk_count']} chunks")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error checking user chunks: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_chunks())
