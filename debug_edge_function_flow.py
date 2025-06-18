#!/usr/bin/env python3
"""
Debug Edge Function Processing Flow
Checks what happens after upload-handler is triggered
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

async def debug_edge_function_flow():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔍 Debug: Edge Function Processing Flow")
        print("=" * 50)
        
        # Get the document IDs from the logs
        target_doc_ids = [
            '08c6d14e-1fec-4d9c-bb00-07b14bd542d4',  # From logs
            '3fcc1922-f26c-405c-8f9a-744ac921239e'   # From Edge Function response
        ]
        
        print("🎯 Checking specific documents from logs:")
        for doc_id in target_doc_ids:
            print(f"\n📄 Document ID: {doc_id}")
            
            # Check document current state
            doc = await conn.fetchrow("""
                SELECT id, original_filename, status, upload_status, processing_status,
                       progress_percentage, created_at, updated_at,
                       EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes,
                       EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60 as stale_minutes
                FROM documents 
                WHERE id = $1
            """, doc_id)
            
            if doc:
                print(f"   📋 Filename: {doc['original_filename']}")
                print(f"   📊 Status: {doc['status']} | Upload: {doc['upload_status']} | Processing: {doc['processing_status']}")
                print(f"   ⏱️  Age: {doc['age_minutes']:.1f}m | Stale: {doc['stale_minutes']:.1f}m")
                print(f"   📈 Progress: {doc['progress_percentage'] or 0}%")
                
                # Check if any vectors were created
                vector_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM document_vectors WHERE document_id = $1
                """, doc_id)
                print(f"   🧠 Vectors: {vector_count}")
                
                # Check processing timeline
                if doc['updated_at'] == doc['created_at']:
                    print(f"   ⚠️  NO PROCESSING UPDATES - Edge Function may have failed silently")
                else:
                    print(f"   ✅ Has processing updates")
            else:
                print(f"   ❌ Document not found")
        
        # Check for any documents that got stuck after Edge Function trigger
        print(f"\n🕵️ Checking for Edge Function failure patterns:")
        
        stuck_after_trigger = await conn.fetch("""
            SELECT id, original_filename, status, 
                   created_at, updated_at,
                   EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes
            FROM documents 
            WHERE created_at > NOW() - INTERVAL '2 hours'
            AND status = 'pending'
            AND updated_at = created_at  -- No updates since creation
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if stuck_after_trigger:
            print(f"   ⚠️  Found {len(stuck_after_trigger)} documents that never got processed after upload:")
            for doc in stuck_after_trigger:
                print(f"   📄 {doc['original_filename']} | Age: {doc['age_minutes']:.1f}m | Status: {doc['status']}")
        else:
            print(f"   ✅ No documents stuck immediately after upload")
        
        # Diagnosis
        print(f"\n💡 DIAGNOSIS:")
        print(f"-" * 30)
        
        all_recent_stuck = len(stuck_after_trigger) if stuck_after_trigger else 0
        if all_recent_stuck > 0:
            print(f"🚨 ISSUE: Edge Function is triggered but fails to process documents")
            print(f"📋 Evidence: {all_recent_stuck} documents stuck immediately after Edge Function call")
            print(f"🔧 Solution: Check Edge Function logs for errors in processing pipeline")
            
            print(f"\n📍 Supabase Edge Function Debug Steps:")
            print(f"   1. Go to Supabase Dashboard")
            print(f"   2. Edge Functions → upload-handler → Logs")
            print(f"   3. Look for entries around 21:02:50 UTC")
            print(f"   4. Check for errors in vector-processor or job-processor calls")
            
            print(f"\n🎯 Likely Issues:")
            print(f"   - OpenAI API key issues (for embeddings)")
            print(f"   - Timeout in vector processing")
            print(f"   - Database connection issues in Edge Function")
            print(f"   - Missing permissions for downstream function calls")
        else:
            print(f"✅ Edge Function appears to be working correctly")
            print(f"📊 Documents are being processed after Edge Function trigger")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(debug_edge_function_flow()) 
"""
Debug Edge Function Processing Flow
Checks what happens after upload-handler is triggered
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

async def debug_edge_function_flow():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔍 Debug: Edge Function Processing Flow")
        print("=" * 50)
        
        # Get the document IDs from the logs
        target_doc_ids = [
            '08c6d14e-1fec-4d9c-bb00-07b14bd542d4',  # From logs
            '3fcc1922-f26c-405c-8f9a-744ac921239e'   # From Edge Function response
        ]
        
        print("🎯 Checking specific documents from logs:")
        for doc_id in target_doc_ids:
            print(f"\n📄 Document ID: {doc_id}")
            
            # Check document current state
            doc = await conn.fetchrow("""
                SELECT id, original_filename, status, upload_status, processing_status,
                       progress_percentage, created_at, updated_at,
                       EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes,
                       EXTRACT(EPOCH FROM (NOW() - updated_at)) / 60 as stale_minutes
                FROM documents 
                WHERE id = $1
            """, doc_id)
            
            if doc:
                print(f"   📋 Filename: {doc['original_filename']}")
                print(f"   📊 Status: {doc['status']} | Upload: {doc['upload_status']} | Processing: {doc['processing_status']}")
                print(f"   ⏱️  Age: {doc['age_minutes']:.1f}m | Stale: {doc['stale_minutes']:.1f}m")
                print(f"   📈 Progress: {doc['progress_percentage'] or 0}%")
                
                # Check if any vectors were created
                vector_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM document_vectors WHERE document_id = $1
                """, doc_id)
                print(f"   🧠 Vectors: {vector_count}")
                
                # Check processing timeline
                if doc['updated_at'] == doc['created_at']:
                    print(f"   ⚠️  NO PROCESSING UPDATES - Edge Function may have failed silently")
                else:
                    print(f"   ✅ Has processing updates")
            else:
                print(f"   ❌ Document not found")
        
        # Check for any documents that got stuck after Edge Function trigger
        print(f"\n🕵️ Checking for Edge Function failure patterns:")
        
        stuck_after_trigger = await conn.fetch("""
            SELECT id, original_filename, status, 
                   created_at, updated_at,
                   EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes
            FROM documents 
            WHERE created_at > NOW() - INTERVAL '2 hours'
            AND status = 'pending'
            AND updated_at = created_at  -- No updates since creation
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if stuck_after_trigger:
            print(f"   ⚠️  Found {len(stuck_after_trigger)} documents that never got processed after upload:")
            for doc in stuck_after_trigger:
                print(f"   📄 {doc['original_filename']} | Age: {doc['age_minutes']:.1f}m | Status: {doc['status']}")
        else:
            print(f"   ✅ No documents stuck immediately after upload")
        
        # Diagnosis
        print(f"\n💡 DIAGNOSIS:")
        print(f"-" * 30)
        
        all_recent_stuck = len(stuck_after_trigger) if stuck_after_trigger else 0
        if all_recent_stuck > 0:
            print(f"🚨 ISSUE: Edge Function is triggered but fails to process documents")
            print(f"📋 Evidence: {all_recent_stuck} documents stuck immediately after Edge Function call")
            print(f"🔧 Solution: Check Edge Function logs for errors in processing pipeline")
            
            print(f"\n📍 Supabase Edge Function Debug Steps:")
            print(f"   1. Go to Supabase Dashboard")
            print(f"   2. Edge Functions → upload-handler → Logs")
            print(f"   3. Look for entries around 21:02:50 UTC")
            print(f"   4. Check for errors in vector-processor or job-processor calls")
            
            print(f"\n🎯 Likely Issues:")
            print(f"   - OpenAI API key issues (for embeddings)")
            print(f"   - Timeout in vector processing")
            print(f"   - Database connection issues in Edge Function")
            print(f"   - Missing permissions for downstream function calls")
        else:
            print(f"✅ Edge Function appears to be working correctly")
            print(f"📊 Documents are being processed after Edge Function trigger")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(debug_edge_function_flow()) 