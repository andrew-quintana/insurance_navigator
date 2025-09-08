#!/usr/bin/env python3
"""
Phase 2 - User Creation and Upload Workflow Test
Tests complete user creation → upload → query workflow
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
UPLOAD_ENDPOINT = "/api/v2/upload"
JOBS_ENDPOINT = "/api/v2/jobs"
CHAT_ENDPOINT = "/chat"
AUTH_ENDPOINT = "/auth/v1/signup"
TOKEN_ENDPOINT = "/auth/v1/token"

class Phase2UserCreationUploadTest:
    """Test complete user creation → upload → query workflow."""
    
    def __init__(self):
        self.test_user_id = str(uuid.uuid4())
        self.test_email = f"phase2_test_{self.test_user_id}@example.com"
        self.test_password = "Phase2Test123!"
        self.jwt_token = None
        self.upload_job_id = None
        self.uploaded_document_id = None
        self.test_document_path = "examples/test_insurance_document.pdf"
        
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Phase 2 user creation and upload test."""
        print("🚀 Starting Phase 2 User Creation and Upload Workflow Test")
        print("=" * 70)
        
        start_time = time.time()
        results = {
            "test_name": "Phase 2 User Creation and Upload Workflow",
            "timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "test_email": self.test_email,
            "tests": {},
            "overall_status": "PENDING",
            "total_time": 0
        }
        
        try:
            # Test 1: User Creation
            print("\n1️⃣ Testing User Creation...")
            user_creation_test = await self._test_user_creation()
            results["tests"]["user_creation"] = user_creation_test
            
            # Test 2: User Authentication
            print("\n2️⃣ Testing User Authentication...")
            auth_test = await self._test_user_authentication()
            results["tests"]["user_authentication"] = auth_test
            
            # Test 3: Document Upload with Authentication
            print("\n3️⃣ Testing Document Upload with Authentication...")
            upload_test = await self._test_authenticated_upload()
            results["tests"]["authenticated_upload"] = upload_test
            
            # Test 4: Document Processing
            print("\n4️⃣ Testing Document Processing...")
            processing_test = await self._test_document_processing()
            results["tests"]["document_processing"] = processing_test
            
            # Test 5: RAG Query with User Context
            print("\n5️⃣ Testing RAG Query with User Context...")
            rag_test = await self._test_user_context_rag()
            results["tests"]["user_context_rag"] = rag_test
            
            # Test 6: Complete Workflow
            print("\n6️⃣ Testing Complete Workflow...")
            workflow_test = await self._test_complete_workflow()
            results["tests"]["complete_workflow"] = workflow_test
            
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
    
    async def _test_user_creation(self) -> Dict[str, Any]:
        """Test user creation with proper UUID generation."""
        try:
            user_data = {
                "email": self.test_email,
                "password": self.test_password,
                "user_metadata": {
                    "test_user": True,
                    "phase": "phase2",
                    "created_at": time.time()
                }
            }
            
            async with aiohttp.ClientSession() as session:
                # Try to create user
                url = f"{UPLOAD_PIPELINE_URL}{AUTH_ENDPOINT}"
                async with session.post(url, json=user_data) as response:
                    response_data = await response.json()
                    
                    if response.status in [200, 201]:
                        return {
                            "status": "PASS",
                            "message": "User created successfully",
                            "user_id": response_data.get('user', {}).get('id'),
                            "email": self.test_email,
                            "response_status": response.status
                        }
                    elif response.status == 409:
                        # User already exists, which is OK for testing
                        return {
                            "status": "PASS",
                            "message": "User already exists (acceptable for testing)",
                            "user_id": self.test_user_id,
                            "email": self.test_email,
                            "response_status": response.status
                        }
                    else:
                        return {
                            "status": "FAIL",
                            "message": f"User creation failed: {response.status}",
                            "response_status": response.status,
                            "error": response_data
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"User creation test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_user_authentication(self) -> Dict[str, Any]:
        """Test user authentication and JWT token generation."""
        try:
            auth_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            async with aiohttp.ClientSession() as session:
                # Authenticate user
                url = f"{UPLOAD_PIPELINE_URL}{TOKEN_ENDPOINT}?grant_type=password"
                async with session.post(url, json=auth_data) as response:
                    if response.status == 200:
                        auth_response = await response.json()
                        self.jwt_token = auth_response.get('access_token')
                        
                        return {
                            "status": "PASS",
                            "message": "User authentication successful",
                            "has_jwt_token": bool(self.jwt_token),
                            "token_length": len(self.jwt_token) if self.jwt_token else 0,
                            "response_status": response.status
                        }
                    else:
                        error_data = await response.json()
                        return {
                            "status": "FAIL",
                            "message": f"User authentication failed: {response.status}",
                            "response_status": response.status,
                            "error": error_data
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"User authentication test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_authenticated_upload(self) -> Dict[str, Any]:
        """Test document upload with JWT authentication."""
        try:
            if not self.jwt_token:
                return {
                    "status": "FAIL",
                    "message": "No JWT token available for authenticated upload"
                }
            
            if not os.path.exists(self.test_document_path):
                return {
                    "status": "FAIL",
                    "message": f"Test document not found: {self.test_document_path}",
                    "document_path": self.test_document_path
                }
            
            async with aiohttp.ClientSession() as session:
                # Prepare file upload with authentication
                with open(self.test_document_path, 'rb') as f:
                    file_data = f.read()
                
                # Create multipart form data
                data = aiohttp.FormData()
                data.add_field('file', file_data, filename='test_insurance_document.pdf', content_type='application/pdf')
                data.add_field('user_id', self.test_user_id)
                
                # Set authorization header
                headers = {
                    'Authorization': f'Bearer {self.jwt_token}'
                }
                
                # Upload document
                url = f"{UPLOAD_PIPELINE_URL}{UPLOAD_ENDPOINT}"
                async with session.post(url, data=data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.upload_job_id = result.get('job_id')
                        self.uploaded_document_id = result.get('document_id')
                        
                        return {
                            "status": "PASS",
                            "message": "Authenticated document upload successful",
                            "job_id": self.upload_job_id,
                            "document_id": self.uploaded_document_id,
                            "response_status": response.status
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "FAIL",
                            "message": f"Authenticated upload failed: {response.status}",
                            "response_status": response.status,
                            "error": error_text
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Authenticated upload test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_document_processing(self) -> Dict[str, Any]:
        """Test document processing with LlamaParse and chunking."""
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
                                # Check for processing details
                                processing_details = job_data.get('processing_details', {})
                                chunks_created = processing_details.get('chunks_created', 0)
                                vectorization_status = processing_details.get('vectorization_status', 'unknown')
                                
                                return {
                                    "status": "PASS",
                                    "message": "Document processing completed successfully",
                                    "job_status": status,
                                    "processing_time": time.time() - start_time,
                                    "chunks_created": chunks_created,
                                    "vectorization_status": vectorization_status,
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
    
    async def _test_user_context_rag(self) -> Dict[str, Any]:
        """Test RAG queries with user context and uploaded documents."""
        try:
            # Test queries that should retrieve from user's uploaded documents
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
                        "conversation_id": f"phase2_conv_{int(time.time())}",
                        "user_id": self.test_user_id,
                        "context": {
                            "user_authenticated": True,
                            "has_uploaded_documents": True,
                            "document_id": self.uploaded_document_id
                        }
                    }
                    
                    # Set authorization header
                    headers = {}
                    if self.jwt_token:
                        headers['Authorization'] = f'Bearer {self.jwt_token}'
                    
                    url = f"{UPLOAD_PIPELINE_URL}{CHAT_ENDPOINT}"
                    async with session.post(url, json=chat_data, headers=headers) as response:
                        if response.status == 200:
                            chat_response = await response.json()
                            response_text = chat_response.get('response', '')
                            
                            results.append({
                                "query": query,
                                "status": "PASS",
                                "response_length": len(response_text),
                                "has_insurance_content": self._check_insurance_content(response_text),
                                "has_user_context": self._check_user_context(response_text),
                                "response": response_text[:200] + "..." if len(response_text) > 200 else response_text
                            })
                        else:
                            error_text = await response.text()
                            results.append({
                                "query": query,
                                "status": "FAIL",
                                "response_status": response.status,
                                "error": error_text
                            })
            
            # Calculate success rate
            successful_queries = [r for r in results if r.get("status") == "PASS"]
            success_rate = len(successful_queries) / len(test_queries)
            
            # Check for user context in responses
            context_aware_responses = [r for r in successful_queries if r.get("has_user_context", False)]
            context_awareness_rate = len(context_aware_responses) / len(successful_queries) if successful_queries else 0
            
            return {
                "status": "PASS" if success_rate >= 0.8 else "FAIL",
                "message": f"User context RAG test completed with {success_rate:.1%} success rate",
                "success_rate": success_rate,
                "context_awareness_rate": context_awareness_rate,
                "total_queries": len(test_queries),
                "successful_queries": len(successful_queries),
                "context_aware_responses": len(context_aware_responses),
                "query_results": results
            }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"User context RAG test failed: {str(e)}",
                "error": str(e)
            }
    
    async def _test_complete_workflow(self) -> Dict[str, Any]:
        """Test complete user creation → upload → query workflow."""
        try:
            workflow_start = time.time()
            
            # Verify all previous steps completed successfully
            required_components = [
                self.test_user_id,
                self.jwt_token,
                self.uploaded_document_id,
                self.upload_job_id
            ]
            
            missing_components = [comp for comp in required_components if not comp]
            if missing_components:
                return {
                    "status": "FAIL",
                    "message": f"Missing required components: {missing_components}",
                    "missing_components": missing_components
                }
            
            # Test final RAG query
            final_query = "Can you summarize my insurance benefits?"
            chat_data = {
                "message": final_query,
                "conversation_id": f"phase2_final_{int(time.time())}",
                "user_id": self.test_user_id,
                "context": {
                    "user_authenticated": True,
                    "has_uploaded_documents": True,
                    "document_id": self.uploaded_document_id,
                    "workflow_test": True
                }
            }
            
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.jwt_token}'}
                url = f"{UPLOAD_PIPELINE_URL}{CHAT_ENDPOINT}"
                async with session.post(url, json=chat_data, headers=headers) as response:
                    if response.status == 200:
                        chat_response = await response.json()
                        response_text = chat_response.get('response', '')
                        
                        total_time = time.time() - workflow_start
                        
                        return {
                            "status": "PASS",
                            "message": "Complete workflow test successful",
                            "total_workflow_time": total_time,
                            "final_query": final_query,
                            "response_length": len(response_text),
                            "has_insurance_content": self._check_insurance_content(response_text),
                            "response": response_text[:300] + "..." if len(response_text) > 300 else response_text
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "status": "FAIL",
                            "message": f"Final RAG query failed: {response.status}",
                            "response_status": response.status,
                            "error": error_text
                        }
        except Exception as e:
            return {
                "status": "FAIL",
                "message": f"Complete workflow test failed: {str(e)}",
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
    
    def _check_user_context(self, response: str) -> bool:
        """Check if response shows user context awareness."""
        context_indicators = [
            "your", "you", "your plan", "your benefits", "your coverage",
            "based on your", "according to your", "in your case"
        ]
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in context_indicators)
    
    def _generate_summary(self, results: Dict[str, Any]):
        """Generate test summary."""
        print("\n" + "=" * 70)
        print("📊 PHASE 2 USER CREATION AND UPLOAD WORKFLOW TEST SUMMARY")
        print("=" * 70)
        
        print(f"Overall Status: {results['overall_status']}")
        print(f"Total Time: {results['total_time']:.2f} seconds")
        print(f"Test User ID: {results['test_user_id']}")
        print(f"Test Email: {results['test_email']}")
        
        print("\nTest Results:")
        for test_name, test_result in results["tests"].items():
            status_icon = "✅" if test_result["status"] == "PASS" else "❌"
            print(f"  {status_icon} {test_name}: {test_result['status']}")
            if "message" in test_result:
                print(f"      {test_result['message']}")
        
        # Show workflow-specific metrics
        if "user_context_rag" in results["tests"]:
            rag_result = results["tests"]["user_context_rag"]
            if "success_rate" in rag_result:
                print(f"\nRAG Success Rate: {rag_result['success_rate']:.1%}")
            if "context_awareness_rate" in rag_result:
                print(f"Context Awareness Rate: {rag_result['context_awareness_rate']:.1%}")
        
        if results["overall_status"] == "PASS":
            print("\n🎉 Phase 2 User Creation and Upload Workflow Test PASSED!")
        else:
            print("\n❌ Phase 2 User Creation and Upload Workflow Test FAILED!")

async def main():
    """Run Phase 2 user creation and upload test."""
    tester = Phase2UserCreationUploadTest()
    results = await tester.run_comprehensive_test()
    
    # Save results
    results_file = f"phase2_user_creation_upload_results_{int(time.time())}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    return results

if __name__ == "__main__":
    asyncio.run(main())
