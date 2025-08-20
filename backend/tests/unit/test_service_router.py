"""
Unit tests for the service router functionality.

Tests service mode selection, health monitoring, and fallback behavior.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from backend.shared.external.service_router import (
    ServiceRouter, ServiceMode, ServiceInterface, ServiceHealth,
    ServiceUnavailableError, ServiceExecutionError
)


class MockService(ServiceInterface):
    """Mock service implementation for testing."""
    
    def __init__(self, name: str, is_available: bool = True, health_status: bool = True):
        self.name = name
        self._is_available = is_available
        self._health_status = health_status
        self.execution_count = 0
        self._fail_on_execute = False
    
    async def is_available(self) -> bool:
        return self._is_available
    
    async def get_health(self) -> ServiceHealth:
        return ServiceHealth(
            is_healthy=self._health_status,
            last_check=datetime.utcnow()
        )
    
    async def execute(self, *args, **kwargs):
        self.execution_count += 1
        if not self._is_available:
            raise ServiceUnavailableError(f"Service {self.name} unavailable")
        if self._fail_on_execute:
            raise ServiceExecutionError(f"Service {self.name} execution failed")
        return f"result_from_{self.name}_{self.execution_count}"


class TestServiceRouter:
    """Test cases for ServiceRouter class."""
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services for testing."""
        mock_llamaparse = MockService("llamaparse", is_available=True, health_status=True)
        real_llamaparse = MockService("llamaparse", is_available=True, health_status=True)
        
        mock_openai = MockService("openai", is_available=True, health_status=True)
        real_openai = MockService("openai", is_available=True, health_status=True)
        
        return {
            'llamaparse': {'mock': mock_llamaparse, 'real': real_llamaparse},
            'openai': {'mock': mock_openai, 'real': real_openai}
        }
    
    @pytest.fixture
    def router(self):
        """Create a service router instance."""
        return ServiceRouter(config={"mode": "hybrid"}, start_health_monitoring=False)
    
    def test_initialization(self, router):
        """Test router initialization."""
        assert router.mode == ServiceMode.HYBRID
        assert router.fallback_enabled is True
        assert router.fallback_timeout == 10
        assert len(router.services) == 0
        assert len(router.health_cache) == 0
    
    def test_register_service(self, router, mock_services):
        """Test service registration."""
        llamaparse_services = mock_services['llamaparse']
        router.register_service('llamaparse', llamaparse_services['mock'], llamaparse_services['real'])
        
        assert 'llamaparse' in router.services
        assert router.services['llamaparse']['mock'] == llamaparse_services['mock']
        assert router.services['llamaparse']['real'] == llamaparse_services['real']
    
    def test_set_mode(self, router):
        """Test service mode setting."""
        router.set_mode(ServiceMode.REAL)
        assert router.mode == ServiceMode.REAL
        
        router.set_mode(ServiceMode.MOCK)
        assert router.mode == ServiceMode.MOCK
    
    @pytest.mark.asyncio
    async def test_get_service_mock_mode(self, router, mock_services):
        """Test service selection in mock mode."""
        router.set_mode(ServiceMode.MOCK)
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        
        service = await router.get_service('llamaparse')
        assert service == mock_services['llamaparse']['mock']
    
    @pytest.mark.asyncio
    async def test_get_service_real_mode_available(self, router, mock_services):
        """Test service selection in real mode when real service is available."""
        router.set_mode(ServiceMode.REAL)
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        
        service = await router.get_service('llamaparse')
        assert service == mock_services['llamaparse']['real']
    
    @pytest.mark.asyncio
    async def test_get_service_real_mode_unavailable_with_fallback(self, router, mock_services):
        """Test service selection in real mode with fallback when real service unavailable."""
        router.set_mode(ServiceMode.REAL)
        router.fallback_enabled = True
        
        # Make real service unavailable
        mock_services['llamaparse']['real']._is_available = False
        
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        
        service = await router.get_service('llamaparse')
        assert service == mock_services['llamaparse']['mock']
    
    @pytest.mark.asyncio
    async def test_get_service_real_mode_unavailable_no_fallback(self, router, mock_services):
        """Test service selection in real mode without fallback when real service unavailable."""
        router.set_mode(ServiceMode.REAL)
        router.fallback_enabled = False
        
        # Make real service unavailable
        mock_services['llamaparse']['real']._is_available = False
        
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        
        with pytest.raises(ServiceUnavailableError):
            await router.get_service('llamaparse')
    
    @pytest.mark.asyncio
    async def test_get_service_hybrid_mode_real_available(self, router, mock_services):
        """Test service selection in hybrid mode when real service is available."""
        router.set_mode(ServiceMode.HYBRID)
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        
        service = await router.get_service('llamaparse')
        assert service == mock_services['llamaparse']['real']
    
    @pytest.mark.asyncio
    async def test_get_service_hybrid_mode_real_unavailable(self, router, mock_services):
        """Test service selection in hybrid mode when real service is unavailable."""
        router.set_mode(ServiceMode.HYBRID)
        
        # Make real service unavailable
        mock_services['llamaparse']['real']._is_available = False
        
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        
        service = await router.get_service('llamaparse')
        assert service == mock_services['llamaparse']['mock']
    
    @pytest.mark.asyncio
    async def test_get_service_unregistered(self, router):
        """Test getting unregistered service."""
        with pytest.raises(ServiceUnavailableError):
            await router.get_service('nonexistent')
    
    @pytest.mark.asyncio
    async def test_execute_service_success(self, router, mock_services):
        """Test successful service execution."""
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        
        result = await router.execute_service('llamaparse', 'test_arg', kwarg='test')
        assert result == "result_from_llamaparse_1"
        assert mock_services['llamaparse']['real'].execution_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_service_failure(self, router, mock_services):
        """Test service execution failure."""
        # Create a service that fails during execution
        failing_service = MockService("llamaparse", is_available=True, health_status=True)
        failing_service._fail_on_execute = True
        
        router.register_service('llamaparse', failing_service, 
                              mock_services['llamaparse']['real'])
        
        # Set to MOCK mode to use the failing service
        router.set_mode(ServiceMode.MOCK)
        
        with pytest.raises(ServiceExecutionError):
            await router.execute_service('llamaparse', 'test_arg')
    
    @pytest.mark.asyncio
    async def test_check_service_health(self, router, mock_services):
        """Test service health checking."""
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        
        health = await router.check_service_health('llamaparse')
        assert health.is_healthy is True
        assert health.last_check is not None
    
    @pytest.mark.asyncio
    async def test_check_service_health_unregistered(self, router):
        """Test health checking for unregistered service."""
        health = await router.check_service_health('nonexistent')
        assert health.is_healthy is False
        assert health.last_check is not None
    
    @pytest.mark.asyncio
    async def test_get_all_services_health(self, router, mock_services):
        """Test getting health for all services."""
        router.register_service('llamaparse', mock_services['llamaparse']['mock'], 
                              mock_services['llamaparse']['real'])
        router.register_service('openai', mock_services['openai']['mock'], 
                              mock_services['openai']['real'])
        
        health_status = await router.get_all_services_health()
        assert 'llamaparse' in health_status
        assert 'openai' in health_status
        assert all(health.is_healthy for health in health_status.values())
    
    def test_update_health_metrics_success(self, router):
        """Test health metrics update for successful operation."""
        router._update_health_metrics('test_service', True, 150.5)
        
        assert 'test_service' in router.health_cache
        health = router.health_cache['test_service']
        assert health.is_healthy is True
        assert health.response_time_ms == 150.5
        assert health.error_count == 0
        assert health.last_error is None
    
    def test_update_health_metrics_failure(self, router):
        """Test health metrics update for failed operation."""
        router._update_health_metrics('test_service', False, None, "Test error")
        
        assert 'test_service' in router.health_cache
        health = router.health_cache['test_service']
        assert health.is_healthy is False
        assert health.error_count == 1
        assert health.last_error == "Test error"
    
    @pytest.mark.asyncio
    async def test_close(self, router):
        """Test router close."""
        # Start health monitoring
        await asyncio.sleep(0.1)  # Allow monitoring to start
        
        # Close
        await router.close()
        
        # Verify close completed
        assert router._health_monitor_task is None or router._health_monitor_task.cancelled()


