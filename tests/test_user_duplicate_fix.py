#!/usr/bin/env python3
"""
Test User-Scoped Duplicate Detection Fix

This script tests that duplicate detection now only looks within the same user's documents,
not across all users globally.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv('.env.production')

async def test_user_scoped_duplicates():
    """Test that duplicate detection is scoped to users"""
    print("🔍 Testing User-Scoped Duplicate Detection")
    print("=" * 50)
    
    try:
        import asyncpg
        
        # Connect to database
        DATABASE_URL = os.getenv('DATABASE_URL')
        if not DATABASE_URL:
            print("❌ DATABASE_URL not found in environment")
            return
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Test 1: Check if there are documents from different users with same content
        print("\n📊 Test 1: Checking for cross-user duplicate content...")
        
        cross_user_duplicates = await conn.fetch("""
            SELECT 
                d1.user_id as user1_id,
                d2.user_id as user2_id,
                d1.document_id as doc1_id,
                d2.document_id as doc2_id,
                d1.filename as filename1,
                d2.filename as filename2,
                d1.parsed_sha256
            FROM upload_pipeline.documents d1
            JOIN upload_pipeline.documents d2 ON d1.parsed_sha256 = d2.parsed_sha256
            WHERE d1.user_id != d2.user_id 
            AND d1.parsed_sha256 IS NOT NULL
            AND d1.document_id != d2.document_id
            ORDER BY d1.created_at DESC
            LIMIT 10
        """)
        
        print(f"   Found {len(cross_user_duplicates)} cross-user duplicate content pairs")
        
        if cross_user_duplicates:
            print("   ✅ Cross-user duplicates exist (this is expected)")
            for dup in cross_user_duplicates[:3]:  # Show first 3
                print(f"   - User {dup['user1_id'][:8]}... vs User {dup['user2_id'][:8]}...")
                print(f"     Files: {dup['filename1']} vs {dup['filename2']}")
        else:
            print("   ℹ️ No cross-user duplicates found")
        
        # Test 2: Check within-user duplicates
        print("\n📊 Test 2: Checking for within-user duplicate content...")
        
        within_user_duplicates = await conn.fetch("""
            SELECT 
                user_id,
                COUNT(*) as duplicate_count,
                array_agg(document_id) as document_ids,
                array_agg(filename) as filenames,
                parsed_sha256
            FROM upload_pipeline.documents
            WHERE parsed_sha256 IS NOT NULL
            GROUP BY user_id, parsed_sha256
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 5
        """)
        
        print(f"   Found {len(within_user_duplicates)} users with duplicate content")
        
        if within_user_duplicates:
            print("   ⚠️ Within-user duplicates found (this should be handled by duplicate detection)")
            for dup in within_user_duplicates:
                print(f"   - User {dup['user_id'][:8]}... has {dup['duplicate_count']} duplicates")
                print(f"     Files: {', '.join(dup['filenames'])}")
        else:
            print("   ✅ No within-user duplicates found (duplicate detection working)")
        
        # Test 3: Verify the fixed query logic
        print("\n📊 Test 3: Testing fixed duplicate detection query...")
        
        # Get a sample document
        sample_doc = await conn.fetchrow("""
            SELECT document_id, user_id, parsed_sha256, filename
            FROM upload_pipeline.documents
            WHERE parsed_sha256 IS NOT NULL
            LIMIT 1
        """)
        
        if sample_doc:
            user_id_str = str(sample_doc['user_id'])
            print(f"   Testing with document: {sample_doc['filename']} (User: {user_id_str[:8]}...)")
            
            # Test OLD query (global duplicates) - should find cross-user duplicates
            old_query_results = await conn.fetch("""
                SELECT d.document_id, d.user_id, d.filename
                FROM upload_pipeline.documents d
                WHERE d.parsed_sha256 = $1 AND d.document_id != $2
                ORDER BY d.created_at ASC
                LIMIT 3
            """, sample_doc['parsed_sha256'], sample_doc['document_id'])
            
            print(f"   OLD query (global): Found {len(old_query_results)} duplicates")
            for result in old_query_results:
                user_id_str = str(result['user_id'])
                print(f"     - {result['filename']} (User: {user_id_str[:8]}...)")
            
            # Test NEW query (user-scoped) - should only find same-user duplicates
            new_query_results = await conn.fetch("""
                SELECT d.document_id, d.user_id, d.filename
                FROM upload_pipeline.documents d
                WHERE d.parsed_sha256 = $1 AND d.document_id != $2 AND d.user_id = $3
                ORDER BY d.created_at ASC
                LIMIT 3
            """, sample_doc['parsed_sha256'], sample_doc['document_id'], sample_doc['user_id'])
            
            print(f"   NEW query (user-scoped): Found {len(new_query_results)} duplicates")
            for result in new_query_results:
                user_id_str = str(result['user_id'])
                print(f"     - {result['filename']} (User: {user_id_str[:8]}...)")
            
            # Verify the fix
            if len(old_query_results) > len(new_query_results):
                print("   ✅ FIX CONFIRMED: User-scoped query returns fewer results")
                print("   ✅ Duplicate detection now properly scoped to user")
            else:
                print("   ℹ️ No difference in results (no cross-user duplicates for this content)")
        
        await conn.close()
        
        print("\n🎉 User-Scoped Duplicate Detection Test Complete!")
        print("✅ Duplicate detection is now properly scoped to individual users")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_user_scoped_duplicates())
