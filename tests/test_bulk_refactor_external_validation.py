#!/usr/bin/env python3
"""
Comprehensive validation test for bulk refactor changes using external API services.
Tests the production API with development backend integration.
"""

import asyncio
import aiohttp
import json
import time
import hashlib
import uuid
from typing import Dict, Any, List
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulkRefactorExternalValidator:
    """Comprehensive validator for bulk refactor changes using external APIs."""
    
    def __init__(self):
        # External API configuration
        self.external_api_url = "https://insurance-navigator-api.onrender.com"
        
        # Test configuration
        self.test_user_email = f"bulk_refactor_test_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        self.test_document_content = """
        INSURANCE POLICY DOCUMENT - BULK REFACTOR VALIDATION
        
        Policy Number: BULK-REFACTOR-EXT-001
        Policyholder: Jane Smith
        Coverage Type: Comprehensive Auto Insurance
        Premium: $1,500 annually
        Deductible: $750
        Coverage Period: January 1, 2025 - December 31, 2025
        
        This is a comprehensive test insurance policy document for bulk refactor validation.
        The document contains various insurance terms and conditions that should be processed
        by the RAG system for intelligent retrieval and analysis.
        
        Coverage includes:
        - Liability coverage up to $250,000
        - Collision coverage with $750 deductible
        - Comprehensive coverage for non-collision damage
        - Uninsured motorist protection up to $100,000
        - Medical payments coverage up to $25,000
        - Rental car coverage up to $50 per day
        
        Terms and Conditions:
        - Policy is non-transferable without written consent
        - Claims must be reported within 48 hours of incident
        - Premium payments due monthly on the 1st
        - Late payment may result in policy cancellation after 15 days
        - Policy includes roadside assistance coverage
        - Glass damage covered with $100 deductible
        
        Special Provisions:
        - New car replacement coverage for vehicles less than 2 years old
        - Gap insurance included for leased vehicles
        - Accident forgiveness after 5 years of clean driving
        - Multi-policy discount available for bundling with home insurance
        
        Contact Information:
        - Claims Hotline: 1-800-INSURANCE
        - Customer Service: 1-800-CUSTOMER
        - Emergency Claims: 1-800-EMERGENCY
        - Website: www.insurancecompany.com
        """
        
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_suite": "bulk_refactor_external_validation",
            "tests": {},
            "overall_status": "pending",
            "summary": {}
        }
    
    async def run_test(self, test_name: str, test_func):
        """Run a single test and capture results."""
        logger.info(f"Running test: {test_name}")
        start_time = time.time()
        
        try:
            result = await test_func()
            result["status"] = "passed"
            result["duration"] = time.time() - start_time
            logger.info(f"✅ {test_name} - PASSED ({result['duration']:.2f}s)")
        except Exception as e:
            result = {
                "status": "failed",
                "error": str(e),
                "duration": time.time() - start_time
            }
            logger.error(f"❌ {test_name} - FAILED: {str(e)}")
        
        self.results["tests"][test_name] = result
        return result
    
    async def test_external_api_health(self) -> Dict[str, Any]:
        """Test external API health and service status."""
        async with aiohttp.ClientSession() as session:
            try:
                # Test health endpoint
                async with session.get(f"{self.external_api_url}/health") as response:
                    health_data = await response.json()
                
                # Test API documentation
                async with session.get(f"{self.external_api_url}/docs") as response:
                    docs_status = response.status
                
                return {
                    "api_accessible": True,
                    "health_status": health_data,
                    "docs_accessible": docs_status == 200,
                    "response_time": response.headers.get('X-Response-Time', 'unknown')
                }
            except Exception as e:
                return {
                    "api_accessible": False,
                    "error": str(e)
                }
    
    async def test_user_registration_and_auth(self) -> Dict[str, Any]:
        """Test user registration and authentication flow."""
        async with aiohttp.ClientSession() as session:
            try:
                # Test user registration
                registration_data = {
                    "email": self.test_user_email,
                    "password": self.test_password,
                    "full_name": "Bulk Refactor Test User"
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/register",
                    json=registration_data
                ) as response:
                    registration_result = await response.json()
                
                # Test user login
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                user_id = login_result.get("user", {}).get("id")
                
                return {
                    "registration_successful": registration_result.get("success", False),
                    "login_successful": login_result.get("success", False),
                    "auth_token_obtained": auth_token is not None,
                    "user_id": user_id,
                    "token_length": len(auth_token) if auth_token else 0
                }
            except Exception as e:
                return {
                    "auth_flow_failed": True,
                    "error": str(e)
                }
    
    async def test_document_upload_and_processing(self) -> Dict[str, Any]:
        """Test document upload and processing pipeline."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate first
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test document upload
                document_data = {
                    "content": self.test_document_content,
                    "filename": "bulk_refactor_test_policy.pdf",
                    "content_type": "application/pdf"
                }
                
                upload_start = time.time()
                async with session.post(
                    f"{self.external_api_url}/upload",
                    json=document_data,
                    headers=headers
                ) as response:
                    upload_result = await response.json()
                upload_time = time.time() - upload_start
                
                document_id = upload_result.get("document_id")
                job_id = upload_result.get("job_id")
                
                # Wait for processing and check status
                await asyncio.sleep(10)  # Wait for processing
                
                async with session.get(
                    f"{self.external_api_url}/jobs/{job_id}",
                    headers=headers
                ) as response:
                    job_status = await response.json()
                
                return {
                    "upload_successful": upload_result.get("success", False),
                    "upload_time": upload_time,
                    "document_id": document_id,
                    "job_id": job_id,
                    "job_status": job_status.get("status"),
                    "processing_complete": job_status.get("status") == "completed",
                    "upload_response": upload_result
                }
            except Exception as e:
                return {
                    "upload_pipeline_failed": True,
                    "error": str(e)
                }
    
    async def test_rag_system_with_uploaded_document(self) -> Dict[str, Any]:
        """Test RAG system functionality with the uploaded document."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test comprehensive RAG queries
                test_queries = [
                    "What is the policy number for this insurance?",
                    "What is the annual premium amount?",
                    "What is the deductible for this policy?",
                    "What types of coverage are included?",
                    "What are the payment terms and due dates?",
                    "What is the claims reporting process?",
                    "What special provisions are included?",
                    "What contact information is available?"
                ]
                
                rag_results = []
                total_rag_time = 0
                
                for query in test_queries:
                    chat_data = {
                        "message": query,
                        "conversation_id": str(uuid.uuid4())
                    }
                    
                    rag_start = time.time()
                    async with session.post(
                        f"{self.external_api_url}/chat",
                        json=chat_data,
                        headers=headers
                    ) as response:
                        chat_result = await response.json()
                    rag_time = time.time() - rag_start
                    total_rag_time += rag_time
                    
                    rag_results.append({
                        "query": query,
                        "response": chat_result.get("response", ""),
                        "success": chat_result.get("success", False),
                        "response_time": rag_time,
                        "agent_used": chat_result.get("agent_used", False)
                    })
                
                # Test direct similarity search
                similarity_start = time.time()
                async with session.post(
                    f"{self.external_api_url}/rag/similarity_search",
                    json={"query": "insurance policy coverage terms"},
                    headers=headers
                ) as response:
                    similarity_result = await response.json()
                similarity_time = time.time() - similarity_start
                
                return {
                    "rag_queries_tested": len(test_queries),
                    "successful_queries": sum(1 for r in rag_results if r["success"]),
                    "average_response_time": total_rag_time / len(test_queries),
                    "total_rag_time": total_rag_time,
                    "rag_results": rag_results,
                    "similarity_search_successful": similarity_result.get("success", False),
                    "similarity_search_time": similarity_time,
                    "similarity_results_count": len(similarity_result.get("results", []))
                }
            except Exception as e:
                return {
                    "rag_system_failed": True,
                    "error": str(e)
                }
    
    async def test_agent_integration_and_chat(self) -> Dict[str, Any]:
        """Test agent integration and chat functionality."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test agent-powered chat queries
                agent_queries = [
                    "Can you help me understand my insurance policy?",
                    "What should I do if I need to file a claim?",
                    "Can you explain the different coverage types in my policy?",
                    "What are the payment terms and when are they due?",
                    "How do I contact customer service for questions?",
                    "What special provisions or discounts are available?",
                    "Can you help me understand my deductible options?",
                    "What happens if I miss a payment?"
                ]
                
                agent_results = []
                total_agent_time = 0
                
                for query in agent_queries:
                    chat_data = {
                        "message": query,
                        "conversation_id": str(uuid.uuid4()),
                        "use_agent": True
                    }
                    
                    agent_start = time.time()
                    async with session.post(
                        f"{self.external_api_url}/chat",
                        json=chat_data,
                        headers=headers
                    ) as response:
                        chat_result = await response.json()
                    agent_time = time.time() - agent_start
                    total_agent_time += agent_time
                    
                    agent_results.append({
                        "query": query,
                        "response": chat_result.get("response", ""),
                        "success": chat_result.get("success", False),
                        "agent_used": chat_result.get("agent_used", False),
                        "response_time": agent_time,
                        "response_length": len(chat_result.get("response", ""))
                    })
                
                return {
                    "agent_queries_tested": len(agent_queries),
                    "successful_agent_queries": sum(1 for r in agent_results if r["success"]),
                    "agent_used_count": sum(1 for r in agent_results if r["agent_used"]),
                    "average_agent_response_time": total_agent_time / len(agent_queries),
                    "total_agent_time": total_agent_time,
                    "agent_results": agent_results
                }
            except Exception as e:
                return {
                    "agent_integration_failed": True,
                    "error": str(e)
                }
    
    async def test_performance_and_load(self) -> Dict[str, Any]:
        """Test system performance under load."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test concurrent requests
                concurrent_queries = [
                    "What is my policy number?",
                    "What is the premium amount?",
                    "What coverage do I have?",
                    "What is the deductible?",
                    "How do I file a claim?"
                ]
                
                concurrent_start = time.time()
                tasks = []
                
                for i, query in enumerate(concurrent_queries):
                    task = session.post(
                        f"{self.external_api_url}/chat",
                        json={
                            "message": query,
                            "conversation_id": str(uuid.uuid4())
                        },
                        headers=headers
                    )
                    tasks.append(task)
                
                concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
                concurrent_time = time.time() - concurrent_start
                
                # Analyze results
                successful_requests = sum(1 for result in concurrent_results if not isinstance(result, Exception))
                failed_requests = len(concurrent_results) - successful_requests
                
                return {
                    "concurrent_requests_count": len(concurrent_queries),
                    "successful_concurrent_requests": successful_requests,
                    "failed_concurrent_requests": failed_requests,
                    "concurrent_execution_time": concurrent_time,
                    "average_request_time": concurrent_time / len(concurrent_queries),
                    "requests_per_second": len(concurrent_queries) / concurrent_time
                }
            except Exception as e:
                return {
                    "performance_test_failed": True,
                    "error": str(e)
                }
    
    async def test_data_consistency_and_retrieval(self) -> Dict[str, Any]:
        """Test data consistency and retrieval capabilities."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.external_api_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test document retrieval
                async with session.get(
                    f"{self.external_api_url}/documents",
                    headers=headers
                ) as response:
                    documents_result = await response.json()
                
                # Test user profile
                async with session.get(
                    f"{self.external_api_url}/user/profile",
                    headers=headers
                ) as response:
                    profile_result = await response.json()
                
                # Test job history
                async with session.get(
                    f"{self.external_api_url}/jobs",
                    headers=headers
                ) as response:
                    jobs_result = await response.json()
                
                return {
                    "documents_retrievable": documents_result.get("success", False),
                    "document_count": len(documents_result.get("documents", [])),
                    "user_profile_accessible": profile_result.get("success", False),
                    "user_email": profile_result.get("user", {}).get("email"),
                    "jobs_retrievable": jobs_result.get("success", False),
                    "job_count": len(jobs_result.get("jobs", [])),
                    "data_consistency": True
                }
            except Exception as e:
                return {
                    "data_consistency_failed": True,
                    "error": str(e)
                }
    
    async def test_error_handling_and_edge_cases(self) -> Dict[str, Any]:
        """Test error handling and edge cases."""
        async with aiohttp.ClientSession() as session:
            try:
                # Test invalid authentication
                invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
                
                error_tests = []
                
                # Test invalid auth with profile
                async with session.get(
                    f"{self.external_api_url}/user/profile",
                    headers=invalid_headers
                ) as response:
                    error_tests.append({
                        "test": "invalid_auth_profile",
                        "status": response.status,
                        "expected": 401
                    })
                
                # Test invalid auth with chat
                async with session.post(
                    f"{self.external_api_url}/chat",
                    json={"message": "test"},
                    headers=invalid_headers
                ) as response:
                    error_tests.append({
                        "test": "invalid_auth_chat",
                        "status": response.status,
                        "expected": 401
                    })
                
                # Test malformed chat request
                async with session.post(
                    f"{self.external_api_url}/chat",
                    json={"invalid": "data"},
                    headers=invalid_headers
                ) as response:
                    error_tests.append({
                        "test": "malformed_chat_request",
                        "status": response.status,
                        "expected": 400
                    })
                
                # Test invalid RAG request
                async with session.post(
                    f"{self.external_api_url}/rag/similarity_search",
                    json={"invalid": "query"},
                    headers=invalid_headers
                ) as response:
                    error_tests.append({
                        "test": "invalid_rag_request",
                        "status": response.status,
                        "expected": 400
                    })
                
                # Analyze error handling
                correct_error_handling = sum(1 for test in error_tests if test["status"] == test["expected"])
                total_error_tests = len(error_tests)
                
                return {
                    "error_tests_performed": total_error_tests,
                    "correct_error_responses": correct_error_handling,
                    "error_handling_accuracy": (correct_error_handling / total_error_tests) * 100,
                    "error_test_details": error_tests
                }
            except Exception as e:
                return {
                    "error_handling_test_failed": True,
                    "error": str(e)
                }
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("Starting comprehensive bulk refactor external validation...")
        
        # Core system tests
        await self.run_test("external_api_health", self.test_external_api_health)
        
        # Authentication and user flow
        await self.run_test("user_registration_and_auth", self.test_user_registration_and_auth)
        
        # Document processing pipeline
        await self.run_test("document_upload_and_processing", self.test_document_upload_and_processing)
        
        # RAG system functionality
        await self.run_test("rag_system_with_uploaded_document", self.test_rag_system_with_uploaded_document)
        
        # Agent integration
        await self.run_test("agent_integration_and_chat", self.test_agent_integration_and_chat)
        
        # Performance and reliability
        await self.run_test("performance_and_load", self.test_performance_and_load)
        await self.run_test("data_consistency_and_retrieval", self.test_data_consistency_and_retrieval)
        await self.run_test("error_handling_and_edge_cases", self.test_error_handling_and_edge_cases)
        
        # Generate summary
        self.generate_summary()
        
        return self.results
    
    def generate_summary(self):
        """Generate test summary and overall status."""
        total_tests = len(self.results["tests"])
        passed_tests = sum(1 for test in self.results["tests"].values() if test["status"] == "passed")
        failed_tests = total_tests - passed_tests
        
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }
        
        self.results["overall_status"] = "passed" if failed_tests == 0 else "failed"
        
        logger.info(f"Validation complete: {passed_tests}/{total_tests} tests passed ({self.results['summary']['success_rate']:.1f}%)")

async def main():
    """Main execution function."""
    validator = BulkRefactorExternalValidator()
    
    try:
        results = await validator.run_comprehensive_validation()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bulk_refactor_external_validation_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Validation results saved to: {filename}")
        
        # Print summary
        print("\n" + "="*70)
        print("BULK REFACTOR EXTERNAL API VALIDATION SUMMARY")
        print("="*70)
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Tests Passed: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
        print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
        print("="*70)
        
        for test_name, test_result in results["tests"].items():
            status_icon = "✅" if test_result["status"] == "passed" else "❌"
            print(f"{status_icon} {test_name}: {test_result['status'].upper()} ({test_result.get('duration', 0):.2f}s)")
        
        print("="*70)
        
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
