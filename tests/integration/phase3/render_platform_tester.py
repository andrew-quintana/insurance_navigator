#!/usr/bin/env python3
"""
Render Platform Testing Module
Specialized testing for Render Web Services and Workers
"""

import asyncio
import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger("render_tester")

class RenderWebServiceTester:
    """Test Render Web Service API endpoints and functionality."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.base_url = self._get_render_url()
        self.session = requests.Session()
        self.session.timeout = 30
        self.results = []
        
    def _get_render_url(self) -> str:
        """Get Render URL based on environment."""
        if self.environment == "production":
            return "https://insurance-navigator-api.onrender.com"
        elif self.environment == "staging":
            return "https://insurance-navigator-api-staging.onrender.com"
        else:  # development
            return "http://localhost:8000"
    
    async def test_fastapi_startup(self) -> Dict[str, Any]:
        """Test FastAPI application startup and initialization."""
        result = {
            "test_name": "fastapi_startup",
            "platform": "render",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Test basic connectivity
            response = self.session.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                result.update({
                    "status": "passed",
                    "details": f"FastAPI application responding: {response.status_code}",
                    "response_time_ms": response.elapsed.total_seconds() * 1000
                })
            else:
                result.update({
                    "status": "failed",
                    "details": f"FastAPI startup failed: {response.status_code}",
                    "error": response.text[:200]
                })
                
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"FastAPI startup error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_health_endpoints(self) -> Dict[str, Any]:
        """Test health check endpoints."""
        result = {
            "test_name": "health_endpoints",
            "platform": "render",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            health_tests = []
            
            # Test /health endpoint
            health_response = self.session.get(f"{self.base_url}/health", timeout=10)
            health_tests.append({
                "endpoint": "/health",
                "status_code": health_response.status_code,
                "response_time_ms": health_response.elapsed.total_seconds() * 1000,
                "success": health_response.status_code == 200
            })
            
            # Test /status endpoint
            status_response = self.session.get(f"{self.base_url}/status", timeout=10)
            health_tests.append({
                "endpoint": "/status",
                "status_code": status_response.status_code,
                "response_time_ms": status_response.elapsed.total_seconds() * 1000,
                "success": status_response.status_code == 200
            })
            
            # Test /ready endpoint (if exists)
            try:
                ready_response = self.session.get(f"{self.base_url}/ready", timeout=10)
                health_tests.append({
                    "endpoint": "/ready",
                    "status_code": ready_response.status_code,
                    "response_time_ms": ready_response.elapsed.total_seconds() * 1000,
                    "success": ready_response.status_code == 200
                })
            except:
                health_tests.append({
                    "endpoint": "/ready",
                    "status_code": "not_found",
                    "response_time_ms": 0,
                    "success": True  # Not required
                })
            
            passed_tests = sum(1 for test in health_tests if test["success"])
            total_tests = len(health_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Health endpoints: {passed_tests}/{total_tests} passed",
                "test_results": health_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Health endpoints error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_authentication_flow(self) -> Dict[str, Any]:
        """Test authentication endpoints and flows."""
        result = {
            "test_name": "authentication_flow",
            "platform": "render",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            auth_tests = []
            
            # Test login endpoint
            login_data = {
                "email": "test@example.com",
                "password": "testpassword"
            }
            login_response = self.session.post(f"{self.base_url}/auth/login", json=login_data, timeout=10)
            auth_tests.append({
                "endpoint": "POST /auth/login",
                "status_code": login_response.status_code,
                "success": login_response.status_code in [200, 401, 422],  # 401/422 expected for invalid credentials
                "response_time_ms": login_response.elapsed.total_seconds() * 1000
            })
            
            # Test registration endpoint
            register_data = {
                "email": "newuser@example.com",
                "password": "newpassword",
                "full_name": "Test User"
            }
            register_response = self.session.post(f"{self.base_url}/auth/register", json=register_data, timeout=10)
            auth_tests.append({
                "endpoint": "POST /auth/register",
                "status_code": register_response.status_code,
                "success": register_response.status_code in [200, 201, 400, 409, 422],
                "response_time_ms": register_response.elapsed.total_seconds() * 1000
            })
            
            # Test refresh token endpoint
            refresh_response = self.session.post(f"{self.base_url}/auth/refresh", json={}, timeout=10)
            auth_tests.append({
                "endpoint": "POST /auth/refresh",
                "status_code": refresh_response.status_code,
                "success": refresh_response.status_code in [200, 401, 422],
                "response_time_ms": refresh_response.elapsed.total_seconds() * 1000
            })
            
            passed_tests = sum(1 for test in auth_tests if test["success"])
            total_tests = len(auth_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Authentication flow: {passed_tests}/{total_tests} endpoints accessible",
                "test_results": auth_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Authentication flow error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_document_processing(self) -> Dict[str, Any]:
        """Test document upload and processing endpoints."""
        result = {
            "test_name": "document_processing",
            "platform": "render",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            doc_tests = []
            
            # Test document upload
            files = {'file': ('test.pdf', b'fake pdf content', 'application/pdf')}
            upload_response = self.session.post(f"{self.base_url}/documents/upload", files=files, timeout=30)
            doc_tests.append({
                "endpoint": "POST /documents/upload",
                "status_code": upload_response.status_code,
                "success": upload_response.status_code in [200, 201, 401, 422],
                "response_time_ms": upload_response.elapsed.total_seconds() * 1000
            })
            
            # Test document list
            list_response = self.session.get(f"{self.base_url}/documents", timeout=10)
            doc_tests.append({
                "endpoint": "GET /documents",
                "status_code": list_response.status_code,
                "success": list_response.status_code in [200, 401],
                "response_time_ms": list_response.elapsed.total_seconds() * 1000
            })
            
            # Test document retrieval
            doc_id = "test_doc_123"
            get_response = self.session.get(f"{self.base_url}/documents/{doc_id}", timeout=10)
            doc_tests.append({
                "endpoint": f"GET /documents/{doc_id}",
                "status_code": get_response.status_code,
                "success": get_response.status_code in [200, 401, 404],
                "response_time_ms": get_response.elapsed.total_seconds() * 1000
            })
            
            passed_tests = sum(1 for test in doc_tests if test["success"])
            total_tests = len(doc_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Document processing: {passed_tests}/{total_tests} endpoints accessible",
                "test_results": doc_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Document processing error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_ai_chat_interface(self) -> Dict[str, Any]:
        """Test AI chat interface endpoints."""
        result = {
            "test_name": "ai_chat_interface",
            "platform": "render",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            chat_tests = []
            
            # Test chat endpoint
            chat_data = {
                "message": "Hello, how can you help me?",
                "conversation_id": "test_conv_123"
            }
            chat_response = self.session.post(f"{self.base_url}/chat", json=chat_data, timeout=30)
            chat_tests.append({
                "endpoint": "POST /chat",
                "status_code": chat_response.status_code,
                "success": chat_response.status_code in [200, 401, 422],
                "response_time_ms": chat_response.elapsed.total_seconds() * 1000
            })
            
            # Test conversation history
            conv_response = self.session.get(f"{self.base_url}/conversations/test_conv_123", timeout=10)
            chat_tests.append({
                "endpoint": "GET /conversations/{id}",
                "status_code": conv_response.status_code,
                "success": conv_response.status_code in [200, 401, 404],
                "response_time_ms": conv_response.elapsed.total_seconds() * 1000
            })
            
            passed_tests = sum(1 for test in chat_tests if test["success"])
            total_tests = len(chat_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"AI chat interface: {passed_tests}/{total_tests} endpoints accessible",
                "test_results": chat_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"AI chat interface error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error response handling and formatting."""
        result = {
            "test_name": "error_handling",
            "platform": "render",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            error_tests = []
            
            # Test 404 endpoint
            not_found_response = self.session.get(f"{self.base_url}/nonexistent", timeout=10)
            error_tests.append({
                "test": "404_not_found",
                "status_code": not_found_response.status_code,
                "success": not_found_response.status_code == 404,
                "response_time_ms": not_found_response.elapsed.total_seconds() * 1000
            })
            
            # Test invalid JSON
            invalid_json_response = self.session.post(
                f"{self.base_url}/auth/login",
                data="invalid json",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            error_tests.append({
                "test": "invalid_json",
                "status_code": invalid_json_response.status_code,
                "success": invalid_json_response.status_code in [400, 422],
                "response_time_ms": invalid_json_response.elapsed.total_seconds() * 1000
            })
            
            # Test method not allowed
            method_not_allowed_response = self.session.delete(f"{self.base_url}/health", timeout=10)
            error_tests.append({
                "test": "method_not_allowed",
                "status_code": method_not_allowed_response.status_code,
                "success": method_not_allowed_response.status_code in [405, 404],
                "response_time_ms": method_not_allowed_response.elapsed.total_seconds() * 1000
            })
            
            passed_tests = sum(1 for test in error_tests if test["success"])
            total_tests = len(error_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Error handling: {passed_tests}/{total_tests} tests passed",
                "test_results": error_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Error handling error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_render_specific_features(self) -> Dict[str, Any]:
        """Test Render-specific configuration and features."""
        result = {
            "test_name": "render_specific_features",
            "platform": "render",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            render_tests = []
            
            # Test environment variables
            env_response = self.session.get(f"{self.base_url}/env", timeout=10)
            render_tests.append({
                "test": "environment_variables",
                "status_code": env_response.status_code,
                "success": env_response.status_code in [200, 401, 404],  # May not be exposed
                "response_time_ms": env_response.elapsed.total_seconds() * 1000
            })
            
            # Test Render health check format
            health_response = self.session.get(f"{self.base_url}/health", timeout=10)
            if health_response.status_code == 200:
                try:
                    health_data = health_response.json()
                    render_tests.append({
                        "test": "health_check_format",
                        "success": "status" in health_data and "timestamp" in health_data,
                        "details": f"Health check format valid: {list(health_data.keys())}"
                    })
                except:
                    render_tests.append({
                        "test": "health_check_format",
                        "success": False,
                        "details": "Health check response not valid JSON"
                    })
            
            # Test response headers
            headers_response = self.session.head(f"{self.base_url}/", timeout=10)
            render_tests.append({
                "test": "response_headers",
                "success": "server" in headers_response.headers or "x-powered-by" in headers_response.headers,
                "details": f"Response headers: {list(headers_response.headers.keys())}"
            })
            
            passed_tests = sum(1 for test in render_tests if test["success"])
            total_tests = len(render_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Render-specific features: {passed_tests}/{total_tests} tests passed",
                "test_results": render_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Render-specific features error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all Render Web Service tests."""
        logger.info(f"Starting Render Web Service testing for {self.environment} environment")
        
        await self.test_fastapi_startup()
        await self.test_health_endpoints()
        await self.test_authentication_flow()
        await self.test_document_processing()
        await self.test_ai_chat_interface()
        await self.test_error_handling()
        await self.test_render_specific_features()
        
        return self.results

class RenderWorkersTester:
    """Test Render Workers background processes and job handling."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.worker_url = self._get_worker_url()
        self.results = []
        
    def _get_worker_url(self) -> str:
        """Get Render Worker URL based on environment."""
        if self.environment == "production":
            return "https://insurance-navigator-worker.onrender.com"
        elif self.environment == "staging":
            return "https://insurance-navigator-worker-staging.onrender.com"
        else:  # development
            return "http://localhost:8001"
    
    async def test_worker_initialization(self) -> Dict[str, Any]:
        """Test worker initialization and startup."""
        result = {
            "test_name": "worker_initialization",
            "platform": "render_workers",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Test worker health check
            health_response = requests.get(f"{self.worker_url}/health", timeout=10)
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                result.update({
                    "status": "passed",
                    "details": f"Worker health check passed: {health_data}",
                    "response_time_ms": health_response.elapsed.total_seconds() * 1000
                })
            else:
                result.update({
                    "status": "failed",
                    "details": f"Worker health check failed: {health_response.status_code}",
                    "error": health_response.text[:200]
                })
                
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Worker initialization error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_job_processing(self) -> Dict[str, Any]:
        """Test job processing capabilities."""
        result = {
            "test_name": "job_processing",
            "platform": "render_workers",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Test job submission
            job_data = {
                "job_type": "document_processing",
                "document_id": "test_doc_123",
                "parameters": {"extract_text": True, "generate_summary": True}
            }
            
            job_response = requests.post(f"{self.worker_url}/jobs", json=job_data, timeout=30)
            
            if job_response.status_code in [200, 201, 202]:
                job_result = job_response.json()
                result.update({
                    "status": "passed",
                    "details": f"Job submission successful: {job_response.status_code}",
                    "job_id": job_result.get("job_id", "unknown"),
                    "response_time_ms": job_response.elapsed.total_seconds() * 1000
                })
            else:
                result.update({
                    "status": "failed",
                    "details": f"Job submission failed: {job_response.status_code}",
                    "error": job_response.text[:200]
                })
                
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Job processing error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_worker_performance(self) -> Dict[str, Any]:
        """Test worker performance under load."""
        result = {
            "test_name": "worker_performance",
            "platform": "render_workers",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Submit multiple jobs to test performance
            job_count = 5
            successful_jobs = 0
            total_response_time = 0
            
            for i in range(job_count):
                job_data = {
                    "job_type": "test_processing",
                    "job_id": f"perf_test_{i}",
                    "parameters": {"test_data": f"performance_test_{i}"}
                }
                
                start_time = time.time()
                job_response = requests.post(f"{self.worker_url}/jobs", json=job_data, timeout=10)
                response_time = (time.time() - start_time) * 1000
                total_response_time += response_time
                
                if job_response.status_code in [200, 201, 202]:
                    successful_jobs += 1
            
            avg_response_time = total_response_time / job_count if job_count > 0 else 0
            
            result.update({
                "status": "passed" if successful_jobs == job_count else "partial",
                "details": f"Performance test: {successful_jobs}/{job_count} jobs successful",
                "average_response_time_ms": avg_response_time,
                "successful_jobs": successful_jobs,
                "total_jobs": job_count
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Worker performance test error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all Render Workers tests."""
        logger.info(f"Starting Render Workers testing for {self.environment} environment")
        
        await self.test_worker_initialization()
        await self.test_job_processing()
        await self.test_worker_performance()
        
        return self.results

async def main():
    """Main execution function for Render platform testing."""
    print("=" * 80)
    print("RENDER PLATFORM TESTING")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Test development environment
    print("\n🧪 Testing Development Environment...")
    dev_web_tester = RenderWebServiceTester("development")
    dev_worker_tester = RenderWorkersTester("development")
    
    dev_web_results = await dev_web_tester.run_all_tests()
    dev_worker_results = await dev_worker_tester.run_all_tests()
    
    # Test staging environment
    print("\n🧪 Testing Staging Environment...")
    staging_web_tester = RenderWebServiceTester("staging")
    staging_worker_tester = RenderWorkersTester("staging")
    
    staging_web_results = await staging_web_tester.run_all_tests()
    staging_worker_results = await staging_worker_tester.run_all_tests()
    
    # Generate combined report
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "environments": {
            "development": {
                "web_service": dev_web_results,
                "workers": dev_worker_results
            },
            "staging": {
                "web_service": staging_web_results,
                "workers": staging_worker_results
            }
        }
    }
    
    # Save report
    os.makedirs("test-results", exist_ok=True)
    report_path = "test-results/render_platform_test_report.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📄 Render platform test report saved to: {report_path}")
    print("=" * 80)
    print("RENDER PLATFORM TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
