"""
Graceful Degradation System for Production Resilience

This module provides graceful degradation mechanisms that allow the system
to continue functioning with reduced capability when services fail.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ServiceLevel(Enum):
    """Service operation levels for graceful degradation."""
    FULL = "full"               # Full functionality
    DEGRADED = "degraded"       # Reduced functionality
    MINIMAL = "minimal"         # Basic functionality only
    UNAVAILABLE = "unavailable" # Service unavailable

@dataclass
class DegradationConfig:
    """Configuration for graceful degradation."""
    enabled: bool = True
    default_level: ServiceLevel = ServiceLevel.FULL
    fallback_level: ServiceLevel = ServiceLevel.DEGRADED
    timeout_seconds: float = 30.0
    max_retries: int = 2
    
    def validate(self) -> bool:
        """Validate degradation configuration."""
        if self.timeout_seconds <= 0:
            logger.error(f"Invalid timeout: {self.timeout_seconds}")
            return False
        if self.max_retries < 0:
            logger.error(f"Invalid max_retries: {self.max_retries}")
            return False
        return True

class FallbackStrategy(ABC):
    """Abstract base class for fallback strategies."""
    
    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the fallback strategy."""
        pass
    
    @abstractmethod
    def get_service_level(self) -> ServiceLevel:
        """Get the service level this strategy provides."""
        pass

class StaticFallback(FallbackStrategy):
    """Static fallback that returns a predetermined response."""
    
    def __init__(self, response: Any, service_level: ServiceLevel = ServiceLevel.MINIMAL):
        self.response = response
        self.service_level = service_level
    
    async def execute(self, *args, **kwargs) -> Any:
        """Return the static response."""
        return self.response
    
    def get_service_level(self) -> ServiceLevel:
        """Get the service level."""
        return self.service_level

class CachedFallback(FallbackStrategy):
    """Fallback that returns cached data when available."""
    
    def __init__(self, cache_key: str, service_level: ServiceLevel = ServiceLevel.DEGRADED):
        self.cache_key = cache_key
        self.service_level = service_level
        self._cache: Dict[str, Any] = {}
    
    async def execute(self, *args, **kwargs) -> Any:
        """Return cached data if available."""
        if self.cache_key in self._cache:
            logger.info(f"Returning cached data for key: {self.cache_key}")
            return self._cache[self.cache_key]
        else:
            raise ValueError(f"No cached data available for key: {self.cache_key}")
    
    def get_service_level(self) -> ServiceLevel:
        """Get the service level."""
        return self.service_level
    
    def set_cache(self, data: Any) -> None:
        """Set cached data."""
        self._cache[self.cache_key] = data
        logger.debug(f"Cached data for key: {self.cache_key}")

