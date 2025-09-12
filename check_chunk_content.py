#!/usr/bin/env python3
"""
Check the actual content of chunks in the database.
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.production')

async def check_chunk_content():
    """Check the actual content of chunks."""
    try:
        # Connect to database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return
            
        conn = await asyncpg.connect(database_url)
        
        # Test user ID
        user_id = "b4b0c962-fd49-49b8-993b-4b14c8edc37b"
        
        print(f"🔍 Checking chunk content for user: {user_id}")
        print("=" * 50)
        
        # Check chunk content
        chunks_query = """
        SELECT c.chunk_id, c.document_id, c.chunk_ord, c.text, c.created_at
        FROM upload_pipeline.document_chunks c
        JOIN upload_pipeline.documents d ON c.document_id = d.document_id
        WHERE d.user_id = $1
        ORDER BY c.created_at DESC
        """
        
        chunks = await conn.fetch(chunks_query, user_id)
        print(f"📊 Found {len(chunks)} chunks:")
        
        for i, chunk in enumerate(chunks):
            print(f"\n📄 Chunk {i+1}:")
            print(f"  - ID: {chunk['chunk_id']}")
            print(f"  - Document ID: {chunk['document_id']}")
            print(f"  - Order: {chunk['chunk_ord']}")
            print(f"  - Created: {chunk['created_at']}")
            print(f"  - Content: {chunk['text'][:200]}...")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error checking chunk content: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_chunk_content())
