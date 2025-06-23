#!/usr/bin/env python3
"""
Debug Upload Issue
Tests the specific database queries that are failing in production.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from db.services.db_pool import DatabasePool
from dotenv import load_dotenv

load_dotenv()

async def debug_upload_issue():
    """Debug the specific upload issue from the logs"""
    print("🔍 DEBUGGING UPLOAD PIPELINE ISSUE...")
    
    # Document ID from the latest upload attempt
    document_id = "08f7c250-c56f-4b5b-86ef-23b8553c83c1"
    
    try:
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        async with db_pool.get_connection() as conn:
            print("✅ Connected to production database")
            
            # Test 1: Check if document exists
            print(f"\n📋 TEST 1: Looking for document {document_id}")
            result = await conn.fetch("""
                SELECT id, user_id, original_filename, status, created_at, updated_at
                FROM documents 
                WHERE id = $1
            """, document_id)
            
            print(f"Documents found: {len(result)}")
            for doc in result:
                print(f"  - ID: {doc['id']}")
                print(f"  - User: {doc['user_id']}")
                print(f"  - Filename: {doc['original_filename']}")
                print(f"  - Status: {doc['status']}")
                print(f"  - Created: {doc['created_at']}")
                print(f"  - Updated: {doc['updated_at']}")
            
            # Test 2: Check for any duplicates
            print(f"\n📋 TEST 2: Checking for duplicate documents")
            result = await conn.fetch("""
                SELECT id, user_id, original_filename, status, created_at
                FROM documents 
                WHERE original_filename = 'scan_classic_hmo.pdf'
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            print(f"Documents with same filename: {len(result)}")
            for doc in result:
                print(f"  - ID: {doc['id'][:8]}... Status: {doc['status']} Created: {doc['created_at']}")
            
            # Test 3: Check documents table schema
            print(f"\n📋 TEST 3: Checking documents table schema")
            schema_result = await conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'documents' 
                ORDER BY ordinal_position
            """)
            
            print("Documents table columns:")
            for col in schema_result:
                print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
            
            # Test 4: Simulate the exact query from edge function
            print(f"\n📋 TEST 4: Simulating edge function query")
            try:
                edge_result = await conn.fetchrow("""
                    SELECT * FROM documents 
                    WHERE id = $1
                """, document_id)
                
                if edge_result:
                    print("✅ Edge function query would succeed")
                    print(f"Document found: {edge_result['original_filename']}")
                else:
                    print("❌ Edge function query would fail - no document found")
                    
            except Exception as e:
                print(f"❌ Edge function query would fail with error: {e}")
        
        await db_pool.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_upload_issue()) 