class FunctionFallback(FallbackStrategy):
    """Fallback that executes an alternative function."""
    
    def __init__(self, fallback_func: Callable, service_level: ServiceLevel = ServiceLevel.DEGRADED):
        self.fallback_func = fallback_func
        self.service_level = service_level
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute the fallback function."""
        if asyncio.iscoroutinefunction(self.fallback_func):
            return await self.fallback_func(*args, **kwargs)
        else:
            return self.fallback_func(*args, **kwargs)
    
    def get_service_level(self) -> ServiceLevel:
        """Get the service level."""
        return self.service_level

@dataclass
class DegradationResult:
    """Result of a graceful degradation operation."""
    success: bool
    result: Any = None
    service_level: ServiceLevel = ServiceLevel.UNAVAILABLE
    strategy_used: Optional[str] = None
    error: Optional[Exception] = None
    execution_time: float = 0.0

class GracefulDegradationManager:
    """
    Manager for graceful degradation strategies.
    
    Provides fallback mechanisms when primary services fail,
    allowing the system to continue operating with reduced functionality.
    """
    
    def __init__(self, name: str, config: DegradationConfig):
        """
        Initialize graceful degradation manager.
        
        Args:
            name: Manager name for logging
            config: Degradation configuration
        """
        self.name = name
        self.config = config
        self.fallback_strategies: List[FallbackStrategy] = []
        self.current_level = config.default_level
        
        if not config.validate():
            raise ValueError(f"Invalid degradation configuration for '{name}'")
        
        logger.info(f"Graceful degradation manager '{name}' initialized")
    
    def add_fallback(self, strategy: FallbackStrategy) -> None:
        """Add a fallback strategy."""
        self.fallback_strategies.append(strategy)
        logger.debug(f"Added fallback strategy for '{self.name}': {strategy.__class__.__name__}")
    
    async def execute_with_fallback(
        self, 
        primary_func: Callable, 
        *args, 
        **kwargs
    ) -> DegradationResult:
        """
        Execute primary function with fallback support.
        
        Args:
            primary_func: Primary function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            DegradationResult containing execution result and metadata
        """
        import time
        start_time = time.time()
        
        if not self.config.enabled:
            # Degradation disabled, execute primary function only
            try:
                if asyncio.iscoroutinefunction(primary_func):
                    result = await primary_func(*args, **kwargs)
                else:
                    result = primary_func(*args, **kwargs)
                
                execution_time = time.time() - start_time
                return DegradationResult(
                    success=True,
                    result=result,
                    service_level=ServiceLevel.FULL,
                    execution_time=execution_time
                )
            except Exception as e:
                execution_time = time.time() - start_time
                return DegradationResult(
                    success=False,
                    error=e,
                    execution_time=execution_time
                )
        
        # Try primary function first
        try:
            if asyncio.iscoroutinefunction(primary_func):
                result = await asyncio.wait_for(
                    primary_func(*args, **kwargs),
                    timeout=self.config.timeout_seconds
                )
            else:
                result = primary_func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            self.current_level = ServiceLevel.FULL
            
            return DegradationResult(
                success=True,
                result=result,
                service_level=ServiceLevel.FULL,
                execution_time=execution_time
            )
            
        except Exception as primary_error:
            logger.warning(f"Primary function failed for '{self.name}': {primary_error}")
            
            # Try fallback strategies in order
            for i, strategy in enumerate(self.fallback_strategies):
                try:
                    result = await strategy.execute(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.current_level = strategy.get_service_level()
                    
                    logger.info(
                        f"Fallback strategy {i+1} succeeded for '{self.name}': "
                        f"{strategy.__class__.__name__} (level: {self.current_level.value})"
                    )
                    
                    return DegradationResult(
                        success=True,
                        result=result,
                        service_level=strategy.get_service_level(),
                        strategy_used=strategy.__class__.__name__,
                        execution_time=execution_time
                    )
                    
                except Exception as fallback_error:
                    logger.warning(
                        f"Fallback strategy {i+1} failed for '{self.name}': {fallback_error}"
                    )
                    continue
            
            # All strategies failed
            execution_time = time.time() - start_time
            self.current_level = ServiceLevel.UNAVAILABLE
            
            logger.error(f"All fallback strategies failed for '{self.name}'")
            return DegradationResult(
                success=False,
                error=primary_error,
                execution_time=execution_time
            )
    
    def get_current_level(self) -> ServiceLevel:
        """Get current service level."""
        return self.current_level
    
    def set_level(self, level: ServiceLevel) -> None:
        """Manually set service level."""
        old_level = self.current_level
        self.current_level = level
        logger.info(f"Service level for '{self.name}' changed from {old_level.value} to {level.value}")
    
    def is_degraded(self) -> bool:
        """Check if service is currently degraded."""
        return self.current_level != ServiceLevel.FULL
    
    def is_available(self) -> bool:
        """Check if service is available at any level."""
        return self.current_level != ServiceLevel.UNAVAILABLE

class RAGServiceDegradation(GracefulDegradationManager):
    """Specialized graceful degradation for RAG services."""
    
    def __init__(self, config: DegradationConfig):
        super().__init__("RAG", config)
        
        # Add standard RAG fallback strategies
        self._setup_rag_fallbacks()
    
    def _setup_rag_fallbacks(self) -> None:
        """Setup RAG-specific fallback strategies."""
        # Fallback 1: Return cached results if available
        cached_fallback = CachedFallback("rag_cache", ServiceLevel.DEGRADED)
        self.add_fallback(cached_fallback)
        
        # Fallback 2: Return generic helpful message
        generic_response = {
            "content": "I apologize, but I'm currently unable to access your documents. Please try again in a moment, or contact support if the issue persists.",
            "confidence": 0.0,
            "sources": ["system"],
            "processing_time": 0.0,
            "agent_sources": ["system"]
        }
        static_fallback = StaticFallback(generic_response, ServiceLevel.MINIMAL)
        self.add_fallback(static_fallback)

class UploadServiceDegradation(GracefulDegradationManager):
    """Specialized graceful degradation for upload services."""
    
    def __init__(self, config: DegradationConfig):
        super().__init__("Upload", config)
        
        # Add standard upload fallback strategies
        self._setup_upload_fallbacks()
    
    def _setup_upload_fallbacks(self) -> None:
        """Setup upload-specific fallback strategies."""
        # Fallback 1: Queue for later processing
        async def queue_for_later(*args, **kwargs):
            # In a real implementation, this would queue the upload
            return {
                "status": "queued",
                "message": "Upload queued for processing when service recovers",
                "retry_after": 300  # 5 minutes
            }
        
        queue_fallback = FunctionFallback(queue_for_later, ServiceLevel.DEGRADED)
        self.add_fallback(queue_fallback)
        
        # Fallback 2: Return service unavailable message
        unavailable_response = {
            "status": "unavailable",
            "message": "Upload service is temporarily unavailable. Please try again later.",
            "retry_after": 600  # 10 minutes
        }
        static_fallback = StaticFallback(unavailable_response, ServiceLevel.MINIMAL)
        self.add_fallback(static_fallback)

class DatabaseServiceDegradation(GracefulDegradationManager):
    """Specialized graceful degradation for database services."""
    
    def __init__(self, config: DegradationConfig):
        super().__init__("Database", config)
        
        # Add standard database fallback strategies
        self._setup_database_fallbacks()
    
    def _setup_database_fallbacks(self) -> None:
        """Setup database-specific fallback strategies."""
        # Fallback 1: Return cached data
        cached_fallback = CachedFallback("db_cache", ServiceLevel.DEGRADED)
        self.add_fallback(cached_fallback)
        
        # Fallback 2: Return empty results with warning
        empty_response = {
            "data": [],
            "message": "Database temporarily unavailable. Showing cached or limited data.",
            "degraded": True
        }
        static_fallback = StaticFallback(empty_response, ServiceLevel.MINIMAL)
        self.add_fallback(static_fallback)

# Registry for degradation managers
class DegradationRegistry:
    """Registry for managing graceful degradation managers."""
    
    def __init__(self):
        self._managers: Dict[str, GracefulDegradationManager] = {}
    
    def register(self, name: str, manager: GracefulDegradationManager) -> None:
        """Register a degradation manager."""
        self._managers[name] = manager
        logger.info(f"Registered degradation manager: {name}")
    
    def get(self, name: str) -> Optional[GracefulDegradationManager]:
        """Get degradation manager by name."""
        return self._managers.get(name)
    
    def get_all_levels(self) -> Dict[str, ServiceLevel]:
        """Get current service levels for all managers."""
        return {name: manager.get_current_level() for name, manager in self._managers.items()}
    
    def get_degraded_services(self) -> List[str]:
        """Get list of services currently running in degraded mode."""
        return [
            name for name, manager in self._managers.items()
            if manager.is_degraded()
        ]
    
    def get_unavailable_services(self) -> List[str]:
        """Get list of services currently unavailable."""
        return [
            name for name, manager in self._managers.items()
            if not manager.is_available()
        ]

# Global degradation registry
_degradation_registry: Optional[DegradationRegistry] = None

def get_degradation_registry() -> DegradationRegistry:
    """Get the global degradation registry."""
    global _degradation_registry
    if _degradation_registry is None:
        _degradation_registry = DegradationRegistry()
    return _degradation_registry

# Convenience functions for creating common degradation managers
def create_rag_degradation_manager() -> RAGServiceDegradation:
    """Create a degradation manager for RAG services."""
    config = DegradationConfig(
        enabled=True,
        timeout_seconds=30.0,
        max_retries=2
    )
    return RAGServiceDegradation(config)

def create_upload_degradation_manager() -> UploadServiceDegradation:
    """Create a degradation manager for upload services."""
    config = DegradationConfig(
        enabled=True,
        timeout_seconds=60.0,
        max_retries=1
    )
    return UploadServiceDegradation(config)

def create_database_degradation_manager() -> DatabaseServiceDegradation:
    """Create a degradation manager for database services."""
    config = DegradationConfig(
        enabled=True,
        timeout_seconds=10.0,
        max_retries=3
    )
    return DatabaseServiceDegradation(config)
