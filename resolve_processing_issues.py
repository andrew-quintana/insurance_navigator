#!/usr/bin/env python3
"""
Resolve Processing Issues
Immediate fixes for the queue processing problems:
1. Clean up stuck jobs
2. Reset documents to proper status
3. Provide action plan for doc-parser
"""

import asyncio
import asyncpg
from datetime import datetime, timezone

# Configuration
DATABASE_URL = 'postgresql://postgres.jhrespvvhbnloxrieycf:beqhar-qincyg-Syxxi8@aws-0-us-west-1.pooler.supabase.com:6543/postgres'

async def main():
    """Resolve processing issues immediately"""
    print("🔧 Resolving Processing Issues")
    print("=" * 50)
    
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL, server_settings={'jit': 'off'}, statement_cache_size=0)
        
        # Step 1: Clean up stuck jobs
        await cleanup_stuck_jobs(conn)
        
        # Step 2: Reset document statuses
        await reset_document_statuses(conn)
        
        # Step 3: Provide action plan
        await provide_action_plan()
        
        # Step 4: Final status check
        await final_status_check(conn)
        
        print("\n✅ Immediate processing issues resolved!")
        
    except Exception as e:
        print(f"❌ Resolution failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            await conn.close()

async def cleanup_stuck_jobs(conn):
    """Clean up all stuck jobs"""
    print("\n🧹 Step 1: Cleaning Up Stuck Jobs")
    print("-" * 40)
    
    # Find all running jobs (they're all stuck)
    stuck_jobs = await conn.fetch("""
        SELECT 
            pj.id, pj.document_id, d.original_filename,
            EXTRACT(EPOCH FROM (NOW() - pj.created_at)) / 60 as age_minutes
        FROM processing_jobs pj
        JOIN documents d ON pj.document_id = d.id
        WHERE pj.status = 'running'
    """)
    
    if stuck_jobs:
        print(f"🚨 Found {len(stuck_jobs)} stuck jobs to clean up:")
        
        for job in stuck_jobs:
            print(f"   📄 {job['original_filename']} (stuck {job['age_minutes']:.1f}m)")
            
            # Mark as failed to allow retry when doc-parser is fixed
            await conn.execute("""
                UPDATE processing_jobs 
                SET 
                    status = 'failed',
                    error_message = 'Doc-parser unavailable - will retry when fixed',
                    updated_at = NOW()
                WHERE id = $1
            """, job['id'])
        
        print(f"   ✅ All {len(stuck_jobs)} jobs marked as failed (will retry)")
    else:
        print("✅ No stuck jobs found")

async def reset_document_statuses(conn):
    """Reset document statuses to reflect reality"""
    print("\n📄 Step 2: Resetting Document Statuses")
    print("-" * 40)
    
    # Reset documents that are stuck in 'parsing' status
    parsing_docs = await conn.fetch("""
        SELECT id, original_filename, status
        FROM documents 
        WHERE status = 'parsing'
    """)
    
    if parsing_docs:
        print(f"📋 Found {len(parsing_docs)} documents stuck in 'parsing' status:")
        
        for doc in parsing_docs:
            print(f"   📄 {doc['original_filename']}")
            
            # Reset to pending so they can be reprocessed
            await conn.execute("""
                UPDATE documents 
                SET 
                    status = 'pending',
                    progress_percentage = 0,
                    updated_at = NOW()
                WHERE id = $1
            """, doc['id'])
        
        print(f"   ✅ Reset {len(parsing_docs)} documents to 'pending' status")
    else:
        print("✅ No documents stuck in parsing status")

async def provide_action_plan():
    """Provide clear action plan for fixing doc-parser"""
    print("\n📋 Step 3: Action Plan for Complete Fix")
    print("-" * 40)
    
    print("🎯 Critical: Fix Doc-Parser Edge Function")
    print()
    
    print("📍 Issue Identified:")
    print("   • Doc-parser edge function is not deployed or accessible")
    print("   • When accessible, it fails to download files from storage")
    print("   • This blocks all document processing")
    print()
    
    print("🔧 Required Actions:")
    print()
    
    print("   1. 🚀 Deploy Doc-Parser Edge Function:")
    print("      • Check Supabase Dashboard → Edge Functions")
    print("      • Ensure 'doc-parser' function is deployed")
    print("      • If not deployed: supabase functions deploy doc-parser")
    print()
    
    print("   2. 🔑 Set Required Environment Variables:")
    print("      • In Supabase Dashboard → Edge Functions → doc-parser → Settings")
    print("      • Set these variables:")
    print("        - OPENAI_API_KEY: [your OpenAI key]")
    print("        - LLAMAPARSE_API_KEY: [your LlamaParse key]")
    print("        - CUSTOM_SERVICE_ROLE_KEY: [the service role key we added]")
    print()
    
    print("   3. 🔗 Verify File Access:")
    print("      • Doc-parser needs to access Supabase Storage")
    print("      • Check storage bucket permissions")
    print("      • Verify service role can read from 'raw_documents' bucket")
    print()
    
    print("   4. 🧪 Test Edge Function:")
    print("      • Use Supabase Dashboard → Edge Functions → doc-parser → Invoke")
    print("      • Test with a document ID and storage path")
    print()
    
    print("🚀 Once Doc-Parser is Fixed:")
    print("   • Failed jobs will automatically retry")
    print("   • Pending documents will be processed")
    print("   • Queue will resume normal operation")

async def final_status_check(conn):
    """Check final status after cleanup"""
    print("\n📊 Step 4: Final Status Check")
    print("-" * 40)
    
    # Check current queue state
    queue_stats = await conn.fetch("""
        SELECT status, COUNT(*) as count
        FROM processing_jobs
        WHERE created_at > NOW() - INTERVAL '1 hour'
        GROUP BY status
        ORDER BY count DESC
    """)
    
    print("📋 Processing Jobs Status:")
    for stat in queue_stats:
        print(f"   {stat['status']}: {stat['count']} jobs")
    
    # Check document status
    doc_stats = await conn.fetch("""
        SELECT status, COUNT(*) as count
        FROM documents 
        GROUP BY status
        ORDER BY count DESC
    """)
    
    print(f"\n📄 Document Status:")
    for stat in doc_stats:
        print(f"   {stat['status']}: {stat['count']} documents")
    
    # Count pending jobs ready for retry
    pending_jobs = await conn.fetch('SELECT * FROM get_pending_jobs(10)')
    print(f"\n⏳ Pending jobs ready for processing: {len(pending_jobs)}")
    
    print(f"\n💡 Next Steps:")
    print(f"   1. Fix doc-parser edge function deployment")
    print(f"   2. Set required environment variables")
    print(f"   3. Test with: python test_queue_processing_only.py")
    print(f"   4. Monitor with: python check_processing_jobs_status.py")

if __name__ == "__main__":
    asyncio.run(main()) 