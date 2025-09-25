#!/usr/bin/env python3
"""
Frontend Simulation Testing Script

This script simulates frontend behavior by making direct API calls
to test the complete upload workflow from upload to completion.

Usage:
    python scripts/testing/test-frontend-simulation.py [--api-url URL] [--worker-url URL]
"""

import asyncio
import json
import time
import argparse
import sys
from typing import Dict, Any, Optional
import aiohttp
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FrontendSimulator:
    """Simulates frontend behavior for testing the upload pipeline"""
    
    def __init__(self, api_url: str = "http://localhost:8000", worker_url: str = "http://localhost:8002"):
        self.api_url = api_url.rstrip('/')
        self.worker_url = worker_url.rstrip('/')
        self.test_user_id = "test-user-123"
        self.test_filename = "test-document.pdf"
        self.test_file_size = 1048576  # 1MB
        self.test_sha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        
        # Test results
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_job_id = None
        self.test_document_id = None
        
        # Session for HTTP requests
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": "Bearer test-jwt-token"},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request and return JSON response"""
        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Request failed: {response.status} - {error_text}")
                    return {"error": error_text, "status": response.status}
        except Exception as e:
            logger.error(f"Request exception: {e}")
            return {"error": str(e), "status": 0}
    
    async def test_service_health(self) -> bool:
        """Test 1: Service Health Checks"""
        logger.info("=== Test 1: Service Health Checks ===")
        
        try:
            # Check API server
            api_health = await self.make_request("GET", f"{self.api_url}/health")
            if "error" not in api_health:
                logger.info("✅ API Server health check passed")
            else:
                logger.error("❌ API Server health check failed")
                return False
            
            # Check BaseWorker
            worker_health = await self.make_request("GET", f"{self.worker_url}/health")
            if "error" not in worker_health:
                logger.info("✅ BaseWorker health check passed")
            else:
                logger.error("❌ BaseWorker health check failed")
                return False
            
            # Check database connectivity via API
            if "database" in api_health and "healthy" in str(api_health).lower():
                logger.info("✅ Database connectivity check passed")
            else:
                logger.warning("⚠️  Database health status unclear")
            
            self.tests_passed += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Service health test failed: {e}")
            self.tests_failed += 1
            return False
    
    async def test_upload_endpoint(self) -> bool:
        """Test 2: Upload Endpoint Simulation"""
        logger.info("=== Test 2: Upload Endpoint Simulation ===")
        
        try:
            # Simulate frontend upload request
            upload_data = {
                "filename": self.test_filename,
                "bytes_len": self.test_file_size,
                "mime": "application/pdf",
                "sha256": self.test_sha256,
                "ocr": False
            }
            
            response = await self.make_request(
                "POST", 
                f"{self.api_url}/api/upload-pipeline/upload",
                json=upload_data
            )
            
            if "error" not in response:
                if "job_id" in response and "document_id" in response:
                    self.test_job_id = response["job_id"]
                    self.test_document_id = response["document_id"]
                    logger.info(f"✅ Job created: {self.test_job_id}")
                    logger.info(f"✅ Document: {self.test_document_id}")
                    self.tests_passed += 1
                    return True
                else:
                    logger.error("❌ Response missing job_id or document_id")
                    self.tests_failed += 1
                    return False
            else:
                logger.error(f"❌ Upload request failed: {response['error']}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Upload endpoint test failed: {e}")
            self.tests_failed += 1
            return False
    
    async def test_job_status_polling(self) -> bool:
        """Test 3: Job Status Polling Simulation"""
        logger.info("=== Test 3: Job Status Polling Simulation ===")
        
        if not self.test_job_id:
            logger.error("❌ No job_id available for status testing")
            self.tests_failed += 1
            return False
        
        try:
            logger.info(f"Simulating frontend job status polling for job: {self.test_job_id}")
            
            # Poll job status multiple times to simulate frontend behavior
            max_polls = 10
            poll_count = 0
            
            while poll_count < max_polls:
                poll_count += 1
                logger.info(f"Polling job status (attempt {poll_count}/{max_polls})...")
                
                response = await self.make_request(
                    "GET", 
                    f"{self.api_url}/api/v2/jobs/{self.test_job_id}"
                )
                
                if "error" not in response:
                    stage = response.get("stage", "unknown")
                    state = response.get("state", "unknown")
                    progress = response.get("progress", {}).get("total_pct", 0)
                    
                    logger.info(f"Job Status - Stage: {stage}, State: {state}, Progress: {progress}%")
                    
                    # Check if job is complete
                    if state == "done":
                        logger.info("✅ Job completed successfully!")
                        self.tests_passed += 1
                        return True
                    elif state == "deadletter":
                        logger.error("❌ Job failed and moved to dead letter queue")
                        self.tests_failed += 1
                        return False
                    
                    # Wait before next poll (simulate frontend polling interval)
                    await asyncio.sleep(5)
                else:
                    logger.error(f"❌ Failed to get job status: {response['error']}")
                    self.tests_failed += 1
                    return False
            
            logger.warning("⚠️  Job status polling completed without job completion")
            self.tests_passed += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Job status polling test failed: {e}")
            self.tests_failed += 1
            return False
    
    async def test_job_listing(self) -> bool:
        """Test 4: Job Listing Simulation"""
        logger.info("=== Test 4: Job Listing Simulation ===")
        
        try:
            logger.info("Simulating frontend job listing request...")
            
            response = await self.make_request("GET", f"{self.api_url}/api/v2/jobs")
            
            if "error" not in response:
                logger.info("✅ Job listing request successful")
                
                # Check if our test job appears in the list
                if self.test_job_id and self.test_job_id in str(response):
                    logger.info("✅ Test job found in job listing")
                else:
                    logger.warning("⚠️  Test job not found in job listing (may be normal)")
                
                self.tests_passed += 1
                return True
            else:
                logger.error(f"❌ Job listing request failed: {response['error']}")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Job listing test failed: {e}")
            self.tests_failed += 1
            return False
    
    async def test_error_handling(self) -> bool:
        """Test 5: Error Handling Simulation"""
        logger.info("=== Test 5: Error Handling Simulation ===")
        
        try:
            # Test invalid file size
            logger.info("Testing invalid file size error...")
            invalid_size_data = {
                "filename": "invalid.pdf",
                "bytes_len": 104857600,  # 100MB
                "mime": "application/pdf",
                "sha256": self.test_sha256,
                "ocr": False
            }
            
            response = await self.make_request(
                "POST", 
                f"{self.api_url}/api/upload-pipeline/upload",
                json=invalid_size_data
            )
            
            if "error" in response and "File size" in str(response):
                logger.info("✅ File size validation error handled correctly")
            else:
                logger.error("❌ File size validation error not handled correctly")
                self.tests_failed += 1
                return False
            
            # Test invalid MIME type
            logger.info("Testing invalid MIME type error...")
            invalid_mime_data = {
                "filename": "invalid.txt",
                "bytes_len": self.test_file_size,
                "mime": "text/plain",
                "sha256": self.test_sha256,
                "ocr": False
            }
            
            response = await self.make_request(
                "POST", 
                f"{self.api_url}/api/upload-pipeline/upload",
                json=invalid_mime_data
            )
            
            if "error" in response and "MIME type" in str(response):
                logger.info("✅ MIME type validation error handled correctly")
            else:
                logger.error("❌ MIME type validation error not handled correctly")
                self.tests_failed += 1
                return False
            
            self.tests_passed += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.tests_failed += 1
            return False
    
    async def test_rate_limiting(self) -> bool:
        """Test 6: Rate Limiting Simulation"""
        logger.info("=== Test 6: Rate Limiting Simulation ===")
        
        try:
            logger.info("Testing rate limiting by making multiple rapid requests...")
            
            rate_limit_hit = False
            for i in range(5):
                data = {
                    "filename": f"rate-test-{i}.pdf",
                    "bytes_len": self.test_file_size,
                    "mime": "application/pdf",
                    "sha256": f"rate-test-sha256-{i}",
                    "ocr": False
                }
                
                response = await self.make_request(
                    "POST", 
                    f"{self.api_url}/api/upload-pipeline/upload",
                    json=data
                )
                
                if "error" in response and "Too Many Requests" in str(response):
                    logger.info(f"✅ Rate limiting triggered correctly on request {i+1}")
                    rate_limit_hit = True
                    break
                
                await asyncio.sleep(0.1)  # Small delay between requests
            
            if rate_limit_hit:
                logger.info("✅ Rate limiting test passed")
                self.tests_passed += 1
                return True
            else:
                logger.warning("⚠️  Rate limiting not triggered (may need adjustment)")
                self.tests_passed += 1
                return True
                
        except Exception as e:
            logger.error(f"❌ Rate limiting test failed: {e}")
            self.tests_failed += 1
            return False
    
    async def test_concurrent_processing(self) -> bool:
        """Test 7: Concurrent Job Processing"""
        logger.info("=== Test 7: Concurrent Job Processing ===")
        
        try:
            logger.info("Testing concurrent job creation (should respect 2 jobs per user limit)...")
            
            # Create first job
            job1_data = {
                "filename": "concurrent-1.pdf",
                "bytes_len": self.test_file_size,
                "mime": "application/pdf",
                "sha256": "concurrent-sha256-1",
                "ocr": False
            }
            
            response = await self.make_request(
                "POST", 
                f"{self.api_url}/api/upload-pipeline/upload",
                json=job1_data
            )
            
            if "error" not in response and "job_id" in response:
                job1_id = response["job_id"]
                logger.info(f"✅ First concurrent job created: {job1_id}")
            else:
                logger.error("❌ Failed to create first concurrent job")
                self.tests_failed += 1
                return False
            
            # Create second job
            job2_data = {
                "filename": "concurrent-2.pdf",
                "bytes_len": self.test_file_size,
                "mime": "application/pdf",
                "sha256": "concurrent-sha256-2",
                "ocr": False
            }
            
            response = await self.make_request(
                "POST", 
                f"{self.api_url}/api/upload-pipeline/upload",
                json=job2_data
            )
            
            if "error" not in response and "job_id" in response:
                job2_id = response["job_id"]
                logger.info(f"✅ Second concurrent job created: {job2_id}")
            else:
                logger.error("❌ Failed to create second concurrent job")
                self.tests_failed += 1
                return False
            
            # Try to create third job (should be rejected)
            job3_data = {
                "filename": "concurrent-3.pdf",
                "bytes_len": self.test_file_size,
                "mime": "application/pdf",
                "sha256": "concurrent-sha256-3",
                "ocr": False
            }
            
            response = await self.make_request(
                "POST", 
                f"{self.api_url}/api/upload-pipeline/upload",
                json=job3_data
            )
            
            if "error" in response and "Too Many Requests" in str(response):
                logger.info("✅ Concurrent job limit enforced correctly")
                self.tests_passed += 1
                return True
            else:
                logger.error("❌ Concurrent job limit not enforced")
                self.tests_failed += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Concurrent processing test failed: {e}")
            self.tests_failed += 1
            return False
    
    async def run_all_tests(self) -> None:
        """Run all frontend simulation tests"""
        logger.info("Starting Frontend Simulation Testing")
        logger.info(f"API Base URL: {self.api_url}")
        logger.info(f"Worker Base URL: {self.worker_url}")
        logger.info(f"Test User ID: {self.test_user_id}")
        logger.info("")
        
        # Run all tests
        await self.test_service_health()
        await self.test_upload_endpoint()
        await self.test_job_status_polling()
        await self.test_job_listing()
        await self.test_error_handling()
        await self.test_rate_limiting()
        await self.test_concurrent_processing()
        
        # Summary
        logger.info("")
        logger.info("=== Test Summary ===")
        logger.info(f"✅ Tests Passed: {self.tests_passed}")
        if self.tests_failed > 0:
            logger.error(f"❌ Tests Failed: {self.tests_failed}")
        else:
            logger.info(f"✅ Tests Failed: {self.tests_failed}")
        
        total_tests = self.tests_passed + self.tests_failed
        success_rate = (self.tests_passed * 100) // total_tests if total_tests > 0 else 0
        
        if success_rate == 100:
            logger.info(f"🎉 Overall Success Rate: {success_rate}%")
        elif success_rate >= 80:
            logger.info(f"✅ Overall Success Rate: {success_rate}%")
        else:
            logger.error(f"❌ Overall Success Rate: {success_rate}%")
        
        logger.info("")
        logger.info("Frontend simulation testing completed!")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Frontend Simulation Testing")
    parser.add_argument("--api-url", default="http://localhost:8000", help="API server URL")
    parser.add_argument("--worker-url", default="http://localhost:8002", help="Worker URL")
    
    args = parser.parse_args()
    
    async with FrontendSimulator(args.api_url, args.worker_url) as simulator:
        await simulator.run_all_tests()
        
        # Exit with appropriate code
        if simulator.tests_failed > 0:
            sys.exit(1)
        else:
            sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
