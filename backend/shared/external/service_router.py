"""
Service Router for managing real vs mock service selection.

This module provides a unified interface for switching between mock and real
external services, enabling cost-controlled testing and development flexibility.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Type, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ServiceMode(Enum):
    """Service operation modes."""
    MOCK = "mock"
    REAL = "real"
    HYBRID = "hybrid"


@dataclass
class ServiceHealth:
    """Service health status information."""
    is_healthy: bool
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    last_error: Optional[str] = None


class ServiceInterface(ABC):
    """Abstract base class for service implementations."""
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the service is available."""
        pass
    
    @abstractmethod
    async def get_health(self) -> ServiceHealth:
        """Get current service health status."""
        pass
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the service operation."""
        pass


class MockService(ServiceInterface):
    """Mock service implementation for testing and fallback."""
    
    def __init__(self, name: str, is_available: bool = True, fail_on_execute: bool = False):
        self.name = name
        self._is_available = is_available
        self._fail_on_execute = fail_on_execute
        self.execution_count = 0
    
    async def is_available(self) -> bool:
        """Check if the service is available."""
        return self._is_available
    
    async def get_health(self) -> ServiceHealth:
        """Get current service health status."""
        return ServiceHealth(
            is_healthy=self._is_available,
            last_check=datetime.utcnow(),
            response_time_ms=1.0,
            error_count=0 if self._is_available else 1,
            last_error=None if self._is_available else f"Service {self.name} unavailable"
        )
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the service operation."""
        if not self._is_available:
            raise ServiceUnavailableError(f"Service {self.name} unavailable")
        if self._fail_on_execute:
            raise ServiceExecutionError(f"Service {self.name} execution failed")
        self.execution_count += 1
        return f"result_from_{self.name}_{self.execution_count}"


