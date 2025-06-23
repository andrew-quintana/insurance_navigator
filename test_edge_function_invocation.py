#!/usr/bin/env python3
"""
Direct Edge Function Invocation Test
Test direct invocation of doc-parser and vector-processor edge functions
to validate our fixes and see what happens when we try to trigger them.
"""

import asyncio
import aiohttp
import json
import tempfile
import os
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class EdgeFunctionInvocationTester:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_anon_key = os.getenv('SUPABASE_ANON_KEY') 
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        self.edge_functions = {
            "doc-parser": f"{self.supabase_url}/functions/v1/doc-parser",
            "vector-processor": f"{self.supabase_url}/functions/v1/vector-processor"
        }
        
        if not all([self.supabase_url, self.supabase_anon_key, self.supabase_service_key]):
            raise ValueError("Missing required Supabase environment variables")
    
    async def test_edge_function_invocation(self) -> Dict[str, Any]:
        """Test direct invocation of edge functions."""
        print("🔧 Testing Direct Edge Function Invocation")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_type": "edge_function_direct_invocation",
            "edge_function_tests": {},
            "real_document_processing": {},
            "summary": {}
        }
        
        # Test 1: Health check calls (GET requests)
        print("\n🏥 Testing Health Check Calls (GET requests)")
        for func_name, url in self.edge_functions.items():
            print(f"\n  Testing {func_name} health check...")
            
            health_result = await self._test_health_check(func_name, url)
            results["edge_function_tests"][f"{func_name}_health"] = health_result
            
            print(f"    Status: {health_result.get('status', 'unknown')}")
            if health_result.get('response_data'):
                print(f"    Response: {health_result['response_data']}")
            if health_result.get('error'):
                print(f"    Error: {health_result['error']}")
        
        # Test 2: Actual function invocation with real document
        print("\n📤 Testing Real Document Processing")
        
        # Get a real document from the database that needs processing
        real_doc_test = await self._test_real_document_processing()
        results["real_document_processing"] = real_doc_test
        
        # Test 3: Direct POST requests with sample data
        print("\n📝 Testing Direct POST Invocation")
        
        # Test doc-parser with sample document
        doc_parser_test = await self._test_doc_parser_invocation()
        results["edge_function_tests"]["doc_parser_invocation"] = doc_parser_test
        
        # Test vector-processor with sample data
        vector_processor_test = await self._test_vector_processor_invocation()
        results["edge_function_tests"]["vector_processor_invocation"] = vector_processor_test
        
        # Generate summary
        results["summary"] = self._generate_invocation_summary(results)
        
        return results
    
    async def _test_health_check(self, func_name: str, url: str) -> Dict[str, Any]:
        """Test health check endpoint (GET request)."""
        try:
            headers = {
                "Authorization": f"Bearer {self.supabase_anon_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                start_time = asyncio.get_event_loop().time()
                async with session.get(url, headers=headers) as response:
                    response_time = asyncio.get_event_loop().time() - start_time
                    
                    response_text = await response.text()
                    
                    result = {
                        "status": "success" if response.status == 200 else "failed",
                        "http_status": response.status,
                        "response_time": response_time,
                        "response_data": response_text,
                        "headers": dict(response.headers)
                    }
                    
                    # Try to parse as JSON if possible
                    try:
                        response_json = json.loads(response_text)
                        result["response_json"] = response_json
                    except json.JSONDecodeError:
                        result["response_type"] = "non_json"
                    
                    return result
                    
        except Exception as e:
            return {
                "status": "exception",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def _test_real_document_processing(self) -> Dict[str, Any]:
        """Test processing of a real document from the database."""
        print("\n  📋 Getting real document for processing...")
        
        try:
            import asyncpg
            db_url = os.getenv('DATABASE_URL')
            
            if not db_url:
                return {"status": "skipped", "reason": "no_database_url"}
            
            conn = await asyncpg.connect(db_url)
            
            # Get a recent document that needs processing
            doc_query = """
                SELECT document_id, title, raw_document_path, status
                FROM regulatory_documents 
                WHERE vectors_generated = FALSE 
                   AND status = 'pending'
                   AND raw_document_path IS NOT NULL
                ORDER BY created_at DESC 
                LIMIT 1
            """
            
            doc = await conn.fetchrow(doc_query)
            await conn.close()
            
            if not doc:
                print("    ⚠️ No documents found that need processing")
                return {"status": "no_documents", "message": "No pending documents found"}
            
            print(f"    📄 Found document: {doc['title']}")
            print(f"       ID: {doc['document_id']}")
            print(f"       Path: {doc['raw_document_path']}")
            print(f"       Status: {doc['status']}")
            
            # Test 1: Invoke doc-parser for this document
            print(f"\n  🔧 Invoking doc-parser for document {doc['document_id']}")
            
            doc_parser_payload = {
                "document_id": str(doc['document_id']),
                "document_path": doc['raw_document_path'],
                "title": doc['title']
            }
            
            doc_parser_result = await self._invoke_edge_function(
                "doc-parser", 
                self.edge_functions["doc-parser"],
                doc_parser_payload
            )
            
            print(f"    Doc-parser result: {doc_parser_result.get('status', 'unknown')}")
            if doc_parser_result.get('error'):
                print(f"    Error: {doc_parser_result['error']}")
            
            # Test 2: If doc-parser succeeds, try vector-processor
            vector_processor_result = {"status": "skipped", "reason": "doc_parser_failed"}
            
            if doc_parser_result.get('status') == 'success':
                print(f"\n  🧮 Invoking vector-processor for document {doc['document_id']}")
                
                vector_payload = {
                    "document_id": str(doc['document_id']),
                    "force_reprocess": True
                }
                
                vector_processor_result = await self._invoke_edge_function(
                    "vector-processor",
                    self.edge_functions["vector-processor"], 
                    vector_payload
                )
                
                print(f"    Vector-processor result: {vector_processor_result.get('status', 'unknown')}")
                if vector_processor_result.get('error'):
                    print(f"    Error: {vector_processor_result['error']}")
            
            return {
                "status": "completed",
                "document": {
                    "id": str(doc['document_id']),
                    "title": doc['title'],
                    "path": doc['raw_document_path']
                },
                "doc_parser_result": doc_parser_result,
                "vector_processor_result": vector_processor_result
            }
            
        except Exception as e:
            print(f"    ❌ Real document processing failed: {e}")
            return {
                "status": "exception",
                "error": str(e)
            }
    
    async def _test_doc_parser_invocation(self) -> Dict[str, Any]:
        """Test direct doc-parser invocation with sample data."""
        print("\n  🔧 Testing doc-parser direct invocation...")
        
        # Create a test payload for doc-parser
        test_payload = {
            "document_id": "test-doc-parser-12345",
            "document_path": "/test/sample.txt", 
            "title": "Test Document for Doc Parser"
        }
        
        result = await self._invoke_edge_function(
            "doc-parser",
            self.edge_functions["doc-parser"],
            test_payload
        )
        
        print(f"    Status: {result.get('status', 'unknown')}")
        if result.get('error'):
            print(f"    Error: {result['error']}")
        if result.get('response_data'):
            print(f"    Response: {str(result['response_data'])[:200]}...")
        
        return result
    
    async def _test_vector_processor_invocation(self) -> Dict[str, Any]:
        """Test direct vector-processor invocation with sample data."""
        print("\n  🧮 Testing vector-processor direct invocation...")
        
        # Create a test payload for vector-processor
        test_payload = {
            "document_id": "test-vector-processor-12345",
            "force_reprocess": True
        }
        
        result = await self._invoke_edge_function(
            "vector-processor",
            self.edge_functions["vector-processor"],
            test_payload
        )
        
        print(f"    Status: {result.get('status', 'unknown')}")
        if result.get('error'):
            print(f"    Error: {result['error']}")
        if result.get('response_data'):
            print(f"    Response: {str(result['response_data'])[:200]}...")
        
        return result
    
    async def _invoke_edge_function(self, func_name: str, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke an edge function with the given payload."""
        try:
            headers = {
                "Authorization": f"Bearer {self.supabase_service_key}",
                "Content-Type": "application/json"
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
                        "response_data": response_text,
                        "payload_sent": payload,
                        "headers": dict(response.headers)
                    }
                    
                    # Try to parse response as JSON
                    try:
                        response_json = json.loads(response_text)
                        result["response_json"] = response_json
                    except json.JSONDecodeError:
                        result["response_type"] = "non_json"
                    
                    return result
                    
        except Exception as e:
            return {
                "status": "exception",
                "error": str(e),
                "error_type": type(e).__name__,
                "payload_sent": payload
            }
    
    def _generate_invocation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of invocation test results."""
        
        edge_tests = results.get("edge_function_tests", {})
        real_doc_test = results.get("real_document_processing", {})
        
        # Count successful invocations
        successful_health_checks = 0
        successful_invocations = 0
        total_tests = 0
        
        for test_name, test_result in edge_tests.items():
            total_tests += 1
            if test_result.get('status') == 'success':
                if 'health' in test_name:
                    successful_health_checks += 1
                else:
                    successful_invocations += 1
        
        # Check real document processing
        real_doc_success = real_doc_test.get('status') == 'completed'
        doc_parser_worked = real_doc_test.get('doc_parser_result', {}).get('status') == 'success'
        vector_processor_worked = real_doc_test.get('vector_processor_result', {}).get('status') == 'success'
        
        summary = {
            "overall_status": "unknown",
            "health_checks_working": successful_health_checks > 0,
            "edge_functions_invokable": successful_invocations > 0,
            "real_document_processing": real_doc_success,
            "doc_parser_functional": doc_parser_worked,
            "vector_processor_functional": vector_processor_worked,
            "critical_issues": [],
            "recommendations": []
        }
        
        # Determine overall status
        if summary["health_checks_working"] and summary["edge_functions_invokable"] and real_doc_success:
            summary["overall_status"] = "excellent"
        elif summary["health_checks_working"] and summary["edge_functions_invokable"]:
            summary["overall_status"] = "good"
        elif summary["health_checks_working"]:
            summary["overall_status"] = "partial"
        else:
            summary["overall_status"] = "failed"
        
        # Identify issues
        if not summary["health_checks_working"]:
            summary["critical_issues"].append("Edge functions not responding to health checks")
            summary["recommendations"].append("Check Supabase edge function deployment and connectivity")
        
        if not summary["edge_functions_invokable"]:
            summary["critical_issues"].append("Edge functions cannot be invoked with POST requests")
            summary["recommendations"].append("Investigate edge function authentication and request handling")
        
        if not summary["doc_parser_functional"]:
            summary["critical_issues"].append("Doc-parser function not working properly")
            summary["recommendations"].append("Check doc-parser implementation and our JSON parsing fixes")
        
        if not summary["vector_processor_functional"]:
            summary["critical_issues"].append("Vector-processor function not working properly") 
            summary["recommendations"].append("Check vector-processor implementation and database connectivity")
        
        if summary["overall_status"] == "excellent":
            summary["recommendations"].append("Edge functions are working - investigate why automatic processing isn't happening")
        elif summary["overall_status"] == "failed":
            summary["recommendations"].append("Edge functions are completely non-functional - check deployment")
        
        return summary

async def main():
    """Main function to run edge function invocation tests."""
    print("🚀 Edge Function Direct Invocation Test")
    print("=" * 50)
    
    try:
        tester = EdgeFunctionInvocationTester()
        results = await tester.test_edge_function_invocation()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"edge_function_invocation_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")
        
        # Display summary
        summary = results.get("summary", {})
        print(f"\n📊 Invocation Test Summary:")
        print(f"   Overall Status: {summary.get('overall_status', 'unknown').upper()}")
        print(f"   Health Checks Working: {summary.get('health_checks_working', False)}")
        print(f"   Edge Functions Invokable: {summary.get('edge_functions_invokable', False)}")
        print(f"   Real Document Processing: {summary.get('real_document_processing', False)}")
        print(f"   Doc-Parser Functional: {summary.get('doc_parser_functional', False)}")
        print(f"   Vector-Processor Functional: {summary.get('vector_processor_functional', False)}")
        
        if summary.get("critical_issues"):
            print(f"\n🚨 Critical Issues:")
            for issue in summary["critical_issues"]:
                print(f"   • {issue}")
        
        if summary.get("recommendations"):
            print(f"\n💡 Recommendations:")
            for rec in summary["recommendations"]:
                print(f"   • {rec}")
        
        return results
        
    except Exception as e:
        print(f"❌ Edge function invocation test failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(main()) 