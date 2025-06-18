#!/usr/bin/env python3
"""
Emergency Fix: Process Stuck Documents
Manually triggers processing for stuck documents
"""

import asyncio
import asyncpg
import aiohttp
import json
from datetime import datetime, timezone

async def fix_stuck_documents():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'})
        
        print("🔧 Emergency Fix: Processing Stuck Documents")
        print("=" * 50)
        
        # Get stuck documents from the last 24 hours (ignore very old ones for now)
        stuck_docs = await conn.fetch("""
            SELECT id, original_filename, user_id, status, file_size
            FROM documents 
            WHERE status IN ('pending', 'uploading')
            AND created_at > NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if not stuck_docs:
            print("✅ No recent stuck documents found")
            return
        
        print(f"Found {len(stuck_docs)} stuck documents to process:")
        
        # Option 1: Update status to trigger Edge Function retry
        print(f"\n🔄 Option 1: Reset documents to trigger retry")
        for doc in stuck_docs:
            print(f"   📄 {doc['original_filename']} (ID: {doc['id']})")
            
            # Reset to pending status to trigger retry
            await conn.execute("""
                UPDATE documents 
                SET status = 'pending',
                    upload_status = 'completed',
                    processing_status = 'pending',
                    updated_at = NOW()
                WHERE id = $1
            """, doc['id'])
            
            print(f"      ✅ Reset to pending status")
        
        print(f"\n🎯 Documents have been reset. They should now be picked up by the processing pipeline.")
        print(f"📊 Monitor the Supabase Edge Function logs to see if they start processing.")
        
        # Option 2: Manual API call to trigger processing
        print(f"\n🔧 Option 2: Manual trigger via API")
        print(f"If the above doesn't work, try calling the Edge Function directly:")
        print(f"curl -X POST https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/upload-handler \\")
        print(f"  -H 'Authorization: Bearer YOUR_SERVICE_KEY' \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{\"documentId\": \"{stuck_docs[0]['id']}\", \"userId\": \"{stuck_docs[0]['user_id']}\"}}'")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(fix_stuck_documents()) 
"""
Emergency Fix: Process Stuck Documents
Manually triggers processing for stuck documents
"""

import asyncio
import asyncpg
import aiohttp
import json
from datetime import datetime, timezone

async def fix_stuck_documents():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'})
        
        print("🔧 Emergency Fix: Processing Stuck Documents")
        print("=" * 50)
        
        # Get stuck documents from the last 24 hours (ignore very old ones for now)
        stuck_docs = await conn.fetch("""
            SELECT id, original_filename, user_id, status, file_size
            FROM documents 
            WHERE status IN ('pending', 'uploading')
            AND created_at > NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if not stuck_docs:
            print("✅ No recent stuck documents found")
            return
        
        print(f"Found {len(stuck_docs)} stuck documents to process:")
        
        # Option 1: Update status to trigger Edge Function retry
        print(f"\n🔄 Option 1: Reset documents to trigger retry")
        for doc in stuck_docs:
            print(f"   📄 {doc['original_filename']} (ID: {doc['id']})")
            
            # Reset to pending status to trigger retry
            await conn.execute("""
                UPDATE documents 
                SET status = 'pending',
                    upload_status = 'completed',
                    processing_status = 'pending',
                    updated_at = NOW()
                WHERE id = $1
            """, doc['id'])
            
            print(f"      ✅ Reset to pending status")
        
        print(f"\n🎯 Documents have been reset. They should now be picked up by the processing pipeline.")
        print(f"📊 Monitor the Supabase Edge Function logs to see if they start processing.")
        
        # Option 2: Manual API call to trigger processing
        print(f"\n🔧 Option 2: Manual trigger via API")
        print(f"If the above doesn't work, try calling the Edge Function directly:")
        print(f"curl -X POST https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/upload-handler \\")
        print(f"  -H 'Authorization: Bearer YOUR_SERVICE_KEY' \\")
        print(f"  -H 'Content-Type: application/json' \\")
        print(f"  -d '{{\"documentId\": \"{stuck_docs[0]['id']}\", \"userId\": \"{stuck_docs[0]['user_id']}\"}}'")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(fix_stuck_documents()) 