class MockLlamaParseService(MockService):
    """Mock LlamaParse service implementation."""
    
    def __init__(self, is_available: bool = True, fail_on_execute: bool = False):
        super().__init__("llamaparse", is_available, fail_on_execute)
    
    async def parse_document(self, file_path: str, correlation_id: str = None) -> Dict[str, Any]:
        """Mock document parsing."""
        if self._fail_on_execute:
            raise ServiceExecutionError("Mock LlamaParse parsing failed")
        
        return {
            "status": "success",
            "content": f"Mock parsed content from {file_path}",
            "metadata": {
                "file_path": file_path,
                "correlation_id": correlation_id,
                "parsed_at": datetime.utcnow().isoformat()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {
            "status": "healthy" if self._is_available else "unhealthy",
            "service": "llamaparse",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def close(self):
        """Mock close method."""
        pass


class MockOpenAIService(MockService):
    """Mock OpenAI service implementation."""
    
    def __init__(self, is_available: bool = True, fail_on_execute: bool = False):
        super().__init__("openai", is_available, fail_on_execute)
    
    async def generate_embeddings(self, texts: List[str], correlation_id: str = None) -> List[List[float]]:
        """Mock embedding generation."""
        if self._fail_on_execute:
            raise ServiceExecutionError("Mock OpenAI embedding generation failed")
        
        # Generate mock embeddings (1536-dimensional vectors)
        import random
        random.seed(42)  # For consistent test results
        
        embeddings = []
        for i, text in enumerate(texts):
            # Generate deterministic mock embedding
            embedding = [random.uniform(-1, 1) for _ in range(1536)]
            embeddings.append(embedding)
        
        return embeddings
    
    async def health_check(self) -> Dict[str, Any]:
        """Mock health check."""
        return {
            "status": "healthy" if self._is_available else "unhealthy",
            "service": "openai",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def close(self):
        """Mock close method."""
        pass


class ServiceRouter:
    """
    Service router for managing service selection and fallback logic.
    
    The router manages service mode switching, health monitoring, and
    automatic fallback to mock services when real services are unavailable.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, start_health_monitoring: bool = False):
        # Parse configuration
        if config is None:
            config = {}
        
        # Parse mode from config, default to hybrid
        mode_str = config.get("mode", "hybrid")
        if isinstance(mode_str, str):
            try:
                self.mode = ServiceMode(mode_str.lower())
            except ValueError:
                logger.warning(f"Invalid mode '{mode_str}', defaulting to hybrid")
                self.mode = ServiceMode.HYBRID
        else:
            self.mode = ServiceMode.HYBRID
        self.services: Dict[str, Dict[str, ServiceInterface]] = {}
        self.health_cache: Dict[str, ServiceHealth] = {}
        self.health_check_interval = 30  # seconds
        self.fallback_enabled = config.get("fallback_enabled", True)
        self.fallback_timeout = config.get("fallback_timeout", 10)  # seconds
        
        # Health monitoring setup (but don't start yet)
        self._health_monitor_task = None
        self._health_monitoring_started = False
        
        # Auto-register services if configuration is provided
        if config:
            self._auto_register_services(config)
        
        # Note: Health monitoring will be started explicitly when needed
        # Don't start it during initialization to avoid blocking
    
    def _auto_register_services(self, config: Dict[str, Any]) -> None:
        """Automatically register services based on configuration"""
        try:
            # Import here to avoid circular imports
            from .llamaparse_real import LlamaParseReal
            from .openai_real import RealOpenAIService
            
            # Register LlamaParse service
            if "llamaparse_config" in config:
                llamaparse_config = config["llamaparse_config"]
                mock_llamaparse = MockLlamaParseService()
                real_llamaparse = LlamaParseReal(llamaparse_config)
                self.register_service("llamaparse", mock_llamaparse, real_llamaparse)
            
            # Register OpenAI service
            if "openai_config" in config:
                openai_config = config["openai_config"]
                mock_openai = MockOpenAIService()
                real_openai = RealOpenAIService(
                    api_key=openai_config["api_key"],
                    base_url=openai_config["api_url"],
                    rate_limit_per_minute=openai_config.get("requests_per_minute", 3500),
                    timeout_seconds=openai_config.get("timeout_seconds", 30),
                    max_retries=openai_config.get("max_retries", 3),
                    max_batch_size=openai_config.get("max_batch_size", 256)
                )
                self.register_service("openai", mock_openai, real_openai)
                
        except ImportError as e:
            logger.warning(f"Could not auto-register services: {e}")
        except Exception as e:
            logger.error(f"Error auto-registering services: {e}")
    
    def register_service(self, service_name: str, mock_impl: ServiceInterface, 
                        real_impl: ServiceInterface) -> None:
        """
        Register mock and real implementations for a service.
        
        Args:
            service_name: Name of the service (e.g., 'llamaparse', 'openai')
            mock_impl: Mock service implementation
            real_impl: Real service implementation
        """
        self.services[service_name] = {
            'mock': mock_impl,
            'real': real_impl
        }
        logger.info(f"Registered service: {service_name}")
    
    def set_mode(self, mode: ServiceMode) -> None:
        """Set the service operation mode."""
        self.mode = mode
        logger.info(f"Service mode changed to: {mode.value}")
    
    async def get_service(self, service_name: str) -> ServiceInterface:
        """
        Get the appropriate service implementation based on current mode.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            ServiceInterface: The selected service implementation
            
        Raises:
            ServiceUnavailableError: If no service is available
        """
        if service_name not in self.services:
            raise ServiceUnavailableError(f"Service '{service_name}' not registered")
        
        mock_service = self.services[service_name]['mock']
        real_service = self.services[service_name]['real']
        
        if self.mode == ServiceMode.MOCK:
            return mock_service
        
        elif self.mode == ServiceMode.REAL:
            if await real_service.is_available():
                return real_service
            elif self.fallback_enabled:
                logger.warning(f"Real service '{service_name}' unavailable, falling back to mock")
                return mock_service
            else:
                raise ServiceUnavailableError(f"Real service '{service_name}' unavailable and fallback disabled")
        
        elif self.mode == ServiceMode.HYBRID:
            # Try real service first, fallback to mock if unavailable
            if await real_service.is_available():
                return real_service
            else:
                logger.info(f"Real service '{service_name}' unavailable, using mock service")
                return mock_service
        
        # Should never reach here
        raise ValueError(f"Invalid service mode: {self.mode}")
    
    async def execute_service(self, service_name: str, *args, **kwargs) -> Any:
        """
        Execute a service operation with automatic service selection.
        
        Args:
            service_name: Name of the service to execute
            *args: Positional arguments for the service operation
            **kwargs: Keyword arguments for the service operation
            
        Returns:
            Any: Result from the service operation
            
        Raises:
            ServiceUnavailableError: If no service is available
            ServiceExecutionError: If the service operation fails
        """
        service = await self.get_service(service_name)
        
        try:
            start_time = datetime.utcnow()
            result = await service.execute(*args, **kwargs)
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update health metrics
            self._update_health_metrics(service_name, True, execution_time)
            
            return result
            
        except Exception as e:
            # Update health metrics
            self._update_health_metrics(service_name, False, None, str(e))
            raise ServiceExecutionError(f"Service '{service_name}' execution failed: {e}") from e
    
    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Check the health of a specific service."""
        if service_name not in self.services:
            return ServiceHealth(is_healthy=False, last_check=datetime.utcnow())
        
        try:
            real_service = self.services[service_name]['real']
            # Check if service is available first
            if not await real_service.is_available():
                return ServiceHealth(
                    is_healthy=False, 
                    last_check=datetime.utcnow(),
                    last_error="Service unavailable"
                )
            
            health = await real_service.get_health()
            self.health_cache[service_name] = health
            return health
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return ServiceHealth(
                is_healthy=False, 
                last_check=datetime.utcnow(),
                last_error=str(e)
            )
    
    async def get_all_services_health(self) -> Dict[str, ServiceHealth]:
        """Get health status for all registered services."""
        health_status = {}
        for service_name in self.services:
            health_status[service_name] = await self.check_service_health(service_name)
        return health_status
    
    def _update_health_metrics(self, service_name: str, success: bool, 
                              response_time_ms: Optional[float], error: Optional[str] = None) -> None:
        """Update health metrics for a service."""
        if service_name not in self.health_cache:
            self.health_cache[service_name] = ServiceHealth(
                is_healthy=True, 
                last_check=datetime.utcnow()
            )
        
        health = self.health_cache[service_name]
        health.last_check = datetime.utcnow()
        
        if success:
            health.is_healthy = True
            health.error_count = 0
            health.last_error = None
            if response_time_ms is not None:
                health.response_time_ms = response_time_ms
        else:
            health.is_healthy = False
            health.error_count += 1
            health.last_error = error
    
    def _start_health_monitoring(self) -> None:
        """Start background health monitoring task."""
        if self._health_monitoring_started:
            logger.info("Health monitoring already started")
            return
            
        try:
            async def health_monitor():
                while True:
                    try:
                        await self._monitor_services_health()
                        await asyncio.sleep(self.health_check_interval)
                    except Exception as e:
                        logger.error(f"Health monitoring error: {e}")
                        await asyncio.sleep(10)  # Shorter sleep on error
            
            self._health_monitor_task = asyncio.create_task(health_monitor())
            self._health_monitoring_started = True
            logger.info("Health monitoring started")
        except RuntimeError as e:
            if "no running event loop" in str(e):
                logger.warning("No event loop available, health monitoring will start when needed")
                self._health_monitoring_started = False
            else:
                raise
    
    async def _monitor_services_health(self) -> None:
        """Monitor health of all services."""
        for service_name in self.services:
            try:
                await self.check_service_health(service_name)
            except Exception as e:
                logger.error(f"Health monitoring failed for {service_name}: {e}")
    
    def start_health_monitoring(self) -> None:
        """Manually start health monitoring if not already started."""
        if not self._health_monitoring_started:
            self._start_health_monitoring()
    
    async def close(self) -> None:
        """Close the service router and cleanup resources."""
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
            self._health_monitor_task = None
        
        # Close all services
        for service_name, implementations in self.services.items():
            for impl_type, impl in implementations.items():
                if hasattr(impl, 'close'):
                    try:
                        await impl.close()
                    except Exception as e:
                        logger.warning(f"Error closing {impl_type} implementation of {service_name}: {e}")
        
        self._health_monitoring_started = False
        logger.info("ServiceRouter closed")
    
    # Convenience methods for BaseWorker integration
    
    async def generate_embeddings(self, texts: List[str], correlation_id: str = None) -> List[List[float]]:
        """Generate embeddings using the OpenAI service."""
        service = await self.get_service("openai")
        
        # Try generate_embeddings first (for compatibility with OpenAIClient)
        if hasattr(service, 'generate_embeddings'):
            return await service.generate_embeddings(texts, correlation_id)
        
        # Try create_embeddings (for RealOpenAIService)
        elif hasattr(service, 'create_embeddings'):
            response = await service.create_embeddings(texts, correlation_id=correlation_id)
            # Extract embeddings from the response
            return [item["embedding"] for item in response.data]
        
        else:
            raise ServiceExecutionError("OpenAI service does not support embedding generation")
    
    async def parse_document(self, file_path: str, correlation_id: str = None) -> Dict[str, Any]:
        """Parse document using the LlamaParse service."""
        service = await self.get_service("llamaparse")
        if hasattr(service, 'parse_document'):
            return await service.parse_document(file_path, correlation_id)
        else:
            raise ServiceExecutionError("LlamaParse service does not support parse_document")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get overall health status of all services."""
        try:
            all_health = await self.get_all_services_health()
            
            # Determine overall status
            healthy_services = sum(1 for health in all_health.values() if health.is_healthy)
            total_services = len(all_health)
            
            overall_status = "healthy" if healthy_services == total_services else "degraded"
            if healthy_services == 0:
                overall_status = "unhealthy"
            
            return {
                "status": overall_status,
                "healthy_services": healthy_services,
                "total_services": total_services,
                "services": all_health,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Exception classes for comprehensive error handling

class ServiceUnavailableError(Exception):
    """Raised when a service is unavailable."""
    
    def __init__(self, message: str, service_name: Optional[str] = None):
        self.service_name = service_name
        super().__init__(message)


class ServiceExecutionError(Exception):
    """Raised when a service operation fails."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 original_error: Optional[Exception] = None):
        self.service_name = service_name
        self.original_error = original_error
        super().__init__(message)


class ServiceConfigurationError(Exception):
    """Raised when service configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        self.config_key = config_key
        super().__init__(message)


# Factory function for creating service router instances

def create_service_router(mode: ServiceMode = ServiceMode.HYBRID) -> ServiceRouter:
    """
    Create a service router instance with the specified mode.
    
    Args:
        mode: Initial service operation mode
        
    Returns:
        ServiceRouter: Configured service router instance
    """
    return ServiceRouter(mode=mode)
