#!/usr/bin/env python3
"""
Force Process Stuck Documents
Manually triggers processing for documents stuck after Edge Function trigger
"""

import asyncio
import asyncpg
import aiohttp
import json
from datetime import datetime, timezone

async def force_process_stuck_docs():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔧 Force Processing Stuck Documents")
        print("=" * 50)
        
        # Get all stuck documents from recent uploads
        stuck_docs = await conn.fetch("""
            SELECT id, original_filename, file_path, status, created_at,
                   EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes
            FROM documents 
            WHERE created_at > NOW() - INTERVAL '4 hours'
            AND status = 'pending'
            AND updated_at = created_at  -- No processing updates
            ORDER BY created_at DESC
        """)
        
        if not stuck_docs:
            print("✅ No stuck documents found")
            await conn.close()
            return
        
        print(f"🎯 Found {len(stuck_docs)} stuck documents:")
        for doc in stuck_docs:
            print(f"   📄 {doc['original_filename']} | ID: {doc['id']} | Age: {doc['age_minutes']:.1f}m")
        
        print(f"\n🚀 Starting manual processing...")
        
        # Manual processing approach: Call the same Edge Function endpoint directly
        supabase_url = "https://jhrespvvhbnloxrieycf.supabase.co"
        supabase_anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpocmVzcHZ2aGJubG94cmileWNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMzNTQ1NjksImV4cCI6MjA0ODkzMDU2OX0.hQqUxdnHhQOw0Dpm5s0VRJz6WVJKF3Ju3FNdj2Yv6g8"
        
        processed_count = 0
        
        async with aiohttp.ClientSession() as session:
            for doc in stuck_docs:
                try:
                    print(f"\n🔄 Processing: {doc['original_filename']} ({doc['id']})")
                    
                    # Try to trigger processing via direct API call
                    payload = {
                        "document_id": str(doc['id']),
                        "file_path": doc['file_path'] if doc['file_path'] else f"documents/{doc['id']}.pdf",
                        "filename": doc['original_filename']
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {supabase_anon_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Try the job-processor Edge Function directly
                    job_processor_url = f"{supabase_url}/functions/v1/job-processor"
                    
                    async with session.post(job_processor_url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"   ✅ Job processor triggered: {result}")
                            processed_count += 1
                            
                            # Update document status to show processing started
                            await conn.execute("""
                                UPDATE documents 
                                SET status = 'processing',
                                    processing_status = 'parsing',
                                    updated_at = NOW()
                                WHERE id = $1
                            """, doc['id'])
                            
                        else:
                            error_text = await response.text()
                            print(f"   ❌ Failed: {response.status} - {error_text}")
                            
                except Exception as e:
                    print(f"   ❌ Error processing {doc['original_filename']}: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   🎯 Total stuck documents: {len(stuck_docs)}")
        print(f"   ✅ Successfully triggered: {processed_count}")
        print(f"   ❌ Failed to process: {len(stuck_docs) - processed_count}")
        
        if processed_count > 0:
            print(f"\n⏰ Wait 2-3 minutes and check document status for progress")
            print(f"📍 Monitor progress in Supabase Dashboard → Table Editor → documents")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(force_process_stuck_docs()) 
"""
Force Process Stuck Documents
Manually triggers processing for documents stuck after Edge Function trigger
"""

import asyncio
import asyncpg
import aiohttp
import json
from datetime import datetime, timezone

async def force_process_stuck_docs():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🔧 Force Processing Stuck Documents")
        print("=" * 50)
        
        # Get all stuck documents from recent uploads
        stuck_docs = await conn.fetch("""
            SELECT id, original_filename, file_path, status, created_at,
                   EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes
            FROM documents 
            WHERE created_at > NOW() - INTERVAL '4 hours'
            AND status = 'pending'
            AND updated_at = created_at  -- No processing updates
            ORDER BY created_at DESC
        """)
        
        if not stuck_docs:
            print("✅ No stuck documents found")
            await conn.close()
            return
        
        print(f"🎯 Found {len(stuck_docs)} stuck documents:")
        for doc in stuck_docs:
            print(f"   📄 {doc['original_filename']} | ID: {doc['id']} | Age: {doc['age_minutes']:.1f}m")
        
        print(f"\n🚀 Starting manual processing...")
        
        # Manual processing approach: Call the same Edge Function endpoint directly
        supabase_url = "https://jhrespvvhbnloxrieycf.supabase.co"
        supabase_anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpocmVzcHZ2aGJubG94cmileWNmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzMzNTQ1NjksImV4cCI6MjA0ODkzMDU2OX0.hQqUxdnHhQOw0Dpm5s0VRJz6WVJKF3Ju3FNdj2Yv6g8"
        
        processed_count = 0
        
        async with aiohttp.ClientSession() as session:
            for doc in stuck_docs:
                try:
                    print(f"\n🔄 Processing: {doc['original_filename']} ({doc['id']})")
                    
                    # Try to trigger processing via direct API call
                    payload = {
                        "document_id": str(doc['id']),
                        "file_path": doc['file_path'] if doc['file_path'] else f"documents/{doc['id']}.pdf",
                        "filename": doc['original_filename']
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {supabase_anon_key}",
                        "Content-Type": "application/json"
                    }
                    
                    # Try the job-processor Edge Function directly
                    job_processor_url = f"{supabase_url}/functions/v1/job-processor"
                    
                    async with session.post(job_processor_url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"   ✅ Job processor triggered: {result}")
                            processed_count += 1
                            
                            # Update document status to show processing started
                            await conn.execute("""
                                UPDATE documents 
                                SET status = 'processing',
                                    processing_status = 'parsing',
                                    updated_at = NOW()
                                WHERE id = $1
                            """, doc['id'])
                            
                        else:
                            error_text = await response.text()
                            print(f"   ❌ Failed: {response.status} - {error_text}")
                            
                except Exception as e:
                    print(f"   ❌ Error processing {doc['original_filename']}: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   🎯 Total stuck documents: {len(stuck_docs)}")
        print(f"   ✅ Successfully triggered: {processed_count}")
        print(f"   ❌ Failed to process: {len(stuck_docs) - processed_count}")
        
        if processed_count > 0:
            print(f"\n⏰ Wait 2-3 minutes and check document status for progress")
            print(f"📍 Monitor progress in Supabase Dashboard → Table Editor → documents")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(force_process_stuck_docs()) 