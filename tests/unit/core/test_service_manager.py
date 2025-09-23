"""
Unit tests for core service manager module.

Tests the ServiceManager class and related functionality including:
- Service registration and discovery
- Dependency injection and lifecycle management
- Health checking and monitoring
- Circuit breaker integration
- Error handling and recovery
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, Optional

from core.service_manager import (
    ServiceManager,
    ServiceInfo,
    ServiceStatus,
    get_service_manager,
    initialize_service_manager
)


class MockService:
    """Mock service for testing."""
    
    def __init__(self, name: str = "test_service", should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.initialized = False
        self.shutdown_called = False
    
    async def initialize(self):
        """Mock initialization."""
        if self.should_fail:
            raise Exception("Service initialization failed")
        self.initialized = True
    
    async def shutdown(self):
        """Mock shutdown."""
        self.shutdown_called = True
    
    async def health_check(self):
        """Mock health check."""
        return not self.should_fail


class TestServiceInfo:
    """Test ServiceInfo dataclass."""
    
    def test_service_info_creation(self):
        """Test basic service info creation."""
        service_info = ServiceInfo(
            name="test_service",
            service_type=MockService,
            dependencies=["dep1", "dep2"],
            enable_circuit_breaker=True
        )
        
        assert service_info.name == "test_service"
        assert service_info.service_type == MockService
        assert service_info.dependencies == ["dep1", "dep2"]
        assert service_info.status == ServiceStatus.UNINITIALIZED
        assert service_info.enable_circuit_breaker is True
        assert service_info.instance is None
        assert service_info.health_check is None
        assert service_info.init_func is None
        assert service_info.shutdown_func is None
        assert service_info.error_message is None
        assert service_info.last_health_check is None
        assert service_info.circuit_breaker is None


class TestServiceManager:
    """Test ServiceManager class."""
    
    @pytest.fixture
    def service_manager(self):
        """Create a ServiceManager instance."""
        return ServiceManager()
    
    def test_service_manager_initialization(self, service_manager):
        """Test service manager initialization."""
        assert service_manager._services == {}
        assert service_manager._initialization_order == []
        assert service_manager._is_initialized is False
        assert service_manager._is_shutting_down is False
    
    def test_register_service_success(self, service_manager):
        """Test successful service registration."""
        service_manager.register_service(
            name="test_service",
            service_type=MockService,
            dependencies=["dep1"],
            health_check=lambda x: True
        )
        
        assert "test_service" in service_manager._services
        service_info = service_manager._services["test_service"]
        assert service_info.name == "test_service"
        assert service_info.service_type == MockService
        assert service_info.dependencies == ["dep1"]
        assert service_info.health_check is not None
    
    def test_register_service_duplicate(self, service_manager):
        """Test registering duplicate service."""
        service_manager.register_service("test_service", MockService)
        
        with pytest.raises(ValueError, match="Service 'test_service' is already registered"):
            service_manager.register_service("test_service", MockService)
    
    def test_get_service_not_found(self, service_manager):
        """Test getting non-existent service."""
        result = service_manager.get_service("nonexistent")
        assert result is None
    
    def test_get_service_not_healthy(self, service_manager):
        """Test getting service that's not healthy."""
        service_manager.register_service("test_service", MockService)
        service_info = service_manager._services["test_service"]
        service_info.status = ServiceStatus.FAILED
        
        result = service_manager.get_service("test_service")
        assert result is None
    
    def test_get_service_success(self, service_manager):
        """Test getting healthy service."""
        service_manager.register_service("test_service", MockService)
        service_info = service_manager._services["test_service"]
        service_info.status = ServiceStatus.HEALTHY
        service_info.instance = Mock()
        
        result = service_manager.get_service("test_service")
        assert result == service_info.instance
    
    def test_get_service_status_not_found(self, service_manager):
        """Test getting status of non-existent service."""
        result = service_manager.get_service_status("nonexistent")
        assert result is None
    
    def test_get_service_status_success(self, service_manager):
        """Test getting service status."""
        service_manager.register_service("test_service", MockService)
        service_info = service_manager._services["test_service"]
        service_info.status = ServiceStatus.HEALTHY
        
        result = service_manager.get_service_status("test_service")
        assert result == ServiceStatus.HEALTHY
    
    def test_calculate_initialization_order_no_dependencies(self, service_manager):
        """Test initialization order calculation with no dependencies."""
        service_manager.register_service("service1", MockService)
        service_manager.register_service("service2", MockService)
        
        order = service_manager._calculate_initialization_order()
        assert len(order) == 2
        assert "service1" in order
        assert "service2" in order
    
    def test_calculate_initialization_order_with_dependencies(self, service_manager):
        """Test initialization order calculation with dependencies."""
        service_manager.register_service("service1", MockService)
        service_manager.register_service("service2", MockService, dependencies=["service1"])
        service_manager.register_service("service3", MockService, dependencies=["service2"])
        
        order = service_manager._calculate_initialization_order()
        assert order == ["service1", "service2", "service3"]
    
    def test_calculate_initialization_order_circular_dependency(self, service_manager):
        """Test initialization order with circular dependency."""
        service_manager.register_service("service1", MockService, dependencies=["service2"])
        service_manager.register_service("service2", MockService, dependencies=["service1"])
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            service_manager._calculate_initialization_order()
    
    def test_calculate_initialization_order_unknown_dependency(self, service_manager):
        """Test initialization order with unknown dependency."""
        service_manager.register_service("service1", MockService, dependencies=["unknown"])
        
        with pytest.raises(ValueError, match="depends on unknown service"):
            service_manager._calculate_initialization_order()
    
    @pytest.mark.asyncio
    async def test_initialize_all_services_success(self, service_manager):
        """Test successful initialization of all services."""
        service_manager.register_service("service1", MockService)
        service_manager.register_service("service2", MockService, dependencies=["service1"])
        
        with patch.object(service_manager, '_initialize_service', return_value=True) as mock_init:
            result = await service_manager.initialize_all_services()
            
            assert result is True
            assert service_manager._is_initialized is True
            assert mock_init.call_count == 2
    
    @pytest.mark.asyncio
    async def test_initialize_all_services_already_initialized(self, service_manager):
        """Test initialization when already initialized."""
        service_manager._is_initialized = True
        
        with patch.object(service_manager, '_initialize_service') as mock_init:
            result = await service_manager.initialize_all_services()
            
            assert result is True
            mock_init.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_initialize_all_services_during_shutdown(self, service_manager):
        """Test initialization during shutdown."""
        service_manager._is_shutting_down = True
        
        result = await service_manager.initialize_all_services()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_initialize_all_services_failure(self, service_manager):
        """Test initialization failure."""
        service_manager.register_service("service1", MockService)
        
        with patch.object(service_manager, '_initialize_service', return_value=False):
            result = await service_manager.initialize_all_services()
            
            assert result is False
            assert service_manager._is_initialized is False
    
    @pytest.mark.asyncio
    async def test_initialize_service_success(self, service_manager):
        """Test successful service initialization."""
        service_manager.register_service("test_service", MockService)
        
        with patch('core.service_manager.create_api_circuit_breaker') as mock_cb:
            mock_circuit_breaker = AsyncMock()
            mock_cb.return_value = mock_circuit_breaker
            
            result = await service_manager._initialize_service("test_service")
            
            assert result is True
            service_info = service_manager._services["test_service"]
            assert service_info.status == ServiceStatus.HEALTHY
            assert service_info.instance is not None
            assert service_info.circuit_breaker == mock_circuit_breaker
    
    @pytest.mark.asyncio
    async def test_initialize_service_with_custom_init_func(self, service_manager):
        """Test service initialization with custom init function."""
        async def custom_init():
            return MockService("custom")
        
        service_manager.register_service(
            "test_service", 
            MockService, 
            init_func=custom_init
        )
        
        with patch('core.service_manager.create_api_circuit_breaker') as mock_cb:
            mock_circuit_breaker = AsyncMock()
            mock_circuit_breaker.call.return_value = MockService("custom")
            mock_cb.return_value = mock_circuit_breaker
            
            result = await service_manager._initialize_service("test_service")
            
            assert result is True
            service_info = service_manager._services["test_service"]
            assert service_info.instance.name == "custom"
    
    @pytest.mark.asyncio
    async def test_initialize_service_dependency_not_healthy(self, service_manager):
        """Test service initialization when dependency is not healthy."""
        service_manager.register_service("dep_service", MockService)
        service_manager.register_service("test_service", MockService, dependencies=["dep_service"])
        
        # Set dependency as failed
        dep_info = service_manager._services["dep_service"]
        dep_info.status = ServiceStatus.FAILED
        
        result = await service_manager._initialize_service("test_service")
        
        assert result is False
        service_info = service_manager._services["test_service"]
        assert service_info.status == ServiceStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_initialize_service_failure(self, service_manager):
        """Test service initialization failure."""
        service_manager.register_service("test_service", MockService)
        
        with patch('core.service_manager.create_api_circuit_breaker') as mock_cb:
            mock_circuit_breaker = AsyncMock()
            mock_circuit_breaker.call.side_effect = Exception("Initialization failed")
            mock_cb.return_value = mock_circuit_breaker
            
            result = await service_manager._initialize_service("test_service")
            
            assert result is False
            service_info = service_manager._services["test_service"]
            assert service_info.status == ServiceStatus.FAILED
            assert "Initialization failed" in service_info.error_message
    
    @pytest.mark.asyncio
    async def test_initialize_service_without_circuit_breaker(self, service_manager):
        """Test service initialization without circuit breaker."""
        service_manager.register_service(
            "test_service", 
            MockService, 
            enable_circuit_breaker=False
        )
        
        result = await service_manager._initialize_service("test_service")
        
        assert result is True
        service_info = service_manager._services["test_service"]
        assert service_info.status == ServiceStatus.HEALTHY
        assert service_info.circuit_breaker is None
    
    @pytest.mark.asyncio
    async def test_initialize_service_health_check_failure(self, service_manager):
        """Test service initialization with health check failure."""
        def failing_health_check(instance):
            return False
        
        service_manager.register_service(
            "test_service", 
            MockService, 
            health_check=failing_health_check
        )
        
        with patch('core.service_manager.create_api_circuit_breaker') as mock_cb:
            mock_circuit_breaker = AsyncMock()
            mock_circuit_breaker.call.return_value = MockService()
            mock_cb.return_value = mock_circuit_breaker
            
            result = await service_manager._initialize_service("test_service")
            
            assert result is False
            service_info = service_manager._services["test_service"]
            assert service_info.status == ServiceStatus.FAILED
    
    @pytest.mark.asyncio
    async def test_shutdown_all_services_success(self, service_manager):
        """Test successful shutdown of all services."""
        service_manager.register_service("service1", MockService)
        service_manager.register_service("service2", MockService)
        service_manager._is_initialized = True
        service_manager._initialization_order = ["service1", "service2"]
        
        with patch.object(service_manager, '_shutdown_service') as mock_shutdown:
            result = await service_manager.shutdown_all_services()
            
            assert result is True
            assert service_manager._is_initialized is False
            assert service_manager._is_shutting_down is False
            assert mock_shutdown.call_count == 2
            # Should be called in reverse order
            assert mock_shutdown.call_args_list[0][0][0] == "service2"
            assert mock_shutdown.call_args_list[1][0][0] == "service1"
    
    @pytest.mark.asyncio
    async def test_shutdown_all_services_not_initialized(self, service_manager):
        """Test shutdown when not initialized."""
        result = await service_manager.shutdown_all_services()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_shutdown_all_services_during_shutdown(self, service_manager):
        """Test shutdown during shutdown."""
        service_manager._is_shutting_down = True
        
        result = await service_manager.shutdown_all_services()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_shutdown_service_success(self, service_manager):
        """Test successful service shutdown."""
        service_manager.register_service("test_service", MockService)
        service_info = service_manager._services["test_service"]
        service_info.instance = MockService()
        service_info.status = ServiceStatus.HEALTHY
        
        await service_manager._shutdown_service("test_service")
        
        assert service_info.status == ServiceStatus.SHUTDOWN
        assert service_info.instance is None
    
    @pytest.mark.asyncio
    async def test_shutdown_service_with_custom_shutdown_func(self, service_manager):
        """Test service shutdown with custom shutdown function."""
        async def custom_shutdown(instance):
            instance.custom_shutdown_called = True
        
        service_manager.register_service(
            "test_service", 
            MockService, 
            shutdown_func=custom_shutdown
        )
        service_info = service_manager._services["test_service"]
        service_info.instance = MockService()
        service_info.status = ServiceStatus.HEALTHY
        
        await service_manager._shutdown_service("test_service")
        
        assert service_info.status == ServiceStatus.SHUTDOWN
        assert service_info.instance is None
    
    @pytest.mark.asyncio
    async def test_shutdown_service_failure(self, service_manager):
        """Test service shutdown failure."""
        service_manager.register_service("test_service", MockService)
        service_info = service_manager._services["test_service"]
        service_info.instance = MockService(should_fail=True)
        service_info.status = ServiceStatus.HEALTHY
        
        await service_manager._shutdown_service("test_service")
        
        assert service_info.status == ServiceStatus.FAILED
        assert service_info.error_message is not None
    
    @pytest.mark.asyncio
    async def test_health_check_all_success(self, service_manager):
        """Test health check on all services."""
        service_manager.register_service("service1", MockService)
        service_manager.register_service("service2", MockService)
        
        service_info1 = service_manager._services["service1"]
        service_info1.status = ServiceStatus.HEALTHY
        service_info1.instance = MockService()
        service_info1.health_check = lambda x: True
        
        service_info2 = service_manager._services["service2"]
        service_info2.status = ServiceStatus.HEALTHY
        service_info2.instance = MockService()
        service_info2.health_check = lambda x: True
        
        result = await service_manager.health_check_all()
        
        assert "service1" in result
        assert "service2" in result
        assert result["service1"]["healthy"] is True
        assert result["service2"]["healthy"] is True
    
    @pytest.mark.asyncio
    async def test_health_check_all_with_failures(self, service_manager):
        """Test health check with service failures."""
        service_manager.register_service("service1", MockService)
        service_manager.register_service("service2", MockService)
        
        service_info1 = service_manager._services["service1"]
        service_info1.status = ServiceStatus.HEALTHY
        service_info1.instance = MockService()
        service_info1.health_check = lambda x: True
        
        service_info2 = service_manager._services["service2"]
        service_info2.status = ServiceStatus.HEALTHY
        service_info2.instance = MockService()
        service_info2.health_check = lambda x: False  # Failing health check
        
        result = await service_manager.health_check_all()
        
        assert result["service1"]["healthy"] is True
        assert result["service2"]["healthy"] is False
    
    @pytest.mark.asyncio
    async def test_health_check_all_with_exceptions(self, service_manager):
        """Test health check with exceptions."""
        service_manager.register_service("service1", MockService)
        
        service_info1 = service_manager._services["service1"]
        service_info1.status = ServiceStatus.HEALTHY
        service_info1.instance = MockService()
        service_info1.health_check = lambda x: (_ for _ in ()).throw(Exception("Health check failed"))
        
        result = await service_manager.health_check_all()
        
        assert result["service1"]["healthy"] is False
        assert "Health check failed" in result["service1"]["error"]
    
    @pytest.mark.asyncio
    async def test_run_health_check_success(self, service_manager):
        """Test successful health check execution."""
        service_info = ServiceInfo(
            name="test_service",
            service_type=MockService,
            health_check=lambda x: True
        )
        service_info.instance = MockService()
        
        result = await service_manager._run_health_check(service_info)
        
        assert result is True
        assert service_info.last_health_check is not None
        assert service_info.error_message is None
    
    @pytest.mark.asyncio
    async def test_run_health_check_async_success(self, service_manager):
        """Test successful async health check execution."""
        async def async_health_check(instance):
            return True
        
        service_info = ServiceInfo(
            name="test_service",
            service_type=MockService,
            health_check=async_health_check
        )
        service_info.instance = MockService()
        
        result = await service_manager._run_health_check(service_info)
        
        assert result is True
        assert service_info.last_health_check is not None
        assert service_info.error_message is None
    
    @pytest.mark.asyncio
    async def test_run_health_check_failure(self, service_manager):
        """Test health check execution failure."""
        service_info = ServiceInfo(
            name="test_service",
            service_type=MockService,
            health_check=lambda x: False
        )
        service_info.instance = MockService()
        
        result = await service_manager._run_health_check(service_info)
        
        assert result is False
        assert service_info.last_health_check is not None
        assert service_info.error_message is None
    
    @pytest.mark.asyncio
    async def test_run_health_check_exception(self, service_manager):
        """Test health check execution with exception."""
        service_info = ServiceInfo(
            name="test_service",
            service_type=MockService,
            health_check=lambda x: (_ for _ in ()).throw(Exception("Health check error"))
        )
        service_info.instance = MockService()
        
        result = await service_manager._run_health_check(service_info)
        
        assert result is False
        assert service_info.last_health_check is not None
        assert "Health check error" in service_info.error_message
    
    def test_get_initialization_order(self, service_manager):
        """Test getting initialization order."""
        service_manager.register_service("service1", MockService)
        service_manager.register_service("service2", MockService, dependencies=["service1"])
        service_manager._initialization_order = ["service1", "service2"]
        
        result = service_manager.get_initialization_order()
        
        assert result == ["service1", "service2"]
        # Should be a copy, not the original
        assert result is not service_manager._initialization_order
    
    def test_is_initialized(self, service_manager):
        """Test initialization status check."""
        assert service_manager.is_initialized() is False
        
        service_manager._is_initialized = True
        assert service_manager.is_initialized() is True
    
    def test_is_shutting_down(self, service_manager):
        """Test shutdown status check."""
        assert service_manager.is_shutting_down() is False
        
        service_manager._is_shutting_down = True
        assert service_manager.is_shutting_down() is True


