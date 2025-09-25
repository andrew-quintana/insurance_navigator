#!/usr/bin/env python3
"""
Test chunk generation with detailed logging to understand the pipeline.
Uses production API since local backend has environment variable issues.
"""

import asyncio
import aiohttp
import hashlib
import json
import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chunk_generation_test.log')
    ]
)
logger = logging.getLogger(__name__)

class ChunkGenerationTest:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "failed_details": []
        }
        self.test_user_email = f"test_chunk_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPassword123!"
        self.auth_token = None
        self.document_id = None
        self.job_id = None

    async def _record_test_result(self, test_name: str, passed: bool, details: Dict[str, Any]):
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
            logger.info(f"✅ {test_name}: PASSED")
        else:
            self.results["failed_tests"] += 1
            self.results["failed_details"].append({"test_name": test_name, "details": details})
            logger.error(f"❌ {test_name}: FAILED - {details.get('error', 'No error message')}")

    async def _test_user_creation(self):
        """Test user creation with proper consent fields."""
        test_name = "User Creation"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                signup_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password,
                    "full_name": "Chunk Generation Test User",
                    "consent_version": "1.0",
                    "consent_timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"Creating user: {self.test_user_email}")
                async with session.post(f"{self.base_url}/auth/signup", json=signup_data) as response:
                    response_text = await response.text()
                    logger.info(f"Signup response status: {response.status}")
                    logger.info(f"Signup response body: {response_text}")
                    
                    if response.status in [200, 201, 409]:  # 409 = user already exists
                        await self._record_test_result(test_name, True, {"message": "User creation successful or user already exists"})
                        return True
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in user creation: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def _test_user_authentication(self):
        """Test user authentication."""
        test_name = "User Authentication"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                auth_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password
                }
                
                logger.info(f"Authenticating user: {self.test_user_email}")
                async with session.post(f"{self.base_url}/auth/login", json=auth_data) as response:
                    response_text = await response.text()
                    logger.info(f"Login response status: {response.status}")
                    logger.info(f"Login response body: {response_text}")
                    
                    if response.status == 200:
                        result = await response.json()
                        self.auth_token = result.get("access_token")
                        logger.info(f"Authentication successful, token: {self.auth_token[:20]}...")
                        await self._record_test_result(test_name, True, {"message": "Authentication successful"})
                        return True
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in authentication: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def _test_document_upload(self):
        """Test document upload."""
        test_name = "Document Upload"
        logger.info(f"🔍 Testing {test_name}")
        
        if not self.auth_token:
            logger.error("No auth token available for document upload")
            await self._record_test_result(test_name, False, {"error": "No auth token"})
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                # Create test document content
                test_doc_content = f"""
                INSURANCE POLICY DOCUMENT
                Policy Number: CHUNK-TEST-{uuid.uuid4().hex[:8]}
                Policyholder: {self.test_user_email}
                
                This is a comprehensive insurance policy document for testing chunk generation.
                It contains multiple sections that should be properly chunked and vectorized.
                
                SECTION 1: COVERAGE DETAILS
                - Medical Coverage: $1,000,000
                - Dental Coverage: $50,000
                - Vision Coverage: $25,000
                - Prescription Coverage: $10,000
                
                SECTION 2: DEDUCTIBLES AND COPAYS
                - Annual Deductible: $2,500
                - Office Visit Copay: $25
                - Specialist Copay: $50
                - Emergency Room Copay: $200
                
                SECTION 3: NETWORK PROVIDERS
                - In-Network: 90% coverage after deductible
                - Out-of-Network: 70% coverage after deductible
                - Preferred Providers: Additional 5% discount
                
                SECTION 4: EXCLUSIONS
                - Cosmetic procedures
                - Experimental treatments
                - Pre-existing conditions (first 12 months)
                - Alternative medicine
                
                SECTION 5: CLAIMS PROCESS
                1. Submit claim within 30 days
                2. Include all required documentation
                3. Allow 15 business days for processing
                4. Appeal process available if denied
                
                This document should generate multiple meaningful chunks for testing purposes.
                Each section should be properly identified and vectorized for retrieval.
                """
                
                test_doc_hash = hashlib.sha256(test_doc_content.encode()).hexdigest()
                filename = f"chunk_test_policy_{uuid.uuid4().hex[:8]}.pdf"
                
                upload_data = {
                    "filename": filename,
                    "bytes_len": len(test_doc_content),
                    "mime": "application/pdf",
                    "sha256": test_doc_hash,
                    "ocr": False
                }
                
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                logger.info(f"Uploading document: {filename}")
                logger.info(f"Document size: {len(test_doc_content)} bytes")
                logger.info(f"Document hash: {test_doc_hash}")
                
                async with session.post(f"{self.base_url}/api/upload-pipeline/upload", json=upload_data, headers=headers) as response:
                    response_text = await response.text()
                    logger.info(f"Upload response status: {response.status}")
                    logger.info(f"Upload response body: {response_text}")
                    
                    if response.status == 200:
                        result = await response.json()
                        self.job_id = result.get("job_id")
                        self.document_id = result.get("document_id")
                        signed_url = result.get("signed_url")
                        
                        logger.info(f"Upload successful - Job ID: {self.job_id}, Document ID: {self.document_id}")
                        
                        # Upload content to signed URL
                        logger.info(f"Uploading content to signed URL: {signed_url}")
                        async with session.put(signed_url, data=test_doc_content.encode(), headers={"Content-Type": "application/pdf"}) as put_response:
                            logger.info(f"Content upload status: {put_response.status}")
                            if put_response.status == 200:
                                logger.info("Content uploaded to signed URL successfully")
                                await self._record_test_result(test_name, True, {
                                    "job_id": self.job_id,
                                    "document_id": self.document_id
                                })
                                return True
                            else:
                                put_text = await put_response.text()
                                logger.error(f"Content upload failed: {put_text}")
                                await self._record_test_result(test_name, False, {
                                    "step": "Content Upload",
                                    "status_code": put_response.status,
                                    "error": put_text
                                })
                                return False
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in document upload: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def _test_job_processing(self):
        """Test job processing and wait for completion."""
        test_name = "Job Processing"
        logger.info(f"🔍 Testing {test_name}")
        
        if not self.document_id:
            logger.error("No document ID available for job processing")
            await self._record_test_result(test_name, False, {"error": "No document ID"})
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Poll for job status
                max_polls = 60  # 2 minutes with 2-second intervals
                poll_interval = 2
                job_completed = False
                final_status = "unknown"
                
                logger.info(f"Polling for job completion for Document ID: {self.document_id}")
                
                for i in range(max_polls):
                    await asyncio.sleep(poll_interval)
                    
                    try:
                        async with session.get(f"{self.base_url}/documents/{self.document_id}/status", headers=headers) as response:
                            response_text = await response.text()
                            logger.info(f"Status poll {i+1}/{max_polls} - Status: {response.status}, Body: {response_text}")
                            
                            if response.status == 200:
                                status_data = await response.json()
                                current_status = status_data.get("status")
                                logger.info(f"Current job status: {current_status}")
                                
                                if current_status == "complete":
                                    job_completed = True
                                    final_status = current_status
                                    logger.info("Job completed successfully!")
                                    break
                                elif current_status and "failed" in current_status:
                                    final_status = current_status
                                    logger.error(f"Job failed with status: {current_status}")
                                    break
                            else:
                                logger.warning(f"Status check failed with status {response.status}: {response_text}")
                    except Exception as e:
                        logger.warning(f"Exception during status check {i+1}: {e}")
                        continue
                
                if job_completed:
                    await self._record_test_result(test_name, True, {"final_status": final_status})
                    return True
                else:
                    await self._record_test_result(test_name, False, {
                        "error": f"Job did not complete in time. Final status: {final_status}"
                    })
                    return False
        except Exception as e:
            logger.error(f"Exception in job processing: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def _test_chunk_verification(self):
        """Test chunk verification in database."""
        test_name = "Chunk Verification"
        logger.info(f"🔍 Testing {test_name}")
        
        if not self.document_id:
            logger.error("No document ID available for chunk verification")
            await self._record_test_result(test_name, False, {"error": "No document ID"})
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                logger.info(f"Checking chunks for Document ID: {self.document_id}")
                async with session.get(f"{self.base_url}/documents/{self.document_id}/chunks", headers=headers) as response:
                    response_text = await response.text()
                    logger.info(f"Chunks response status: {response.status}")
                    logger.info(f"Chunks response body: {response_text}")
                    
                    if response.status == 200:
                        chunks_data = await response.json()
                        if chunks_data and len(chunks_data) > 0:
                            logger.info(f"Found {len(chunks_data)} chunks")
                            for i, chunk in enumerate(chunks_data[:3]):  # Log first 3 chunks
                                logger.info(f"Chunk {i+1}: {chunk.get('text', '')[:100]}...")
                            
                            await self._record_test_result(test_name, True, {
                                "chunk_count": len(chunks_data),
                                "first_chunk_preview": chunks_data[0].get("text", "")[:100] if chunks_data else ""
                            })
                            return True
                        else:
                            logger.error("No chunks found in response")
                            await self._record_test_result(test_name, False, {
                                "error": "No chunks found in database"
                            })
                            return False
                    else:
                        await self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": response_text
                        })
                        return False
        except Exception as e:
            logger.error(f"Exception in chunk verification: {e}")
            await self._record_test_result(test_name, False, {"error": str(e)})
            return False

    async def run_all_tests(self):
        """Run all tests in sequence."""
        logger.info("🚀 Starting Chunk Generation Test with Detailed Logging")
        logger.info(f"Using API: {self.base_url}")
        logger.info(f"Test user: {self.test_user_email}")
        
        # Test sequence
        tests = [
            self._test_user_creation,
            self._test_user_authentication,
            self._test_document_upload,
            self._test_job_processing,
            self._test_chunk_verification
        ]
        
        for test_func in tests:
            try:
                result = await test_func()
                if not result:
                    logger.error(f"Test {test_func.__name__} failed, stopping test sequence")
                    break
            except Exception as e:
                logger.error(f"Exception in test {test_func.__name__}: {e}")
                break
        
        # Generate report
        success_rate = (self.results["passed_tests"] / self.results["total_tests"]) * 100 if self.results["total_tests"] > 0 else 0
        self.results["success_rate"] = success_rate
        
        logger.info("=" * 60)
        logger.info("📊 CHUNK GENERATION TEST REPORT")
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
            logger.error("💥 CHUNK GENERATION TEST FAILED!")
            return False
        else:
            logger.info("🎉 CHUNK GENERATION TEST SUCCESSFUL!")
            return True

if __name__ == "__main__":
    # Use production API since local backend has environment issues
    api_base_url = "https://insurance-navigator-api.onrender.com"
    test_runner = ChunkGenerationTest(api_base_url)
    asyncio.run(test_runner.run_all_tests())
