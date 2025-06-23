#!/usr/bin/env python3
"""
Edge Function Pipeline Diagnostic
================================

Analyzes the complete edge function pipeline to identify where
document processing is failing based on the live test results.

Key Issues Found:
- document_vectors table empty
- Processing jobs stuck
- Duplicate documents
- Incomplete edge function chain

Usage:
    python test_edge_function_pipeline.py --document-id 74001edd-dd9b-46bc-ab9a-bda92e09e985
"""

import os
import sys
import json
import asyncio
import logging
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

class EdgeFunctionPipelineDiagnostic:
    """Comprehensive edge function pipeline analysis"""
    
    def __init__(self):
        self.db_connection = None
        self.supabase_client = None
        self.setup_connections()
    
    def setup_connections(self):
        """Setup database and Supabase connections"""
        try:
            # Database connection
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_url = (os.getenv('DATABASE_URL') or 
                     os.getenv('SUPABASE_DB_URL') or
                     os.getenv('DB_URL'))
            
            if db_url:
                self.db_connection = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
                logger.info("✅ Database connection established")
            else:
                logger.warning("⚠️ No database URL found")
            
            # Supabase client for edge function logs
            try:
                from supabase import create_client
                
                supabase_url = os.getenv('SUPABASE_URL')
                supabase_key = os.getenv('SUPABASE_ANON_KEY') or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                
                if supabase_url and supabase_key:
                    self.supabase_client = create_client(supabase_url, supabase_key)
                    logger.info("✅ Supabase client initialized")
                else:
                    logger.warning("⚠️ Supabase credentials not found")
                    
            except ImportError:
                logger.warning("⚠️ Supabase client not available")
                
        except Exception as e:
            logger.error(f"❌ Connection setup failed: {e}")
    
    async def analyze_document_pipeline(self, document_id: str) -> Dict[str, Any]:
        """Analyze complete pipeline for a specific document"""
        logger.info(f"🔍 Analyzing pipeline for document: {document_id}")
        
        analysis = {
            "document_id": document_id,
            "timestamp": datetime.now().isoformat(),
            "pipeline_stages": {},
            "issues_found": [],
            "recommendations": []
        }
        
        # Stage 1: Document Record Analysis
        analysis["pipeline_stages"]["document_record"] = await self.analyze_document_record(document_id)
        
        # Stage 2: Processing Jobs Analysis
        analysis["pipeline_stages"]["processing_jobs"] = await self.analyze_processing_jobs(document_id)
        
        # Stage 3: Vector Processing Analysis
        analysis["pipeline_stages"]["vector_processing"] = await self.analyze_vector_processing(document_id)
        
        # Stage 4: Edge Function Logs Analysis
        analysis["pipeline_stages"]["edge_functions"] = await self.analyze_edge_function_logs(document_id)
        
        # Stage 5: Storage Analysis
        analysis["pipeline_stages"]["storage"] = await self.analyze_storage_status(document_id)
        
        # Generate recommendations
        analysis["recommendations"] = self.generate_recommendations(analysis)
        
        return analysis
    
    async def analyze_document_record(self, document_id: str) -> Dict[str, Any]:
        """Analyze document table records"""
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
        
        try:
            with self.db_connection.cursor() as cursor:
                # Check for document records
                cursor.execute("""
                    SELECT 
                        id, 
                        filename, 
                        file_size, 
                        storage_path,
                        upload_status,
                        processing_status,
                        created_at,
                        updated_at,
                        user_id
                    FROM documents 
                    WHERE id = %s OR filename LIKE %s
                    ORDER BY created_at DESC
                """, (document_id, f"%{document_id}%"))
                
                documents = cursor.fetchall()
                
                # Check for duplicates
                cursor.execute("""
                    SELECT filename, COUNT(*) as count
                    FROM documents 
                    WHERE filename = (SELECT filename FROM documents WHERE id = %s LIMIT 1)
                    GROUP BY filename
                    HAVING COUNT(*) > 1
                """, (document_id,))
                
                duplicates = cursor.fetchall()
                
                return {
                    "status": "success",
                    "documents_found": len(documents),
                    "documents": [dict(doc) for doc in documents],
                    "duplicates": [dict(dup) for dup in duplicates],
                    "has_duplicates": len(duplicates) > 0
                }
                
        except Exception as e:
            logger.error(f"❌ Document record analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def analyze_processing_jobs(self, document_id: str) -> Dict[str, Any]:
        """Analyze processing jobs table"""
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
        
        try:
            with self.db_connection.cursor() as cursor:
                # Check processing jobs
                cursor.execute("""
                    SELECT 
                        id,
                        document_id,
                        job_type,
                        status,
                        progress,
                        error_message,
                        created_at,
                        updated_at,
                        metadata
                    FROM processing_jobs 
                    WHERE document_id = %s
                    ORDER BY created_at DESC
                """, (document_id,))
                
                jobs = cursor.fetchall()
                
                # Check for stuck jobs (created >10 minutes ago, still processing)
                cursor.execute("""
                    SELECT COUNT(*) as stuck_count
                    FROM processing_jobs 
                    WHERE document_id = %s 
                    AND status IN ('pending', 'processing')
                    AND created_at < NOW() - INTERVAL '10 minutes'
                """, (document_id,))
                
                stuck_result = cursor.fetchone()
                stuck_count = stuck_result['stuck_count'] if stuck_result else 0
                
                return {
                    "status": "success",
                    "jobs_found": len(jobs),
                    "jobs": [dict(job) for job in jobs],
                    "stuck_jobs": stuck_count,
                    "job_types": list(set(job['job_type'] for job in jobs)) if jobs else []
                }
                
        except Exception as e:
            logger.error(f"❌ Processing jobs analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def analyze_vector_processing(self, document_id: str) -> Dict[str, Any]:
        """Analyze vector processing results"""
        if not self.db_connection:
            return {"status": "error", "message": "No database connection"}
        
        try:
            with self.db_connection.cursor() as cursor:
                # Check document_vectors table
                cursor.execute("""
                    SELECT 
                        id,
                        document_id,
                        chunk_index,
                        content_preview,
                        embedding_model,
                        created_at
                    FROM document_vectors 
                    WHERE document_id = %s
                    ORDER BY chunk_index
                """, (document_id,))
                
                vectors = cursor.fetchall()
                
                # Check total vectors in table
                cursor.execute("SELECT COUNT(*) as total_vectors FROM document_vectors")
                total_result = cursor.fetchone()
                total_vectors = total_result['total_vectors'] if total_result else 0
                
                # Check if document exists but no vectors
                cursor.execute("""
                    SELECT COUNT(*) as doc_exists 
                    FROM documents 
                    WHERE id = %s
                """, (document_id,))
                
                doc_exists_result = cursor.fetchone()
                doc_exists = doc_exists_result['doc_exists'] > 0 if doc_exists_result else False
                
                return {
                    "status": "success",
                    "vectors_found": len(vectors),
                    "vectors": [dict(vec) for vec in vectors],
                    "total_vectors_in_table": total_vectors,
                    "document_exists": doc_exists,
                    "vectorization_failed": doc_exists and len(vectors) == 0
                }
                
        except Exception as e:
            logger.error(f"❌ Vector processing analysis failed: {e}")
            return {"status": "error", "message": str(e)}
    
    async def analyze_edge_function_logs(self, document_id: str) -> Dict[str, Any]:
        """Analyze edge function execution logs"""
        # This would require Supabase Management API access
        # For now, return structure for manual log checking
        
        expected_functions = [
            "upload-handler",
            "doc-parser", 
            "vector-processor",
            "trigger-processor"
        ]
        
        return {
            "status": "manual_check_required",
            "expected_functions": expected_functions,
            "message": "Check Supabase Dashboard > Edge Functions > Logs for each function",
            "search_terms": [document_id, "aetna_sample_ppo.pdf"]
        }
    
    async def analyze_storage_status(self, document_id: str) -> Dict[str, Any]:
        """Analyze Supabase storage status"""
        if not self.supabase_client:
            return {"status": "error", "message": "No Supabase client"}
        
        try:
            # This would check if files exist in storage
            # Implementation depends on storage structure
            return {
                "status": "manual_check_required",
                "message": "Check Supabase Dashboard > Storage > documents bucket",
                "search_path": f"*/{document_id}/*"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Check for duplicate documents
        doc_analysis = analysis["pipeline_stages"].get("document_record", {})
        if doc_analysis.get("has_duplicates"):
            recommendations.append("🔧 CRITICAL: Remove duplicate document records to prevent processing conflicts")
        
        # Check for stuck jobs
        job_analysis = analysis["pipeline_stages"].get("processing_jobs", {})
        if job_analysis.get("stuck_jobs", 0) > 0:
            recommendations.append("🔧 URGENT: Reset stuck processing jobs or investigate job processor")
        
        # Check for vectorization failure
        vector_analysis = analysis["pipeline_stages"].get("vector_processing", {})
        if vector_analysis.get("vectorization_failed"):
            recommendations.append("🔧 HIGH: Document exists but no vectors created - check doc-parser and vector-processor edge functions")
        
        # Check for missing job types
        expected_job_types = ["parse", "vectorize", "index"]
        actual_job_types = job_analysis.get("job_types", [])
        missing_jobs = set(expected_job_types) - set(actual_job_types)
        if missing_jobs:
            recommendations.append(f"🔧 MEDIUM: Missing job types: {missing_jobs} - check edge function triggers")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ No critical issues found - check edge function logs for detailed error messages")
        
        return recommendations
    
    async def run_diagnostic(self, document_id: str = None):
        """Run complete diagnostic"""
        if not document_id:
            # Use the document ID from the live test
            document_id = "74001edd-dd9b-46bc-ab9a-bda92e09e985"
        
        logger.info(f"🚀 Starting edge function pipeline diagnostic for: {document_id}")
        
        analysis = await self.analyze_document_pipeline(document_id)
        
        # Print results
        self.print_analysis_report(analysis)
        
        # Save results
        output_file = f"edge_function_diagnostic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        logger.info(f"📊 Diagnostic results saved to: {output_file}")
        
        return analysis
    
    def print_analysis_report(self, analysis: Dict[str, Any]):
        """Print formatted analysis report"""
        print("\n" + "="*80)
        print("🔍 EDGE FUNCTION PIPELINE DIAGNOSTIC REPORT")
        print("="*80)
        print(f"Document ID: {analysis['document_id']}")
        print(f"Analysis Time: {analysis['timestamp']}")
        print()
        
        # Document Records
        doc_stage = analysis["pipeline_stages"]["document_record"]
        print("📄 DOCUMENT RECORDS:")
        if doc_stage.get("status") == "success":
            print(f"   Documents Found: {doc_stage['documents_found']}")
            if doc_stage.get("has_duplicates"):
                print("   ❌ DUPLICATES DETECTED!")
                for dup in doc_stage["duplicates"]:
                    print(f"      - {dup['filename']}: {dup['count']} copies")
            else:
                print("   ✅ No duplicates found")
        else:
            print(f"   ❌ Error: {doc_stage.get('message')}")
        print()
        
        # Processing Jobs
        job_stage = analysis["pipeline_stages"]["processing_jobs"]
        print("⚙️ PROCESSING JOBS:")
        if job_stage.get("status") == "success":
            print(f"   Jobs Found: {job_stage['jobs_found']}")
            print(f"   Job Types: {job_stage['job_types']}")
            if job_stage.get("stuck_jobs", 0) > 0:
                print(f"   ❌ STUCK JOBS: {job_stage['stuck_jobs']}")
            else:
                print("   ✅ No stuck jobs")
        else:
            print(f"   ❌ Error: {job_stage.get('message')}")
        print()
        
        # Vector Processing
        vector_stage = analysis["pipeline_stages"]["vector_processing"]
        print("🔢 VECTOR PROCESSING:")
        if vector_stage.get("status") == "success":
            print(f"   Vectors Found: {vector_stage['vectors_found']}")
            print(f"   Total Vectors in DB: {vector_stage['total_vectors_in_table']}")
            if vector_stage.get("vectorization_failed"):
                print("   ❌ VECTORIZATION FAILED!")
            else:
                print("   ✅ Vectorization status OK")
        else:
            print(f"   ❌ Error: {vector_stage.get('message')}")
        print()
        
        # Recommendations
        print("🎯 RECOMMENDATIONS:")
        for i, rec in enumerate(analysis["recommendations"], 1):
            print(f"   {i}. {rec}")
        print()
        
        print("="*80)

async def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Edge Function Pipeline Diagnostic")
    parser.add_argument("--document-id", help="Document ID to analyze")
    parser.add_argument("--live-test", action="store_true", help="Use document ID from live test")
    
    args = parser.parse_args()
    
    document_id = args.document_id
    if args.live_test or not document_id:
        # Use the document ID from the live test logs
        document_id = "74001edd-dd9b-46bc-ab9a-bda92e09e985"
    
    diagnostic = EdgeFunctionPipelineDiagnostic()
    await diagnostic.run_diagnostic(document_id)

if __name__ == "__main__":
    asyncio.run(main()) 