#!/usr/bin/env python3
"""
Phase 3 Production Real User Test
Test RAG system with existing users who have real documents in production database
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

class Phase3ProductionRealUserTest:
    """Test RAG system with real users from production database."""
    
    def __init__(self):
        self.api_base_url = "https://insurance-navigator-api.onrender.com"
        self.results = {
            "test_name": "Phase 3 Production Real User Test",
            "timestamp": time.time(),
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
    
    async def test_production_database_users(self) -> Dict[str, Any]:
        """Test with known users from production database."""
        try:
            # Known users from our local database that should exist in production
            known_users = [
                '752ae479-0fc4-41d3-b2fa-8f8ac467685f',  # User with 29 documents
                '756f1572-dd6b-45fe-aded-a57a0a9ccd62',  # User with 1 document
                'f16aa61c-e47a-4670-bb5a-f066a8bc6b9c',  # User with 1 document
                'e54ff1a9-daf6-49d2-a6f5-21408a199744',  # User with 1 document
                'fd771369-6bbd-4ec9-88e1-7ce1800195ee'   # User with 1 document
            ]
            
            results = {}
            
            for user_id in known_users:
                try:
                    # Test RAG system directly with this user
                    from agents.tooling.rag.core import RAGTool, RetrievalConfig
                    
                    config = RetrievalConfig.default()
                    config.similarity_threshold = 0.1  # Lower threshold for testing
                    config.max_chunks = 5
                    
                    rag_tool = RAGTool(user_id=user_id, config=config)
                    
                    # Test query
                    test_query = 'What is my deductible?'
                    chunks = await rag_tool.retrieve_chunks_from_text(test_query)
                    
                    results[user_id] = {
                        "chunks_retrieved": len(chunks),
                        "chunks": [
                            {
                                "similarity": chunk.similarity,
                                "content_preview": chunk.content[:200] if chunk.content else "No content",
                                "content_full": chunk.content  # Full content for analysis
                            }
                            for chunk in chunks[:3]  # First 3 chunks
                        ]
                    }
                    
                    if chunks:
                        logger.info(f"✅ User {user_id}: Retrieved {len(chunks)} chunks")
                    else:
                        logger.info(f"❌ User {user_id}: No chunks retrieved")
                        
                except Exception as e:
                    results[user_id] = {
                        "error": str(e),
                        "chunks_retrieved": 0
                    }
                    logger.error(f"❌ User {user_id}: Error - {e}")
            
            return {
                "users_tested": len(known_users),
                "users_with_chunks": len([r for r in results.values() if r.get("chunks_retrieved", 0) > 0]),
                "user_results": results
            }
        
        except Exception as e:
            raise Exception(f"Production database users test failed: {e}")
    
    async def test_production_chat_endpoint(self) -> Dict[str, Any]:
        """Test production chat endpoint with real users."""
        try:
            # Create a test user first
            test_user_id = str(uuid.uuid4())
            test_email = f"chat_test_{int(time.time())}@example.com"
            test_password = "chat_test_123"
            
            async with aiohttp.ClientSession() as session:
                # Register user
                registration_data = {
                    "email": test_email,
                    "password": test_password,
                    "user_id": test_user_id
                }
                
                async with session.post(f"{self.api_base_url}/register", json=registration_data) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Registration failed: {response.status} - {response_text}")
                
                # Login user
                login_data = {
                    "email": test_email,
                    "password": test_password
                }
                
                async with session.post(f"{self.api_base_url}/login", json=login_data) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Login failed: {response.status} - {response_text}")
                    
                    result = await response.json()
                    auth_token = result.get("access_token")
                    
                    if not auth_token:
                        raise Exception("No authentication token received")
                
                # Test chat endpoint
                test_queries = [
                    "What is my deductible?",
                    "What does my insurance cover?",
                    "How much do I pay for doctor visits?"
                ]
                
                chat_results = {}
                headers = {
                    'Authorization': f'Bearer {auth_token}',
                    'Content-Type': 'application/json'
                }
                
                for query in test_queries:
                    chat_data = {
                        "message": query,
                        "user_id": test_user_id
                    }
                    
                    async with session.post(f"{self.api_base_url}/chat", json=chat_data, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result.get("response", "")
                            
                            chat_results[query] = {
                                "status_code": response.status,
                                "response_length": len(response_text),
                                "response_preview": response_text[:300],
                                "response_full": response_text
                            }
                        else:
                            response_text = await response.text()
                            chat_results[query] = {
                                "status_code": response.status,
                                "error": response_text
                            }
                
                return {
                    "test_user_id": test_user_id,
                    "queries_tested": len(test_queries),
                    "successful_queries": len([r for r in chat_results.values() if r.get("status_code") == 200]),
                    "chat_results": chat_results
                }
        
        except Exception as e:
            raise Exception(f"Production chat endpoint test failed: {e}")
    
    async def test_upload_endpoint_debug(self) -> Dict[str, Any]:
        """Debug the upload endpoint to understand the 500 error."""
        try:
            # Create a test user first
            test_user_id = str(uuid.uuid4())
            test_email = f"upload_debug_{int(time.time())}@example.com"
            test_password = "upload_debug_123"
            
            async with aiohttp.ClientSession() as session:
                # Register user
                registration_data = {
                    "email": test_email,
                    "password": test_password,
                    "user_id": test_user_id
                }
                
                async with session.post(f"{self.api_base_url}/register", json=registration_data) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Registration failed: {response.status} - {response_text}")
                
                # Login user
                login_data = {
                    "email": test_email,
                    "password": test_password
                }
                
                async with session.post(f"{self.api_base_url}/login", json=login_data) as response:
                    if response.status != 200:
                        response_text = await response.text()
                        raise Exception(f"Login failed: {response.status} - {response_text}")
                    
                    result = await response.json()
                    auth_token = result.get("access_token")
                    
                    if not auth_token:
                        raise Exception("No authentication token received")
                
                # Test upload with different approaches
                test_doc_path = "examples/test_insurance_document.pdf"
                if not os.path.exists(test_doc_path):
                    raise Exception(f"Test document not found at {test_doc_path}")
                
                with open(test_doc_path, 'rb') as f:
                    file_data = f.read()
                
                headers = {
                    'Authorization': f'Bearer {auth_token}'
                }
                
                # Test 1: Basic multipart upload
                data = aiohttp.FormData()
                data.add_field('file', file_data, filename='test_insurance_document.pdf', content_type='application/pdf')
                data.add_field('user_id', test_user_id)
                
                async with session.post(f"{self.api_base_url}/api/upload-pipeline/upload", data=data, headers=headers) as response:
                    response_text = await response.text()
                    
                    return {
                        "test_user_id": test_user_id,
                        "upload_status": response.status,
                        "response": response_text,
                        "file_size": len(file_data)
                    }
        
        except Exception as e:
            raise Exception(f"Upload endpoint debug failed: {e}")
    
    async def run_production_real_user_test(self) -> Dict[str, Any]:
        """Run the production real user test."""
        logger.info("🚀 Starting Phase 3 Production Real User Test")
        logger.info("=" * 70)
        logger.info(f"🌐 Using Production API: {self.api_base_url}")
        logger.info("=" * 70)
        
        # Run all tests in sequence
        test_functions = [
            ("Production Database Users", self.test_production_database_users),
            ("Production Chat Endpoint", self.test_production_chat_endpoint),
            ("Upload Endpoint Debug", self.test_upload_endpoint_debug)
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
        logger.info("📊 PHASE 3 PRODUCTION REAL USER TEST SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Overall Status: {self.results['summary']['overall_status']}")
        logger.info(f"Total Time: {time.time() - self.results['timestamp']:.2f} seconds")
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
            logger.info("🎉 Phase 3 Production Real User Test PASSED!")
        else:
            logger.info("❌ Phase 3 Production Real User Test FAILED!")
        
        # Save results
        results_file = f"phase3_production_real_user_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main function to run the production real user test."""
    test = Phase3ProductionRealUserTest()
    await test.run_production_real_user_test()

if __name__ == "__main__":
    asyncio.run(main())
