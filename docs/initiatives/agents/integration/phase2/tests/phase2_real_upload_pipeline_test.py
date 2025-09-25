#!/usr/bin/env python3
"""
Phase 2 - Real Upload Pipeline Integration Test
Tests the real upload pipeline integration with production database RAG
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List
import aiohttp
import os
from pathlib import Path

# Test configuration
UPLOAD_PIPELINE_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = "/api/upload-pipeline/upload"
JOBS_ENDPOINT = "/api/v2/jobs"
CHAT_ENDPOINT = "/chat"

class Phase2RealUploadPipelineTest:
    """Test real upload pipeline integration with production database RAG."""
    
    def __init__(self):
        self.test_user_id = str(uuid.uuid4())
        self.test_document_path = "examples/test_insurance_document.pdf"
        self.upload_job_id = None
        self.uploaded_document_id = None
        
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Phase 2 real upload pipeline test."""
        print("🚀 Starting Phase 2 Real Upload Pipeline Integration Test")
        print("=" * 60)
        
        start_time = time.time()
        results = {
            "test_name": "Phase 2 Real Upload Pipeline Integration",
            "timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "tests": {},
            "overall_status": "PENDING",
            "total_time": 0
        }
        
        try:
            # Test 1: Upload Endpoint Functionality
            print("\n1️⃣ Testing Upload Endpoint Functionality...")
            upload_test = await self._test_upload_endpoint()
            results["tests"]["upload_endpoint"] = upload_test
            
            # Test 2: User Authentication
            print("\n2️⃣ Testing User Authentication...")
            auth_test = await self._test_user_authentication()
            results["tests"]["user_authentication"] = auth_test
            
            # Test 3: Document Upload
            print("\n3️⃣ Testing Document Upload...")
            doc_upload_test = await self._test_document_upload()
            results["tests"]["document_upload"] = doc_upload_test
            
            # Test 4: Document Processing
            print("\n4️⃣ Testing Document Processing...")
            processing_test = await self._test_document_processing()
            results["tests"]["document_processing"] = processing_test
            
            # Test 5: RAG Integration
            print("\n5️⃣ Testing RAG Integration...")
            rag_test = await self._test_rag_integration()
            results["tests"]["rag_integration"] = rag_test
            
            # Test 6: End-to-End Workflow
            print("\n6️⃣ Testing End-to-End Workflow...")
            e2e_test = await self._test_end_to_end_workflow()
            results["tests"]["end_to_end_workflow"] = e2e_test
            
            # Calculate overall results
            total_time = time.time() - start_time
            results["total_time"] = total_time
            
            # Determine overall status
            all_tests_passed = all(
                test.get("status") == "PASS" 
                for test in results["tests"].values()
            )
            results["overall_status"] = "PASS" if all_tests_passed else "FAIL"
            
            # Generate summary
            self._generate_summary(results)
            
        except Exception as e:
            results["overall_status"] = "ERROR"
            results["error"] = str(e)
            print(f"❌ Test failed with error: {e}")
            
        return results
    
    async def _test_upload_endpoint(self) -> Dict[str, Any]:
        """Test upload endpoint functionality."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test endpoint availability
                url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
                async with session.get(url) as response:
                    if response.status == 405:  # Method not allowed (expected for GET)
                        return {
                            "status": "PASS",
                            "message": "Upload endpoint is available",
                            "endpoint": url,
                            "response_status": response.status
                        }
                    else:
                        return {
                            "status": "FAIL",
                            "message": f"Unexpected response status: {response.status}",
                            "endpoint": url,
                            "response_status": response.status
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Upload endpoint test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_user_authentication(self) -> Dict[str, Any]:
        """Test user authentication for uploads."""
        try:
            # Create test user
            user_data = {
                "email": f"test_user_{self.test_user_id}@example.com",
                "password": "test_password_123"
            }
            
            async with aiohttp.ClientSession() as session:
                # Try to create user (may fail if user exists, which is OK)
                url = f"{UPLOAD_PIPELINE_URL}/auth/signup"
                async with session.post(url, json=user_data) as response:
                    if response.status in [200, 201, 409]:  # Success or user exists
                        return {
                            "status": "PASS",
                            "message": "User authentication setup successful",
                            "user_id": self.test_user_id,
                            "response_status": response.status
                        }
                    else:
                        return {
                            "status": "FAIL",
                            "message": f"User creation failed: {response.status}",
                            "response_status": response.status
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"User authentication test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_document_upload(self) -> Dict[str, Any]:
        """Test document upload via real pipeline."""
        try:
            if not os.path.exists(self.test_document_path):
                return {
                    "status": "FAIL",
                    "message": f"Test document not found: {self.test_document_path}",
                    "document_path": self.test_document_path
                }
            
            async with aiohttp.ClientSession() as session:
                # Prepare file upload
                with open(self.test_document_path, 'rb') as f:
                    file_data = f.read()
                
                # Create multipart form data
                data = aiohttp.FormData()
                data.add_field('file', file_data, filename='test_insurance_document.pdf', content_type='application/pdf')
                data.add_field('user_id', self.test_user_id)
                
                # Upload document
                url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.upload_job_id = result.get('job_id')
                        self.uploaded_document_id = result.get('document_id')
                        
                        return {
                            "status": "PASS",
                            "message": "Document upload successful",
                            "job_id": self.upload_job_id,
                            "document_id": self.uploaded_document_id,
                            "response_status": response.status
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "FAIL",
                            "message": f"Document upload failed: {response.status}",
                            "response_status": response.status,
                            "error": error_text
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Document upload test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_document_processing(self) -> Dict[str, Any]:
        """Test document processing (LlamaParse + chunking)."""
        try:
            if not self.upload_job_id:
                return {
                    "status": "FAIL",
                    "message": "No upload job ID available for processing test"
                }
            
            # Wait for document processing
            max_wait_time = 300  # 5 minutes
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                while time.time() - start_time < max_wait_time:
                    url = f"{UPLOAD_PIPELINE_URL}{JOBS_ENDPOINT}/{self.upload_job_id}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            job_data = await response.json()
                            status = job_data.get('status', 'unknown')
                            
                            if status == 'completed':
                                return {
                                    "status": "PASS",
                                    "message": "Document processing completed successfully",
                                    "job_status": status,
                                    "processing_time": time.time() - start_time,
                                    "job_data": job_data
                                }
                            elif status == 'failed':
                                return {
                                    "status": "FAIL",
                                    "message": "Document processing failed",
                                    "job_status": status,
                                    "job_data": job_data
                                }
                            else:
                                print(f"   Processing status: {status}, waiting...")
                                await asyncio.sleep(10)
                        else:
                            return {
                                "status": "FAIL",
                                "message": f"Failed to check job status: {response.status}",
                                "response_status": response.status
                            }
                
                return {
                    "status": "FAIL",
                    "message": f"Document processing timed out after {max_wait_time} seconds"
                }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Document processing test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_rag_integration(self) -> Dict[str, Any]:
        """Test RAG integration with uploaded documents."""
        try:
            # Test queries that should retrieve from uploaded document
            test_queries = [
                "What is my deductible?",
                "What are my copays for doctor visits?",
                "What services are covered under my plan?",
                "How do I find a doctor in my network?",
                "What are my prescription drug benefits?"
            ]
            
            results = []
            async with aiohttp.ClientSession() as session:
                for query in test_queries:
                    chat_data = {
                        "message": query,
                        "conversation_id": f"test_conv_{int(time.time())}",
                        "user_id": self.test_user_id
                    }
                    
                    url = f"{UPLOAD_PIPELINE_URL}{CHAT_ENDPOINT}"
                    async with session.post(url, json=chat_data) as response:
                        if response.status == 200:
                            chat_response = await response.json()
                            results.append({
                                "query": query,
                                "status": "PASS",
                                "response_length": len(chat_response.get('response', '')),
                                "has_insurance_content": self._check_insurance_content(chat_response.get('response', '')),
                                "response": chat_response.get('response', '')[:200] + "..." if len(chat_response.get('response', '')) > 200 else chat_response.get('response', '')
                            })
                        else:
                            results.append({
                                "query": query,
                                "status": "FAIL",
                                "response_status": response.status,
                                "error": await response.text()
                            })
            
            # Calculate success rate
            successful_queries = [r for r in results if r.get("status") == "PASS"]
            success_rate = len(successful_queries) / len(test_queries)
            
            return {
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "message": f"RAG integration test completed with {success_rate:.1%} success rate",
                "success_rate": success_rate,
                "total_queries": len(test_queries),
                "successful_queries": len(successful_queries),
                "query_results": results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"RAG integration test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow."""
        try:
            # Test complete workflow: upload → process → query
            workflow_start = time.time()
            
            # Step 1: Upload document (if not already done)
            if not self.uploaded_document_id:
                upload_result = await self._test_document_upload()
                if upload_result["status"] != "PASS":
                    return {
                        "status": "FAIL",
                        "message": "End-to-end workflow failed at upload step",
                        "upload_result": upload_result
                    }
            
            # Step 2: Wait for processing (if not already done)
            if not self.upload_job_id:
                return {
                    "status": "FAIL",
                    "message": "No upload job ID for end-to-end test"
                }
            
            # Step 3: Test RAG query
            rag_result = await self._test_rag_integration()
            
            total_time = time.time() - workflow_start
            
            return {
                "status": "PASS" if rag_result["status"] == "PASS" else "FAIL",
                "message": "End-to-end workflow completed",
                "total_workflow_time": total_time,
                "rag_result": rag_result
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"End-to-end workflow test failed: {str(e)}",
                "error": str(e)
            }
    
    def _check_insurance_content(self, response: str) -> bool:
        """Check if response contains insurance-related content."""
        insurance_keywords = [
            "deductible", "copay", "coverage", "benefits", "premium",
            "network", "prescription", "doctor", "visit", "plan"
        ]
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in insurance_keywords)
    
    def _generate_summary(self, results: Dict[str, Any]):
        """Generate test summary."""
        print("\n" + "=" * 60)
        print("📊 PHASE 2 REAL UPLOAD PIPELINE TEST SUMMARY")
        print("=" * 60)
        
        print(f"Overall Status: {results['overall_status']}")
        print(f"Total Time: {results['total_time']:.2f} seconds")
        print(f"Test User ID: {results['test_user_id']}")
        
        print("\nTest Results:")
        for test_name, test_result in results["tests"].items():
            status_icon = "✅" if test_result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {test_name}: {test_result['status']}")
            if "message" in test_result:
                print(f"      {test_result['message']}")
        
        if results["overall_status"] == "PASS":
            print("\n🎉 Phase 2 Real Upload Pipeline Integration Test PASSED!")
        else:
            print("\n❌ Phase 2 Real Upload Pipeline Integration Test FAILED!")

async def main():
    """Run Phase 2 real upload pipeline test."""
    tester = Phase2RealUploadPipelineTest()
    results = await tester.run_comprehensive_test()
    
    # Save results
    results_file = f"phase2_real_upload_pipeline_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
