#!/usr/bin/env python3
"""
Debug UUID Validation - Check what's actually in the database
"""

import asyncio
import uuid
import asyncpg
from dotenv import load_dotenv
import os

async def main():
    load_dotenv('.env.production')
    database_url = os.getenv('DATABASE_URL')
    
    conn = await asyncpg.connect(database_url)
    
    # Get all documents
    documents = await conn.fetch("SELECT document_id, user_id, filename FROM upload_pipeline.documents LIMIT 5")
    
    print("Sample documents:")
    for doc in documents:
        print(f"  Document ID: {doc['document_id']}")
        print(f"  User ID: {doc['user_id']}")
        print(f"  Filename: {doc['filename']}")
        
        # Check UUID version
        try:
            uuid_obj = uuid.UUID(doc['document_id'])
            print(f"  UUID Version: {uuid_obj.version}")
            print(f"  Is UUIDv5: {uuid_obj.version == 5}")
        except Exception as e:
            print(f"  UUID Error: {e}")
        print()
    
    # Get all chunks
    chunks = await conn.fetch("SELECT chunk_id, document_id FROM upload_pipeline.document_chunks LIMIT 5")
    
    print("Sample chunks:")
    for chunk in chunks:
        print(f"  Chunk ID: {chunk['chunk_id']}")
        print(f"  Document ID: {chunk['document_id']}")
        
        # Check UUID version
        try:
            uuid_obj = uuid.UUID(chunk['chunk_id'])
            print(f"  UUID Version: {uuid_obj.version}")
            print(f"  Is UUIDv5: {uuid_obj.version == 5}")
        except Exception as e:
            print(f"  UUID Error: {e}")
        print()
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
