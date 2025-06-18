#!/usr/bin/env python3
"""
Trigger Stuck Document Processing
Creates processing jobs for documents that are stuck in pending status
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

async def trigger_stuck_processing():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🚀 Triggering Stuck Document Processing")
        print("=" * 50)
        
        # Get stuck documents that need processing
        stuck_docs = await conn.fetch("""
            SELECT id, original_filename, user_id, status, created_at,
                   EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes
            FROM documents 
            WHERE status = 'pending'
            AND created_at > NOW() - INTERVAL '4 hours'
            AND updated_at = created_at  -- No processing updates
            ORDER BY created_at DESC
        """)
        
        if not stuck_docs:
            print("✅ No stuck documents found")
            await conn.close()
            return
        
        print(f"🎯 Found {len(stuck_docs)} stuck documents:")
        for doc in stuck_docs:
            print(f"   📄 {doc['original_filename']} | Age: {doc['age_minutes']:.1f}m")
        
        # Create processing jobs for each stuck document
        jobs_created = 0
        
        for doc in stuck_docs:
            print(f"\n🔄 Creating processing job for: {doc['original_filename']}")
            
            try:
                # Check if processing job already exists
                existing_job = await conn.fetchval("""
                    SELECT id FROM processing_jobs 
                    WHERE document_id = $1 
                    AND status IN ('pending', 'running', 'retrying')
                """, doc['id'])
                
                if existing_job:
                    print(f"   ⚠️  Processing job already exists: {existing_job}")
                    continue
                
                # Create new processing job
                job_id = await conn.fetchval("""
                    INSERT INTO processing_jobs (
                        document_id, user_id, job_type, status, priority,
                        scheduled_at, payload, created_at, updated_at
                    ) VALUES (
                        $1, $2, 'parse', 'pending', 1,
                        NOW(), '{"source": "manual_trigger"}'::jsonb, NOW(), NOW()
                    ) RETURNING id
                """, doc['id'], doc['user_id'])
                
                print(f"   ✅ Created processing job: {job_id}")
                jobs_created += 1
                
                # Update document status
                await conn.execute("""
                    UPDATE documents 
                    SET status = 'processing', updated_at = NOW()
                    WHERE id = $1
                """, doc['id'])
                
            except Exception as e:
                print(f"   ❌ Failed to create job: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   🎯 Stuck documents found: {len(stuck_docs)}")
        print(f"   ✅ Processing jobs created: {jobs_created}")
        
        if jobs_created > 0:
            print(f"\n🚀 Processing should start automatically within 1-2 minutes")
            print(f"📍 Monitor progress in Supabase Dashboard → Table Editor → documents")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(trigger_stuck_processing()) 
"""
Trigger Stuck Document Processing
Creates processing jobs for documents that are stuck in pending status
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

async def trigger_stuck_processing():
    db_url = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'
    
    try:
        conn = await asyncpg.connect(db_url, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        print("🚀 Triggering Stuck Document Processing")
        print("=" * 50)
        
        # Get stuck documents that need processing
        stuck_docs = await conn.fetch("""
            SELECT id, original_filename, user_id, status, created_at,
                   EXTRACT(EPOCH FROM (NOW() - created_at)) / 60 as age_minutes
            FROM documents 
            WHERE status = 'pending'
            AND created_at > NOW() - INTERVAL '4 hours'
            AND updated_at = created_at  -- No processing updates
            ORDER BY created_at DESC
        """)
        
        if not stuck_docs:
            print("✅ No stuck documents found")
            await conn.close()
            return
        
        print(f"🎯 Found {len(stuck_docs)} stuck documents:")
        for doc in stuck_docs:
            print(f"   📄 {doc['original_filename']} | Age: {doc['age_minutes']:.1f}m")
        
        # Create processing jobs for each stuck document
        jobs_created = 0
        
        for doc in stuck_docs:
            print(f"\n🔄 Creating processing job for: {doc['original_filename']}")
            
            try:
                # Check if processing job already exists
                existing_job = await conn.fetchval("""
                    SELECT id FROM processing_jobs 
                    WHERE document_id = $1 
                    AND status IN ('pending', 'running', 'retrying')
                """, doc['id'])
                
                if existing_job:
                    print(f"   ⚠️  Processing job already exists: {existing_job}")
                    continue
                
                # Create new processing job
                job_id = await conn.fetchval("""
                    INSERT INTO processing_jobs (
                        document_id, user_id, job_type, status, priority,
                        scheduled_at, payload, created_at, updated_at
                    ) VALUES (
                        $1, $2, 'parse', 'pending', 1,
                        NOW(), '{"source": "manual_trigger"}'::jsonb, NOW(), NOW()
                    ) RETURNING id
                """, doc['id'], doc['user_id'])
                
                print(f"   ✅ Created processing job: {job_id}")
                jobs_created += 1
                
                # Update document status
                await conn.execute("""
                    UPDATE documents 
                    SET status = 'processing', updated_at = NOW()
                    WHERE id = $1
                """, doc['id'])
                
            except Exception as e:
                print(f"   ❌ Failed to create job: {e}")
        
        print(f"\n📊 Summary:")
        print(f"   🎯 Stuck documents found: {len(stuck_docs)}")
        print(f"   ✅ Processing jobs created: {jobs_created}")
        
        if jobs_created > 0:
            print(f"\n🚀 Processing should start automatically within 1-2 minutes")
            print(f"📍 Monitor progress in Supabase Dashboard → Table Editor → documents")
        
        await conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    asyncio.run(trigger_stuck_processing()) 