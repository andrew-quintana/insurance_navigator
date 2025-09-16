"""
Phase 3 Integration Test Suite

Comprehensive integration tests to validate system components work together
correctly with all resilience features enabled.
"""

import pytest
import asyncio
import logging
from typing import Dict, Any
import time
import os

# Import resilience components
from core.resilience import (
    get_system_monitor,
    get_degradation_registry,
    get_circuit_breaker_registry,
    AlertLevel
)

# Import configuration and service management
from config.configuration_manager import get_config_manager
from core.service_manager import get_service_manager

logger = logging.getLogger(__name__)

class TestPhase3Integration:
    """Integration tests for Phase 3 resilience features."""
    
    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup and teardown for integration tests."""
        # Setup
        self.system_monitor = get_system_monitor()
        self.degradation_registry = get_degradation_registry()
        self.circuit_breaker_registry = get_circuit_breaker_registry()
        
        yield
        
        # Teardown - reset any test state
        # Reset circuit breakers
        await self.circuit_breaker_registry.reset_all()
    
    @pytest.mark.asyncio
    async def test_system_monitor_initialization(self):
        """Test that system monitor initializes correctly."""
        # Test system monitor is available
        assert self.system_monitor is not None
        
        # Test system status
        system_status = await self.system_monitor.get_system_status()
        
        # Validate system status structure
        assert "overall_health" in system_status
        assert "status" in system_status
        assert "health_checks" in system_status
        assert "active_alerts" in system_status
        assert "timestamp" in system_status
        
        # Health should be a float between 0 and 1
        assert isinstance(system_status["overall_health"], float)
        assert 0.0 <= system_status["overall_health"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_degradation_registry_setup(self):
        """Test that degradation managers are properly registered."""
        # Test degradation registry is available
        assert self.degradation_registry is not None
        
        # Test expected degradation managers are registered
        service_levels = self.degradation_registry.get_all_levels()
        
        expected_services = ["rag", "upload", "database"]
        for service in expected_services:
            assert service in service_levels, f"Degradation manager for {service} not registered"
        
        # Test service levels are valid
        for service, level in service_levels.items():
            assert level.value in ["full", "degraded", "minimal", "unavailable"]
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_registry_setup(self):
        """Test that circuit breakers are properly configured."""
        # Test circuit breaker registry is available
        assert self.circuit_breaker_registry is not None
        
        # Test circuit breaker stats
        all_stats = await self.circuit_breaker_registry.get_all_stats()
        
        # Should have some circuit breakers registered
        assert len(all_stats) > 0, "No circuit breakers registered"
        
        # Test circuit breaker states
        for name, stats in all_stats.items():
            assert stats.state.value in ["closed", "open", "half_open"]
            assert stats.total_calls >= 0
            assert stats.total_failures >= 0
            assert stats.total_successes >= 0
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_functionality(self):
        """Test graceful degradation works correctly."""
        # Get RAG degradation manager
        rag_degradation = self.degradation_registry.get("rag")
        assert rag_degradation is not None
        
        # Test successful execution
        async def successful_operation():
            return {"result": "success", "data": "test_data"}
        
        result = await rag_degradation.execute_with_fallback(successful_operation)
        
        assert result.success is True
        assert result.service_level.value == "full"
        assert result.result["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_fallback(self):
        """Test graceful degradation fallback mechanisms."""
        # Get RAG degradation manager
        rag_degradation = self.degradation_registry.get("rag")
        assert rag_degradation is not None
        
        # Test failed operation that should trigger fallback
        async def failing_operation():
            raise Exception("Simulated service failure")
        
        result = await rag_degradation.execute_with_fallback(failing_operation)
        
        # Should succeed with fallback
        assert result.success is True
        assert result.service_level.value in ["degraded", "minimal"]
        assert result.strategy_used is not None
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self):
        """Test circuit breaker protection works correctly."""
        # Create a test circuit breaker
        from core.resilience import CircuitBreakerConfig, CircuitBreaker
        
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=1,
            timeout=1.0
        )
        
        circuit_breaker = CircuitBreaker("test_breaker", config)
        
        # Test successful operation
        async def successful_operation():
            return "success"
        
        result = await circuit_breaker.call(successful_operation)
        assert result == "success"
        assert circuit_breaker.is_closed()
        
        # Test failing operation
        async def failing_operation():
            raise Exception("Test failure")
        
        # Trigger failures to open circuit
        for _ in range(3):
            try:
                await circuit_breaker.call(failing_operation)
            except Exception:
                pass  # Expected failures
        
        # Circuit should be open after failures
        assert circuit_breaker.is_open()
    
    @pytest.mark.asyncio
    async def test_monitoring_metrics_collection(self):
        """Test that monitoring collects metrics correctly."""
        metrics = self.system_monitor.metrics
        
        # Record test metrics
        await metrics.increment_counter("test.counter", 1.0, {"test": "phase3"})
        await metrics.set_gauge("test.gauge", 42.0, {"test": "phase3"})
        await metrics.record_timer("test.timer", 1.5, {"test": "phase3"})
        
        # Verify metrics were recorded
        counter_value = await metrics.get_latest_value("test.counter")
        gauge_value = await metrics.get_latest_value("test.gauge")
        timer_value = await metrics.get_latest_value("test.timer")
        
        assert counter_value == 1.0
        assert gauge_value == 42.0
        assert timer_value == 1.5
    
    @pytest.mark.asyncio
    async def test_alert_system_functionality(self):
        """Test that alert system works correctly."""
        alert_manager = self.system_monitor.alerts
        
        # Create test alert
        alert = await alert_manager.create_alert(
            "test_alert_001",
            AlertLevel.WARNING,
            "Test Alert",
            "This is a test alert for Phase 3 validation",
            "integration_test",
            {"test": "phase3"}
        )
        
        assert alert.id == "test_alert_001"
        assert alert.level == AlertLevel.WARNING
        assert alert.title == "Test Alert"
        assert not alert.resolved
        
        # Test alert retrieval
        active_alerts = await alert_manager.get_active_alerts()
        assert len(active_alerts) >= 1
        assert any(alert.id == "test_alert_001" for alert in active_alerts)
        
        # Test alert resolution
        resolved = await alert_manager.resolve_alert("test_alert_001")
        assert resolved is True
        
        # Verify alert is resolved
        active_alerts_after = await alert_manager.get_active_alerts()
        assert not any(alert.id == "test_alert_001" for alert in active_alerts_after)
    
    @pytest.mark.asyncio
    async def test_service_manager_integration(self):
        """Test service manager integration with resilience features."""
        service_manager = get_service_manager()
        
        # Test service manager is initialized
        assert service_manager is not None
        
        # Test service registration with circuit breaker
        service_manager.register_service(
            name="test_service",
            service_type=dict,
            enable_circuit_breaker=True
        )
        
        # Verify service is registered
        assert "test_service" in service_manager._services
        service_info = service_manager._services["test_service"]
        assert service_info.enable_circuit_breaker is True
    
    @pytest.mark.asyncio
    async def test_configuration_manager_integration(self):
        """Test configuration manager integration."""
        config_manager = get_config_manager()
        
        # Test configuration manager is available
        assert config_manager is not None
        
        # Test environment detection
        environment = config_manager.get_environment()
        assert environment is not None
        
        # Test RAG configuration
        rag_threshold = config_manager.get_rag_similarity_threshold()
        assert isinstance(rag_threshold, float)
        assert 0.0 < rag_threshold <= 1.0
        
        # Test configuration validation
        config_dict = config_manager.to_dict()
        assert "environment" in config_dict
        assert "database" in config_dict
        assert "rag" in config_dict
        assert "api" in config_dict
        assert "service" in config_dict
    
    @pytest.mark.asyncio
    async def test_end_to_end_resilience_flow(self):
        """Test complete resilience flow from request to response."""
        # This test simulates a complete request flow with resilience features
        
        # 1. Test metric recording
        metrics = self.system_monitor.metrics
        start_time = time.time()
        
        # 2. Test degradation manager
        rag_degradation = self.degradation_registry.get("rag")
        
        # 3. Simulate a service call with potential failure
        async def simulated_service_call():
            # Simulate some processing time
            await asyncio.sleep(0.1)
            return {"status": "success", "data": "processed_data"}
        
        # 4. Execute with degradation protection
        result = await rag_degradation.execute_with_fallback(simulated_service_call)
        
        # 5. Record metrics
        duration = time.time() - start_time
        await metrics.record_timer("test.end_to_end_flow", duration, {"test": "phase3"})
        
        # 6. Validate results
        assert result.success is True
        assert result.result is not None
        assert result.execution_time > 0
        
        # 7. Verify metric was recorded
        recorded_duration = await metrics.get_latest_value("test.end_to_end_flow")
        assert recorded_duration is not None
        assert recorded_duration > 0

# Pytest configuration for Phase 3 tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test configuration
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest for Phase 3 integration tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "resilience: mark test as a resilience feature test"
    )

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.resilience]
