#!/usr/bin/env python3
"""
Phase 3 Upload Pipeline Integration Test
Test upload pipeline integration with RAG system in cloud deployment
"""

import asyncio
import aiohttp
import json
import time
import uuid
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Phase3UploadPipelineIntegrationTest:
    """Test upload pipeline integration with RAG system in cloud deployment."""
    
    def __init__(self):
        self.base_url = "***REMOVED***"
        self.test_user_id = str(uuid.uuid4())
        self.test_email = f"test_user_{int(time.time())}@example.com"
        self.test_password = "test_password_123"
        self.auth_token = None
        self.upload_job_id = None
        self.results = {
            "test_name": "Phase 3 Upload Pipeline Integration Test",
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
    
    async def test_cloud_api_availability(self) -> Dict[str, Any]:
        """Test if cloud API is available."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return {"status": "available", "response_time": response.headers.get("X-Response-Time", "unknown")}
                else:
                    raise Exception(f"API not available: {response.status}")
    
    async def test_user_registration(self) -> Dict[str, Any]:
        """Test user registration for upload pipeline."""
        async with aiohttp.ClientSession() as session:
            registration_data = {
                "email": self.test_email,
                "password": self.test_password,
                "user_id": self.test_user_id
            }
            
            async with session.post(f"{self.base_url}/register", json=registration_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return {"user_id": result.get("user_id"), "email": self.test_email}
                else:
                    raise Exception(f"Registration failed: {response.status}")
    
    async def test_user_authentication(self) -> Dict[str, Any]:
        """Test user authentication for upload pipeline."""
        async with aiohttp.ClientSession() as session:
            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            async with session.post(f"{self.base_url}/login", json=login_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.auth_token = result.get("access_token")
                    return {"authenticated": True, "token_available": self.auth_token is not None}
                else:
                    raise Exception(f"Authentication failed: {response.status}")
    
    async def test_upload_endpoint_availability(self) -> Dict[str, Any]:
        """Test if upload endpoint is available."""
        if not self.auth_token:
            raise Exception("No authentication token available")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with aiohttp.ClientSession() as session:
            # Test with GET to check if endpoint exists
            async with session.get(f"{self.base_url}/api/upload-pipeline/upload", headers=headers) as response:
                if response.status == 405:  # Method Not Allowed is expected for GET
                    return {"endpoint_available": True, "method_supported": "POST"}
                elif response.status == 200:
                    return {"endpoint_available": True, "method_supported": "GET"}
                else:
                    raise Exception(f"Upload endpoint not available: {response.status}")
    
    async def test_document_upload(self) -> Dict[str, Any]:
        """Test document upload functionality."""
        if not self.auth_token:
            raise Exception("No authentication token available")
        
        # Create a test document content
        test_document_content = """
        Insurance Policy Document
        
        Policy Number: TEST-12345
        Policyholder: Test User
        Coverage Type: Health Insurance
        Premium: $500/month
        Deductible: $1000
        Coverage Period: 2024-2025
        
        This is a test insurance document for Phase 3 upload pipeline testing.
        The document contains sample insurance information for testing purposes.
        """
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Create form data for file upload
        form_data = aiohttp.FormData()
        form_data.add_field('file', test_document_content.encode(), filename='test_insurance_document.txt', content_type='text/plain')
        form_data.add_field('user_id', self.test_user_id)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/upload-pipeline/upload", data=form_data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    self.upload_job_id = result.get("job_id")
                    return {
                        "upload_successful": True,
                        "job_id": self.upload_job_id,
                        "document_id": result.get("document_id")
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Upload failed: {response.status} - {error_text}")
    
    async def test_job_status_tracking(self) -> Dict[str, Any]:
        """Test job status tracking."""
        if not self.upload_job_id:
            raise Exception("No upload job ID available")
        
        if not self.auth_token:
            raise Exception("No authentication token available")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/v2/jobs/{self.upload_job_id}", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "job_status_available": True,
                        "job_id": self.upload_job_id,
                        "status": result.get("status"),
                        "stage": result.get("stage")
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Job status check failed: {response.status} - {error_text}")
    
    async def test_rag_integration_with_uploaded_document(self) -> Dict[str, Any]:
        """Test RAG integration with uploaded document."""
        if not self.auth_token:
            raise Exception("No authentication token available")
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test queries related to the uploaded document
        test_queries = [
            "What is the policy number?",
            "What is the coverage type?",
            "What is the premium amount?",
            "What is the deductible?"
        ]
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for query in test_queries:
                chat_data = {
                    "message": query,
                    "user_id": self.test_user_id
                }
                
                async with session.post(f"{self.base_url}/chat", json=chat_data, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result.get("response", "")
                        
                        # Check if response contains relevant information
                        relevant_info = any(keyword in response_text.lower() for keyword in [
                            "test-12345", "health insurance", "500", "1000", "policy"
                        ])
                        
                        results.append({
                            "query": query,
                            "response_received": True,
                            "response_length": len(response_text),
                            "relevant_info_found": relevant_info,
                            "response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text
                        })
                    else:
                        results.append({
                            "query": query,
                            "response_received": False,
                            "error": f"HTTP {response.status}"
                        })
        
        return {
            "queries_tested": len(test_queries),
            "successful_responses": len([r for r in results if r.get("response_received")]),
            "relevant_responses": len([r for r in results if r.get("relevant_info_found")]),
            "query_results": results
        }
    
    async def test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow."""
        workflow_steps = [
            "API Availability",
            "User Registration", 
            "User Authentication",
            "Upload Endpoint Availability",
            "Document Upload",
            "Job Status Tracking",
            "RAG Integration"
        ]
        
        completed_steps = []
        failed_steps = []
        
        # Check which steps were completed successfully
        for step in workflow_steps:
            step_key = step.lower().replace(" ", "_")
            if step_key in self.results["tests"]:
                if self.results["tests"][step_key]["status"] == "PASSED":
                    completed_steps.append(step)
                else:
                    failed_steps.append(step)
        
        return {
            "workflow_complete": len(failed_steps) == 0,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "completion_rate": len(completed_steps) / len(workflow_steps) * 100
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive upload pipeline integration test."""
        logger.info("🚀 Starting Phase 3 Upload Pipeline Integration Test")
        logger.info("=" * 60)
        
        # Run all tests
        test_functions = [
            ("API Availability", self.test_cloud_api_availability),
            ("User Registration", self.test_user_registration),
            ("User Authentication", self.test_user_authentication),
            ("Upload Endpoint Availability", self.test_upload_endpoint_availability),
            ("Document Upload", self.test_document_upload),
            ("Job Status Tracking", self.test_job_status_tracking),
            ("RAG Integration", self.test_rag_integration_with_uploaded_document),
            ("End-to-End Workflow", self.test_end_to_end_workflow)
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
        logger.info("📊 PHASE 3 UPLOAD PIPELINE INTEGRATION TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {self.results['summary']['overall_status']}")
        logger.info(f"Total Time: {time.time() - self.results['timestamp']:.2f} seconds")
        logger.info(f"Test User ID: {self.test_user_id}")
        logger.info(f"Test Email: {self.test_email}")
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
            logger.info("🎉 Phase 3 Upload Pipeline Integration Test PASSED!")
        else:
            logger.info("❌ Phase 3 Upload Pipeline Integration Test FAILED!")
        
        # Save results
        results_file = f"phase3_upload_pipeline_integration_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"📁 Results saved to: {results_file}")
        
        return self.results

async def main():
    """Main function to run the test."""
    test = Phase3UploadPipelineIntegrationTest()
    await test.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main())
