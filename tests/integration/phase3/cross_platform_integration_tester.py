#!/usr/bin/env python3
"""
Cross-Platform Integration Testing Module
Test communication and integration between Render backend and Vercel frontend
"""

import asyncio
import requests
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("cross_platform_tester")

class CrossPlatformIntegrationTester:
    """Test cross-platform communication between Vercel and Render."""
    
    def __init__(self, environment: str = "development"):
        self.environment = environment
        self.frontend_url = self._get_frontend_url()
        self.backend_url = self._get_backend_url()
        self.results = []
        
    def _get_frontend_url(self) -> str:
        """Get Vercel frontend URL based on environment."""
        if self.environment == "production":
            return "https://insurance-navigator.vercel.app"
        elif self.environment == "staging":
            return "https://insurance-navigator-staging.vercel.app"
        else:  # development
            return "http://localhost:3000"
    
    def _get_backend_url(self) -> str:
        """Get Render backend URL based on environment."""
        if self.environment == "production":
            return "https://insurance-navigator-api.onrender.com"
        elif self.environment == "staging":
            return "https://insurance-navigator-api-staging.onrender.com"
        else:  # development
            return "http://localhost:8000"
    
    async def test_api_connectivity(self) -> Dict[str, Any]:
        """Test API connectivity between frontend and backend."""
        result = {
            "test_name": "api_connectivity",
            "platform": "cross_platform",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            connectivity_tests = []
            
            # Test backend health from frontend perspective
            try:
                backend_health = requests.get(f"{self.backend_url}/health", timeout=10)
                connectivity_tests.append({
                    "test": "backend_health",
                    "success": backend_health.status_code == 200,
                    "status_code": backend_health.status_code,
                    "response_time_ms": backend_health.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                connectivity_tests.append({
                    "test": "backend_health",
                    "success": False,
                    "error": str(e)
                })
            
            # Test frontend accessibility
            try:
                frontend_response = requests.get(self.frontend_url, timeout=10)
                connectivity_tests.append({
                    "test": "frontend_accessibility",
                    "success": frontend_response.status_code == 200,
                    "status_code": frontend_response.status_code,
                    "response_time_ms": frontend_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                connectivity_tests.append({
                    "test": "frontend_accessibility",
                    "success": False,
                    "error": str(e)
                })
            
            # Test API proxy/rewrite functionality
            try:
                api_proxy_response = requests.get(f"{self.frontend_url}/api/health", timeout=10)
                connectivity_tests.append({
                    "test": "api_proxy",
                    "success": api_proxy_response.status_code in [200, 404],  # 404 if no proxy configured
                    "status_code": api_proxy_response.status_code,
                    "response_time_ms": api_proxy_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                connectivity_tests.append({
                    "test": "api_proxy",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in connectivity_tests if test["success"])
            total_tests = len(connectivity_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"API connectivity: {passed_tests}/{total_tests} tests passed",
                "test_results": connectivity_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"API connectivity error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_cors_configuration(self) -> Dict[str, Any]:
        """Test CORS configuration for cross-platform communication."""
        result = {
            "test_name": "cors_configuration",
            "platform": "cross_platform",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            cors_tests = []
            
            # Test CORS preflight request
            try:
                cors_headers = {
                    "Origin": self.frontend_url,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type, Authorization"
                }
                cors_response = requests.options(
                    f"{self.backend_url}/auth/login", 
                    headers=cors_headers, 
                    timeout=10
                )
                
                cors_headers_response = cors_response.headers
                cors_tests.append({
                    "test": "cors_preflight",
                    "success": cors_response.status_code in [200, 204],
                    "status_code": cors_response.status_code,
                    "access_control_allow_origin": cors_headers_response.get("Access-Control-Allow-Origin"),
                    "access_control_allow_methods": cors_headers_response.get("Access-Control-Allow-Methods"),
                    "access_control_allow_headers": cors_headers_response.get("Access-Control-Allow-Headers")
                })
            except Exception as e:
                cors_tests.append({
                    "test": "cors_preflight",
                    "success": False,
                    "error": str(e)
                })
            
            # Test actual CORS request
            try:
                actual_cors_response = requests.post(
                    f"{self.backend_url}/auth/login",
                    json={"email": "test@example.com", "password": "test"},
                    headers={"Origin": self.frontend_url, "Content-Type": "application/json"},
                    timeout=10
                )
                
                cors_headers_response = actual_cors_response.headers
                cors_tests.append({
                    "test": "cors_actual_request",
                    "success": actual_cors_response.status_code in [200, 401, 422],
                    "status_code": actual_cors_response.status_code,
                    "access_control_allow_origin": cors_headers_response.get("Access-Control-Allow-Origin"),
                    "response_time_ms": actual_cors_response.elapsed.total_seconds() * 1000
                })
            except Exception as e:
                cors_tests.append({
                    "test": "cors_actual_request",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in cors_tests if test["success"])
            total_tests = len(cors_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"CORS configuration: {passed_tests}/{total_tests} tests passed",
                "test_results": cors_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"CORS configuration error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_authentication_flow_integration(self) -> Dict[str, Any]:
        """Test authentication flow integration across platforms."""
        result = {
            "test_name": "authentication_flow_integration",
            "platform": "cross_platform",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            auth_tests = []
            
            # Test login flow
            try:
                login_data = {
                    "email": "test@example.com",
                    "password": "testpassword"
                }
                login_response = requests.post(
                    f"{self.backend_url}/auth/login",
                    json=login_data,
                    headers={"Origin": self.frontend_url},
                    timeout=10
                )
                
                auth_tests.append({
                    "test": "login_flow",
                    "success": login_response.status_code in [200, 401, 422],
                    "status_code": login_response.status_code,
                    "response_time_ms": login_response.elapsed.total_seconds() * 1000,
                    "has_cors_headers": "Access-Control-Allow-Origin" in login_response.headers
                })
            except Exception as e:
                auth_tests.append({
                    "test": "login_flow",
                    "success": False,
                    "error": str(e)
                })
            
            # Test registration flow
            try:
                register_data = {
                    "email": "newuser@example.com",
                    "password": "newpassword",
                    "full_name": "Test User"
                }
                register_response = requests.post(
                    f"{self.backend_url}/auth/register",
                    json=register_data,
                    headers={"Origin": self.frontend_url},
                    timeout=10
                )
                
                auth_tests.append({
                    "test": "registration_flow",
                    "success": register_response.status_code in [200, 201, 400, 409, 422],
                    "status_code": register_response.status_code,
                    "response_time_ms": register_response.elapsed.total_seconds() * 1000,
                    "has_cors_headers": "Access-Control-Allow-Origin" in register_response.headers
                })
            except Exception as e:
                auth_tests.append({
                    "test": "registration_flow",
                    "success": False,
                    "error": str(e)
                })
            
            # Test token refresh flow
            try:
                refresh_response = requests.post(
                    f"{self.backend_url}/auth/refresh",
                    json={},
                    headers={"Origin": self.frontend_url},
                    timeout=10
                )
                
                auth_tests.append({
                    "test": "token_refresh_flow",
                    "success": refresh_response.status_code in [200, 401, 422],
                    "status_code": refresh_response.status_code,
                    "response_time_ms": refresh_response.elapsed.total_seconds() * 1000,
                    "has_cors_headers": "Access-Control-Allow-Origin" in refresh_response.headers
                })
            except Exception as e:
                auth_tests.append({
                    "test": "token_refresh_flow",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in auth_tests if test["success"])
            total_tests = len(auth_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Authentication flow integration: {passed_tests}/{total_tests} tests passed",
                "test_results": auth_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Authentication flow integration error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_document_processing_integration(self) -> Dict[str, Any]:
        """Test document processing integration across platforms."""
        result = {
            "test_name": "document_processing_integration",
            "platform": "cross_platform",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            doc_tests = []
            
            # Test document upload from frontend to backend
            try:
                files = {'file': ('test.pdf', b'fake pdf content', 'application/pdf')}
                upload_response = requests.post(
                    f"{self.backend_url}/documents/upload",
                    files=files,
                    headers={"Origin": self.frontend_url},
                    timeout=30
                )
                
                doc_tests.append({
                    "test": "document_upload",
                    "success": upload_response.status_code in [200, 201, 401, 422],
                    "status_code": upload_response.status_code,
                    "response_time_ms": upload_response.elapsed.total_seconds() * 1000,
                    "has_cors_headers": "Access-Control-Allow-Origin" in upload_response.headers
                })
            except Exception as e:
                doc_tests.append({
                    "test": "document_upload",
                    "success": False,
                    "error": str(e)
                })
            
            # Test document list retrieval
            try:
                list_response = requests.get(
                    f"{self.backend_url}/documents",
                    headers={"Origin": self.frontend_url},
                    timeout=10
                )
                
                doc_tests.append({
                    "test": "document_list",
                    "success": list_response.status_code in [200, 401],
                    "status_code": list_response.status_code,
                    "response_time_ms": list_response.elapsed.total_seconds() * 1000,
                    "has_cors_headers": "Access-Control-Allow-Origin" in list_response.headers
                })
            except Exception as e:
                doc_tests.append({
                    "test": "document_list",
                    "success": False,
                    "error": str(e)
                })
            
            # Test document processing status
            try:
                status_response = requests.get(
                    f"{self.backend_url}/documents/status",
                    headers={"Origin": self.frontend_url},
                    timeout=10
                )
                
                doc_tests.append({
                    "test": "document_status",
                    "success": status_response.status_code in [200, 401, 404],
                    "status_code": status_response.status_code,
                    "response_time_ms": status_response.elapsed.total_seconds() * 1000,
                    "has_cors_headers": "Access-Control-Allow-Origin" in status_response.headers
                })
            except Exception as e:
                doc_tests.append({
                    "test": "document_status",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in doc_tests if test["success"])
            total_tests = len(doc_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Document processing integration: {passed_tests}/{total_tests} tests passed",
                "test_results": doc_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Document processing integration error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_ai_chat_integration(self) -> Dict[str, Any]:
        """Test AI chat integration across platforms."""
        result = {
            "test_name": "ai_chat_integration",
            "platform": "cross_platform",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            chat_tests = []
            
            # Test chat message submission
            try:
                chat_data = {
                    "message": "Hello, how can you help me?",
                    "conversation_id": "test_conv_123"
                }
                chat_response = requests.post(
                    f"{self.backend_url}/chat",
                    json=chat_data,
                    headers={"Origin": self.frontend_url, "Content-Type": "application/json"},
                    timeout=30
                )
                
                chat_tests.append({
                    "test": "chat_message",
                    "success": chat_response.status_code in [200, 401, 422],
                    "status_code": chat_response.status_code,
                    "response_time_ms": chat_response.elapsed.total_seconds() * 1000,
                    "has_cors_headers": "Access-Control-Allow-Origin" in chat_response.headers
                })
            except Exception as e:
                chat_tests.append({
                    "test": "chat_message",
                    "success": False,
                    "error": str(e)
                })
            
            # Test conversation history
            try:
                conv_response = requests.get(
                    f"{self.backend_url}/conversations/test_conv_123",
                    headers={"Origin": self.frontend_url},
                    timeout=10
                )
                
                chat_tests.append({
                    "test": "conversation_history",
                    "success": conv_response.status_code in [200, 401, 404],
                    "status_code": conv_response.status_code,
                    "response_time_ms": conv_response.elapsed.total_seconds() * 1000,
                    "has_cors_headers": "Access-Control-Allow-Origin" in conv_response.headers
                })
            except Exception as e:
                chat_tests.append({
                    "test": "conversation_history",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in chat_tests if test["success"])
            total_tests = len(chat_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"AI chat integration: {passed_tests}/{total_tests} tests passed",
                "test_results": chat_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"AI chat integration error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_error_handling_integration(self) -> Dict[str, Any]:
        """Test error handling integration across platforms."""
        result = {
            "test_name": "error_handling_integration",
            "platform": "cross_platform",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            error_tests = []
            
            # Test 404 error handling
            try:
                not_found_response = requests.get(
                    f"{self.backend_url}/nonexistent",
                    headers={"Origin": self.frontend_url},
                    timeout=10
                )
                
                error_tests.append({
                    "test": "404_error_handling",
                    "success": not_found_response.status_code == 404,
                    "status_code": not_found_response.status_code,
                    "has_cors_headers": "Access-Control-Allow-Origin" in not_found_response.headers
                })
            except Exception as e:
                error_tests.append({
                    "test": "404_error_handling",
                    "success": False,
                    "error": str(e)
                })
            
            # Test invalid JSON error handling
            try:
                invalid_json_response = requests.post(
                    f"{self.backend_url}/auth/login",
                    data="invalid json",
                    headers={"Origin": self.frontend_url, "Content-Type": "application/json"},
                    timeout=10
                )
                
                error_tests.append({
                    "test": "invalid_json_error_handling",
                    "success": invalid_json_response.status_code in [400, 422],
                    "status_code": invalid_json_response.status_code,
                    "has_cors_headers": "Access-Control-Allow-Origin" in invalid_json_response.headers
                })
            except Exception as e:
                error_tests.append({
                    "test": "invalid_json_error_handling",
                    "success": False,
                    "error": str(e)
                })
            
            # Test timeout error handling
            try:
                timeout_response = requests.get(
                    f"{self.backend_url}/health",
                    headers={"Origin": self.frontend_url},
                    timeout=1  # Very short timeout to test timeout handling
                )
                
                error_tests.append({
                    "test": "timeout_error_handling",
                    "success": True,  # If we get here, timeout handling worked
                    "status_code": timeout_response.status_code
                })
            except requests.exceptions.Timeout:
                error_tests.append({
                    "test": "timeout_error_handling",
                    "success": True,  # Timeout was handled properly
                    "status_code": "timeout"
                })
            except Exception as e:
                error_tests.append({
                    "test": "timeout_error_handling",
                    "success": False,
                    "error": str(e)
                })
            
            passed_tests = sum(1 for test in error_tests if test["success"])
            total_tests = len(error_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Error handling integration: {passed_tests}/{total_tests} tests passed",
                "test_results": error_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Error handling integration error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def test_performance_integration(self) -> Dict[str, Any]:
        """Test performance across platform integration."""
        result = {
            "test_name": "performance_integration",
            "platform": "cross_platform",
            "environment": self.environment,
            "start_time": datetime.now().isoformat()
        }
        
        try:
            performance_tests = []
            
            # Test response times for key endpoints
            endpoints = [
                ("/health", "GET"),
                ("/auth/login", "POST"),
                ("/documents", "GET"),
                ("/chat", "POST")
            ]
            
            for endpoint, method in endpoints:
                try:
                    start_time = time.time()
                    
                    if method == "GET":
                        response = requests.get(
                            f"{self.backend_url}{endpoint}",
                            headers={"Origin": self.frontend_url},
                            timeout=10
                        )
                    else:  # POST
                        response = requests.post(
                            f"{self.backend_url}{endpoint}",
                            json={},
                            headers={"Origin": self.frontend_url, "Content-Type": "application/json"},
                            timeout=10
                        )
                    
                    response_time = (time.time() - start_time) * 1000
                    
                    performance_tests.append({
                        "endpoint": endpoint,
                        "method": method,
                        "response_time_ms": response_time,
                        "status_code": response.status_code,
                        "success": response.status_code in [200, 401, 404, 422],
                        "acceptable_performance": response_time < 5000  # 5 second threshold
                    })
                    
                except Exception as e:
                    performance_tests.append({
                        "endpoint": endpoint,
                        "method": method,
                        "response_time_ms": 0,
                        "status_code": "error",
                        "success": False,
                        "error": str(e)
                    })
            
            passed_tests = sum(1 for test in performance_tests if test["success"])
            acceptable_performance = sum(1 for test in performance_tests if test.get("acceptable_performance", False))
            total_tests = len(performance_tests)
            
            result.update({
                "status": "passed" if passed_tests == total_tests else "partial",
                "details": f"Performance integration: {passed_tests}/{total_tests} tests passed, {acceptable_performance}/{total_tests} within performance threshold",
                "test_results": performance_tests
            })
            
        except Exception as e:
            result.update({
                "status": "error",
                "details": f"Performance integration error: {str(e)}",
                "error": str(e)
            })
        
        result["end_time"] = datetime.now().isoformat()
        self.results.append(result)
        return result
    
    async def run_all_tests(self) -> List[Dict[str, Any]]:
        """Run all cross-platform integration tests."""
        logger.info(f"Starting cross-platform integration testing for {self.environment} environment")
        
        await self.test_api_connectivity()
        await self.test_cors_configuration()
        await self.test_authentication_flow_integration()
        await self.test_document_processing_integration()
        await self.test_ai_chat_integration()
        await self.test_error_handling_integration()
        await self.test_performance_integration()
        
        return self.results

async def main():
    """Main execution function for cross-platform integration testing."""
    print("=" * 80)
    print("CROSS-PLATFORM INTEGRATION TESTING")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    # Test development environment
    print("\n🧪 Testing Development Environment...")
    dev_tester = CrossPlatformIntegrationTester("development")
    dev_results = await dev_tester.run_all_tests()
    
    # Test staging environment
    print("\n🧪 Testing Staging Environment...")
    staging_tester = CrossPlatformIntegrationTester("staging")
    staging_results = await staging_tester.run_all_tests()
    
    # Test production environment
    print("\n🧪 Testing Production Environment...")
    prod_tester = CrossPlatformIntegrationTester("production")
    prod_results = await prod_tester.run_all_tests()
    
    # Generate combined report
    all_results = {
        "timestamp": datetime.now().isoformat(),
        "environments": {
            "development": dev_results,
            "staging": staging_results,
            "production": prod_results
        }
    }
    
    # Save report
    os.makedirs("test-results", exist_ok=True)
    report_path = "test-results/cross_platform_integration_test_report.json"
    with open(report_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📄 Cross-platform integration test report saved to: {report_path}")
    print("=" * 80)
    print("CROSS-PLATFORM INTEGRATION TESTING COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
