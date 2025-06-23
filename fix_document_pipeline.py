#!/usr/bin/env python3
"""
Document Pipeline Repair Script
==============================

Fixes the broken document processing pipeline by:
1. Cleaning up duplicate/stuck documents
2. Manually triggering missing edge functions
3. Completing vectorization for uploaded documents

Based on live test analysis showing:
- document_vectors table empty
- Processing jobs stuck
- Edge function chain broken after upload-handler

Usage:
    python fix_document_pipeline.py --repair-document 74001edd-dd9b-46bc-ab9a-bda92e09e985
    python fix_document_pipeline.py --cleanup-duplicates
    python fix_document_pipeline.py --reset-stuck-jobs
"""

import os
import sys
import json
import asyncio
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentPipelineRepairer:
    """Repairs broken document processing pipeline"""
    
    def __init__(self):
        self.db_connection = None
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        self.setup_connections()
    
    def setup_connections(self):
        """Setup database connections"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_url = (os.getenv('DATABASE_URL') or 
                     os.getenv('SUPABASE_DB_URL') or
                     os.getenv('DB_URL'))
            
            if db_url:
                self.db_connection = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
                logger.info("✅ Database connection established")
            else:
                logger.error("❌ No database URL found")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def cleanup_duplicate_documents(self) -> Dict[str, Any]:
        """Remove duplicate document records"""
        logger.info("🧹 Cleaning up duplicate documents...")
        
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
        
        try:
            with self.db_connection.cursor() as cursor:
                # Find duplicates by filename
                cursor.execute("""
                    SELECT filename, array_agg(id ORDER BY created_at) as ids, COUNT(*) as count
                    FROM documents 
                    GROUP BY filename 
                    HAVING COUNT(*) > 1
                """)
                
                duplicates = cursor.fetchall()
                
                cleaned_count = 0
                for duplicate in duplicates:
                    filename = duplicate['filename']
                    ids = duplicate['ids']
                    
                    # Keep the first (oldest) record, delete the rest
                    keep_id = ids[0]
                    delete_ids = ids[1:]
                    
                    logger.info(f"📄 {filename}: keeping {keep_id}, deleting {delete_ids}")
                    
                    # Delete duplicate records
                    for delete_id in delete_ids:
                        cursor.execute("DELETE FROM documents WHERE id = %s", (delete_id,))
                        cleaned_count += 1
                
                self.db_connection.commit()
                
                return {
                    "status": "success",
                    "duplicates_found": len(duplicates),
                    "records_cleaned": cleaned_count
                }
                
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            self.db_connection.rollback()
            return {"status": "error", "message": str(e)}
    
    async def reset_stuck_jobs(self) -> Dict[str, Any]:
        """Reset stuck processing jobs"""
        logger.info("🔄 Resetting stuck processing jobs...")
        
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
        
        try:
            with self.db_connection.cursor() as cursor:
                # Find stuck jobs (processing for >10 minutes)
                cursor.execute("""
                    SELECT id, document_id, job_type, status, created_at
                    FROM processing_jobs 
                    WHERE status IN ('pending', 'processing')
                    AND created_at < NOW() - INTERVAL '10 minutes'
                """)
                
                stuck_jobs = cursor.fetchall()
                
                # Reset stuck jobs to failed so they can be retried
                reset_count = 0
                for job in stuck_jobs:
                    logger.info(f"🔄 Resetting job {job['id']}: {job['job_type']} for document {job['document_id']}")
                    
                    cursor.execute("""
                        UPDATE processing_jobs 
                        SET status = 'failed', 
                            error_message = 'Reset due to stuck status',
                            updated_at = NOW()
                        WHERE id = %s
                    """, (job['id'],))
                    
                    reset_count += 1
                
                self.db_connection.commit()
                
                return {
                    "status": "success",
                    "stuck_jobs_found": len(stuck_jobs),
                    "jobs_reset": reset_count
                }
                
        except Exception as e:
            logger.error(f"❌ Job reset failed: {e}")
            self.db_connection.rollback()
            return {"status": "error", "message": str(e)}
    
    async def manually_trigger_vectorization(self, document_id: str) -> Dict[str, Any]:
        """Manually trigger vectorization for a document"""
        logger.info(f"🚀 Manually triggering vectorization for document: {document_id}")
        
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
        
        try:
            # Get document details
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, filename, storage_path, file_size, user_id
                    FROM documents 
                    WHERE id = %s
                """, (document_id,))
                
                document = cursor.fetchone()
                
                if not document:
                    return {"status": "error", "message": "Document not found"}
                
                document = dict(document)
            
            # Trigger edge functions manually
            results = {}
            
            # 1. Trigger doc-parser
            parser_result = await self.trigger_edge_function("doc-parser", {
                "documentId": document_id,
                "filename": document["filename"],
                "storagePath": document["storage_path"],
                "userId": document["user_id"]
            })
            results["doc_parser"] = parser_result
            
            # 2. Wait a bit then trigger vector-processor
            await asyncio.sleep(2)
            
            vector_result = await self.trigger_edge_function("vector-processor", {
                "documentId": document_id,
                "filename": document["filename"],
                "storagePath": document["storage_path"],
                "userId": document["user_id"]
            })
            results["vector_processor"] = vector_result
            
            return {
                "status": "success",
                "document": document,
                "edge_function_results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Manual vectorization failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def trigger_edge_function(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a specific edge function"""
        if not self.supabase_url or not self.supabase_key:
            return {"status": "error", "message": "Missing Supabase credentials"}
        
        try:
            url = f"{self.supabase_url}/functions/v1/{function_name}"
            headers = {
                "Authorization": f"Bearer {self.supabase_key}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"🔗 Triggering {function_name} with payload: {payload}")
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ {function_name} triggered successfully")
                return {
                    "status": "success",
                    "response": response.json() if response.content else None
                }
            else:
                logger.error(f"❌ {function_name} failed: {response.status_code} - {response.text}")
                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "message": response.text
                }
                
        except Exception as e:
            logger.error(f"❌ Edge function trigger failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def check_vectorization_status(self, document_id: str) -> Dict[str, Any]:
        """Check if vectorization completed successfully"""
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
        
        try:
            with self.db_connection.cursor() as cursor:
                # Check document_vectors
                cursor.execute("""
                    SELECT COUNT(*) as vector_count
                    FROM document_vectors 
                    WHERE document_id = %s
                """, (document_id,))
                
                vector_result = cursor.fetchone()
                vector_count = vector_result['vector_count'] if vector_result else 0
                
                # Check processing jobs
                cursor.execute("""
                    SELECT job_type, status, error_message
                    FROM processing_jobs 
                    WHERE document_id = %s
                    ORDER BY created_at DESC
                """, (document_id,))
                
                jobs = cursor.fetchall()
                
                return {
                    "status": "success",
                    "vector_count": vector_count,
                    "vectorization_complete": vector_count > 0,
                    "processing_jobs": [dict(job) for job in jobs]
                }
                
        except Exception as e:
            logger.error(f"❌ Status check failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def repair_document(self, document_id: str) -> Dict[str, Any]:
        """Complete repair workflow for a specific document"""
        logger.info(f"🔧 Starting complete repair for document: {document_id}")
        
        repair_results = {
            "document_id": document_id,
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        # Step 1: Check initial status
        logger.info("1️⃣ Checking initial status...")
        initial_status = await self.check_vectorization_status(document_id)
        repair_results["steps"]["initial_status"] = initial_status
        
        # Step 2: Reset any stuck jobs for this document
        logger.info("2️⃣ Resetting stuck jobs...")
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
        
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE processing_jobs 
                    SET status = 'failed', 
                        error_message = 'Reset for manual repair',
                        updated_at = NOW()
                    WHERE document_id = %s 
                    AND status IN ('pending', 'processing')
                """, (document_id,))
                
                self.db_connection.commit()
                logger.info("✅ Document-specific jobs reset")
        except Exception as e:
            logger.error(f"❌ Job reset failed: {e}")
        
        # Step 3: Manually trigger vectorization
        logger.info("3️⃣ Manually triggering vectorization...")
        vectorization_result = await self.manually_trigger_vectorization(document_id)
        repair_results["steps"]["vectorization"] = vectorization_result
        
        # Step 4: Wait and check final status
        logger.info("4️⃣ Waiting for processing...")
        await asyncio.sleep(10)  # Wait for edge functions to process
        
        final_status = await self.check_vectorization_status(document_id)
        repair_results["steps"]["final_status"] = final_status
        
        # Determine overall success
        repair_results["success"] = (
            final_status.get("vectorization_complete", False) or
            vectorization_result.get("status") == "success"
        )
        
        return repair_results
    
    async def run_complete_repair(self):
        """Run complete pipeline repair"""
        logger.info("🚀 Starting complete document pipeline repair...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "operations": {}
        }
        
        # 1. Cleanup duplicates
        logger.info("\n1️⃣ CLEANING UP DUPLICATES")
        cleanup_result = await self.cleanup_duplicate_documents()
        results["operations"]["cleanup_duplicates"] = cleanup_result
        
        # 2. Reset stuck jobs
        logger.info("\n2️⃣ RESETTING STUCK JOBS")
        reset_result = await self.reset_stuck_jobs()
        results["operations"]["reset_jobs"] = reset_result
        
        # 3. Repair the specific document from live test
        logger.info("\n3️⃣ REPAIRING LIVE TEST DOCUMENT")
        document_id = "74001edd-dd9b-46bc-ab9a-bda92e09e985"
        repair_result = await self.repair_document(document_id)
        results["operations"]["repair_document"] = repair_result
        
        # Save results
        output_file = f"pipeline_repair_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n📊 Repair results saved to: {output_file}")
        
        # Print summary
        self.print_repair_summary(results)
        
        return results
    
    def print_repair_summary(self, results: Dict[str, Any]):
        """Print formatted repair summary"""
        print("\n" + "="*80)
        print("🔧 DOCUMENT PIPELINE REPAIR SUMMARY")
        print("="*80)
        
        operations = results.get("operations", {})
        
        # Cleanup summary
        cleanup = operations.get("cleanup_duplicates", {})
        if cleanup.get("status") == "success":
            print(f"✅ Duplicates Cleaned: {cleanup.get('records_cleaned', 0)} records")
        else:
            print(f"❌ Cleanup Failed: {cleanup.get('message', 'Unknown error')}")
        
        # Job reset summary
        reset = operations.get("reset_jobs", {})
        if reset.get("status") == "success":
            print(f"✅ Jobs Reset: {reset.get('jobs_reset', 0)} stuck jobs")
        else:
            print(f"❌ Job Reset Failed: {reset.get('message', 'Unknown error')}")
        
        # Document repair summary
        repair = operations.get("repair_document", {})
        if repair.get("success"):
            final_status = repair.get("steps", {}).get("final_status", {})
            vector_count = final_status.get("vector_count", 0)
            print(f"✅ Document Repair: SUCCESS - {vector_count} vectors created")
        else:
            print("❌ Document Repair: FAILED - check edge function logs")
        
        print("="*80)
        print("\n🎯 NEXT STEPS:")
        print("1. Check Supabase Dashboard > Edge Functions > Logs")
        print("2. Test document upload again")
        print("3. Monitor document_vectors table for new entries")
        print("4. If still failing, check edge function code and triggers")

async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Document Pipeline Repair Script")
    parser.add_argument("--repair-document", help="Repair specific document ID")
    parser.add_argument("--cleanup-duplicates", action="store_true", help="Clean up duplicate documents")
    parser.add_argument("--reset-stuck-jobs", action="store_true", help="Reset stuck processing jobs")
    parser.add_argument("--complete-repair", action="store_true", help="Run complete repair workflow")
    
    args = parser.parse_args()
    
    repairer = DocumentPipelineRepairer()
    
    if args.complete_repair or not any([args.repair_document, args.cleanup_duplicates, args.reset_stuck_jobs]):
        # Run complete repair by default
        await repairer.run_complete_repair()
    else:
        if args.cleanup_duplicates:
            result = await repairer.cleanup_duplicate_documents()
            print(f"Cleanup result: {result}")
        
        if args.reset_stuck_jobs:
            result = await repairer.reset_stuck_jobs()
            print(f"Reset result: {result}")
        
        if args.repair_document:
            result = await repairer.repair_document(args.repair_document)
            print(f"Repair result: {result}")

if __name__ == "__main__":
    asyncio.run(main()) 