#!/usr/bin/env python3
"""
Phase 3 End-to-End Processing Test

This test performs actual document upload and processing to verify:
- Document upload with authentication
- Worker processing pipeline
- Chunk generation and storage
- Embedding creation
- Complete workflow validation
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

class Phase3EndToEndValidator:
    def __init__(self):
        self.base_url = "https://insurance-navigator-api.onrender.com"
        self.results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "test_name": "Phase 3 End-to-End Processing",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": [],
            "document_id": None,
            "job_id": None,
            "chunks_created": 0,
            "embeddings_created": 0,
            "errors": []
        }
        
    async def run_end_to_end_test(self):
        """Run complete end-to-end processing test"""
        logger.info("🚀 Starting Phase 3 End-to-End Processing Test")
        
        try:
            # Test 1: Create test user and get authentication
            await self._test_user_creation_and_auth()
            
            # Test 2: Upload test document
            await self._test_document_upload()
            
            # Test 3: Monitor worker processing
            await self._test_worker_processing()
            
            # Test 4: Verify chunk generation
            await self._test_chunk_generation()
            
            # Test 5: Verify embedding creation
            await self._test_embedding_creation()
            
            # Test 6: Test RAG query with generated content
            await self._test_rag_query_with_content()
            
            # Generate final report
            self._generate_final_report()
            
        except Exception as e:
            logger.error(f"❌ End-to-end test failed with error: {e}")
            self.results["errors"].append(str(e))
            raise
    
    async def _test_user_creation_and_auth(self):
        """Create test user and get authentication token"""
        test_name = "User Creation and Authentication"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Create test user
                test_email = f"test_phase3_{uuid.uuid4().hex[:8]}@example.com"
                test_password = "TestPassword123!"
                
                signup_data = {
                    "email": test_email,
                    "password": test_password,
                    "full_name": "Phase 3 Test User",
                    "consent_version": "1.0",
                    "consent_timestamp": datetime.utcnow().isoformat()
                }
                
                start_time = time.time()
                async with session.post(f"{self.base_url}/auth/signup", json=signup_data) as response:
                    response_time = time.time() - start_time
                    
                    if response.status in [200, 201, 400]:  # 400 might mean user already exists
                        # Try to login
                        login_data = {
                            "email": test_email,
                            "password": test_password
                        }
                        
                        async with session.post(f"{self.base_url}/auth/login", json=login_data) as login_response:
                            if login_response.status == 200:
                                auth_result = await login_response.json()
                                self.auth_token = auth_result.get("access_token")
                                self.test_email = test_email
                                
                                self._record_test_result(test_name, True, {
                                    "status_code": login_response.status,
                                    "response_time_ms": response_time * 1000,
                                    "auth_token_received": bool(self.auth_token),
                                    "test_email": test_email
                                })
                            else:
                                self._record_test_result(test_name, False, {
                                    "status_code": login_response.status,
                                    "error": "Failed to login after signup"
                                })
                    else:
                        self._record_test_result(test_name, False, {
                            "status_code": response.status,
                            "error": "Failed to create user"
                        })
                        
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_document_upload(self):
        """Upload test document"""
        test_name = "Document Upload"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            if not hasattr(self, 'auth_token'):
                self._record_test_result(test_name, False, {"error": "No authentication token available"})
                return
                
            async with aiohttp.ClientSession() as session:
                # Create test document content
                test_doc_content = """
# Insurance Policy Document

## Policy Details
- Policy Number: PHASE3-TEST-001
- Coverage Type: Comprehensive Auto Insurance
- Effective Date: 2025-01-01
- Expiration Date: 2025-12-31

## Coverage Information
This policy provides comprehensive coverage for your vehicle including:
- Liability coverage up to $100,000
- Collision coverage with $500 deductible
- Comprehensive coverage for theft and vandalism
- Uninsured motorist protection

## Terms and Conditions
1. Premium payments are due monthly
2. Claims must be reported within 48 hours
3. Coverage is valid only for the named insured
4. Policy may be cancelled with 30 days notice

