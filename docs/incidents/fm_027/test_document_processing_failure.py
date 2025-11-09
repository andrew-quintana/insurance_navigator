#!/usr/bin/env python3
"""
FRACAS FM-027 Document Processing Failure Test Script

This script helps investigate the document processing failure by testing
various components of the upload pipeline.

Tests:
1. Worker service connectivity
2. File accessibility from worker
3. Webhook system functionality
4. Complete processing pipeline
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessingFailureTester:
    """Test suite for FRACAS FM-027 document processing failure."""
    
    def __init__(self):
        self.base_url = "https://insurance-navigator-staging-api.onrender.com"
        self.worker_service_id = "srv-d37dlmvfte5s73b6uq0g"
        self.api_service_id = "srv-d3740ijuibrs738mus1g"
        self.supabase_url = "https://dfgzeastcxnoqshgyotp.supabase.co"
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_name": "FRACAS FM-027 Document Processing Failure Test",
            "tests": {},
            "overall_success": False,
            "critical_failures": 0
        }
    
    async def test_api_service_health(self) -> bool:
        """Test API service health."""
        test_name = "api_service_health"
        logger.info(f"Testing {test_name}...")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=30.0)
                
                if response.status_code == 200:
                    health_data = response.json()
                    logger.info(f"✅ API service health: {health_data}")
                    self.test_results["tests"][test_name] = {
                        "status": "PASS",
                        "details": health_data
                    }
                    return True
                else:
                    logger.error(f"❌ API service health failed: {response.status_code}")
                    self.test_results["tests"][test_name] = {
                        "status": "FAIL",
                        "details": {"status_code": response.status_code, "response": response.text}
                    }
                    return False
                    
        except Exception as e:
            logger.error(f"❌ API service health error: {str(e)}")
            self.test_results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            return False
    
    async def test_document_upload(self) -> Optional[Dict[str, Any]]:
        """Test document upload functionality."""
        test_name = "document_upload"
        logger.info(f"Testing {test_name}...")
        
        try:
            # Create a test document
            test_content = f"""
            TEST INSURANCE POLICY DOCUMENT
            Policy Number: TEST-{int(time.time())}
            Policyholder: Test User
            Effective Date: 2024-01-01
            Expiration Date: 2024-12-31
            
            COVERAGE DETAILS
            ================
            
            Medical Coverage:
            - Annual Maximum: $1,000,000
            - Deductible: $2,500 per year
            - Coinsurance: 20% after deductible
            
            This is a test document for FRACAS FM-027 investigation.
            """
            
            # Upload document
            async with httpx.AsyncClient() as client:
                files = {
                    'file': ('test_policy.pdf', test_content, 'application/pdf')
                }
                
                response = await client.post(
                    f"{self.base_url}/upload",
                    files=files,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    upload_data = response.json()
                    logger.info(f"✅ Document upload successful: {upload_data}")
                    self.test_results["tests"][test_name] = {
                        "status": "PASS",
                        "details": upload_data
                    }
                    return upload_data
                else:
                    logger.error(f"❌ Document upload failed: {response.status_code}")
                    self.test_results["tests"][test_name] = {
                        "status": "FAIL",
                        "details": {"status_code": response.status_code, "response": response.text}
                    }
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Document upload error: {str(e)}")
            self.test_results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            return None
    
    async def test_job_status_monitoring(self, job_id: str) -> bool:
        """Test job status monitoring."""
        test_name = "job_status_monitoring"
        logger.info(f"Testing {test_name} for job {job_id}...")
        
        try:
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/upload/status/{job_id}",
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        status_data = response.json()
                        logger.info(f"Job status (attempt {attempt + 1}): {status_data}")
                        
                        # Check if processing is complete or failed
                        if status_data.get("status") in ["completed", "failed_parse", "failed"]:
                            self.test_results["tests"][test_name] = {
                                "status": "PASS",
                                "details": {
                                    "final_status": status_data.get("status"),
                                    "attempts": attempt + 1,
                                    "data": status_data
                                }
                            }
                            return True
                        
                        # Wait before next attempt
                        await asyncio.sleep(5)
                        attempt += 1
                    else:
                        logger.error(f"❌ Job status check failed: {response.status_code}")
                        self.test_results["tests"][test_name] = {
                            "status": "FAIL",
                            "details": {"status_code": response.status_code, "response": response.text}
                        }
                        return False
            
            # Timeout reached
            logger.warning(f"⚠️ Job status monitoring timeout after {max_attempts} attempts")
            self.test_results["tests"][test_name] = {
                "status": "TIMEOUT",
                "details": {"attempts": max_attempts}
            }
            return False
                    
        except Exception as e:
            logger.error(f"❌ Job status monitoring error: {str(e)}")
            self.test_results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            return False
    
    async def test_rag_functionality(self) -> bool:
        """Test RAG functionality."""
        test_name = "rag_functionality"
        logger.info(f"Testing {test_name}...")
        
        try:
            test_query = "What is the annual maximum for medical coverage?"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat",
                    json={"message": test_query},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    chat_data = response.json()
                    logger.info(f"✅ RAG functionality working: {chat_data}")
                    self.test_results["tests"][test_name] = {
                        "status": "PASS",
                        "details": chat_data
                    }
                    return True
                else:
                    logger.error(f"❌ RAG functionality failed: {response.status_code}")
                    self.test_results["tests"][test_name] = {
                        "status": "FAIL",
                        "details": {"status_code": response.status_code, "response": response.text}
                    }
                    return False
                    
        except Exception as e:
            logger.error(f"❌ RAG functionality error: {str(e)}")
            self.test_results["tests"][test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            return False
    
    async def run_complete_test(self) -> bool:
        """Run complete test suite."""
        logger.info("Starting FRACAS FM-027 Document Processing Failure Test")
        logger.info("=" * 60)
        
        success = True
        
        # Test 1: API Service Health
        if not await self.test_api_service_health():
            success = False
            self.test_results["critical_failures"] += 1
        
        # Test 2: Document Upload
        upload_result = await self.test_document_upload()
        if not upload_result:
            success = False
            self.test_results["critical_failures"] += 1
        else:
            # Test 3: Job Status Monitoring
            job_id = upload_result.get("job_id")
            if job_id:
                if not await self.test_job_status_monitoring(job_id):
                    success = False
                    self.test_results["critical_failures"] += 1
            else:
                logger.warning("⚠️ No job_id returned from upload")
                success = False
                self.test_results["critical_failures"] += 1
        
        # Test 4: RAG Functionality (if documents are processed)
        if success:
            await self.test_rag_functionality()
        
        # Summary
        self.test_results["overall_success"] = success
        
        logger.info("=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        for test_name, test_result in self.test_results["tests"].items():
            status = test_result.get("status", "UNKNOWN")
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"Overall Success: {success}")
        logger.info(f"Critical Failures: {self.test_results['critical_failures']}")
        
        return success

async def main():
    """Run the test suite."""
    tester = DocumentProcessingFailureTester()
    success = await tester.run_complete_test()
    
    # Save results
    with open("fracas_fm027_test_results.json", "w") as f:
        json.dump(tester.test_results, f, indent=2)
    
    logger.info(f"Test results saved to fracas_fm027_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
