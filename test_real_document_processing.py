#!/usr/bin/env python3
"""
Real Document Processing Test
Test real document processing with proper authentication after edge function deployment.
"""

import asyncio
import aiohttp
import json
import asyncpg
from datetime import datetime
from typing import Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class RealDocumentProcessor:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.db_url = os.getenv('DATABASE_URL')
        
        if not all([self.supabase_url, self.supabase_service_key, self.db_url]):
            raise ValueError("Missing required environment variables")
        
        self.edge_functions = {
            "doc-parser": f"{self.supabase_url}/functions/v1/doc-parser",
            "vector-processor": f"{self.supabase_url}/functions/v1/vector-processor"
        }
    
    async def test_real_processing_pipeline(self) -> Dict[str, Any]:
        """Test the complete document processing pipeline with a real document."""
        print("🔍 Testing Real Document Processing Pipeline")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "real_document_processing_pipeline",
            "document_selection": {},
            "doc_parser_test": {},
            "vector_processor_test": {},
            "pipeline_validation": {},
            "summary": {}
        }
        
        # Step 1: Find a pending document
        pending_doc = await self._find_pending_document()
        results["document_selection"] = pending_doc
        
        if not pending_doc.get("success"):
            print("❌ No pending documents found for testing")
            return results
        
        document_id = pending_doc["document"]["document_id"]
        document_title = pending_doc["document"]["title"]
        
        print(f"\n📄 Selected Document: {document_title}")
        print(f"   ID: {document_id}")
        
        # Step 2: Test doc-parser with proper parameters
        print(f"\n🔧 Testing doc-parser with real document...")
        
        doc_parser_payload = {
            "documentId": document_id,
            "document_path": pending_doc["document"]["raw_document_path"],
            "title": document_title
        }
        
        doc_parser_result = await self._call_edge_function(
            "doc-parser",
            self.edge_functions["doc-parser"],
            doc_parser_payload
        )
        
        results["doc_parser_test"] = doc_parser_result
        
        print(f"   Status: {doc_parser_result.get('status', 'unknown')}")
        if doc_parser_result.get('success'):
            print(f"   ✅ Doc-parser processed successfully")
            print(f"   Response: {doc_parser_result.get('response_summary', 'N/A')}")
        else:
            print(f"   ❌ Doc-parser failed: {doc_parser_result.get('error', 'Unknown error')}")
        
        # Step 3: If doc-parser succeeded, test vector-processor
        if doc_parser_result.get('success') and doc_parser_result.get('extracted_text'):
            print(f"\n🧮 Testing vector-processor with extracted text...")
            
            vector_payload = {
                "documentId": document_id,
                "extractedText": doc_parser_result["extracted_text"],
                "documentType": "regulatory"
            }
            
            vector_result = await self._call_edge_function(
                "vector-processor", 
                self.edge_functions["vector-processor"],
                vector_payload
            )
            
            results["vector_processor_test"] = vector_result
            
            print(f"   Status: {vector_result.get('status', 'unknown')}")
            if vector_result.get('success'):
                print(f"   ✅ Vector-processor completed successfully")
                print(f"   Vectors created: {vector_result.get('vectors_created', 'Unknown')}")
            else:
                print(f"   ❌ Vector-processor failed: {vector_result.get('error', 'Unknown error')}")
        else:
            print(f"\n⏭️ Skipping vector-processor (doc-parser failed)")
            results["vector_processor_test"] = {"status": "skipped", "reason": "doc_parser_failed"}
        
        # Step 4: Validate pipeline results
        validation_result = await self._validate_pipeline_results(document_id)
        results["pipeline_validation"] = validation_result
        
        # Generate summary
        results["summary"] = self._generate_processing_summary(results)
        
        return results
    
    async def _find_pending_document(self) -> Dict[str, Any]:
        """Find a pending document for testing."""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # Get a recent pending document
            query = """
                SELECT 
                    document_id,
                    title,
                    raw_document_path,
                    status,
                    vectors_generated,
                    vector_count,
                    created_at
                FROM regulatory_documents 
                WHERE status = 'pending' 
                   AND vectors_generated = FALSE
                   AND raw_document_path IS NOT NULL
                ORDER BY created_at DESC 
                LIMIT 1
            """
            
            doc = await conn.fetchrow(query)
            await conn.close()
            
            if not doc:
                return {"success": False, "reason": "no_pending_documents"}
            
            return {
                "success": True,
                "document": {
                    "document_id": str(doc['document_id']),
                    "title": doc['title'],
                    "raw_document_path": doc['raw_document_path'],
                    "status": doc['status'],
                    "vectors_generated": doc['vectors_generated'],
                    "vector_count": doc['vector_count'],
                    "created_at": doc['created_at'].isoformat()
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _call_edge_function(self, func_name: str, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call an edge function with proper authentication."""
        try:
            headers = {
                "Authorization": f"Bearer {self.supabase_service_key}",
                "Content-Type": "application/json",
                "apikey": self.supabase_service_key
            }
            
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.post(url, headers=headers, json=payload) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    response_text = await response.text()
                    
                    result = {
                        "status": "success" if response.status in [200, 201] else "failed",
                        "http_status": response.status,
                        "response_time": response_time,
                        "payload_sent": payload
                    }
                    
                    # Parse response
                    try:
                        response_json = json.loads(response_text)
                        result["response_json"] = response_json
                        result["success"] = response_json.get('success', False)
                        
                        # Extract key information
                        if func_name == "doc-parser" and result["success"]:
                            result["extracted_text"] = response_json.get('extractedText', '')
                            result["response_summary"] = f"Processed {len(result['extracted_text'])} chars"
                        elif func_name == "vector-processor" and result["success"]:
                            result["vectors_created"] = response_json.get('vectorsCreated', 0)
                        
                        if not result["success"]:
                            result["error"] = response_json.get('error', 'Unknown error')
                            result["error_details"] = response_json.get('details', '')
                            
                    except json.JSONDecodeError:
                        result["response_text"] = response_text
                        result["error"] = "Non-JSON response"
                        result["success"] = False
                    
                    return result
                    
        except Exception as e:
            return {
                "status": "exception",
                "success": False,
                "error": str(e),
                "payload_sent": payload
            }
    
    async def _validate_pipeline_results(self, document_id: str) -> Dict[str, Any]:
        """Validate the results of the processing pipeline."""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            # Check document status
            doc_query = """
                SELECT 
                    status,
                    vectors_generated,
                    vector_count,
                    extraction_method,
                    progress_percentage,
                    updated_at
                FROM regulatory_documents 
                WHERE document_id = $1
            """
            
            doc_result = await conn.fetchrow(doc_query, document_id)
            
            # Check if vectors were created
            vector_query = """
                SELECT COUNT(*) as vector_count
                FROM document_vectors 
                WHERE regulatory_document_id = $1
            """
            
            vector_result = await conn.fetchrow(vector_query, document_id)
            
            await conn.close()
            
            return {
                "success": True,
                "document_status": {
                    "status": doc_result['status'] if doc_result else None,
                    "vectors_generated": doc_result['vectors_generated'] if doc_result else None,
                    "vector_count": doc_result['vector_count'] if doc_result else None,
                    "extraction_method": doc_result['extraction_method'] if doc_result else None,
                    "progress_percentage": doc_result['progress_percentage'] if doc_result else None,
                    "updated_at": doc_result['updated_at'].isoformat() if doc_result and doc_result['updated_at'] else None
                },
                "actual_vector_count": vector_result['vector_count'] if vector_result else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_processing_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of processing test results."""
        
        doc_selection = results.get("document_selection", {})
        doc_parser = results.get("doc_parser_test", {})
        vector_processor = results.get("vector_processor_test", {})
        validation = results.get("pipeline_validation", {})
        
        summary = {
            "overall_status": "unknown",
            "document_found": doc_selection.get("success", False),
            "doc_parser_working": doc_parser.get("success", False),
            "vector_processor_working": vector_processor.get("success", False),
            "pipeline_complete": False,
            "vectors_created": 0,
            "critical_achievements": [],
            "remaining_issues": [],
            "recommendations": []
        }
        
        # Check if pipeline completed successfully
        if (summary["doc_parser_working"] and 
            summary["vector_processor_working"] and 
            validation.get("success")):
            summary["pipeline_complete"] = True
            summary["vectors_created"] = validation.get("actual_vector_count", 0)
        
        # Determine overall status
        if summary["pipeline_complete"] and summary["vectors_created"] > 0:
            summary["overall_status"] = "excellent"
        elif summary["doc_parser_working"] and summary["vector_processor_working"]:
            summary["overall_status"] = "good"
        elif summary["doc_parser_working"]:
            summary["overall_status"] = "partial"
        else:
            summary["overall_status"] = "failed"
        
        # Track achievements
        if summary["doc_parser_working"]:
            summary["critical_achievements"].append("Doc-parser edge function is now functional")
        
        if summary["vector_processor_working"]:
            summary["critical_achievements"].append("Vector-processor edge function is now functional")
        
        if summary["pipeline_complete"]:
            summary["critical_achievements"].append("Complete document processing pipeline working")
        
        if summary["vectors_created"] > 0:
            summary["critical_achievements"].append(f"Vector creation successful - {summary['vectors_created']} vectors created")
        
        # Identify remaining issues
        if not summary["doc_parser_working"]:
            summary["remaining_issues"].append("Doc-parser still has functional issues")
        
        if not summary["vector_processor_working"] and summary["doc_parser_working"]:
            summary["remaining_issues"].append("Vector-processor has issues despite doc-parser working")
        
        if summary["pipeline_complete"] and summary["vectors_created"] == 0:
            summary["remaining_issues"].append("Pipeline completes but no vectors are actually created")
        
        # Generate recommendations
        if summary["overall_status"] == "excellent":
            summary["recommendations"].append("Pipeline fully functional - ready for production validation")
        elif summary["overall_status"] == "good":
            summary["recommendations"].append("Core processing working - investigate vector storage issues")
        elif summary["overall_status"] == "partial":
            summary["recommendations"].append("Doc parsing working - investigate vector processing configuration")
        else:
            summary["recommendations"].append("Doc processing still failing - check authentication and database access")
        
        return summary

async def main():
    """Main function to run real document processing test."""
    print("🚀 Real Document Processing Pipeline Test")
    print("=" * 50)
    
    try:
        processor = RealDocumentProcessor()
        results = await processor.test_real_processing_pipeline()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_document_processing_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        
        # Display summary
        summary = results.get("summary", {})
        print(f"\n📊 Processing Test Summary:")
        print(f"   Overall Status: {summary.get('overall_status', 'unknown').upper()}")
        print(f"   Document Found: {summary.get('document_found', False)}")
        print(f"   Doc-Parser Working: {summary.get('doc_parser_working', False)}")
        print(f"   Vector-Processor Working: {summary.get('vector_processor_working', False)}")
        print(f"   Pipeline Complete: {summary.get('pipeline_complete', False)}")
        print(f"   Vectors Created: {summary.get('vectors_created', 0)}")
        
        if summary.get("critical_achievements"):
            print(f"\n🎉 Critical Achievements:")
            for achievement in summary["critical_achievements"]:
                print(f"   • {achievement}")
        
        if summary.get("remaining_issues"):
            print(f"\n⚠️ Remaining Issues:")
            for issue in summary["remaining_issues"]:
                print(f"   • {issue}")
        
        if summary.get("recommendations"):
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"   • {rec}")
        
        return results
        
    except Exception as e:
        print(f"❌ Real document processing test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main()) 