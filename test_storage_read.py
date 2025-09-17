#!/usr/bin/env python3
"""
Test storage manager read functionality
"""

import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from shared.storage.storage_manager import StorageManager

load_dotenv('.env.development')

async def test_storage_read():
    """Test reading parsed content from storage"""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    try:
        # Get a document with parsed content
        doc = await conn.fetchrow("""
            SELECT document_id, parsed_path, processing_status
            FROM upload_pipeline.documents 
            WHERE parsed_path IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        if not doc:
            print("❌ No documents with parsed content found")
            return
        
        print(f"📄 Testing document: {doc['document_id']}")
        print(f"📄 Parsed path: {doc['parsed_path']}")
        print(f"📄 Processing status: {doc['processing_status']}")
        
        # Initialize storage manager
        storage = StorageManager({
            "storage_url": "http://127.0.0.1:54321",
            "anon_key": "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
            "service_role_key": "***REMOVED***.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
        })
        
        # Test reading the parsed content
        print(f"\n🔍 Testing storage manager read...")
        try:
            content = await storage.read_blob(doc['parsed_path'])
            if content:
                print(f"✅ Successfully read parsed content!")
                print(f"📏 Content length: {len(content)}")
                print(f"📄 Content preview: {content[:200]}...")
            else:
                print(f"❌ Storage manager returned None")
        except Exception as e:
            print(f"❌ Storage manager read failed: {e}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
        
        await storage.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_storage_read())
