#!/usr/bin/env python3
"""
Phase B.3.1: Direct SQL Cleanup
UUID Standardization - Direct SQL cleanup of old random UUID data

This script uses direct SQL to clean up old random UUID documents
in a more efficient way.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any

import asyncpg
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv('.env.production')
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return
    
    logger.info("🚀 Starting direct SQL cleanup...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        logger.info("✅ Database connected successfully")
        
        # Get current state
        total_docs = await conn.fetchval("SELECT COUNT(*) FROM upload_pipeline.documents")
        random_docs = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.documents
            WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        """)
        deterministic_docs = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.documents
            WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        """)
        
        logger.info(f"📊 Current state: {total_docs} total, {random_docs} random, {deterministic_docs} deterministic")
        
        # Direct SQL cleanup - delete all random UUID documents and their related data
        logger.info("🗑️ Executing direct SQL cleanup...")
        
        # Delete in separate transactions to avoid rollback issues
        # Delete buffer entries for random UUID documents
        try:
            buffer_deleted = await conn.execute("""
                DELETE FROM upload_pipeline.document_vector_buffer
                WHERE chunk_id IN (
                    SELECT dc.chunk_id FROM upload_pipeline.document_chunks dc
                    JOIN upload_pipeline.documents d ON dc.document_id = d.document_id
                    WHERE d.document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                )
            """)
            logger.info(f"  🗑️ Deleted buffer entries: {buffer_deleted}")
        except Exception as e:
            logger.info(f"  ⚠️ Buffer cleanup skipped: {e}")
        
        # Delete chunks for random UUID documents
        try:
            chunks_deleted = await conn.execute("""
                DELETE FROM upload_pipeline.document_chunks
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents
                    WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                )
            """)
            logger.info(f"  🗑️ Deleted chunks: {chunks_deleted}")
        except Exception as e:
            logger.info(f"  ⚠️ Chunks cleanup skipped: {e}")
        
        # Delete events for random UUID documents
        try:
            events_deleted = await conn.execute("""
                DELETE FROM upload_pipeline.events
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents
                    WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                )
            """)
            logger.info(f"  🗑️ Deleted events: {events_deleted}")
        except Exception as e:
            logger.info(f"  ⚠️ Events cleanup skipped: {e}")
        
        # Delete jobs for random UUID documents
        try:
            jobs_deleted = await conn.execute("""
                DELETE FROM upload_pipeline.upload_jobs
                WHERE document_id IN (
                    SELECT document_id FROM upload_pipeline.documents
                    WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                )
            """)
            logger.info(f"  🗑️ Deleted jobs: {jobs_deleted}")
        except Exception as e:
            logger.info(f"  ⚠️ Jobs cleanup skipped: {e}")
        
        # Delete random UUID documents
        docs_deleted = await conn.execute("""
            DELETE FROM upload_pipeline.documents
            WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        """)
        logger.info(f"  🗑️ Deleted documents: {docs_deleted}")
        
        # Get final state
        final_total_docs = await conn.fetchval("SELECT COUNT(*) FROM upload_pipeline.documents")
        final_random_docs = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.documents
            WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        """)
        final_deterministic_docs = await conn.fetchval("""
            SELECT COUNT(*) FROM upload_pipeline.documents
            WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        """)
        
        # Save results
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "before": {
                "total_documents": total_docs,
                "random_documents": random_docs,
                "deterministic_documents": deterministic_docs
            },
            "after": {
                "total_documents": final_total_docs,
                "random_documents": final_random_docs,
                "deterministic_documents": final_deterministic_docs
            },
            "deleted_documents": total_docs - final_total_docs,
            "success": True
        }
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = f"phase_b_direct_cleanup_results_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"📊 Cleanup results saved to: {output_file}")
        
        # Print summary
        print(f"\n📊 DIRECT CLEANUP SUMMARY")
        print(f"Before: {total_docs} total, {random_docs} random, {deterministic_docs} deterministic")
        print(f"After: {final_total_docs} total, {final_random_docs} random, {final_deterministic_docs} deterministic")
        print(f"Deleted documents: {total_docs - final_total_docs}")
        print(f"Deterministic percentage: {(final_deterministic_docs / final_total_docs * 100) if final_total_docs > 0 else 0:.1f}%")
        
        await conn.close()
        logger.info("✅ Direct cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Direct cleanup failed: {e}")
        print(f"❌ Direct cleanup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
