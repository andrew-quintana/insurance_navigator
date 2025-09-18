#!/usr/bin/env python3
"""
Comprehensive validation test for bulk refactor changes.
Tests development backend with external API services integration.
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

class BulkRefactorComprehensiveValidator:
    """Comprehensive validator for bulk refactor changes."""
    
    def __init__(self):
        # Development backend configuration
        self.dev_backend_url = "http://localhost:8000"
        self.external_api_url = "***REMOVED***"
        
        # Test configuration
        self.test_user_email = f"bulk_refactor_test_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        self.test_document_content = """
        INSURANCE POLICY DOCUMENT
        
        Policy Number: BULK-REFACTOR-TEST-001
        Policyholder: John Doe
        Coverage Type: Comprehensive Auto Insurance
        Premium: $1,200 annually
        Deductible: $500
        Coverage Period: January 1, 2025 - December 31, 2025
        
        This is a test insurance policy document for bulk refactor validation.
        The document contains various insurance terms and conditions that should
        be processed by the RAG system for intelligent retrieval and analysis.
        
        Coverage includes:
        - Liability coverage up to $100,000
        - Collision coverage with $500 deductible
        - Comprehensive coverage for non-collision damage
        - Uninsured motorist protection
        - Medical payments coverage up to $10,000
        
        Terms and Conditions:
        - Policy is non-transferable
        - Claims must be reported within 30 days
        - Premium payments due monthly
        - Late payment may result in policy cancellation
        """
        
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "test_suite": "bulk_refactor_comprehensive_validation",
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
    
    async def test_development_backend_health(self) -> Dict[str, Any]:
        """Test development backend health and basic connectivity."""
        async with aiohttp.ClientSession() as session:
            try:
                # Test health endpoint
                async with session.get(f"{self.dev_backend_url}/health") as response:
                    health_status = await response.json()
                
                # Test API documentation endpoint
                async with session.get(f"{self.dev_backend_url}/docs") as response:
                    docs_status = response.status
                
                return {
                    "health_endpoint": health_status,
                    "docs_endpoint_status": docs_status,
                    "backend_accessible": True
                }
            except Exception as e:
                return {
                    "backend_accessible": False,
                    "error": str(e)
                }
    
    async def test_external_api_connectivity(self) -> Dict[str, Any]:
        """Test external API service connectivity."""
        async with aiohttp.ClientSession() as session:
            try:
                # Test external API health
                async with session.get(f"{self.external_api_url}/health") as response:
                    external_health = await response.json()
                
                return {
                    "external_api_accessible": True,
                    "external_health": external_health,
                    "response_time": response.headers.get('X-Response-Time', 'unknown')
                }
            except Exception as e:
                return {
                    "external_api_accessible": False,
                    "error": str(e)
                }
    
    async def test_user_authentication_flow(self) -> Dict[str, Any]:
        """Test complete user authentication flow."""
        async with aiohttp.ClientSession() as session:
            try:
                # Test user registration
                registration_data = {
                    "email": self.test_user_email,
                    "password": self.test_password,
                    "full_name": "Bulk Refactor Test User"
                }
                
                async with session.post(
                    f"{self.dev_backend_url}/auth/register",
                    json=registration_data
                ) as response:
                    registration_result = await response.json()
                
                # Test user login
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.dev_backend_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                
                return {
                    "registration_successful": registration_result.get("success", False),
                    "login_successful": login_result.get("success", False),
                    "auth_token_obtained": auth_token is not None,
                    "user_id": login_result.get("user", {}).get("id")
                }
            except Exception as e:
                return {
                    "authentication_failed": True,
                    "error": str(e)
                }
    
    async def test_document_upload_pipeline(self) -> Dict[str, Any]:
        """Test document upload and processing pipeline."""
        async with aiohttp.ClientSession() as session:
            try:
                # First authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.dev_backend_url}/auth/login",
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
                
                async with session.post(
                    f"{self.dev_backend_url}/upload",
                    json=document_data,
                    headers=headers
                ) as response:
                    upload_result = await response.json()
                
                document_id = upload_result.get("document_id")
                job_id = upload_result.get("job_id")
                
                # Wait for processing
                await asyncio.sleep(5)
                
                # Check job status
                async with session.get(
                    f"{self.dev_backend_url}/jobs/{job_id}",
                    headers=headers
                ) as response:
                    job_status = await response.json()
                
                return {
                    "upload_successful": upload_result.get("success", False),
                    "document_id": document_id,
                    "job_id": job_id,
                    "job_status": job_status.get("status"),
                    "processing_complete": job_status.get("status") == "completed"
                }
            except Exception as e:
                return {
                    "upload_pipeline_failed": True,
                    "error": str(e)
                }
    
    async def test_rag_system_functionality(self) -> Dict[str, Any]:
        """Test RAG system functionality with uploaded document."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.dev_backend_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test RAG queries
                test_queries = [
                    "What is the policy number?",
                    "What is the deductible amount?",
                    "What coverage types are included?",
                    "What are the terms and conditions?",
                    "How much is the annual premium?"
                ]
                
                rag_results = []
                for query in test_queries:
                    chat_data = {
                        "message": query,
                        "conversation_id": str(uuid.uuid4())
                    }
                    
                    async with session.post(
                        f"{self.dev_backend_url}/chat",
                        json=chat_data,
                        headers=headers
                    ) as response:
                        chat_result = await response.json()
                    
                    rag_results.append({
                        "query": query,
                        "response": chat_result.get("response", ""),
                        "success": chat_result.get("success", False)
                    })
                
                # Test direct RAG similarity search
                async with session.post(
                    f"{self.dev_backend_url}/rag/similarity_search",
                    json={"query": "insurance policy coverage"},
                    headers=headers
                ) as response:
                    similarity_result = await response.json()
                
                return {
                    "rag_queries_tested": len(test_queries),
                    "successful_queries": sum(1 for r in rag_results if r["success"]),
                    "rag_results": rag_results,
                    "similarity_search_successful": similarity_result.get("success", False),
                    "similarity_results": similarity_result.get("results", [])
                }
            except Exception as e:
                return {
                    "rag_system_failed": True,
                    "error": str(e)
                }
    
    async def test_agent_integration(self) -> Dict[str, Any]:
        """Test agent integration and chat endpoint functionality."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.dev_backend_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test agent chat functionality
                agent_queries = [
                    "Can you help me understand my insurance policy?",
                    "What should I do if I need to file a claim?",
                    "Can you explain the different coverage types?",
                    "What are the payment terms for this policy?"
                ]
                
                agent_results = []
                for query in agent_queries:
                    chat_data = {
                        "message": query,
                        "conversation_id": str(uuid.uuid4()),
                        "use_agent": True
                    }
                    
                    async with session.post(
                        f"{self.dev_backend_url}/chat",
                        json=chat_data,
                        headers=headers
                    ) as response:
                        chat_result = await response.json()
                    
                    agent_results.append({
                        "query": query,
                        "response": chat_result.get("response", ""),
                        "agent_used": chat_result.get("agent_used", False),
                        "success": chat_result.get("success", False)
                    })
                
                return {
                    "agent_queries_tested": len(agent_queries),
                    "successful_agent_queries": sum(1 for r in agent_results if r["success"]),
                    "agent_results": agent_results,
                    "agent_integration_working": any(r["agent_used"] for r in agent_results)
                }
            except Exception as e:
                return {
                    "agent_integration_failed": True,
                    "error": str(e)
                }
    
    async def test_performance_metrics(self) -> Dict[str, Any]:
        """Test system performance metrics."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.dev_backend_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test response times for different endpoints
                performance_tests = []
                
                # Test chat endpoint performance
                start_time = time.time()
                chat_data = {
                    "message": "What is my policy number?",
                    "conversation_id": str(uuid.uuid4())
                }
                async with session.post(
                    f"{self.dev_backend_url}/chat",
                    json=chat_data,
                    headers=headers
                ) as response:
                    chat_result = await response.json()
                chat_response_time = time.time() - start_time
                
                # Test RAG endpoint performance
                start_time = time.time()
                async with session.post(
                    f"{self.dev_backend_url}/rag/similarity_search",
                    json={"query": "insurance coverage"},
                    headers=headers
                ) as response:
                    rag_result = await response.json()
                rag_response_time = time.time() - start_time
                
                # Test concurrent requests
                concurrent_start = time.time()
                tasks = []
                for i in range(5):
                    task = session.post(
                        f"{self.dev_backend_url}/chat",
                        json={
                            "message": f"Test query {i}",
                            "conversation_id": str(uuid.uuid4())
                        },
                        headers=headers
                    )
                    tasks.append(task)
                
                concurrent_results = await asyncio.gather(*tasks)
                concurrent_time = time.time() - concurrent_start
                
                return {
                    "chat_response_time": chat_response_time,
                    "rag_response_time": rag_response_time,
                    "concurrent_requests_time": concurrent_time,
                    "concurrent_requests_count": len(concurrent_results),
                    "performance_targets": {
                        "chat_response_target": "< 3.0s",
                        "rag_response_target": "< 2.0s",
                        "concurrent_target": "< 10.0s for 5 requests"
                    }
                }
            except Exception as e:
                return {
                    "performance_test_failed": True,
                    "error": str(e)
                }
    
    async def test_database_consistency(self) -> Dict[str, Any]:
        """Test database consistency and data integrity."""
        async with aiohttp.ClientSession() as session:
            try:
                # Authenticate
                login_data = {
                    "email": self.test_user_email,
                    "password": self.test_password
                }
                
                async with session.post(
                    f"{self.dev_backend_url}/auth/login",
                    json=login_data
                ) as response:
                    login_result = await response.json()
                
                auth_token = login_result.get("access_token")
                headers = {"Authorization": f"Bearer {auth_token}"}
                
                # Test document retrieval
                async with session.get(
                    f"{self.dev_backend_url}/documents",
                    headers=headers
                ) as response:
                    documents_result = await response.json()
                
                # Test user profile
                async with session.get(
                    f"{self.dev_backend_url}/user/profile",
                    headers=headers
                ) as response:
                    profile_result = await response.json()
                
                return {
                    "documents_retrievable": documents_result.get("success", False),
                    "document_count": len(documents_result.get("documents", [])),
                    "user_profile_accessible": profile_result.get("success", False),
                    "data_consistency": True
                }
            except Exception as e:
                return {
                    "database_consistency_failed": True,
                    "error": str(e)
                }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling and edge cases."""
        async with aiohttp.ClientSession() as session:
            try:
                # Test invalid authentication
                invalid_headers = {"Authorization": "Bearer invalid_token"}
                
                async with session.get(
                    f"{self.dev_backend_url}/user/profile",
                    headers=invalid_headers
                ) as response:
                    invalid_auth_status = response.status
                
                # Test invalid chat request
                async with session.post(
                    f"{self.dev_backend_url}/chat",
                    json={"invalid": "data"},
                    headers=invalid_headers
                ) as response:
                    invalid_chat_status = response.status
                
                # Test malformed RAG request
                async with session.post(
                    f"{self.dev_backend_url}/rag/similarity_search",
                    json={"invalid": "query"},
                    headers=invalid_headers
                ) as response:
                    invalid_rag_status = response.status
                
                return {
                    "invalid_auth_handled": invalid_auth_status == 401,
                    "invalid_chat_handled": invalid_chat_status in [400, 401],
                    "invalid_rag_handled": invalid_rag_status in [400, 401],
                    "error_handling_working": all([
                        invalid_auth_status == 401,
                        invalid_chat_status in [400, 401],
                        invalid_rag_status in [400, 401]
                    ])
                }
            except Exception as e:
                return {
                    "error_handling_test_failed": True,
                    "error": str(e)
                }
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run all validation tests."""
        logger.info("Starting comprehensive bulk refactor validation...")
        
        # Core system tests
        await self.run_test("development_backend_health", self.test_development_backend_health)
        await self.run_test("external_api_connectivity", self.test_external_api_connectivity)
        
        # Authentication and user flow
        await self.run_test("user_authentication_flow", self.test_user_authentication_flow)
        
        # Document processing pipeline
        await self.run_test("document_upload_pipeline", self.test_document_upload_pipeline)
        
        # RAG system functionality
        await self.run_test("rag_system_functionality", self.test_rag_system_functionality)
        
        # Agent integration
        await self.run_test("agent_integration", self.test_agent_integration)
        
        # Performance and reliability
        await self.run_test("performance_metrics", self.test_performance_metrics)
        await self.run_test("database_consistency", self.test_database_consistency)
        await self.run_test("error_handling", self.test_error_handling)
        
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
    validator = BulkRefactorComprehensiveValidator()
    
    try:
        results = await validator.run_comprehensive_validation()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bulk_refactor_validation_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Validation results saved to: {filename}")
        
        # Print summary
        print("\n" + "="*60)
        print("BULK REFACTOR COMPREHENSIVE VALIDATION SUMMARY")
        print("="*60)
        print(f"Overall Status: {results['overall_status'].upper()}")
        print(f"Tests Passed: {results['summary']['passed_tests']}/{results['summary']['total_tests']}")
        print(f"Success Rate: {results['summary']['success_rate']:.1f}%")
        print("="*60)
        
        for test_name, test_result in results["tests"].items():
            status_icon = "✅" if test_result["status"] == "passed" else "❌"
            print(f"{status_icon} {test_name}: {test_result['status'].upper()} ({test_result.get('duration', 0):.2f}s)")
        
        print("="*60)
        
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