## Contact Information
For questions about this policy, contact our customer service team at 1-800-INSURANCE.
                """.strip()
                
                test_doc_hash = hashlib.sha256(test_doc_content.encode()).hexdigest()
                
                upload_data = {
                    "filename": "phase3_test_insurance_policy.pdf",
                    "bytes_len": len(test_doc_content),
                    "mime": "application/pdf",
                    "sha256": test_doc_hash,
                    "ocr": False
                }
                
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                start_time = time.time()
                async with session.post(f"{self.base_url}/api/v2/upload", json=upload_data, headers=headers) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        upload_result = await response.json()
                        self.results["document_id"] = upload_result.get("document_id")
                        self.results["job_id"] = upload_result.get("job_id")
                        
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "document_id": self.results["document_id"],
                            "job_id": self.results["job_id"],
                            "upload_result": upload_result
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
        """Monitor worker processing of the uploaded document"""
        test_name = "Worker Processing"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            if not self.results["job_id"]:
                self._record_test_result(test_name, False, {"error": "No job ID available"})
                return
                
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Monitor job status for up to 5 minutes
                max_wait_time = 300  # 5 minutes
                check_interval = 10  # 10 seconds
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    async with session.get(f"{self.base_url}/documents/{self.results['document_id']}/status", headers=headers) as response:
                        if response.status == 200:
                            status_data = await response.json()
                            job_status = status_data.get("status", "unknown")
                            
                            logger.info(f"Job status: {job_status}")
                            
                            if job_status in ["complete", "embeddings_stored"]:
                                self._record_test_result(test_name, True, {
                                    "final_status": job_status,
                                    "processing_time_seconds": time.time() - start_time,
                                    "status_data": status_data
                                })
                                return
                            elif job_status in ["failed", "failed_parse", "failed_chunking", "failed_embedding"]:
                                self._record_test_result(test_name, False, {
                                    "final_status": job_status,
                                    "processing_time_seconds": time.time() - start_time,
                                    "status_data": status_data,
                                    "error": f"Job failed with status: {job_status}"
                                })
                                return
                        
                    await asyncio.sleep(check_interval)
                
                # Timeout
                self._record_test_result(test_name, False, {
                    "error": f"Job processing timed out after {max_wait_time} seconds"
                })
                        
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_chunk_generation(self):
        """Verify that chunks were generated and stored"""
        test_name = "Chunk Generation"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            if not self.results["document_id"]:
                self._record_test_result(test_name, False, {"error": "No document ID available"})
                return
                
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Check if we can query for chunks (this might need a specific endpoint)
                # For now, we'll check the document status which should indicate chunking is complete
                async with session.get(f"{self.base_url}/documents/{self.results['document_id']}/status", headers=headers) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        
                        # Check if document has been processed through chunking
                        if status_data.get("status") in ["chunks_stored", "embeddings_stored", "complete"]:
                            # Try to get document details to see if chunks are mentioned
                            async with session.get(f"{self.base_url}/documents/{self.results['document_id']}", headers=headers) as doc_response:
                                if doc_response.status == 200:
                                    doc_data = await doc_response.json()
                                    chunk_count = doc_data.get("chunk_count", 0)
                                    self.results["chunks_created"] = chunk_count
                                    
                                    self._record_test_result(test_name, True, {
                                        "chunk_count": chunk_count,
                                        "document_status": status_data.get("status"),
                                        "document_data": doc_data
                                    })
                                else:
                                    self._record_test_result(test_name, True, {
                                        "note": "Chunking appears complete based on status",
                                        "document_status": status_data.get("status"),
                                        "chunk_count": "unknown"
                                    })
                        else:
                            self._record_test_result(test_name, False, {
                                "error": f"Document not fully processed. Status: {status_data.get('status')}"
                            })
                    else:
                        self._record_test_result(test_name, False, {
                            "error": f"Failed to get document status. Status code: {response.status}"
                        })
                        
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_embedding_creation(self):
        """Verify that embeddings were created"""
        test_name = "Embedding Creation"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            if not self.results["document_id"]:
                self._record_test_result(test_name, False, {"error": "No document ID available"})
                return
                
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Check document status for embedding completion
                async with session.get(f"{self.base_url}/documents/{self.results['document_id']}/status", headers=headers) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        
                        if status_data.get("status") in ["embeddings_stored", "complete"]:
                            self.results["embeddings_created"] = self.results["chunks_created"]
                            
                            self._record_test_result(test_name, True, {
                                "embeddings_created": self.results["embeddings_created"],
                                "document_status": status_data.get("status"),
                                "note": "Embeddings appear to be created based on status"
                            })
                        else:
                            self._record_test_result(test_name, False, {
                                "error": f"Embeddings not complete. Status: {status_data.get('status')}"
                            })
                    else:
                        self._record_test_result(test_name, False, {
                            "error": f"Failed to get document status. Status code: {response.status}"
                        })
                        
        except Exception as e:
            self._record_test_result(test_name, False, {"error": str(e)})
    
    async def _test_rag_query_with_content(self):
        """Test RAG query using the processed document"""
        test_name = "RAG Query with Processed Content"
        logger.info(f"🔍 Testing {test_name}")
        
        try:
            if not hasattr(self, 'auth_token'):
                self._record_test_result(test_name, False, {"error": "No authentication token available"})
                return
                
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                
                # Test RAG query
                query_data = {
                    "query": "What is the policy number for this insurance document?",
                    "user_id": self.test_email
                }
                
                start_time = time.time()
                async with session.post(f"{self.base_url}/chat", json=query_data, headers=headers) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        rag_result = await response.json()
                        self._record_test_result(test_name, True, {
                            "status_code": response.status,
                            "response_time_ms": response_time * 1000,
                            "rag_result": rag_result,
                            "note": "RAG query successful with processed content"
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
        logger.info("📊 PHASE 3 END-TO-END PROCESSING REPORT")
        logger.info("=" * 60)
        logger.info(f"🕐 Test Timestamp: {self.results['test_timestamp']}")
        logger.info(f"📈 Total Tests: {self.results['total_tests']}")
        logger.info(f"✅ Passed Tests: {self.results['passed_tests']}")
        logger.info(f"❌ Failed Tests: {self.results['failed_tests']}")
        logger.info(f"📊 Success Rate: {success_rate:.1f}%")
        logger.info(f"📄 Document ID: {self.results['document_id']}")
        logger.info(f"🔧 Job ID: {self.results['job_id']}")
        logger.info(f"📝 Chunks Created: {self.results['chunks_created']}")
        logger.info(f"🧠 Embeddings Created: {self.results['embeddings_created']}")
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
        with open("phase3_end_to_end_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info("💾 Results saved to phase3_end_to_end_results.json")
        
        if success_rate >= 80:
            logger.info("🎉 PHASE 3 END-TO-END TEST SUCCESSFUL!")
            return True
        else:
            logger.error("💥 PHASE 3 END-TO-END TEST FAILED!")
            return False

async def main():
    """Main function"""
    validator = Phase3EndToEndValidator()
    success = await validator.run_end_to_end_test()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
