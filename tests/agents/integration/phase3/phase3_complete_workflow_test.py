#!/usr/bin/env python3
"""
Phase 3 Complete Workflow Test
Test the complete user workflow: create user, sign in, upload document, run RAG queries
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

class Phase3CompleteWorkflowTest:
    """Complete workflow test for Phase 3 RAG system."""
    
    def __init__(self):
        self.base_url = "https://insurance-navigator-api.onrender.com"
        self.test_user_id = str(uuid.uuid4())
        self.test_email = f"workflow_test_{int(time.time())}@example.com"
        self.test_password = "test_password_123"
        self.auth_token = None
        self.uploaded_document_id = None
        self.results = {
            "test_name": "Phase 3 Complete Workflow Test",
            "timestamp": time.time(),
            "test_user_id": self.test_user_id,
            "test_email": self.test_email,
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
    
    async def test_user_registration(self) -> Dict[str, Any]:
        """Test user registration."""
        try:
            async with aiohttp.ClientSession() as session:
                registration_data = {
                    "email": self.test_email,
                    "password": self.test_password,
                    "user_id": self.test_user_id
                }
                
                async with session.post(f"{self.base_url}/register", json=registration_data) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Registration failed: {response.status} - {response_text}")
                    
                    result = await response.json()
                    return {
                        "status_code": response.status,
                        "response": result,
                        "user_id": self.test_user_id,
                        "email": self.test_email
                    }
        
        except Exception as e:
            raise Exception(f"User registration failed: {e}")
    
    async def test_user_login(self) -> Dict[str, Any]:
        """Test user login and get authentication token."""
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    "email": self.test_email,
                    "password": self.test_password
                }
                
                async with session.post(f"{self.base_url}/login", json=login_data) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Login failed: {response.status} - {response_text}")
                    
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
            raise Exception(f"User login failed: {e}")
    
    async def test_document_upload(self) -> Dict[str, Any]:
        """Test document upload via upload endpoint."""
        try:
            # Check if test document exists
            test_doc_path = "examples/test_insurance_document.pdf"
            if not os.path.exists(test_doc_path):
                raise Exception(f"Test document not found at {test_doc_path}")
            
            async with aiohttp.ClientSession() as session:
                # Prepare file upload
                with open(test_doc_path, 'rb') as f:
                    file_data = f.read()
                
                # Create multipart form data
                data = aiohttp.FormData()
                data.add_field('file', file_data, filename='test_insurance_document.pdf', content_type='application/pdf')
                data.add_field('user_id', self.test_user_id)
                
                # Set authorization header
                headers = {
                    'Authorization': f'Bearer {self.auth_token}'
                }
                
                async with session.post(f"{self.base_url}/api/upload-pipeline/upload", data=data, headers=headers) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Upload failed: {response.status} - {response_text}")
                    
                    result = await response.json()
                    self.uploaded_document_id = result.get("document_id")
                    
                    return {
                        "status_code": response.status,
                        "response": result,
                        "document_id": self.uploaded_document_id,
                        "file_size": len(file_data)
                    }
        
        except Exception as e:
            raise Exception(f"Document upload failed: {e}")
    
    async def test_document_processing_wait(self) -> Dict[str, Any]:
        """Wait for document processing to complete."""
        try:
            if not self.uploaded_document_id:
                raise Exception("No document ID available")
            
            max_wait_time = 120  # 2 minutes
            check_interval = 5  # 5 seconds
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.auth_token}'}
                
                while time.time() - start_time < max_wait_time:
                    # Check job status
                    async with session.get(f"{self.base_url}/api/v2/jobs/{self.uploaded_document_id}", headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            status = result.get("status", "unknown")
                            
                            logger.info(f"Document processing status: {status}")
                            
                            if status == "complete":
                                return {
                                    "status": "complete",
                                    "wait_time": time.time() - start_time,
                                    "job_details": result
                                }
                            elif status in ["failed", "error"]:
                                raise Exception(f"Document processing failed: {result}")
                        
                        await asyncio.sleep(check_interval)
                
                raise Exception(f"Document processing timed out after {max_wait_time} seconds")
        
        except Exception as e:
            raise Exception(f"Document processing wait failed: {e}")
    
    async def test_rag_similarity_search(self) -> Dict[str, Any]:
        """Test RAG similarity search with various queries."""
        try:
            if not self.uploaded_document_id:
                raise Exception("No document ID available")
            
            # Test queries
            test_queries = [
                "What is my deductible?",
                "What does my insurance cover?",
                "How much do I pay for doctor visits?",
                "What are my prescription drug benefits?",
                "Is physical therapy covered?"
            ]
            
            results = {}
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/json'
                }
                
                for query in test_queries:
                    chat_data = {
                        "message": query,
                        "user_id": self.test_user_id
                    }
                    
                    async with session.post(f"{self.base_url}/chat", json=chat_data, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get("response", "")
                            
                            results[query] = {
                                "status_code": response.status,
                                "response_length": len(response_text),
                                "response_preview": response_text[:200],
                                "contains_insurance_info": any(keyword in response_text.lower() for keyword in [
                                    "deductible", "insurance", "coverage", "plan", "benefits", "copay", "doctor", "prescription"
                                ])
                            }
                        else:
                            response_text = await response.text()
                            results[query] = {
                                "status_code": response.status,
                                "error": response_text
                            }
            
            return {
                "queries_tested": len(test_queries),
                "successful_queries": len([r for r in results.values() if r.get("status_code") == 200]),
                "query_results": results
            }
        
        except Exception as e:
            raise Exception(f"RAG similarity search failed: {e}")
    
    async def test_direct_rag_system(self) -> Dict[str, Any]:
        """Test RAG system directly with the uploaded document."""
        try:
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            
            # Create RAG tool with test user
            config = RetrievalConfig.default()
            config.similarity_threshold = 0.1  # Lower threshold for testing
            config.max_chunks = 5
            
            rag_tool = RAGTool(user_id=self.test_user_id, config=config)
            
            # Test queries
            test_queries = [
                "What is my deductible?",
                "What does my insurance cover?",
                "How much do I pay for doctor visits?"
            ]
            
            results = {}
            
            for query in test_queries:
                chunks = await rag_tool.retrieve_chunks_from_text(query)
                
                results[query] = {
                    "chunks_retrieved": len(chunks),
                    "chunks": [
                        {
                            "similarity": chunk.similarity,
                            "content_preview": chunk.content[:100] if chunk.content else "No content"
                        }
                        for chunk in chunks[:3]  # First 3 chunks
                    ]
                }
            
            return {
                "queries_tested": len(test_queries),
                "query_results": results
            }
        
        except Exception as e:
            raise Exception(f"Direct RAG system test failed: {e}")
    
    async def run_complete_workflow_test(self) -> Dict[str, Any]:
        """Run the complete workflow test."""
        logger.info("🚀 Starting Phase 3 Complete Workflow Test")
        logger.info("=" * 60)
        
        # Run all tests in sequence
        test_functions = [
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Document Upload", self.test_document_upload),
            ("Document Processing Wait", self.test_document_processing_wait),
            ("RAG Similarity Search", self.test_rag_similarity_search),
            ("Direct RAG System", self.test_direct_rag_system)
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
        logger.info("=" * 60)
        logger.info("📊 PHASE 3 COMPLETE WORKFLOW TEST SUMMARY")
        logger.info("=" * 60)
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
            logger.info("🎉 Phase 3 Complete Workflow Test PASSED!")
        else:
            logger.info("❌ Phase 3 Complete Workflow Test FAILED!")
        
        # Save results
        results_file = f"phase3_complete_workflow_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main function to run the complete workflow test."""
    test = Phase3CompleteWorkflowTest()
    await test.run_complete_workflow_test()

if __name__ == "__main__":
    asyncio.run(main())
