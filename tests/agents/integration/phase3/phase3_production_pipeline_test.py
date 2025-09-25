#!/usr/bin/env python3
"""
Phase 3 Production Pipeline Test
Test the complete production workflow: create user, sign in, upload real document via production API,
wait for production worker processing, and test RAG with real production data
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

class Phase3ProductionPipelineTest:
    """Production pipeline test for Phase 3 RAG system."""
    
    def __init__(self):
        # Use production API service
        self.api_base_url = "https://insurance-navigator-api.onrender.com"
        self.test_user_id = str(uuid.uuid4())
        self.test_email = f"production_test_{int(time.time())}@example.com"
        self.test_password = "production_test_123"
        self.auth_token = None
        self.uploaded_document_id = None
        self.results = {
            "test_name": "Phase 3 Production Pipeline Test",
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
                    async with session.get(f"{self.api_base_url}/api/upload-pipeline/upload") as upload_response:
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
    
    async def test_user_registration(self) -> Dict[str, Any]:
        """Test user registration via production API."""
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
        """Test user login via production API."""
        try:
            async with aiohttp.ClientSession() as session:
                login_data = {
                    "email": self.test_email,
                    "password": self.test_password
                }
                
                async with session.post(f"{self.api_base_url}/login", json=login_data) as response:
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
    
    async def test_production_document_upload(self) -> Dict[str, Any]:
        """Test document upload via production API with real insurance document."""
        try:
            # Use the real insurance document
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
                
                async with session.post(f"{self.api_base_url}/api/upload-pipeline/upload", data=data, headers=headers) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Upload failed: {response.status} - {response_text}")
                    
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
            raise Exception(f"Production document upload failed: {e}")
    
    async def test_production_worker_processing(self) -> Dict[str, Any]:
        """Wait for production worker to process the document."""
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
                            
                            logger.info(f"Production worker status: {status}")
                            
                            if status == "complete":
                                return {
                                    "status": "complete",
                                    "wait_time": time.time() - start_time,
                                    "job_details": result,
                                    "processing_time": time.time() - start_time
                                }
                            elif status in ["failed", "error"]:
                                raise Exception(f"Production worker processing failed: {result}")
                        
                        await asyncio.sleep(check_interval)
                
                raise Exception(f"Production worker processing timed out after {max_wait_time} seconds")
        
        except Exception as e:
            raise Exception(f"Production worker processing wait failed: {e}")
    
    async def test_production_rag_queries(self) -> Dict[str, Any]:
        """Test RAG queries via production chat endpoint."""
        try:
            if not self.uploaded_document_id:
                raise Exception("No document ID available")
            
            # Test queries that should work with real insurance documents
            test_queries = [
                "What is my deductible?",
                "What does my insurance plan cover?",
                "How much do I pay for doctor visits?",
                "What are my prescription drug benefits?",
                "Is physical therapy covered?",
                "What is my copay for emergency room visits?",
                "Does my plan cover mental health services?",
                "What is my out-of-pocket maximum?",
                "Are preventive services covered?",
                "What is my coinsurance rate?"
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
                    
                    async with session.post(f"{self.api_base_url}/chat", json=chat_data, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get("response", "")
                            
                            # Check if response contains real insurance information
                            contains_insurance_info = any(keyword in response_text.lower() for keyword in [
                                "deductible", "insurance", "coverage", "plan", "benefits", "copay", 
                                "doctor", "prescription", "therapy", "emergency", "mental health",
                                "out-of-pocket", "preventive", "coinsurance", "premium"
                            ])
                            
                            results[query] = {
                                "status_code": response.status,
                                "response_length": len(response_text),
                                "response_preview": response_text[:300],
                                "contains_insurance_info": contains_insurance_info,
                                "response_full": response_text  # Full response for analysis
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
                "queries_with_insurance_info": len([r for r in results.values() if r.get("contains_insurance_info", False)]),
                "query_results": results
            }
        
        except Exception as e:
            raise Exception(f"Production RAG queries failed: {e}")
    
    async def test_production_direct_rag_system(self) -> Dict[str, Any]:
        """Test RAG system directly with production data."""
        try:
            from agents.tooling.rag.core import RAGTool, RetrievalConfig
            
            # Create RAG tool with test user
            config = RetrievalConfig.default()
            config.similarity_threshold = 0.1  # Lower threshold for testing
            config.max_chunks = 10
            
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
                            "content_preview": chunk.content[:200] if chunk.content else "No content",
                            "content_full": chunk.content  # Full content for analysis
                        }
                        for chunk in chunks[:5]  # First 5 chunks
                    ]
                }
            
            return {
                "queries_tested": len(test_queries),
                "query_results": results
            }
        
        except Exception as e:
            raise Exception(f"Production direct RAG system test failed: {e}")
    
    async def run_production_pipeline_test(self) -> Dict[str, Any]:
        """Run the complete production pipeline test."""
        logger.info("🚀 Starting Phase 3 Production Pipeline Test")
        logger.info("=" * 70)
        logger.info(f"🌐 Using Production API: {self.api_base_url}")
        logger.info(f"👤 Test User: {self.test_email}")
        logger.info("=" * 70)
        
        # Run all tests in sequence
        test_functions = [
            ("Production API Health", self.test_production_api_health),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Production Document Upload", self.test_production_document_upload),
            ("Production Worker Processing", self.test_production_worker_processing),
            ("Production RAG Queries", self.test_production_rag_queries),
            ("Production Direct RAG System", self.test_production_direct_rag_system)
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
        logger.info("=" * 70)
        logger.info("📊 PHASE 3 PRODUCTION PIPELINE TEST SUMMARY")
        logger.info("=" * 70)
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
            logger.info("🎉 Phase 3 Production Pipeline Test PASSED!")
        else:
            logger.info("❌ Phase 3 Production Pipeline Test FAILED!")
        
        # Save results
        results_file = f"phase3_production_pipeline_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main function to run the production pipeline test."""
    test = Phase3ProductionPipelineTest()
    await test.run_production_pipeline_test()

if __name__ == "__main__":
    asyncio.run(main())
