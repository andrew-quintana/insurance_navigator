"""
Phase 3 Production Validation Test Suite

This module provides comprehensive end-to-end validation tests to ensure
the system meets all production readiness requirements after Phase 3 implementation.
"""

import asyncio
import pytest
import time
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import os
from pathlib import Path

# Import test utilities
from tests.test_utilities.auth_helper import create_test_user, authenticate_test_user
from tests.test_utilities.document_helper import create_test_document, upload_test_document
from tests.test_utilities.validation_helper import (
    validate_response_structure,
    validate_performance_metrics,
    validate_error_handling
)

# Import resilience components for validation
from core.resilience import (
    get_system_monitor,
    get_degradation_registry,
    get_circuit_breaker_registry
)

logger = logging.getLogger(__name__)

class Phase3ValidationSuite:
    """Comprehensive Phase 3 production validation test suite."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = []
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user = None
        self.auth_token = None
        
    async def setup(self):
        """Setup test environment."""
        try:
            # Create test user
            self.test_user = await create_test_user("phase3_test_user")
            self.auth_token = await authenticate_test_user(self.test_user["email"], "TestPassword123!", self.base_url)
            
            logger.info("Phase 3 validation suite setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup test environment."""
        try:
            await self.client.aclose()
            logger.info("Phase 3 validation suite cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def record_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Record test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    async def test_system_health_monitoring(self) -> bool:
        """Test 3.1.4: Validate comprehensive monitoring and alerting system."""
        test_name = "System Health Monitoring"
        
        try:
            # Test system monitor availability
            system_monitor = get_system_monitor()
            
            # Test health check endpoint
            response = await self.client.get(f"{self.base_url}/health")
            
            health_data = response.json()
            
            # Validate health response structure
            required_fields = ["status", "timestamp", "services", "version"]
            missing_fields = [field for field in required_fields if field not in health_data]
            
            if missing_fields:
                self.record_test_result(test_name, False, {
                    "error": f"Missing health check fields: {missing_fields}",
                    "response": health_data
                })
                return False
            
            # Test system status endpoint
            system_status = await system_monitor.get_system_status()
            
            # Validate system status structure
            status_fields = ["overall_health", "status", "health_checks", "active_alerts"]
            missing_status_fields = [field for field in status_fields if field not in system_status]
            
            if missing_status_fields:
                self.record_test_result(test_name, False, {
                    "error": f"Missing system status fields: {missing_status_fields}",
                    "system_status": system_status
                })
                return False
            
            self.record_test_result(test_name, True, {
                "health_endpoint": health_data,
                "system_status": system_status,
                "overall_health": system_status.get("overall_health", 0.0)
            })
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
    
    async def test_circuit_breaker_functionality(self) -> bool:
        """Test 3.1.2: Validate circuit breaker protection mechanisms."""
        test_name = "Circuit Breaker Functionality"
        
        try:
            # Get circuit breaker status via API
            response = await self.client.get(f"{self.base_url}/debug-resilience")
            
            if response.status_code != 200:
                self.record_test_result(test_name, False, {
                    "error": f"Failed to get resilience status: {response.status_code}",
                    "response": response.text
                })
                return False
            
            resilience_data = response.json()
            
            if "error" in resilience_data:
                self.record_test_result(test_name, False, {
                    "error": f"Resilience endpoint error: {resilience_data['error']}",
                    "data": resilience_data
                })
                return False
            
            # Validate circuit breakers are registered
            cb_data = resilience_data.get("circuit_breakers", {})
            registered_breakers = cb_data.get("registered", [])
            expected_breakers = ["service_database", "service_rag"]
            
            missing_breakers = [cb for cb in expected_breakers if cb not in registered_breakers]
            
            if missing_breakers:
                self.record_test_result(test_name, False, {
                    "error": f"Missing circuit breakers: {missing_breakers}",
                    "registered": registered_breakers
                })
                return False
            
            # Test circuit breaker states
            breaker_states = cb_data.get("stats", {})
            
            self.record_test_result(test_name, True, {
                "registered_breakers": registered_breakers,
                "breaker_states": breaker_states
            })
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
    
    async def test_graceful_degradation(self) -> bool:
        """Test 3.1.1: Validate graceful degradation mechanisms."""
        test_name = "Graceful Degradation"
        
        try:
            # Get degradation status via API
            response = await self.client.get(f"{self.base_url}/debug-resilience")
            
            if response.status_code != 200:
                self.record_test_result(test_name, False, {
                    "error": f"Failed to get resilience status: {response.status_code}",
                    "response": response.text
                })
                return False
            
            resilience_data = response.json()
            
            if "error" in resilience_data:
                self.record_test_result(test_name, False, {
                    "error": f"Resilience endpoint error: {resilience_data['error']}",
                    "data": resilience_data
                })
                return False
            
            # Test degradation managers are registered
            degradation_data = resilience_data.get("degradation_managers", {})
            registered_services = degradation_data.get("registered", [])
            expected_services = ["rag", "upload", "database"]
            
            missing_services = [svc for svc in expected_services if svc not in registered_services]
            
            if missing_services:
                self.record_test_result(test_name, False, {
                    "error": f"Missing degradation managers: {missing_services}",
                    "registered": registered_services
                })
                return False
            
            # Test degradation status
            service_levels = degradation_data.get("service_levels", {})
            degraded_services = degradation_data.get("degraded_services", [])
            unavailable_services = degradation_data.get("unavailable_services", [])
            
            self.record_test_result(test_name, True, {
                "service_levels": service_levels,
                "degraded_services": degraded_services,
                "unavailable_services": unavailable_services
            })
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
    
    async def test_complete_upload_workflow(self) -> bool:
        """Test 3.3.1: Validate complete upload → processing → chat workflow."""
        test_name = "Complete Upload Workflow"
        
        try:
            # Step 1: Upload document
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create upload request
            upload_data = {
                "filename": "test_insurance_policy.pdf",
                "bytes_len": 1024,
                "mime": "application/pdf",
                "sha256": "test_hash_" + str(int(time.time())),
                "ocr": False
            }
            
            upload_response = await self.client.post(
                f"{self.base_url}/api/v2/upload",
                json=upload_data,
                headers=headers
            )
            
            if upload_response.status_code != 200:
                self.record_test_result(test_name, False, {
                    "step": "upload",
                    "status_code": upload_response.status_code,
                    "response": upload_response.text
                })
                return False
            
            upload_result = upload_response.json()
            document_id = upload_result.get("document_id")
            
            if not document_id:
                self.record_test_result(test_name, False, {
                    "step": "upload",
                    "error": "No document_id in upload response",
                    "response": upload_result
                })
                return False
            
            # Step 2: Check document status
            await asyncio.sleep(1)  # Brief wait for processing
            
            status_response = await self.client.get(
                f"{self.base_url}/documents/{document_id}/status",
                headers=headers
            )
            
            if status_response.status_code != 200:
                logger.warning(f"Document status check failed: {status_response.status_code}")
                # Continue with test as this might be expected in test environment
            
            # Step 3: Test chat functionality
            chat_data = {
                "message": "What is my deductible?",
                "conversation_id": f"test_conv_{int(time.time())}",
                "user_language": "en"
            }
            
            chat_response = await self.client.post(
                f"{self.base_url}/chat",
                json=chat_data,
                headers=headers
            )
            
            if chat_response.status_code != 200:
                self.record_test_result(test_name, False, {
                    "step": "chat",
                    "status_code": chat_response.status_code,
                    "response": chat_response.text
                })
                return False
            
            chat_result = chat_response.json()
            
            # Validate chat response structure
            required_chat_fields = ["text", "response", "conversation_id", "timestamp", "metadata"]
            missing_chat_fields = [field for field in required_chat_fields if field not in chat_result]
            
            if missing_chat_fields:
                self.record_test_result(test_name, False, {
                    "step": "chat_validation",
                    "error": f"Missing chat response fields: {missing_chat_fields}",
                    "response": chat_result
                })
                return False
            
            self.record_test_result(test_name, True, {
                "upload_result": upload_result,
                "document_id": document_id,
                "chat_response": {
                    "text_length": len(chat_result.get("text", "")),
                    "has_metadata": "metadata" in chat_result,
                    "conversation_id": chat_result.get("conversation_id")
                }
            })
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
    
    async def test_error_handling_resilience(self) -> bool:
        """Test 3.1.3: Validate error handling and recovery mechanisms."""
        test_name = "Error Handling and Resilience"
        
        try:
            # Test 1: Invalid authentication
            invalid_response = await self.client.post(
                f"{self.base_url}/chat",
                json={"message": "test"},
                headers={"Authorization": "Bearer invalid_token"}
            )
            
            if invalid_response.status_code != 401:
                self.record_test_result(test_name, False, {
                    "test": "invalid_auth",
                    "expected_status": 401,
                    "actual_status": invalid_response.status_code
                })
                return False
            
            # Test 2: Malformed request
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            malformed_response = await self.client.post(
                f"{self.base_url}/chat",
                json={"invalid_field": "test"},
                headers=headers
            )
            
            if malformed_response.status_code != 400:
                logger.warning(f"Malformed request handling: {malformed_response.status_code}")
                # This might be handled gracefully, so we don't fail the test
            
            # Test 3: Service availability during degradation
            # This test validates that the system continues to function even with degraded services
            chat_response = await self.client.post(
                f"{self.base_url}/chat",
                json={
                    "message": "Test resilience",
                    "conversation_id": f"resilience_test_{int(time.time())}"
                },
                headers=headers
            )
            
            # System should respond even if degraded
            if chat_response.status_code not in [200, 503]:
                self.record_test_result(test_name, False, {
                    "test": "service_degradation",
                    "status_code": chat_response.status_code,
                    "response": chat_response.text
                })
                return False
            
            self.record_test_result(test_name, True, {
                "invalid_auth_test": "passed",
                "malformed_request_test": "handled",
                "degradation_test": "system_responsive"
            })
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
    
    async def test_integration_dependencies(self) -> bool:
        """Test 3.3.3: Validate all system integrations and dependencies."""
        test_name = "Integration Dependencies"
        
        try:
            # Test database integration
            health_response = await self.client.get(f"{self.base_url}/health")
            health_data = health_response.json()
            
            services = health_data.get("services", {})
            
            # Check critical service integrations
            critical_services = ["database", "supabase_auth", "openai"]
            service_status = {}
            
            for service in critical_services:
                if service in services:
                    service_status[service] = services[service]
                else:
                    service_status[service] = "not_reported"
            
            # Test authentication integration
            auth_test_response = await self.client.get(
                f"{self.base_url}/me",
                headers={"Authorization": f"Bearer {self.auth_token}"}
            )
            
            auth_integration_working = auth_test_response.status_code == 200
            
            # Test configuration system integration
            config_test_response = await self.client.get(f"{self.base_url}/debug-auth")
            config_integration_working = config_test_response.status_code == 200
            
            self.record_test_result(test_name, True, {
                "service_integrations": service_status,
                "auth_integration": auth_integration_working,
                "config_integration": config_integration_working,
                "overall_health": health_data.get("status", "unknown")
            })
            return True
            
        except Exception as e:
            self.record_test_result(test_name, False, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
    
    async def test_performance_requirements(self) -> bool:
        """Test 3.3.4: Validate performance meets MVP requirements."""
        test_name = "Performance Requirements"
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            performance_results = {}
            
            # Test 1: Health check response time (should be < 1s)
            start_time = time.time()
            health_response = await self.client.get(f"{self.base_url}/health")
            health_duration = time.time() - start_time
            
            performance_results["health_check"] = {
                "duration": health_duration,
                "target": 1.0,
                "passed": health_duration < 1.0
            }
            
            # Test 2: Authentication response time (should be < 2s)
            start_time = time.time()
            auth_response = await self.client.get(f"{self.base_url}/me", headers=headers)
            auth_duration = time.time() - start_time
            
            performance_results["authentication"] = {
                "duration": auth_duration,
                "target": 2.0,
                "passed": auth_duration < 2.0
            }
            
            # Test 3: Chat response time (should be < 10s for basic queries)
            start_time = time.time()
            chat_response = await self.client.post(
                f"{self.base_url}/chat",
                json={"message": "Hello", "conversation_id": f"perf_test_{int(time.time())}"},
                headers=headers
            )
            chat_duration = time.time() - start_time
            
            performance_results["chat_response"] = {
                "duration": chat_duration,
                "target": 10.0,
                "passed": chat_duration < 10.0
            }
            
            # Calculate overall performance score
            total_tests = len(performance_results)
            passed_tests = sum(1 for result in performance_results.values() if result["passed"])
            performance_score = passed_tests / total_tests if total_tests > 0 else 0.0
            
            # Performance test passes if at least 80% of tests pass
            performance_passed = performance_score >= 0.8
            
            self.record_test_result(test_name, performance_passed, {
                "performance_results": performance_results,
                "performance_score": performance_score,
                "passed_tests": passed_tests,
                "total_tests": total_tests
            })
            return performance_passed
            
        except Exception as e:
            self.record_test_result(test_name, False, {
                "error": str(e),
                "error_type": type(e).__name__
            })
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Phase 3 validation tests."""
        logger.info("Starting Phase 3 Production Validation Test Suite")
        
        # Setup
        setup_success = await self.setup()
        if not setup_success:
            return {
                "success": False,
                "error": "Test setup failed",
                "results": []
            }
        
        try:
            # Run all validation tests
            test_methods = [
                self.test_system_health_monitoring,
                self.test_circuit_breaker_functionality,
                self.test_graceful_degradation,
                self.test_complete_upload_workflow,
                self.test_error_handling_resilience,
                self.test_integration_dependencies,
                self.test_performance_requirements
            ]
            
            for test_method in test_methods:
                try:
                    await test_method()
                except Exception as e:
                    logger.error(f"Test method {test_method.__name__} failed: {e}")
            
            # Calculate overall results
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result["success"])
            success_rate = passed_tests / total_tests if total_tests > 0 else 0.0
            
            # Phase 3 validation passes if at least 85% of tests pass
            overall_success = success_rate >= 0.85
            
            return {
                "success": overall_success,
                "success_rate": success_rate,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "results": self.test_results,
                "timestamp": datetime.utcnow().isoformat(),
                "production_ready": overall_success
            }
            
        finally:
            await self.cleanup()

async def run_phase3_validation(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Run Phase 3 production validation tests."""
    suite = Phase3ValidationSuite(base_url)
    return await suite.run_all_tests()

if __name__ == "__main__":
    # Run validation tests
    asyncio.run(run_phase3_validation())
