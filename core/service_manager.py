"""
Service Manager for Insurance Navigator System

This module provides a centralized service management system that handles
service registration, dependency injection, lifecycle management, and health checks.
Enhanced with production resilience features including circuit breakers and monitoring.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Type, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

# Import resilience components
from .resilience import (
    CircuitBreaker,
    CircuitBreakerConfig,
    get_circuit_breaker_registry,
    get_system_monitor
)

logger = logging.getLogger("ServiceManager")

class ServiceStatus(Enum):
    """Service status enumeration."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

@dataclass
class ServiceInfo:
    """Service information container."""
    name: str
    service_type: Type
    instance: Optional[Any] = None
    status: ServiceStatus = ServiceStatus.UNINITIALIZED
    dependencies: List[str] = field(default_factory=list)
    health_check: Optional[Callable] = None
    init_func: Optional[Callable] = None
    shutdown_func: Optional[Callable] = None
    error_message: Optional[str] = None
    last_health_check: Optional[float] = None
    circuit_breaker: Optional[CircuitBreaker] = None
    enable_circuit_breaker: bool = True

class ServiceManager:
    """
    Centralized service manager for the Insurance Navigator system.
    
    Provides service registration, dependency injection, lifecycle management,
    and health monitoring for all system services.
    """
    
    def __init__(self):
        """Initialize the service manager."""
        self._services: Dict[str, ServiceInfo] = {}
        self._initialization_order: List[str] = []
        self._is_initialized = False
        self._is_shutting_down = False
        self._logger = logging.getLogger("ServiceManager")
        self._circuit_breaker_registry = get_circuit_breaker_registry()
        self._system_monitor = get_system_monitor()
    
    def register_service(
        self,
        name: str,
        service_type: Type,
        dependencies: Optional[List[str]] = None,
        health_check: Optional[Callable] = None,
        init_func: Optional[Callable] = None,
        shutdown_func: Optional[Callable] = None,
        enable_circuit_breaker: bool = True
    ) -> None:
        """
        Register a service with the service manager.
        
        Args:
            name: Unique service name
            service_type: Service class type
            dependencies: List of service names this service depends on
            health_check: Optional health check function
            init_func: Optional custom initialization function
            shutdown_func: Optional custom shutdown function
            enable_circuit_breaker: Whether to enable circuit breaker for this service
        """
        if name in self._services:
            raise ValueError(f"Service '{name}' is already registered")
        
        # Circuit breaker will be created during initialization
        # Store the flag to enable it during service initialization
        
        self._services[name] = ServiceInfo(
            name=name,
            service_type=service_type,
            dependencies=dependencies or [],
            health_check=health_check,
            init_func=init_func,
            shutdown_func=shutdown_func,
            circuit_breaker=None,  # Will be created during initialization
            enable_circuit_breaker=enable_circuit_breaker
        )
        
        self._logger.info(f"Registered service: {name}")
    
    def get_service(self, name: str) -> Optional[Any]:
        """
        Get a service instance by name.
        
        Args:
            name: Service name
            
        Returns:
            Service instance or None if not found/initialized
        """
        service_info = self._services.get(name)
        if not service_info or service_info.status != ServiceStatus.HEALTHY:
            return None
        return service_info.instance
    
    def get_service_status(self, name: str) -> Optional[ServiceStatus]:
        """
        Get the status of a service.
        
        Args:
            name: Service name
            
        Returns:
            Service status or None if not found
        """
        service_info = self._services.get(name)
        return service_info.status if service_info else None
    
    async def initialize_all_services(self) -> bool:
        """
        Initialize all registered services in dependency order.
        
        Returns:
            True if all services initialized successfully, False otherwise
        """
        if self._is_initialized:
            self._logger.warning("Services already initialized")
            return True
        
        if self._is_shutting_down:
            self._logger.error("Cannot initialize services during shutdown")
            return False
        
        try:
            # Calculate initialization order based on dependencies
            self._initialization_order = self._calculate_initialization_order()
            
            # Initialize services in order
            for service_name in self._initialization_order:
                success = await self._initialize_service(service_name)
                if not success:
                    self._logger.error(f"Failed to initialize service: {service_name}")
                    return False
            
            self._is_initialized = True
            self._logger.info("All services initialized successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Service initialization failed: {e}")
            return False
    
    async def shutdown_all_services(self) -> bool:
        """
        Shutdown all services in reverse initialization order.
        
        Returns:
            True if all services shutdown successfully, False otherwise
        """
        if not self._is_initialized:
            self._logger.warning("Services not initialized")
            return True
        
        if self._is_shutting_down:
            self._logger.warning("Shutdown already in progress")
            return False
        
        self._is_shutting_down = True
        
        try:
            # Shutdown services in reverse order
            for service_name in reversed(self._initialization_order):
                await self._shutdown_service(service_name)
            
            self._is_initialized = False
            self._is_shutting_down = False
            self._logger.info("All services shutdown successfully")
            return True
            
        except Exception as e:
            self._logger.error(f"Service shutdown failed: {e}")
            return False
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Perform health check on all services.
        
        Returns:
            Dictionary of service health statuses
        """
        health_status = {}
        
        for service_name, service_info in self._services.items():
            try:
                if service_info.health_check:
                    is_healthy = await self._run_health_check(service_info)
                    health_status[service_name] = {
                        "status": service_info.status.value,
                        "healthy": is_healthy,
                        "last_check": service_info.last_health_check,
                        "error": service_info.error_message
                    }
                else:
                    health_status[service_name] = {
                        "status": service_info.status.value,
                        "healthy": service_info.status == ServiceStatus.HEALTHY,
                        "last_check": service_info.last_health_check,
                        "error": service_info.error_message
                    }
            except Exception as e:
                health_status[service_name] = {
                    "status": service_info.status.value,
                    "healthy": False,
                    "last_check": service_info.last_health_check,
                    "error": str(e)
                }
        
        return health_status
    
    def _calculate_initialization_order(self) -> List[str]:
        """Calculate the order in which services should be initialized."""
        # Simple topological sort for dependency resolution
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(service_name: str):
            if service_name in temp_visited:
                raise ValueError(f"Circular dependency detected involving service: {service_name}")
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            service_info = self._services[service_name]
            
            # Visit dependencies first
            for dep in service_info.dependencies:
                if dep not in self._services:
                    raise ValueError(f"Service '{service_name}' depends on unknown service: {dep}")
                visit(dep)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            order.append(service_name)
        
        for service_name in self._services:
            if service_name not in visited:
                visit(service_name)
        
        return order
    
    async def _initialize_service(self, service_name: str) -> bool:
        """Initialize a single service."""
        service_info = self._services[service_name]
        service_info.status = ServiceStatus.INITIALIZING
        
        try:
            # Check dependencies are healthy
            for dep_name in service_info.dependencies:
                dep_info = self._services[dep_name]
                if dep_info.status != ServiceStatus.HEALTHY:
                    raise ValueError(f"Dependency '{dep_name}' is not healthy for service '{service_name}'")
            
            # Create circuit breaker if enabled
            if service_info.enable_circuit_breaker:
                try:
                    if service_name == "database":
                        from .resilience import create_database_circuit_breaker
                        circuit_breaker = create_database_circuit_breaker(f"service_{service_name}")
                    elif service_name == "rag":
                        from .resilience import create_rag_circuit_breaker
                        circuit_breaker = create_rag_circuit_breaker(f"service_{service_name}")
                    else:
                        from .resilience import create_api_circuit_breaker
                        circuit_breaker = create_api_circuit_breaker(f"service_{service_name}")
                    
                    service_info.circuit_breaker = circuit_breaker
                    self._logger.info(f"Created circuit breaker for service: {service_name}")
                    
                except Exception as e:
                    self._logger.warning(f"Failed to create circuit breaker for service '{service_name}': {e}")
            
            # Initialize service with circuit breaker protection if available
            if service_info.circuit_breaker:
                if service_info.init_func:
                    service_info.instance = await service_info.circuit_breaker.call(service_info.init_func)
                else:
                    # Default initialization - try to instantiate the service type
                    if hasattr(service_info.service_type, '__call__'):
                        service_info.instance = service_info.service_type()
                    else:
                        raise ValueError(f"Cannot initialize service type: {service_info.service_type}")
            else:
                # Initialize without circuit breaker
                if service_info.init_func:
                    service_info.instance = await service_info.init_func()
                else:
                    # Default initialization - try to instantiate the service type
                    if hasattr(service_info.service_type, '__call__'):
                        service_info.instance = service_info.service_type()
                    else:
                        raise ValueError(f"Cannot initialize service type: {service_info.service_type}")
            
            # Run health check if available
            if service_info.health_check:
                is_healthy = await self._run_health_check(service_info)
                if not is_healthy:
                    service_info.status = ServiceStatus.FAILED
                    return False
            
            service_info.status = ServiceStatus.HEALTHY
            service_info.error_message = None
            
            # Record service initialization metric
            await self._system_monitor.metrics.increment_counter(
                f"service.{service_name}.initialized",
                tags={"service": service_name}
            )
            
            self._logger.info(f"Service '{service_name}' initialized successfully")
            return True
            
        except Exception as e:
            service_info.status = ServiceStatus.FAILED
            service_info.error_message = str(e)
            
            # Record service initialization failure
            await self._system_monitor.metrics.increment_counter(
                f"service.{service_name}.initialization_failed",
                tags={"service": service_name, "error": str(e)[:100]}
            )
            
            # Create alert for service initialization failure
            await self._system_monitor.alerts.create_alert(
                f"service_init_failed_{service_name}",
                self._system_monitor.alerts.AlertLevel.ERROR,
                f"Service Initialization Failed: {service_name}",
                f"Service '{service_name}' failed to initialize: {str(e)}",
                "service_manager",
                {"service": service_name}
            )
            
            self._logger.error(f"Failed to initialize service '{service_name}': {e}")
            return False
    
    async def _shutdown_service(self, service_name: str) -> None:
        """Shutdown a single service."""
        service_info = self._services[service_name]
        service_info.status = ServiceStatus.SHUTTING_DOWN
        
        try:
            if service_info.shutdown_func:
                await service_info.shutdown_func(service_info.instance)
            elif hasattr(service_info.instance, 'shutdown'):
                await service_info.instance.shutdown()
            elif hasattr(service_info.instance, 'close'):
                await service_info.instance.close()
            
            service_info.status = ServiceStatus.SHUTDOWN
            service_info.instance = None
            self._logger.info(f"Service '{service_name}' shutdown successfully")
            
        except Exception as e:
            service_info.status = ServiceStatus.FAILED
            service_info.error_message = str(e)
            self._logger.error(f"Failed to shutdown service '{service_name}': {e}")
    
    async def _run_health_check(self, service_info: ServiceInfo) -> bool:
        """Run health check for a service."""
        try:
            if asyncio.iscoroutinefunction(service_info.health_check):
                result = await service_info.health_check(service_info.instance)
            else:
                result = service_info.health_check(service_info.instance)
            
            service_info.last_health_check = asyncio.get_event_loop().time()
            return bool(result)
            
        except Exception as e:
            service_info.error_message = str(e)
            service_info.last_health_check = asyncio.get_event_loop().time()
            return False
    
    def get_initialization_order(self) -> List[str]:
        """Get the service initialization order."""
        return self._initialization_order.copy()
    
    def is_initialized(self) -> bool:
        """Check if all services are initialized."""
        return self._is_initialized
    
    def is_shutting_down(self) -> bool:
        """Check if services are shutting down."""
        return self._is_shutting_down

# Global service manager instance
_service_manager: Optional[ServiceManager] = None

def get_service_manager() -> ServiceManager:
    """Get the global service manager instance."""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager

def initialize_service_manager() -> ServiceManager:
    """Initialize the global service manager."""
    global _service_manager
    _service_manager = ServiceManager()
    return _service_manager