class TestServiceMode:
    """Test cases for ServiceMode enum."""
    
    def test_service_mode_values(self):
        """Test service mode enum values."""
        assert ServiceMode.MOCK.value == "mock"
        assert ServiceMode.REAL.value == "real"
        assert ServiceMode.HYBRID.value == "hybrid"
    
    def test_service_mode_comparison(self):
        """Test service mode comparison."""
        assert ServiceMode.MOCK != ServiceMode.REAL
        assert ServiceMode.HYBRID != ServiceMode.MOCK
        assert ServiceMode.REAL != ServiceMode.HYBRID


class TestServiceHealth:
    """Test cases for ServiceHealth dataclass."""
    
    def test_service_health_creation(self):
        """Test ServiceHealth creation."""
        now = datetime.utcnow()
        health = ServiceHealth(
            is_healthy=True,
            last_check=now,
            response_time_ms=100.5,
            error_count=0
        )
        
        assert health.is_healthy is True
        assert health.last_check == now
        assert health.response_time_ms == 100.5
        assert health.error_count == 0
        assert health.last_error is None
    
    def test_service_health_defaults(self):
        """Test ServiceHealth default values."""
        now = datetime.utcnow()
        health = ServiceHealth(is_healthy=True, last_check=now)
        
        assert health.response_time_ms is None
        assert health.error_count == 0
        assert health.last_error is None


