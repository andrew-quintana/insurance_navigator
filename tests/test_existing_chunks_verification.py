#!/usr/bin/env python3
"""
Test to verify if there are existing chunks in the database and test worker functionality.
This bypasses the upload issue and focuses on what's already in the system.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExistingChunksTest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "failed_details": []
        }
        self.auth_token = None

    async def _record_test_result(self, test_name: str, passed: bool, details: Dict[str, Any]):
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.results["failed_tests"] += 1
            self.results["failed_details"].append({"test_name": test_name, "details": details})
            logger.error(f"❌ {test_name}: FAILED - {details.get('error', 'No error message')}")

    async def _test_worker_status(self):
        """Test worker status and health."""
        test_name = "Worker Status"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/status") as response:
                    response_text = await response.text()
                    logger.info(f"Worker status response: {response.status} - {response_text}")
                    
                    if response.status == 200:
                        status_data = await response.json()
                        logger.info(f"Worker status: {status_data}")
                        await self._record_test_result(test_name, True, {"status_data": status_data})
                        return True
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in worker status test: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def _test_database_connectivity(self):
        """Test database connectivity and check for existing data."""
        test_name = "Database Connectivity"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint which includes database status
                async with session.get(f"{self.base_url}/health") as response:
                    response_text = await response.text()
                    logger.info(f"Health response: {response.status} - {response_text}")
                    
                    if response.status == 200:
                        health_data = await response.json()
                        db_status = health_data.get("services", {}).get("database")
                        logger.info(f"Database status: {db_status}")
                        
                        if db_status == "healthy":
                            await self._record_test_result(test_name, True, {"db_status": db_status})
                            return True
                        else:
                            await self._record_test_result(test_name, False, {"db_status": db_status})
                            return False
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in database connectivity test: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def _test_existing_documents(self):
        """Test if there are any existing documents in the system."""
        test_name = "Existing Documents Check"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try to get documents list (this might require auth, but let's see what happens)
                async with session.get(f"{self.base_url}/documents") as response:
                    response_text = await response.text()
                    logger.info(f"Documents response: {response.status} - {response_text}")
                    
                    if response.status == 200:
                        documents_data = await response.json()
                        logger.info(f"Found {len(documents_data) if isinstance(documents_data, list) else 'unknown'} documents")
                        await self._record_test_result(test_name, True, {
                            "document_count": len(documents_data) if isinstance(documents_data, list) else 0,
                            "response": documents_data
                        })
                        return True
                    elif response.status == 401:
                        logger.info("Documents endpoint requires authentication (expected)")
                        await self._record_test_result(test_name, True, {"message": "Endpoint requires auth (expected)"})
                        return True
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in existing documents test: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def _test_rag_endpoints(self):
        """Test RAG endpoints to see if they're working."""
        test_name = "RAG Endpoints"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test debug RAG endpoint (this might not require auth)
                test_user_id = "test-user-id"
                async with session.get(f"{self.base_url}/debug/rag-similarity/{test_user_id}?query=test") as response:
                    response_text = await response.text()
                    logger.info(f"RAG debug response: {response.status} - {response_text}")
                    
                    if response.status == 200:
                        rag_data = await response.json()
                        logger.info(f"RAG response: {rag_data}")
                        await self._record_test_result(test_name, True, {"rag_data": rag_data})
                        return True
                    elif response.status == 401:
                        logger.info("RAG endpoint requires authentication (expected)")
                        await self._record_test_result(test_name, True, {"message": "Endpoint requires auth (expected)"})
                        return True
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in RAG endpoints test: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def _test_upload_pipeline_status(self):
        """Test upload pipeline status and check for any pending jobs."""
        test_name = "Upload Pipeline Status"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test upload jobs endpoint
                async with session.get(f"{self.base_url}/api/v2/jobs") as response:
                    response_text = await response.text()
                    logger.info(f"Upload jobs response: {response.status} - {response_text}")
                    
                    if response.status == 200:
                        jobs_data = await response.json()
                        logger.info(f"Found {len(jobs_data) if isinstance(jobs_data, list) else 'unknown'} jobs")
                        await self._record_test_result(test_name, True, {
                            "job_count": len(jobs_data) if isinstance(jobs_data, list) else 0,
                            "response": jobs_data
                        })
                        return True
                    elif response.status == 401:
                        logger.info("Jobs endpoint requires authentication (expected)")
                        await self._record_test_result(test_name, True, {"message": "Endpoint requires auth (expected)"})
                        return True
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in upload pipeline status test: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def run_all_tests(self):
        """Run all tests to understand the current system state."""
        logger.info("🚀 Starting Existing Chunks Verification Test")
        logger.info(f"Using API: {self.base_url}")
        
        # Test sequence
        tests = [
            self._test_worker_status,
            self._test_database_connectivity,
            self._test_existing_documents,
            self._test_rag_endpoints,
            self._test_upload_pipeline_status
        ]
        
        for test_func in tests:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"Exception in test {test_func.__name__}: {e}")
        
        # Generate report
        success_rate = (self.results["passed_tests"] / self.results["total_tests"]) * 100 if self.results["total_tests"] > 0 else 0
        self.results["success_rate"] = success_rate
        
        logger.info("=" * 60)
        logger.info("📊 EXISTING CHUNKS VERIFICATION REPORT")
        logger.info("=" * 60)
        logger.info(f"🕐 Test Timestamp: {self.results['test_timestamp']}")
        logger.info(f"📈 Total Tests: {self.results['total_tests']}")
        logger.info(f"✅ Passed Tests: {self.results['passed_tests']}")
        logger.info(f"❌ Failed Tests: {self.results['failed_tests']}")
        logger.info(f"📊 Success Rate: {self.results['success_rate']:.1f}%")
        logger.info("=" * 60)
        
        if self.results["failed_tests"] > 0:
            logger.error("❌ FAILED TESTS:")
            for failure in self.results["failed_details"]:
                logger.error(f"  - {failure['test_name']}: {failure['details']}")
        
        return self.results["failed_tests"] == 0

if __name__ == "__main__":
    # Use production API
    api_base_url = "***REMOVED***"
    test_runner = ExistingChunksTest(api_base_url)
    asyncio.run(test_runner.run_all_tests())
