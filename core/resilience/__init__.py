"""
Production Resilience Module

This module provides comprehensive production resilience capabilities including:
- Circuit breaker patterns for service protection
- Graceful degradation with fallback strategies
- System monitoring and alerting
- Error handling and recovery mechanisms

Phase 3.1 Implementation: Error Handling and Resilience
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerState,
    CircuitBreakerStats,
    CircuitBreakerOpenException,
    CircuitBreakerRegistry,
    get_circuit_breaker_registry,
    create_api_circuit_breaker,
    create_database_circuit_breaker,
    create_rag_circuit_breaker
)

from .graceful_degradation import (
    GracefulDegradationManager,
    DegradationConfig,
    DegradationResult,
    ServiceLevel,
    FallbackStrategy,
    StaticFallback,
    CachedFallback,
    FunctionFallback,
    RAGServiceDegradation,
    UploadServiceDegradation,
    DatabaseServiceDegradation,
    DegradationRegistry,
    get_degradation_registry,
    create_rag_degradation_manager,
    create_upload_degradation_manager,
    create_database_degradation_manager
)

from .monitoring import (
    SystemMonitor,
    MetricsCollector,
    AlertManager,
    HealthMonitor,
    MetricPoint,
    MetricType,
    Alert,
    AlertLevel,
    HealthCheck,
    get_system_monitor,
    MetricTimer,
    time_metric
)

__all__ = [
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitBreakerConfig',
    'CircuitBreakerState',
    'CircuitBreakerStats',
    'CircuitBreakerOpenException',
    'CircuitBreakerRegistry',
    'get_circuit_breaker_registry',
    'create_api_circuit_breaker',
    'create_database_circuit_breaker',
    'create_rag_circuit_breaker',
    
    # Graceful Degradation
    'GracefulDegradationManager',
    'DegradationConfig',
    'DegradationResult',
    'ServiceLevel',
    'FallbackStrategy',
    'StaticFallback',
    'CachedFallback',
    'FunctionFallback',
    'RAGServiceDegradation',
    'UploadServiceDegradation',
    'DatabaseServiceDegradation',
    'DegradationRegistry',
    'get_degradation_registry',
    'create_rag_degradation_manager',
    'create_upload_degradation_manager',
    'create_database_degradation_manager',
    
    # Monitoring
    'SystemMonitor',
    'MetricsCollector',
    'AlertManager',
    'HealthMonitor',
    'MetricPoint',
    'MetricType',
    'Alert',
    'AlertLevel',
    'HealthCheck',
    'get_system_monitor',
    'MetricTimer',
    'time_metric'
]