class TestGlobalServiceManager:
    """Test global service manager functions."""
    
    def test_get_service_manager_singleton(self):
        """Test service manager singleton pattern."""
        manager1 = get_service_manager()
        manager2 = get_service_manager()
        
        assert manager1 is manager2
        assert isinstance(manager1, ServiceManager)
    
    def test_initialize_service_manager(self):
        """Test service manager initialization."""
        manager = initialize_service_manager()
        
        assert isinstance(manager, ServiceManager)
        assert manager is get_service_manager()


class TestServiceManagerIntegration:
    """Integration tests for ServiceManager."""
    
    @pytest.mark.asyncio
    async def test_full_service_lifecycle(self):
        """Test complete service lifecycle."""
        manager = ServiceManager()
        
        # Register services with dependencies
        manager.register_service("database", MockService)
        manager.register_service("api", MockService, dependencies=["database"])
        manager.register_service("worker", MockService, dependencies=["database", "api"])
        
        # Initialize all services
        with patch.object(manager, '_initialize_service', return_value=True) as mock_init:
            result = await manager.initialize_all_services()
            
            assert result is True
            assert manager.is_initialized() is True
            assert mock_init.call_count == 3
        
        # Check service statuses
        assert manager.get_service_status("database") == ServiceStatus.HEALTHY
        assert manager.get_service_status("api") == ServiceStatus.HEALTHY
        assert manager.get_service_status("worker") == ServiceStatus.HEALTHY
        
        # Shutdown all services
        with patch.object(manager, '_shutdown_service') as mock_shutdown:
            result = await manager.shutdown_all_services()
            
            assert result is True
            assert manager.is_initialized() is False
            assert mock_shutdown.call_count == 3
    
    @pytest.mark.asyncio
    async def test_service_dependency_resolution(self):
        """Test service dependency resolution."""
        manager = ServiceManager()
        
        # Register services in random order
        manager.register_service("worker", MockService, dependencies=["api", "database"])
        manager.register_service("api", MockService, dependencies=["database"])
        manager.register_service("database", MockService)
        
        # Calculate initialization order
        order = manager._calculate_initialization_order()
        
        # Database should be first, then api, then worker
        assert order == ["database", "api", "worker"]
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self):
        """Test health monitoring across services."""
        manager = ServiceManager()
        
        # Register services with health checks
        manager.register_service(
            "healthy_service", 
            MockService, 
            health_check=lambda x: True
        )
        manager.register_service(
            "unhealthy_service", 
            MockService, 
            health_check=lambda x: False
        )
        
        # Set up service instances
        manager._services["healthy_service"].instance = MockService()
        manager._services["healthy_service"].status = ServiceStatus.HEALTHY
        manager._services["unhealthy_service"].instance = MockService()
        manager._services["unhealthy_service"].status = ServiceStatus.HEALTHY
        
        # Run health checks
        health_status = await manager.health_check_all()
        
        assert health_status["healthy_service"]["healthy"] is True
        assert health_status["unhealthy_service"]["healthy"] is False


if __name__ == "__main__":
    pytest.main([__file__])
