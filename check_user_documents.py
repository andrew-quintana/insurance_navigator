#!/usr/bin/env python3
"""
Check if documents exist for a user in the database.
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.production')

async def check_user_documents():
    """Check documents for a specific user."""
    try:
        # Connect to database
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found in environment")
            return
            
        conn = await asyncpg.connect(database_url)
        
        # Test user ID
        user_id = "b4b0c962-fd49-49b8-993b-4b14c8edc37b"
        
        print(f"🔍 Checking documents for user: {user_id}")
        print("=" * 50)
        
        # Check documents table
        documents_query = """
        SELECT document_id, filename, created_at
        FROM upload_pipeline.documents 
        WHERE user_id = $1
        ORDER BY created_at DESC
        """
        
        documents = await conn.fetch(documents_query, user_id)
        print(f"📄 Documents found: {len(documents)}")
        
        for doc in documents:
            print(f"  - {doc['filename']} (ID: {doc['document_id']}, Created: {doc['created_at']})")
        
        # Check what tables exist
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'upload_pipeline'
        ORDER BY table_name
        """
        
        tables = await conn.fetch(tables_query)
        print(f"\n📊 Available tables in upload_pipeline schema:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check if there's a different chunks table
        all_tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%chunk%'
        ORDER BY table_name
        """
        
        chunk_tables = await conn.fetch(all_tables_query)
        print(f"\n📊 Tables with 'chunk' in name:")
        for table in chunk_tables:
            print(f"  - {table['table_name']}")
        
        # Check all users with documents
        all_users_query = """
        SELECT d.user_id, COUNT(*) as doc_count
        FROM upload_pipeline.documents d
        GROUP BY d.user_id
        ORDER BY doc_count DESC
        """
        
        all_users = await conn.fetch(all_users_query)
        print(f"\n👥 All users with documents:")
        for user in all_users:
            print(f"  - {user['user_id']}: {user['doc_count']} docs")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error checking documents: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_user_documents())