class TestServiceInterface:
    """Test cases for ServiceInterface abstract class."""
    
    def test_service_interface_abstract(self):
        """Test that ServiceInterface cannot be instantiated."""
        with pytest.raises(TypeError):
            ServiceInterface()


class TestMockService:
    """Test cases for MockService implementation."""
    
    @pytest.fixture
    def mock_service(self):
        """Create a mock service instance."""
        return MockService("test_service", is_available=True, health_status=True)
    
    @pytest.mark.asyncio
    async def test_mock_service_availability(self, mock_service):
        """Test mock service availability."""
        assert await mock_service.is_available() is True
    
    @pytest.mark.asyncio
    async def test_mock_service_health(self, mock_service):
        """Test mock service health."""
        health = await mock_service.get_health()
        assert health.is_healthy is True
        assert health.last_check is not None
    
    @pytest.mark.asyncio
    async def test_mock_service_execution(self, mock_service):
        """Test mock service execution."""
        result = await mock_service.execute("test_arg")
        assert result == "result_from_test_service_1"
        assert mock_service.execution_count == 1
    
    @pytest.mark.asyncio
    async def test_mock_service_execution_failure(self):
        """Test mock service execution failure."""
        mock_service = MockService("test_service", is_available=False)
        
        with pytest.raises(ServiceUnavailableError):
            await mock_service.execute("test_arg")


# Integration test scenarios

class TestServiceRouterIntegration:
    """Integration test scenarios for ServiceRouter."""
    
    @pytest.fixture
    def complex_router(self):
        """Create a router with multiple services for integration testing."""
        router = ServiceRouter(config={"mode": "hybrid"}, start_health_monitoring=False)
        
        # Register multiple services
        router.register_service('llamaparse', 
                              MockService("llamaparse_mock", True, True),
                              MockService("llamaparse_real", True, True))
        
        router.register_service('openai',
                              MockService("openai_mock", True, True),
                              MockService("openai_real", True, True))
        
        return router
    
    @pytest.mark.asyncio
    async def test_service_mode_switching(self, complex_router):
        """Test switching between service modes."""
        # Test MOCK mode
        complex_router.set_mode(ServiceMode.MOCK)
        llamaparse_service = await complex_router.get_service('llamaparse')
        assert "mock" in str(llamaparse_service.name)
        
        # Test REAL mode
        complex_router.set_mode(ServiceMode.REAL)
        llamaparse_service = await complex_router.get_service('llamaparse')
        assert "real" in str(llamaparse_service.name)
        
        # Test HYBRID mode
        complex_router.set_mode(ServiceMode.HYBRID)
        llamaparse_service = await complex_router.get_service('llamaparse')
        assert "real" in str(llamaparse_service.name)  # Should prefer real when available
    
    @pytest.mark.asyncio
    async def test_concurrent_service_access(self, complex_router):
        """Test concurrent access to services."""
        async def access_service(service_name: str):
            service = await complex_router.get_service(service_name)
            result = await service.execute("test")
            return result
        
        # Access multiple services concurrently
        tasks = [
            access_service('llamaparse'),
            access_service('openai')
        ]
        
        results = await asyncio.gather(*tasks)
        assert len(results) == 2
        assert all("result_from" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_health_monitoring_integration(self, complex_router):
        """Test health monitoring integration."""
        # Wait for health monitoring to run
        await asyncio.sleep(0.1)
        
        # Check health status
        health_status = await complex_router.get_all_services_health()
        assert len(health_status) == 2
        assert all(health.is_healthy for health in health_status.values())


# Error handling test scenarios

class TestServiceRouterErrorHandling:
    """Test error handling scenarios for ServiceRouter."""
    
    @pytest.fixture
    def error_router(self):
        """Create a router with error-prone services."""
        router = ServiceRouter(config={"mode": "hybrid"}, start_health_monitoring=False)
        
        # Create services that will fail
        failing_mock = MockService("failing_mock", False, False)
        failing_real = MockService("failing_real", False, False)
        
        router.register_service('failing', failing_mock, failing_real)
        return router
    
    @pytest.mark.asyncio
    async def test_service_unavailable_error(self, error_router):
        """Test handling of service unavailable errors."""
        # Set to REAL mode to force use of real service
        error_router.set_mode(ServiceMode.REAL)
        error_router.fallback_enabled = False
        
        with pytest.raises(ServiceUnavailableError):
            await error_router.get_service('failing')
    
    @pytest.mark.asyncio
    async def test_service_execution_error(self, error_router):
        """Test handling of service execution errors."""
        with pytest.raises(ServiceExecutionError):
            await error_router.execute_service('failing', 'test')
    
    @pytest.mark.asyncio
    async def test_health_check_error_handling(self, error_router):
        """Test error handling during health checks."""
        health = await error_router.check_service_health('failing')
        assert health.is_healthy is False
        assert health.last_error is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
