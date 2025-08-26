#!/usr/bin/env python3
"""
Phase 3.7 Database State Validation Script
Validates current database state for Phase 3.7 pipeline testing.
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database functions
from api.upload_pipeline.database import get_database

async def check_database_state():
    """Check current database state and job distribution."""
    db = get_database()
    
    try:
        # Initialize database connection
        await db.initialize()
        
        print("🔍 Phase 3.7 Database State Validation")
        print("=" * 50)
        
        # Check current job distribution
        jobs = await db.fetch("""
            SELECT stage, COUNT(*) as count 
            FROM upload_jobs 
            GROUP BY stage 
            ORDER BY stage
        """)
        
        print("📊 Current Job Distribution:")
        total_jobs = 0
        for job in jobs:
            print(f"  {job['stage']}: {job['count']} jobs")
            total_jobs += job['count']
        print(f"  Total: {total_jobs} jobs")
        print()
        
        # Check specific job details
        job_details = await db.fetch("""
            SELECT id, document_id, stage, created_at, updated_at 
            FROM upload_jobs 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        print("📝 Recent Job Details:")
        for job in job_details:
            print(f"  Job {job['id']}: doc_{job['document_id']}, stage={job['stage']}")
            print(f"    Created: {job['created_at']}, Updated: {job['updated_at']}")
        print()
        
        # Check buffer table states
        chunk_buffer_count = await db.fetchval("SELECT COUNT(*) FROM document_chunk_buffer")
        vector_buffer_count = await db.fetchval("SELECT COUNT(*) FROM document_vector_buffer")
        final_chunks_count = await db.fetchval("SELECT COUNT(*) FROM document_chunks")
        
        print("🗃️  Buffer and Final Table States:")
        print(f"  Chunk buffer: {chunk_buffer_count} entries")
        print(f"  Vector buffer: {vector_buffer_count} entries")
        print(f"  Final chunks: {final_chunks_count} entries")
        print()
        
        # Check for embedded stage jobs (Phase 3.7 target)
        embedded_jobs = await db.fetch("""
            SELECT id, document_id, created_at, updated_at 
            FROM upload_jobs 
            WHERE stage = 'embedded'
            ORDER BY created_at
        """)
        
        print("🎯 Phase 3.7 Target Jobs (embedded stage):")
        if embedded_jobs:
            for job in embedded_jobs:
                print(f"  Job {job['id']}: doc_{job['document_id']}")
                print(f"    Ready for completion testing: {job['updated_at']}")
        else:
            print("  No jobs in embedded stage found")
        print()
        
        # Check for any jobs that might need processing
        ready_for_processing = await db.fetch("""
            SELECT stage, COUNT(*) as count 
            FROM upload_jobs 
            WHERE stage NOT IN ('completed', 'failed')
            GROUP BY stage 
            ORDER BY stage
        """)
        
        print("⚙️  Jobs Available for Processing:")
        if ready_for_processing:
            for job in ready_for_processing:
                print(f"  {job['stage']}: {job['count']} jobs")
        else:
            print("  No jobs available for processing")
        print()
        
        # Provide Phase 3.7 readiness assessment
        print("📋 Phase 3.7 Readiness Assessment:")
        embedded_count = sum(job['count'] for job in jobs if job['stage'] == 'embedded')
        
        if embedded_count > 0:
            print(f"  ✅ {embedded_count} job(s) ready for completion testing")
            print("  ✅ Phase 3.7 can proceed with job finalization testing")
        else:
            # Check if there are jobs in earlier stages that can be processed
            processable_jobs = sum(job['count'] for job in jobs if job['stage'] in ['queued', 'job_validated', 'parsing', 'parsed', 'parse_validated', 'chunking', 'chunks_buffered', 'embedding'])
            
            if processable_jobs > 0:
                print(f"  ⚠️  No jobs in embedded stage, but {processable_jobs} job(s) available for processing")
                print("  ⚠️  Consider running worker to advance jobs to embedded stage first")
            else:
                print("  ❌ No jobs available for Phase 3.7 testing")
                print("  ❌ Consider uploading test documents first")
        
        return {
            'total_jobs': total_jobs,
            'job_distribution': {job['stage']: job['count'] for job in jobs},
            'embedded_jobs': len(embedded_jobs),
            'chunk_buffer': chunk_buffer_count,
            'vector_buffer': vector_buffer_count,
            'final_chunks': final_chunks_count,
            'ready_for_processing': {job['stage']: job['count'] for job in ready_for_processing} if ready_for_processing else {}
        }
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return None
        
    finally:
        await db.close()

async def main():
    """Run database state validation."""
    print(f"Database check started at: {datetime.now()}")
    print()
    
    result = await check_database_state()
    
    if result:
        print()
        print("✅ Database state validation completed successfully")
        
        # Save results to JSON for reference
        results_file = f"phase37_database_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"📁 Results saved to: {results_file}")
    else:
        print()
        print("❌ Database state validation failed")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())