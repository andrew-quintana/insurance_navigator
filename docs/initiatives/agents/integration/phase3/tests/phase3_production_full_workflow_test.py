#!/usr/bin/env python3
"""
Phase 3 Production Full Workflow Test
Complete production testing: create user, sign in, upload real document via production API,
wait for production worker processing, and test RAG with real insurance queries
"""

import asyncio
import aiohttp
import json
import time
import uuid
from typing import Dict, Any, List, Optional
import logging
import os
import sys
from dotenv import load_dotenv

# Add project root to path
sys.path.append('/Users/aq_home/1Projects/accessa/insurance_navigator')

# Load environment variables
load_dotenv('.env.development')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3ProductionFullWorkflowTest:
    """Complete production workflow test for Phase 3 RAG system."""
    
    def __init__(self):
        # Use production API service
        self.api_base_url = "https://insurance-navigator-api.onrender.com"
        self.test_user_id = str(uuid.uuid4())
        self.test_email = f"full_workflow_test_{int(time.time())}@example.com"
        self.test_password = "full_workflow_test_123"
        self.auth_token = None
        self.uploaded_document_id = None
        self.results = {
            "test_name": "Phase 3 Production Full Workflow Test",
            "timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "test_email": self.test_email,
            "api_base_url": self.api_base_url,
            "tests": {},
            "summary": {}
        }
    
    async def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func()
            duration = time.time() - start_time
            
            self.results["tests"][test_name] = {
                "status": "PASSED",
                "duration": duration,
                "details": result
            }
            logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.results["tests"][test_name] = {
                "status": "FAILED",
                "duration": duration,
                "error": str(e)
            }
            logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s): {str(e)}")
            return False
    
    async def test_production_api_health(self) -> Dict[str, Any]:
        """Test production API health and availability."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test API health
                async with session.get(f"{self.api_base_url}/health") as response:
                    if response.status != 200:
                        raise Exception(f"API health check failed: {response.status}")
                    
                    health_data = await response.json()
                    
                    # Test upload endpoint availability
                    async with session.get(f"{self.api_base_url}/api/v2/upload") as upload_response:
                        upload_status = upload_response.status
                    
                    # Test jobs endpoint availability
                    async with session.get(f"{self.api_base_url}/api/v2/jobs") as jobs_response:
                        jobs_status = jobs_response.status
                    
                    return {
                        "api_health": health_data,
                        "upload_endpoint_status": upload_status,
                        "jobs_endpoint_status": jobs_status,
                        "api_base_url": self.api_base_url
                    }
        
        except Exception as e:
            raise Exception(f"Production API health check failed: {e}")
    
    async def test_create_new_user(self) -> Dict[str, Any]:
        """Create a new user via production API."""
        try:
            async with aiohttp.ClientSession() as session:
                registration_data = {
                    "email": self.test_email,
                    "password": self.test_password,
                    "user_id": self.test_user_id
                }
                
                async with session.post(f"{self.api_base_url}/register", json=registration_data) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"User creation failed: {response.status} - {response_text}")
                    
                    result = await response.json()
                    return {
                        "status_code": response.status,
                        "response": result,
                        "user_id": self.test_user_id,
                        "email": self.test_email
                    }
        
        except Exception as e:
            raise Exception(f"User creation failed: {e}")
    
    async def test_sign_in_user(self) -> Dict[str, Any]:
        """Sign in the user via production API."""
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    "email": self.test_email,
                    "password": self.test_password
                }
                
                async with session.post(f"{self.api_base_url}/login", json=login_data) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"User sign in failed: {response.status} - {response_text}")
                    
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    
                    if not self.auth_token:
                        raise Exception("No authentication token received")
                    
                    return {
                        "status_code": response.status,
                        "response": result,
                        "auth_token_received": True
                    }
        
        except Exception as e:
            raise Exception(f"User sign in failed: {e}")
    
    async def test_upload_insurance_document(self) -> Dict[str, Any]:
        """Upload the test insurance document via production upload endpoint."""
        try:
            # Use the real insurance document
            test_doc_path = "examples/test_insurance_document.pdf"
            if not os.path.exists(test_doc_path):
                raise Exception(f"Test insurance document not found at {test_doc_path}")
            
            async with aiohttp.ClientSession() as session:
                # Prepare file upload
                with open(test_doc_path, 'rb') as f:
                    file_data = f.read()
                
                # Create multipart form data for legacy endpoint
                data = aiohttp.FormData()
                data.add_field('file', file_data, filename='test_insurance_document.pdf', content_type='application/pdf')
                data.add_field('policy_id', 'test_insurance_document')
                
                # Set authorization header
                headers = {
                    'Authorization': f'Bearer {self.auth_token}'
                }
                
                async with session.post(f"{self.api_base_url}/upload-document-backend", data=data, headers=headers) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Document upload failed: {response.status} - {response_text}")
                    
                    result = await response.json()
                    self.uploaded_document_id = result.get("document_id")
                    
                    return {
                        "status_code": response.status,
                        "response": result,
                        "document_id": self.uploaded_document_id,
                        "file_size": len(file_data),
                        "file_name": "test_insurance_document.pdf"
                    }
        
        except Exception as e:
            raise Exception(f"Document upload failed: {e}")
    
    async def test_wait_for_document_processing(self) -> Dict[str, Any]:
        """Wait for production worker to process the uploaded document."""
        try:
            if not self.uploaded_document_id:
                raise Exception("No document ID available")
            
            max_wait_time = 300  # 5 minutes for production processing
            check_interval = 10  # 10 seconds
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                
                while time.time() - start_time < max_wait_time:
                    # Check job status
                    async with session.get(f"{self.api_base_url}/api/v2/jobs/{self.uploaded_document_id}", headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            status = result.get("status", "unknown")
                            
                            logger.info(f"Document processing status: {status}")
                            
                            if status == "complete":
                                return {
                                    "status": "complete",
                                    "wait_time": time.time() - start_time,
                                    "job_details": result,
                                    "processing_time": time.time() - start_time
                                }
                            elif status in ["failed", "error"]:
                                raise Exception(f"Document processing failed: {result}")
                        
                        await asyncio.sleep(check_interval)
                
                raise Exception(f"Document processing timed out after {max_wait_time} seconds")
        
        except Exception as e:
            raise Exception(f"Document processing wait failed: {e}")
    
    async def test_rag_similarity_search_queries(self) -> Dict[str, Any]:
        """Test RAG similarity search with real insurance queries."""
        try:
            if not self.uploaded_document_id:
                raise Exception("No document ID available")
            
            # Real insurance queries that should work with the test document
            insurance_queries = [
                "What's my deductible?",
                "What is my deductible?",
                "How much is my deductible?",
                "What does my insurance cover?",
                "What are my insurance benefits?",
                "How much do I pay for doctor visits?",
                "What is my copay?",
                "What are my prescription benefits?",
                "Is physical therapy covered?",
                "What is my out-of-pocket maximum?",
                "What is my coinsurance?",
                "Are preventive services covered?",
                "What is my premium?",
                "What is my annual limit?",
                "What is my lifetime maximum?"
            ]
            
            results = {}
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/json'
                }
                
                for query in insurance_queries:
                    chat_data = {
                        "message": query,
                        "user_id": self.test_user_id
                    }
                    
                    async with session.post(f"{self.api_base_url}/chat", json=chat_data, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get("response", "")
                            
                            # Check if response contains real insurance information
                            contains_insurance_info = any(keyword in response_text.lower() for keyword in [
                                "deductible", "insurance", "coverage", "plan", "benefits", "copay", 
                                "doctor", "prescription", "therapy", "emergency", "mental health",
                                "out-of-pocket", "preventive", "coinsurance", "premium", "annual", "lifetime"
                            ])
                            
                            # Check if response is not an error message
                            is_error_response = any(phrase in response_text.lower() for phrase in [
                                "error", "apologize", "try again", "moment", "encountered", "processing"
                            ])
                            
                            results[query] = {
                                "status_code": response.status,
                                "response_length": len(response_text),
                                "response_preview": response_text[:300],
                                "response_full": response_text,
                                "contains_insurance_info": contains_insurance_info,
                                "is_error_response": is_error_response
                            }
                        else:
                            response_text = await response.text()
                            results[query] = {
                                "status_code": response.status,
                                "error": response_text
                            }
            
            return {
                "queries_tested": len(insurance_queries),
                "successful_queries": len([r for r in results.values() if r.get("status_code") == 200]),
                "queries_with_insurance_info": len([r for r in results.values() if r.get("contains_insurance_info", False)]),
                "error_responses": len([r for r in results.values() if r.get("is_error_response", False)]),
                "query_results": results
            }
        
        except Exception as e:
            raise Exception(f"RAG similarity search queries failed: {e}")
    
    async def test_direct_rag_system_with_real_user(self) -> Dict[str, Any]:
        """Test RAG system directly with the real user who uploaded the document."""
        try:
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            
            # Create RAG tool with the real user who uploaded the document
            config = RetrievalConfig.default()
            config.similarity_threshold = 0.1  # Lower threshold for testing
            config.max_chunks = 10
            
            rag_tool = RAGTool(user_id=self.test_user_id, config=config)
            
            # Test queries
            test_queries = [
                "What's my deductible?",
                "What does my insurance cover?",
                "How much do I pay for doctor visits?",
                "What are my prescription benefits?",
                "Is physical therapy covered?"
            ]
            
            results = {}
            
            for query in test_queries:
                chunks = await rag_tool.retrieve_chunks_from_text(query)
                
                results[query] = {
                    "chunks_retrieved": len(chunks),
                    "chunks": [
                        {
                            "similarity": chunk.similarity,
                            "content_preview": chunk.content[:200] if chunk.content else "No content",
                            "content_full": chunk.content  # Full content for analysis
                        }
                        for chunk in chunks[:5]  # First 5 chunks
                    ]
                }
            
            return {
                "queries_tested": len(test_queries),
                "queries_with_chunks": len([r for r in results.values() if r.get("chunks_retrieved", 0) > 0]),
                "query_results": results
            }
        
        except Exception as e:
            raise Exception(f"Direct RAG system test failed: {e}")
    
    async def run_production_full_workflow_test(self) -> Dict[str, Any]:
        """Run the complete production full workflow test."""
        logger.info("🚀 Starting Phase 3 Production Full Workflow Test")
        logger.info("=" * 80)
        logger.info(f"🌐 Using Production API: {self.api_base_url}")
        logger.info(f"👤 Test User: {self.test_email}")
        logger.info(f"🆔 User ID: {self.test_user_id}")
        logger.info(f"📄 Test Document: examples/test_insurance_document.pdf")
        logger.info("=" * 80)
        
        # Run all tests in sequence
        test_functions = [
            ("Production API Health", self.test_production_api_health),
            ("Create New User", self.test_create_new_user),
            ("Sign In User", self.test_sign_in_user),
            ("Upload Insurance Document", self.test_upload_insurance_document),
            ("Wait for Document Processing", self.test_wait_for_document_processing),
            ("RAG Similarity Search Queries", self.test_rag_similarity_search_queries),
            ("Direct RAG System with Real User", self.test_direct_rag_system_with_real_user)
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            success = await self.run_test(test_name, test_func)
            if success:
                passed_tests += 1
        
        # Generate summary
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "overall_status": "PASSED" if passed_tests == total_tests else "FAILED"
        }
        
        # Log summary
        logger.info("=" * 80)
        logger.info("📊 PHASE 3 PRODUCTION FULL WORKFLOW TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Overall Status: {self.results['summary']['overall_status']}")
        logger.info(f"Total Time: {time.time() - self.results['timestamp']:.2f} seconds")
        logger.info(f"Test User ID: {self.test_user_id}")
        logger.info(f"Uploaded Document ID: {self.uploaded_document_id}")
        logger.info("")
        logger.info("Test Results:")
        
        for test_name, test_result in self.results["tests"].items():
            status_icon = "✅" if test_result["status"] == "PASSED" else "❌"
            logger.info(f"  {status_icon} {test_name}: {test_result['status']}")
            if test_result["status"] == "FAILED" and "error" in test_result:
                logger.info(f"      Error: {test_result['error']}")
        
        logger.info("")
        logger.info(f"📊 Summary: {passed_tests}/{total_tests} tests passed ({self.results['summary']['success_rate']:.1f}%)")
        
        if self.results['summary']['overall_status'] == "PASSED":
            logger.info("🎉 Phase 3 Production Full Workflow Test PASSED!")
        else:
            logger.info("❌ Phase 3 Production Full Workflow Test FAILED!")
        
        # Save results
        results_file = f"phase3_production_full_workflow_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main function to run the production full workflow test."""
    test = Phase3ProductionFullWorkflowTest()
    await test.run_production_full_workflow_test()

if __name__ == "__main__":
    asyncio.run(main())
