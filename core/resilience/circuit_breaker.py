"""
Circuit Breaker Pattern Implementation for Production Resilience

This module provides a comprehensive circuit breaker implementation to protect
services from cascade failures and provide graceful degradation during outages.
"""

import asyncio
import time
from typing import Any, Callable, Dict, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Circuit is open, rejecting calls
    HALF_OPEN = "half_open" # Testing if service has recovered

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5           # Number of failures before opening
    success_threshold: int = 3           # Number of successes to close from half-open
    timeout: float = 60.0               # Timeout before trying half-open (seconds)
    expected_exception: type = Exception # Exception type that counts as failure
    
    def validate(self) -> bool:
        """Validate configuration parameters."""
        if self.failure_threshold <= 0:
            logger.error(f"Invalid failure_threshold: {self.failure_threshold}")
            return False
        if self.success_threshold <= 0:
            logger.error(f"Invalid success_threshold: {self.success_threshold}")
            return False
        if self.timeout <= 0:
            logger.error(f"Invalid timeout: {self.timeout}")
            return False
        return True

@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    state_changes: int = 0
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_calls == 0:
            return 1.0
        return self.total_successes / self.total_calls
    
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate()

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""
    
    def __init__(self, name: str, stats: CircuitBreakerStats):
        self.name = name
        self.stats = stats
        super().__init__(f"Circuit breaker '{name}' is open")

class CircuitBreaker:
    """
    Circuit Breaker implementation for service resilience.
    
    The circuit breaker monitors service calls and automatically opens
    when failures exceed the threshold, preventing cascade failures.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker name for logging
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        if not config.validate():
            raise ValueError(f"Invalid circuit breaker configuration for '{name}'")
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException: When circuit is open
        """
        async with self._lock:
            self.stats.total_calls += 1
            
            # Check if circuit should transition from open to half-open
            if self.stats.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitBreakerOpenException(self.name, self.stats)
            
            # In half-open state, only allow limited calls
            if self.stats.state == CircuitBreakerState.HALF_OPEN:
                if self.stats.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
        
        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self._on_success()
            return result
            
        except self.config.expected_exception as e:
            await self._on_failure()
            raise
        except Exception as e:
            # Unexpected exceptions don't count as failures
            logger.warning(f"Unexpected exception in circuit breaker '{self.name}': {e}")
            raise
    
    @asynccontextmanager
    async def protect(self):
        """
        Context manager for circuit breaker protection.
        
        Usage:
            async with circuit_breaker.protect():
                # Protected code here
                result = await some_service_call()
        """
        async with self._lock:
            self.stats.total_calls += 1
            
            if self.stats.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                else:
                    raise CircuitBreakerOpenException(self.name, self.stats)
        
        try:
            yield
            await self._on_success()
        except self.config.expected_exception as e:
            await self._on_failure()
            raise
        except Exception as e:
            logger.warning(f"Unexpected exception in circuit breaker '{self.name}': {e}")
            raise
    
    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            self.stats.success_count += 1
            self.stats.total_successes += 1
            self.stats.last_success_time = time.time()
            
            # Reset failure count on success
            self.stats.failure_count = 0
            
            # Transition from half-open to closed if we have enough successes
            if (self.stats.state == CircuitBreakerState.HALF_OPEN and 
                self.stats.success_count >= self.config.success_threshold):
                self._transition_to_closed()
    
    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self.stats.failure_count += 1
            self.stats.total_failures += 1
            self.stats.last_failure_time = time.time()
            
            # Reset success count on failure
            self.stats.success_count = 0
            
            # Open circuit if failure threshold exceeded
            if (self.stats.state == CircuitBreakerState.CLOSED and 
                self.stats.failure_count >= self.config.failure_threshold):
                self._transition_to_open()
            elif self.stats.state == CircuitBreakerState.HALF_OPEN:
                # Any failure in half-open state reopens the circuit
                self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset from open to half-open."""
        if self.stats.last_failure_time is None:
            return True
        
        time_since_failure = time.time() - self.stats.last_failure_time
        return time_since_failure >= self.config.timeout
    
    def _transition_to_closed(self) -> None:
        """Transition circuit breaker to closed state."""
        old_state = self.stats.state
        self.stats.state = CircuitBreakerState.CLOSED
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self.stats.state_changes += 1
        
        logger.info(f"Circuit breaker '{self.name}' transitioned from {old_state.value} to closed")
    
    def _transition_to_open(self) -> None:
        """Transition circuit breaker to open state."""
        old_state = self.stats.state
        self.stats.state = CircuitBreakerState.OPEN
        self.stats.success_count = 0
        self.stats.state_changes += 1
        
        logger.warning(f"Circuit breaker '{self.name}' transitioned from {old_state.value} to open")
    
    def _transition_to_half_open(self) -> None:
        """Transition circuit breaker to half-open state."""
        old_state = self.stats.state
        self.stats.state = CircuitBreakerState.HALF_OPEN
        self.stats.success_count = 0
        self.stats.state_changes += 1
        
        logger.info(f"Circuit breaker '{self.name}' transitioned from {old_state.value} to half-open")
    
    def get_stats(self) -> CircuitBreakerStats:
        """Get current circuit breaker statistics."""
        return self.stats
    
    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.stats.state
    
    def is_closed(self) -> bool:
        """Check if circuit breaker is closed (normal operation)."""
        return self.stats.state == CircuitBreakerState.CLOSED
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open (rejecting calls)."""
        return self.stats.state == CircuitBreakerState.OPEN
    
    def is_half_open(self) -> bool:
        """Check if circuit breaker is half-open (testing recovery)."""
        return self.stats.state == CircuitBreakerState.HALF_OPEN
    
    async def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        async with self._lock:
            self._transition_to_closed()
            logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    async def force_open(self) -> None:
        """Manually force circuit breaker to open state."""
        async with self._lock:
            self._transition_to_open()
            logger.warning(f"Circuit breaker '{self.name}' manually forced open")

class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def get_or_create(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Get existing circuit breaker or create a new one."""
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]
    
    async def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)
    
    async def remove(self, name: str) -> bool:
        """Remove circuit breaker from registry."""
        async with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                return True
            return False
    
    async def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers."""
        return {name: breaker.get_stats() for name, breaker in self._breakers.items()}
    
    async def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for breaker in self._breakers.values():
            await breaker.reset()
    
    def list_names(self) -> list[str]:
        """List all circuit breaker names."""
        return list(self._breakers.keys())

# Global circuit breaker registry
_circuit_breaker_registry: Optional[CircuitBreakerRegistry] = None

def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    global _circuit_breaker_registry
    if _circuit_breaker_registry is None:
        _circuit_breaker_registry = CircuitBreakerRegistry()
    return _circuit_breaker_registry

# Convenience functions for common circuit breaker configurations
def create_api_circuit_breaker(name: str) -> CircuitBreaker:
    """Create a circuit breaker optimized for API calls."""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout=60.0,
        expected_exception=Exception
    )
    return CircuitBreaker(name, config)

def create_database_circuit_breaker(name: str) -> CircuitBreaker:
    """Create a circuit breaker optimized for database operations."""
    config = CircuitBreakerConfig(
        failure_threshold=3,  # Lower threshold for database
        success_threshold=2,
        timeout=30.0,         # Shorter timeout for database
        expected_exception=Exception
    )
    return CircuitBreaker(name, config)

def create_rag_circuit_breaker(name: str) -> CircuitBreaker:
    """Create a circuit breaker optimized for RAG operations."""
    config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=45.0,
        expected_exception=Exception
    )
    return CircuitBreaker(name, config)
