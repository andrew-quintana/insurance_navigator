"""Circuit breaker pattern implementation for translation services.

This module provides circuit breaker functionality to prevent cascade failures
when translation services become unavailable or slow.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Service unavailable, fast fail
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    # Failure threshold before opening circuit
    failure_threshold: int = 5
    
    # Time to wait before attempting recovery (seconds)
    recovery_timeout: float = 60.0
    
    # Expected timeout for successful operations (seconds)
    expected_timeout: float = 30.0
    
    # Number of successful calls needed to close circuit
    success_threshold: int = 3
    
    # Maximum number of concurrent calls when half-open
    max_concurrent_half_open: int = 1


class CircuitBreaker:
    """Circuit breaker implementation for translation services."""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker.
        
        Args:
            name: Name of the circuit breaker (e.g., "elevenlabs", "flash")
            config: Configuration for circuit breaker behavior
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.last_state_change = time.time()
        
        # Concurrency control for half-open state
        self.half_open_calls = 0
        self.half_open_lock = asyncio.Lock()
        
        # Statistics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.circuit_opens = 0
        
        logger.info(f"Circuit breaker '{name}' initialized with config: {self.config}")
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "circuit_opens": self.circuit_opens,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "uptime": time.time() - self.last_state_change
        }
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset to half-open."""
        if self.state != CircuitState.OPEN:
            return False
        
        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful operation."""
        self.success_count += 1
        self.failure_count = 0
        self.total_calls += 1
        self.successful_calls += 1
        
        # Check if we should close the circuit
        if self.state == CircuitState.HALF_OPEN and self.success_count >= self.config.success_threshold:
            self._close_circuit()
    
    def _on_failure(self) -> None:
        """Handle failed operation."""
        self.failure_count += 1
        self.total_calls += 1
        self.failed_calls += 1
        self.last_failure_time = time.time()
        
        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
            self._open_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            self._open_circuit()
    
    def _open_circuit(self) -> None:
        """Open the circuit (service unavailable)."""
        if self.state != CircuitState.OPEN:
            old_state = self.state
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self.circuit_opens += 1
            self.half_open_calls = 0
            
            logger.warning(
                f"Circuit breaker '{self.name}' opened: "
                f"{old_state.value} -> {self.state.value} "
                f"(failures: {self.failure_count})"
            )
    
    def _close_circuit(self) -> None:
        """Close the circuit (normal operation)."""
        if self.state != CircuitState.CLOSED:
            old_state = self.state
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            self.success_count = 0
            self.failure_count = 0
            
            logger.info(
                f"Circuit breaker '{self.name}' closed: "
                f"{old_state.value} -> {self.state.value}"
            )
    
    def _try_half_open(self) -> bool:
        """Attempt to transition to half-open state."""
        if not self._should_attempt_reset():
            return False
        
        if self.half_open_calls >= self.config.max_concurrent_half_open:
            return False
        
        old_state = self.state
        self.state = CircuitState.HALF_OPEN
        self.last_state_change = time.time()
        self.success_count = 0
        self.half_open_calls += 1
        
        logger.info(
            f"Circuit breaker '{self.name}' half-open: "
            f"{old_state.value} -> {self.state.value}"
        )
        return True
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function execution fails
        """
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if not self._try_half_open():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Service unavailable for {self.config.recovery_timeout:.1f}s"
                )
        
        # Execute function with timeout
        try:
            async with asyncio.timeout(self.config.expected_timeout):
                result = await func(*args, **kwargs)
                self._on_success()
                return result
                
        except asyncio.TimeoutError:
            logger.warning(f"Circuit breaker '{self.name}': Operation timed out")
            self._on_failure()
            raise
        except Exception as e:
            logger.warning(f"Circuit breaker '{self.name}': Operation failed: {e}")
            self._on_failure()
            raise
        finally:
            # Decrement half-open call counter
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls = max(0, self.half_open_calls - 1)
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        old_state = self.state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        self.half_open_calls = 0
        
        logger.info(
            f"Circuit breaker '{self.name}' manually reset: "
            f"{old_state.value} -> {self.state.value}"
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if not self._should_attempt_reset():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open. "
                    f"Service unavailable for {self.config.recovery_timeout} seconds"
                )
            else:
                # Try to transition to half-open
                if not self._try_half_open():
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open and max concurrent calls reached"
                    )
        
        # Check half-open concurrency limit
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.max_concurrent_half_open:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' half-open concurrency limit reached"
                )
            self.half_open_calls += 1
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Decrement half-open call counter
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls = max(0, self.half_open_calls - 1)
        
        # Update circuit state based on exception
        if exc_type is None:
            self._on_success()
        else:
            self._on_failure()


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreakerManager:
    """Manager for multiple circuit breakers."""
    
    def __init__(self):
        """Initialize circuit breaker manager."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.default_config = CircuitBreakerConfig()
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """Get or create circuit breaker for a service.
        
        Args:
            name: Service name
            config: Optional configuration override
            
        Returns:
            CircuitBreaker instance
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(
                name, 
                config or self.default_config
            )
        
        return self.circuit_breakers[name]
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        return {
            name: cb.get_stats() 
            for name, cb in self.circuit_breakers.items()
        }
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for cb in self.circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")
    
    def get_healthy_services(self) -> list[str]:
        """Get list of services with closed circuits."""
        healthy = []
        for name, cb in self.circuit_breakers.items():
            if cb.get_state() == CircuitState.CLOSED:
                healthy.append(name)
        return healthy


# Global circuit breaker manager instance
circuit_breaker_manager = CircuitBreakerManager()


@asynccontextmanager
async def circuit_breaker_protection(name: str, config: Optional[CircuitBreakerConfig] = None):
    """Context manager for circuit breaker protection.
    
    Args:
        name: Service name for circuit breaker
        config: Optional configuration override
        
    Yields:
        CircuitBreaker instance
    """
    cb = circuit_breaker_manager.get_circuit_breaker(name, config)
    try:
        yield cb
    finally:
        pass  # Circuit breaker state is managed automatically 