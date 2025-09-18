#!/usr/bin/env python3
"""
Simplified Phase 2 Test - Focus on core functionality
"""

import asyncio
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.shared.exceptions import UserFacingError
from backend.shared.external.service_router import ServiceRouter, ServiceMode
from backend.shared.external.service_router import MockLlamaParseService
from backend.shared.config.worker_config import WorkerConfig


async def test_user_facing_error():
    """Test UserFacingError UUID generation"""
    print("Testing UserFacingError...")
    
    error = UserFacingError(
        message="Test error message",
        error_code="TEST_ERROR"
    )
    
    uuid = error.get_support_uuid()
    user_message = error.get_user_message()
    
    print(f"  UUID: {uuid}")
    print(f"  User message: {user_message}")
    
    assert len(uuid) == 36, "UUID should be 36 characters"
    assert uuid in user_message, "User message should include UUID"
    
    print("  ✅ UserFacingError test passed")


async def test_production_mode_validation():
    """Test production mode validation"""
    print("Testing production mode validation...")
    
    # Set production environment
    os.environ["ENVIRONMENT"] = "production"
    
    try:
        # This should fail in production
        config = {"mode": "mock"}
        router = ServiceRouter(config)
        print("  ❌ Should have failed for mock mode in production")
        return False
    except Exception as e:
        if "Mock mode is not allowed in production" in str(e):
            print("  ✅ Correctly rejected mock mode in production")
            return True
        else:
            print(f"  ❌ Unexpected error: {e}")
            return False
    finally:
        os.environ.pop("ENVIRONMENT", None)


async def test_worker_config():
    """Test WorkerConfig production settings"""
    print("Testing WorkerConfig...")
    
    # Set production environment
    os.environ["ENVIRONMENT"] = "production"
    
    try:
        config = WorkerConfig.from_environment()
        service_config = config.get_service_router_config()
        
        print(f"  Mode: {service_config['mode']}")
        print(f"  Fallback enabled: {service_config['fallback_enabled']}")
        
        assert service_config["mode"] == "REAL", "Should be REAL mode in production"
        assert not service_config["fallback_enabled"], "Fallback should be disabled in production"
        
        print("  ✅ WorkerConfig test passed")
        return True
    except Exception as e:
        print(f"  ❌ WorkerConfig test failed: {e}")
        return False
    finally:
        os.environ.pop("ENVIRONMENT", None)


async def test_service_router_fallback():
    """Test ServiceRouter fallback behavior"""
    print("Testing ServiceRouter fallback...")
    
    # Test development mode with fallback
    os.environ["ENVIRONMENT"] = "development"
    
    try:
        config = {
            "mode": "hybrid",
            "fallback_enabled": True
        }
        router = ServiceRouter(config)
        
        # Register services
        mock_service = MockLlamaParseService()
        # Create a mock real service that's unavailable
        class UnavailableService:
            async def is_available(self):
                return False
            async def get_health(self):
                return None
            async def execute(self, *args, **kwargs):
                raise Exception("Service unavailable")
        
        real_service = UnavailableService()
        router.register_service("llamaparse", mock_service, real_service)
        
        # Should get mock service in development
        service = await router.get_service("llamaparse")
        assert isinstance(service, MockLlamaParseService), "Should get mock service in development"
        
        print("  ✅ ServiceRouter fallback test passed")
        return True
    except Exception as e:
        print(f"  ❌ ServiceRouter fallback test failed: {e}")
        return False
    finally:
        os.environ.pop("ENVIRONMENT", None)


async def main():
    """Run all tests"""
    print("Phase 2 Simplified Test Suite")
    print("=" * 40)
    
    tests = [
        test_user_facing_error,
        test_production_mode_validation,
        test_worker_config,
        test_service_router_fallback
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 40)
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
