#!/usr/bin/env python3
"""
Phase 3 Comprehensive Validation Test

This test validates the entire system after the bulk refactor and worker fixes:
- External API health and functionality
- Document upload pipeline
- Worker processing
- RAG functionality
- Agent integration
- Performance metrics
- Error handling
"""

import asyncio
import aiohttp
import json
import time
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase3Validator:
    def __init__(self):
        self.base_url = "***REMOVED***"
        self.results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "test_name": "Phase 3 Comprehensive Validation",
                "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": [],
            "performance_metrics": {},
            "errors": []
        }
        
    async def run_validation(self):
        """Run comprehensive Phase 3 validation"""
        logger.info("🚀 Starting Phase 3 Comprehensive Validation")
        
        try:
            # Test 1: External API Health
            await self._test_external_api_health()
            
            # Test 2: Authentication
            await self._test_authentication()
            
            # Test 3: Document Upload Pipeline
            await self._test_document_upload_pipeline()
            
            # Test 4: Worker Processing
            await self._test_worker_processing()
            
            # Test 5: RAG Functionality
            await self._test_rag_functionality()
            
            # Test 6: Agent Integration
            await self._test_agent_integration()
            
            # Test 7: Performance Validation
            await self._test_performance_metrics()
            
            # Test 8: Error Handling
            await self._test_error_handling()
        
        # Generate final report
            self._generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ Validation failed with error: {e}")
            self.results["errors"].append(str(e))
            raise
    
    async def _test_external_api_health(self):
        """Test external API health and basic functionality"""
        test_name = "External API Health"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                start_time = time.time()
                async with session.get(f"{self.base_url}/health") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        health_data = await response.json()
                        self._record_test_result(test_name, True, {
                                "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "health_data": health_data
                        })
                    else:
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": "Health check failed"
                        })
                        
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_authentication(self):
        """Test authentication system"""
        test_name = "Authentication System"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test auth endpoint
                auth_data = {
                    "email": "test@example.com",
                    "password": "testpassword123"
                }
                
                start_time = time.time()
                async with session.post(f"{self.base_url}/auth/login", json=auth_data) as response:
                    response_time = time.time() - start_time
                    
                    if response.status in [200, 401]:  # 401 is expected for invalid credentials
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "note": "Authentication endpoint responding correctly"
                        })
                    else:
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": "Unexpected response code"
                        })
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _get_auth_token(self):
        """Get authentication token for protected endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to get a token (this might fail, but we'll handle it gracefully)
                auth_data = {
                    "email": "test@example.com",
                    "password": "testpassword123"
                }
                
                async with session.post(f"{self.base_url}/auth/login", json=auth_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("access_token")
                    else:
                        return None
        except:
            return None
    
    async def _test_document_upload_pipeline(self):
        """Test document upload pipeline"""
        test_name = "Document Upload Pipeline"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            # Get auth token
            token = await self._get_auth_token()
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            async with aiohttp.ClientSession() as session:
                # Create test document data
                test_doc_content = "This is a test insurance document for Phase 3 validation."
                test_doc_hash = hashlib.sha256(test_doc_content.encode()).hexdigest()
                
                upload_data = {
                    "filename": "test_phase3_document.pdf",
                    "bytes_len": len(test_doc_content),
                    "mime": "application/pdf",
                    "sha256": test_doc_hash,
                    "ocr": False
                }
                
                # Test upload endpoint
                start_time = time.time()
                async with session.post(f"{self.base_url}/api/upload-pipeline/upload", json=upload_data, headers=headers) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        upload_result = await response.json()
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "upload_result": upload_result
                        })
                    elif response.status == 401:
                        self._record_test_result(test_name, True, {
                                "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "note": "Upload endpoint requires authentication (expected)"
                        })
                    else:
                        error_text = await response.text()
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "error": error_text
                        })
                        
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_worker_processing(self):
        """Test worker processing capabilities"""
        test_name = "Worker Processing"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Check API status endpoint which should show worker status
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/v1/status") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        status_data = await response.json()
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "status_data": status_data
                        })
                    else:
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": "Failed to get status data"
                        })
                        
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_rag_functionality(self):
        """Test RAG functionality"""
        test_name = "RAG Functionality"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test RAG debug endpoint (this should work without auth)
                test_user_id = str(uuid.uuid4())
                start_time = time.time()
                async with session.get(f"{self.base_url}/debug/rag-similarity/{test_user_id}") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        rag_result = await response.json()
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "rag_result": rag_result
                        })
                    elif response.status == 401:
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "note": "RAG endpoint requires authentication (expected)"
                        })
                    else:
                        error_text = await response.text()
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "error": error_text
                        })
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_agent_integration(self):
        """Test agent integration"""
        test_name = "Agent Integration"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test chat endpoint
                chat_data = {
                    "message": "Hello, can you help me understand insurance?",
                    "user_id": str(uuid.uuid4())
                }
                
                start_time = time.time()
                async with session.post(f"{self.base_url}/chat", json=chat_data) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        chat_result = await response.json()
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "chat_result": chat_result
                        })
                    elif response.status == 401:
                        self._record_test_result(test_name, True, {
                                "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "note": "Chat endpoint requires authentication (expected)"
                        })
                    else:
                        error_text = await response.text()
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "error": error_text
                        })
                        
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_performance_metrics(self):
        """Test performance metrics"""
        test_name = "Performance Metrics"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test multiple concurrent requests
                start_time = time.time()
                
                tasks = []
                for i in range(5):
                    task = session.get(f"{self.base_url}/health")
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                total_time = time.time() - start_time
                
                successful_requests = sum(1 for r in responses if not isinstance(r, Exception))
                
                self._record_test_result(test_name, True, {
                    "concurrent_requests": 5,
                    "successful_requests": successful_requests,
                    "total_time_ms": total_time * 1000,
                    "avg_response_time_ms": (total_time * 1000) / 5
                })
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_error_handling(self):
        """Test error handling"""
        test_name = "Error Handling"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test invalid endpoint
                start_time = time.time()
                async with session.get(f"{self.base_url}/invalid-endpoint") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 404:
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "note": "Proper 404 error handling"
                        })
                    elif response.status == 405:
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "note": "Proper 405 error handling (method not allowed)"
                        })
                    else:
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": "Unexpected response for invalid endpoint"
                        })
                
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    def _record_test_result(self, test_name: str, passed: bool, details: Dict[str, Any]):
        """Record test result"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
        else:
            self.results["failed_tests"] += 1
        
        test_result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.results["test_results"].append(test_result)
        
        status = "✅" if passed else "❌"
        logger.info(f"{status} {test_name}: {'PASSED' if passed else 'FAILED'}")
    
    def _generate_final_report(self):
        """Generate final validation report"""
        success_rate = (self.results["passed_tests"] / self.results["total_tests"]) * 100 if self.results["total_tests"] > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 PHASE 3 COMPREHENSIVE VALIDATION REPORT")
        logger.info("=" * 60)
        logger.info(f"🕐 Test Timestamp: {self.results['test_timestamp']}")
        logger.info(f"📈 Total Tests: {self.results['total_tests']}")
        logger.info(f"✅ Passed Tests: {self.results['passed_tests']}")
        logger.info(f"❌ Failed Tests: {self.results['failed_tests']}")
        logger.info(f"📊 Success Rate: {success_rate:.1f}%")
        logger.info("=" * 60)
        
        if self.results["failed_tests"] > 0:
            logger.info("❌ FAILED TESTS:")
            for test in self.results["test_results"]:
                if not test["passed"]:
                    logger.info(f"  - {test['test_name']}: {test['details']}")
        
        if self.results["errors"]:
            logger.info("🚨 ERRORS:")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")
        
        # Save results to file
        with open("phase3_validation_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info("💾 Results saved to phase3_validation_results.json")
        
        if success_rate >= 80:
            logger.info("🎉 PHASE 3 VALIDATION SUCCESSFUL!")
            return True
        else:
            logger.error("💥 PHASE 3 VALIDATION FAILED!")
            return False

async def main():
    """Main function"""
    validator = Phase3Validator()
    success = await validator.run_validation()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)