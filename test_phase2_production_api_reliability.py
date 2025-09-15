#!/usr/bin/env python3
"""
Phase 2: Production API Reliability - Test Suite

This test suite validates the implementation of Phase 2 requirements:
- Mock fallback removal in production environments
- Error handling implementation with UUID generation
- Retry mechanisms with exponential backoff
- User-facing error message enhancement
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.shared.external.service_router import ServiceRouter, ServiceMode, ServiceUnavailableError, ServiceExecutionError
from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.external.service_router import MockLlamaParseService
from backend.shared.exceptions import UserFacingError
from backend.shared.config.worker_config import WorkerConfig


class Phase2TestSuite:
    """Test suite for Phase 2: Production API Reliability"""
    
    def __init__(self):
        self.test_results = []
        self.environment_backup = os.environ.get("ENVIRONMENT", "development")
    
    def setup_production_environment(self):
        """Set up production environment for testing"""
        os.environ["ENVIRONMENT"] = "production"
        os.environ["LLAMAPARSE_API_KEY"] = "test-key"
        os.environ["LLAMAPARSE_API_URL"] = "https://api.cloud.llamaindex.ai"
    
    def setup_development_environment(self):
        """Set up development environment for testing"""
        os.environ["ENVIRONMENT"] = "development"
        os.environ["LLAMAPARSE_API_KEY"] = "test-key"
        os.environ["LLAMAPARSE_API_URL"] = "https://api.cloud.llamaindex.ai"
    
    def restore_environment(self):
        """Restore original environment"""
        if self.environment_backup:
            os.environ["ENVIRONMENT"] = self.environment_backup
        else:
            os.environ.pop("ENVIRONMENT", None)
    
    async def test_production_mode_validation(self):
        """Test that mock mode is not allowed in production"""
        print("Testing production mode validation...")
        
        try:
            self.setup_production_environment()
            
            # Test that MOCK mode raises error in production
            config = {
                "mode": "mock",
                "llamaparse_config": {
                    "api_key": "test-key",
                    "api_url": "https://api.cloud.llamaindex.ai"
                }
            }
            
            try:
                router = ServiceRouter(config)
                self.test_results.append({
                    "test": "production_mode_validation",
                    "status": "FAILED",
                    "message": "Should have raised ServiceConfigurationError for mock mode in production"
                })
            except Exception as e:
                if "Mock mode is not allowed in production" in str(e):
                    self.test_results.append({
                        "test": "production_mode_validation",
                        "status": "PASSED",
                        "message": "Correctly rejected mock mode in production"
                    })
                else:
                    self.test_results.append({
                        "test": "production_mode_validation",
                        "status": "FAILED",
                        "message": f"Unexpected error: {e}"
                    })
        
        except Exception as e:
            self.test_results.append({
                "test": "production_mode_validation",
                "status": "ERROR",
                "message": f"Test setup failed: {e}"
            })
        finally:
            self.restore_environment()
    
    async def test_production_fallback_disabled(self):
        """Test that fallback to mock is disabled in production"""
        print("Testing production fallback disabled...")
        
        try:
            self.setup_production_environment()
            
            # Test REAL mode with fallback disabled
            config = {
                "mode": "real",
                "fallback_enabled": False,
                "llamaparse_config": {
                    "api_key": "invalid-key",  # This will cause service to be unavailable
                    "api_url": "https://api.cloud.llamaindex.ai"
                }
            }
            
            router = ServiceRouter(config)
            
            # Verify fallback is disabled
            if not router.fallback_enabled:
                print("  ✓ Fallback correctly disabled")
            else:
                print("  ✗ Fallback should be disabled")
            
            # Register mock and real services
            mock_service = MockLlamaParseService()
            real_service = RealLlamaParseService(
                api_key="invalid-key",
                base_url="https://api.cloud.llamaindex.ai"
            )
            router.register_service("llamaparse", mock_service, real_service)
            
            # Try to get service - should raise UserFacingError in production
            try:
                service = await router.get_service("llamaparse")
                self.test_results.append({
                    "test": "production_fallback_disabled",
                    "status": "FAILED",
                    "message": "Should have raised UserFacingError when service unavailable in production"
                })
            except UserFacingError as e:
                if "Document processing service is temporarily unavailable" in e.get_user_message():
                    self.test_results.append({
                        "test": "production_fallback_disabled",
                        "status": "PASSED",
                        "message": "Correctly raised UserFacingError in production when service unavailable"
                    })
                else:
                    self.test_results.append({
                        "test": "production_fallback_disabled",
                        "status": "FAILED",
                        "message": f"Unexpected user message: {e.get_user_message()}"
                    })
            except Exception as e:
                self.test_results.append({
                    "test": "production_fallback_disabled",
                    "status": "FAILED",
                    "message": f"Unexpected error type: {type(e).__name__}: {e}"
                })
        
        except Exception as e:
            self.test_results.append({
                "test": "production_fallback_disabled",
                "status": "ERROR",
                "message": f"Test setup failed: {e}"
            })
        finally:
            self.restore_environment()
    
    async def test_development_fallback_enabled(self):
        """Test that fallback to mock is enabled in development"""
        print("Testing development fallback enabled...")
        
        try:
            self.setup_development_environment()
            
            # Test HYBRID mode with fallback enabled
            config = {
                "mode": "hybrid",
                "fallback_enabled": True,
                "llamaparse_config": {
                    "api_key": "invalid-key",  # This will cause service to be unavailable
                    "api_url": "https://api.cloud.llamaindex.ai"
                }
            }
            
            router = ServiceRouter(config)
            
            # Register mock and real services
            mock_service = MockLlamaParseService()
            real_service = RealLlamaParseService(
                api_key="invalid-key",
                base_url="https://api.cloud.llamaindex.ai"
            )
            router.register_service("llamaparse", mock_service, real_service)
            
            # Try to get service - should return mock service in development
            try:
                service = await router.get_service("llamaparse")
                if isinstance(service, MockLlamaParseService):
                    self.test_results.append({
                        "test": "development_fallback_enabled",
                        "status": "PASSED",
                        "message": "Correctly fell back to mock service in development"
                    })
                else:
                    self.test_results.append({
                        "test": "development_fallback_enabled",
                        "status": "FAILED",
                        "message": f"Expected MockLlamaParseService, got {type(service).__name__}"
                    })
            except Exception as e:
                self.test_results.append({
                    "test": "development_fallback_enabled",
                    "status": "FAILED",
                    "message": f"Unexpected error: {e}"
                })
        
        except Exception as e:
            self.test_results.append({
                "test": "development_fallback_enabled",
                "status": "ERROR",
                "message": f"Test setup failed: {e}"
            })
        finally:
            self.restore_environment()
    
    async def test_user_facing_error_uuid_generation(self):
        """Test that UserFacingError generates UUIDs for traceability"""
        print("Testing UserFacingError UUID generation...")
        
        try:
            # Test UserFacingError creation
            error = UserFacingError(
                message="Test error message",
                error_code="TEST_ERROR",
                context={"test": "value"}
            )
            
            # Check that UUID was generated
            support_uuid = error.get_support_uuid()
            if support_uuid and len(support_uuid) == 36:  # UUID4 format
                self.test_results.append({
                    "test": "user_facing_error_uuid_generation",
                    "status": "PASSED",
                    "message": f"Correctly generated UUID: {support_uuid}"
                })
            else:
                self.test_results.append({
                    "test": "user_facing_error_uuid_generation",
                    "status": "FAILED",
                    "message": f"Invalid UUID format: {support_uuid}"
                })
            
            # Test user message includes UUID
            user_message = error.get_user_message()
            if support_uuid in user_message:
                self.test_results.append({
                    "test": "user_facing_error_message_includes_uuid",
                    "status": "PASSED",
                    "message": "User message correctly includes support UUID"
                })
            else:
                self.test_results.append({
                    "test": "user_facing_error_message_includes_uuid",
                    "status": "FAILED",
                    "message": f"User message does not include UUID: {user_message}"
                })
        
        except Exception as e:
            self.test_results.append({
                "test": "user_facing_error_uuid_generation",
                "status": "ERROR",
                "message": f"Test failed: {e}"
            })
    
    async def test_llamaparse_error_handling(self):
        """Test that LlamaParse service raises UserFacingError for various error conditions"""
        print("Testing LlamaParse error handling...")
        
        try:
            # Test with invalid API key
            service = RealLlamaParseService(
                api_key="invalid-key",
                base_url="https://api.cloud.llamaindex.ai"
            )
            
            # This should raise UserFacingError due to authentication failure
            try:
                await service.parse_document("test.pdf", correlation_id="test-123")
                self.test_results.append({
                    "test": "llamaparse_error_handling",
                    "status": "FAILED",
                    "message": "Should have raised UserFacingError for invalid API key"
                })
            except UserFacingError as e:
                if "authentication failed" in e.get_user_message().lower():
                    self.test_results.append({
                        "test": "llamaparse_error_handling",
                        "status": "PASSED",
                        "message": "Correctly raised UserFacingError for authentication failure"
                    })
                else:
                    self.test_results.append({
                        "test": "llamaparse_error_handling",
                        "status": "FAILED",
                        "message": f"Unexpected error message: {e.get_user_message()}"
                    })
            except Exception as e:
                self.test_results.append({
                    "test": "llamaparse_error_handling",
                    "status": "FAILED",
                    "message": f"Unexpected error type: {type(e).__name__}: {e}"
                })
        
        except Exception as e:
            self.test_results.append({
                "test": "llamaparse_error_handling",
                "status": "ERROR",
                "message": f"Test setup failed: {e}"
            })
    
    async def test_retry_mechanism(self):
        """Test that retry mechanism works with exponential backoff"""
        print("Testing retry mechanism...")
        
        try:
            self.setup_production_environment()
            
            # Create a service that will fail
            config = {
                "mode": "real",
                "fallback_enabled": False,
                "llamaparse_config": {
                    "api_key": "invalid-key",
                    "api_url": "https://api.cloud.llamaindex.ai"
                }
            }
            
            router = ServiceRouter(config)
            
            # Verify fallback is disabled
            if not router.fallback_enabled:
                print("  ✓ Fallback correctly disabled")
            else:
                print("  ✗ Fallback should be disabled")
            
            # Register mock and real services
            mock_service = MockLlamaParseService()
            real_service = RealLlamaParseService(
                api_key="invalid-key",
                base_url="https://api.cloud.llamaindex.ai"
            )
            router.register_service("llamaparse", mock_service, real_service)
            
            # Test execute_service with retry
            start_time = datetime.utcnow()
            try:
                await router.execute_service("llamaparse", "test.pdf", correlation_id="test-123")
                self.test_results.append({
                    "test": "retry_mechanism",
                    "status": "FAILED",
                    "message": "Should have raised UserFacingError after retries"
                })
            except UserFacingError as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                # Should have taken some time due to retries
                if duration > 1:  # At least 1 second for retries
                    self.test_results.append({
                        "test": "retry_mechanism",
                        "status": "PASSED",
                        "message": f"Correctly implemented retry mechanism (duration: {duration:.2f}s)"
                    })
                else:
                    self.test_results.append({
                        "test": "retry_mechanism",
                        "status": "FAILED",
                        "message": f"Retry mechanism may not be working (duration: {duration:.2f}s)"
                    })
            except Exception as e:
                self.test_results.append({
                    "test": "retry_mechanism",
                    "status": "FAILED",
                    "message": f"Unexpected error type: {type(e).__name__}: {e}"
                })
        
        except Exception as e:
            self.test_results.append({
                "test": "retry_mechanism",
                "status": "ERROR",
                "message": f"Test setup failed: {e}"
            })
        finally:
            self.restore_environment()
    
    async def test_worker_config_production_mode(self):
        """Test that WorkerConfig sets production mode correctly"""
        print("Testing WorkerConfig production mode...")
        
        try:
            self.setup_production_environment()
            
            config = WorkerConfig.from_environment()
            service_config = config.get_service_router_config()
            
            if service_config["mode"] == "REAL":
                self.test_results.append({
                    "test": "worker_config_production_mode",
                    "status": "PASSED",
                    "message": "Correctly set mode to REAL in production"
                })
            else:
                self.test_results.append({
                    "test": "worker_config_production_mode",
                    "status": "FAILED",
                    "message": f"Expected mode 'REAL', got '{service_config['mode']}'"
                })
            
            if not service_config["fallback_enabled"]:
                self.test_results.append({
                    "test": "worker_config_fallback_disabled",
                    "status": "PASSED",
                    "message": "Correctly disabled fallback in production"
                })
            else:
                self.test_results.append({
                    "test": "worker_config_fallback_disabled",
                    "status": "FAILED",
                    "message": "Fallback should be disabled in production"
                })
        
        except Exception as e:
            self.test_results.append({
                "test": "worker_config_production_mode",
                "status": "ERROR",
                "message": f"Test failed: {e}"
            })
        finally:
            self.restore_environment()
    
    async def run_all_tests(self):
        """Run all Phase 2 tests"""
        print("Starting Phase 2: Production API Reliability Test Suite")
        print("=" * 60)
        
        tests = [
            self.test_production_mode_validation,
            self.test_production_fallback_disabled,
            self.test_development_fallback_enabled,
            self.test_user_facing_error_uuid_generation,
            self.test_llamaparse_error_handling,
            self.test_retry_mechanism,
            self.test_worker_config_production_mode
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                print(f"Test {test.__name__} failed with exception: {e}")
        
        # Print results
        print("\n" + "=" * 60)
        print("PHASE 2 TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        failed = 0
        errors = 0
        
        for result in self.test_results:
            status = result["status"]
            if status == "PASSED":
                passed += 1
                print(f"✅ {result['test']}: {result['message']}")
            elif status == "FAILED":
                failed += 1
                print(f"❌ {result['test']}: {result['message']}")
            else:  # ERROR
                errors += 1
                print(f"🔥 {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        print(f"SUMMARY: {passed} passed, {failed} failed, {errors} errors")
        print("=" * 60)
        
        return {
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "total": len(self.test_results),
            "results": self.test_results
        }


async def main():
    """Main test runner"""
    test_suite = Phase2TestSuite()
    results = await test_suite.run_all_tests()
    
    # Exit with error code if any tests failed
    if results["failed"] > 0 or results["errors"] > 0:
        sys.exit(1)
    else:
        print("\n🎉 All Phase 2 tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
