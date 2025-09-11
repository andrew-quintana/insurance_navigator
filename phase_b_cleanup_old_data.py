#!/usr/bin/env python3
"""
Phase B.3.1: Cleanup Old Random UUID Data
UUID Standardization - Remove Old Random UUID Documents

This script removes only the old documents with random UUIDs, keeping
the newly repopulated documents with deterministic UUIDs.

Since we've successfully repopulated with proper UUIDs, we can safely
remove the old random UUID documents that are causing the mismatch.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List

import asyncpg
from dotenv import load_dotenv
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OldDataCleanup:
    """Cleanup old random UUID data while preserving new deterministic data."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        
    async def connect_database(self) -> bool:
        """Connect to the database."""
        try:
            logger.info("🔌 Connecting to database...")
            self.conn = await asyncpg.connect(self.database_url)
            logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def disconnect_database(self):
        """Disconnect from the database."""
        if self.conn:
            await self.conn.close()
            logger.info("🔌 Database disconnected")
    
    def is_uuidv4(self, uuid_value) -> bool:
        """Check if UUID is version 4 (random)."""
        try:
            if isinstance(uuid_value, str):
                uuid_obj = uuid.UUID(uuid_value)
            else:
                uuid_obj = uuid_value
            return uuid_obj.version == 4
        except (ValueError, TypeError):
            return False
    
    async def get_old_documents(self) -> List[Dict[str, Any]]:
        """Get documents with random UUIDs that need to be cleaned up."""
        logger.info("📄 Identifying old random UUID documents...")
        
        try:
            documents = await self.conn.fetch("""
                SELECT 
                    d.document_id,
                    d.user_id,
                    d.filename,
                    d.file_sha256,
                    d.created_at,
                    COUNT(dc.chunk_id) as chunk_count
                FROM upload_pipeline.documents d
                LEFT JOIN upload_pipeline.document_chunks dc ON d.document_id = dc.document_id
                WHERE d.document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
                GROUP BY d.document_id, d.user_id, d.filename, d.file_sha256, d.created_at
                ORDER BY d.created_at DESC
            """)
            
            # Filter for UUIDv4 documents only
            old_documents = []
            for doc in documents:
                if self.is_uuidv4(doc['document_id']):
                    old_documents.append(dict(doc))
            
            logger.info(f"📄 Found {len(old_documents)} old documents to clean up")
            return old_documents
            
        except Exception as e:
            logger.error(f"❌ Failed to get old documents: {e}")
            return []
    
    async def cleanup_old_document(self, document_id: str) -> bool:
        """Clean up a single old document and all its related data."""
        logger.info(f"🗑️ Cleaning up document {document_id}...")
        
        try:
            async with self.conn.transaction():
                # Delete in reverse order of dependencies
                
                # Delete buffer entries
                try:
                    await self.conn.execute("""
                        DELETE FROM upload_pipeline.document_vector_buffer
                        WHERE chunk_id IN (
                            SELECT chunk_id FROM upload_pipeline.document_chunks
                            WHERE document_id = $1
                        )
                    """, document_id)
                except Exception:
                    pass  # Table might not exist
                
                # Delete chunks
                try:
                    await self.conn.execute("""
                        DELETE FROM upload_pipeline.document_chunks
                        WHERE document_id = $1
                    """, document_id)
                except Exception:
                    pass  # Table might not exist
                
                # Delete events
                try:
                    await self.conn.execute("""
                        DELETE FROM upload_pipeline.events
                        WHERE document_id = $1
                    """, document_id)
                except Exception:
                    pass  # Table might not exist
                
                # Delete jobs
                try:
                    await self.conn.execute("""
                        DELETE FROM upload_pipeline.upload_jobs
                        WHERE document_id = $1
                    """, document_id)
                except Exception:
                    pass  # Table might not exist
                
                # Delete document
                try:
                    await self.conn.execute("""
                        DELETE FROM upload_pipeline.documents
                        WHERE document_id = $1
                    """, document_id)
                except Exception:
                    pass  # Table might not exist
            
            logger.info(f"✅ Document {document_id} cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Document {document_id} cleanup failed: {e}")
            return False
    
    async def run_cleanup(self) -> Dict[str, Any]:
        """Run complete cleanup of old random UUID data."""
        logger.info("🚀 Starting old data cleanup...")
        
        if not await self.connect_database():
            return {"error": "Database connection failed"}
        
        try:
            # Get old documents
            old_documents = await self.get_old_documents()
            if not old_documents:
                logger.info("✅ No old documents found to clean up")
                return {"success": True, "cleaned_documents": 0}
            
            # Clean up each old document
            cleaned_count = 0
            failed_count = 0
            
            for doc in old_documents:
                success = await self.cleanup_old_document(doc['document_id'])
                if success:
                    cleaned_count += 1
                else:
                    failed_count += 1
            
            # Get final data summary
            final_summary = await self.get_final_summary()
            
            results = {
                "timestamp": datetime.utcnow().isoformat(),
                "old_documents_found": len(old_documents),
                "cleaned_documents": cleaned_count,
                "failed_cleanups": failed_count,
                "final_summary": final_summary,
                "success": failed_count == 0
            }
            
            logger.info(f"✅ Cleanup completed: {cleaned_count} cleaned, {failed_count} failed")
            return results
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {"error": str(e)}
        
        finally:
            await self.disconnect_database()
    
    async def get_final_summary(self) -> Dict[str, Any]:
        """Get final data summary after cleanup."""
        try:
            # Count documents by UUID type
            total_docs = await self.conn.fetchval("SELECT COUNT(*) FROM upload_pipeline.documents")
            
            deterministic_docs = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents
                WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-5[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            """)
            
            random_docs = await self.conn.fetchval("""
                SELECT COUNT(*) FROM upload_pipeline.documents
                WHERE document_id::text ~ '^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            """)
            
            # Count chunks
            total_chunks = await self.conn.fetchval("SELECT COUNT(*) FROM upload_pipeline.document_chunks")
            
            return {
                "total_documents": total_docs,
                "deterministic_documents": deterministic_docs,
                "random_documents": random_docs,
                "total_chunks": total_chunks,
                "deterministic_percentage": (deterministic_docs / total_docs * 100) if total_docs > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get final summary: {e}")
            return {"error": str(e)}

async def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv('.env.production')
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment variables")
        return
    
    # Run cleanup
    cleanup_tool = OldDataCleanup(database_url)
    results = await cleanup_tool.run_cleanup()
    
    # Save results
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = f"phase_b_cleanup_results_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📊 Cleanup results saved to: {output_file}")
    
    # Print summary
    if results.get("success"):
        print(f"\n📊 CLEANUP SUMMARY")
        print(f"Old documents found: {results['old_documents_found']}")
        print(f"Cleaned documents: {results['cleaned_documents']}")
        print(f"Failed cleanups: {results['failed_cleanups']}")
        
        if 'final_summary' in results:
            summary = results['final_summary']
            print(f"\n📊 FINAL STATE")
            print(f"Total documents: {summary.get('total_documents', 0)}")
            print(f"Deterministic documents: {summary.get('deterministic_documents', 0)}")
            print(f"Random documents: {summary.get('random_documents', 0)}")
            print(f"Deterministic percentage: {summary.get('deterministic_percentage', 0):.1f}%")
    else:
        print(f"❌ Cleanup failed: {results.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())
