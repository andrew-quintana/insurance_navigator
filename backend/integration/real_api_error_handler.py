"""
Real API Error Handler for Phase 2 Integration

This module provides comprehensive error handling for real LlamaParse and OpenAI API
integration, including rate limiting, retry logic, and error recovery strategies.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors that can occur with real APIs."""
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
    AUTHENTICATION = "authentication"
    NETWORK = "network"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class APIError:
    """Structured representation of an API error."""
    error_type: ErrorType
    message: str
    status_code: Optional[int] = None
    retry_after: Optional[int] = None
    cost_impact: Optional[float] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class RealAPIErrorHandler:
    """Comprehensive error handler for real API integration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.error_counts: Dict[str, int] = {}
        self.last_error_time: Dict[str, float] = {}
        self.retry_delays: Dict[str, List[int]] = {}
        
        # Rate limiting configuration
        self.llamaparse_rate_limit = config.get('LLAMAPARSE_RATE_LIMIT_REQUESTS_PER_MINUTE', 60)
        self.openai_rate_limit = config.get('OPENAI_RATE_LIMIT_REQUESTS_PER_MINUTE', 3000)
        
        # Retry configuration
        self.llamaparse_retry_attempts = config.get('LLAMAPARSE_RETRY_ATTEMPTS', 3)
        self.openai_retry_attempts = config.get('OPENAI_RETRY_ATTEMPTS', 3)
        self.llamaparse_retry_delay = config.get('LLAMAPARSE_RETRY_DELAY', 5)
        self.openai_retry_delay = config.get('OPENAI_RETRY_DELAY', 1)
        
        # Cost monitoring
        self.enable_cost_monitoring = config.get('ENABLE_COST_MONITORING', True)
        self.cost_alert_threshold = config.get('COST_ALERT_THRESHOLD_USD', 10.00)
        self.total_cost = 0.0
    
    async def handle_llamaparse_errors(self, error: Exception, context: str = "") -> APIError:
        """Handle real LlamaParse API errors and retry logic."""
        try:
            # Parse error details
            api_error = self._parse_llamaparse_error(error)
            
            # Log error for debugging
            logger.error(f"LlamaParse API error in {context}: {api_error}")
            
            # Update error tracking
            self._update_error_tracking('llamaparse', api_error)
            
            # Handle specific error types
            if api_error.error_type == ErrorType.RATE_LIMIT:
                await self._handle_rate_limit('llamaparse', api_error)
            elif api_error.error_type == ErrorType.QUOTA_EXCEEDED:
                await self._handle_quota_exceeded('llamaparse', api_error)
            elif api_error.error_type == ErrorType.AUTHENTICATION:
                await self._handle_authentication_error('llamaparse', api_error)
            
            return api_error
            
        except Exception as e:
            logger.error(f"Error handling LlamaParse error: {e}")
            return APIError(
                error_type=ErrorType.UNKNOWN,
                message=f"Failed to handle LlamaParse error: {str(e)}"
            )
    
    async def handle_openai_errors(self, error: Exception, context: str = "") -> APIError:
        """Handle real OpenAI API errors and retry logic."""
        try:
            # Parse error details
            api_error = self._parse_openai_error(error)
            
            # Log error for debugging
            logger.error(f"OpenAI API error in {context}: {api_error}")
            
            # Update error tracking
            self._update_error_tracking('openai', api_error)
            
            # Handle specific error types
            if api_error.error_type == ErrorType.RATE_LIMIT:
                await self._handle_rate_limit('openai', api_error)
            elif api_error.error_type == ErrorType.QUOTA_EXCEEDED:
                await self._handle_quota_exceeded('openai', api_error)
            elif api_error.error_type == ErrorType.AUTHENTICATION:
                await self._handle_authentication_error('openai', api_error)
            
            return api_error
            
        except Exception as e:
            logger.error(f"Error handling OpenAI error: {e}")
            return APIError(
                error_type=ErrorType.UNKNOWN,
                message=f"Failed to handle OpenAI error: {str(e)}"
            )
    
    def _parse_llamaparse_error(self, error: Exception) -> APIError:
        """Parse LlamaParse API error and determine error type."""
        error_str = str(error).lower()
        
        if 'rate limit' in error_str or '429' in error_str:
            return APIError(
                error_type=ErrorType.RATE_LIMIT,
                message=str(error),
                status_code=429,
                retry_after=60  # Default retry after 1 minute
            )
        elif 'quota' in error_str or 'limit exceeded' in error_str:
            return APIError(
                error_type=ErrorType.QUOTA_EXCEEDED,
                message=str(error),
                cost_impact=0.0  # LlamaParse typically has usage-based pricing
            )
        elif 'unauthorized' in error_str or '401' in error_str:
            return APIError(
                error_type=ErrorType.AUTHENTICATION,
                message=str(error),
                status_code=401
            )
        elif 'timeout' in error_str:
            return APIError(
                error_type=ErrorType.TIMEOUT,
                message=str(error)
            )
        else:
            return APIError(
                error_type=ErrorType.UNKNOWN,
                message=str(error)
            )
    
    def _parse_openai_error(self, error: Exception) -> APIError:
        """Parse OpenAI API error and determine error type."""
        error_str = str(error).lower()
        
        if 'rate limit' in error_str or '429' in error_str:
            return APIError(
                error_type=ErrorType.RATE_LIMIT,
                message=str(error),
                status_code=429,
                retry_after=1  # OpenAI typically allows retry after 1 second
            )
        elif 'quota' in error_str or 'insufficient_quota' in error_str:
            return APIError(
                error_type=ErrorType.QUOTA_EXCEEDED,
                message=str(error),
                cost_impact=0.0  # OpenAI has usage-based pricing
            )
        elif 'unauthorized' in error_str or '401' in error_str:
            return APIError(
                error_type=ErrorType.AUTHENTICATION,
                message=str(error),
                status_code=401
            )
        elif 'timeout' in error_str:
            return APIError(
                error_type=ErrorType.TIMEOUT,
                message=str(error)
            )
        else:
            return APIError(
                error_type=ErrorType.UNKNOWN,
                message=str(error)
            )
    
    async def _handle_rate_limit(self, service: str, error: APIError):
        """Handle rate limiting errors with exponential backoff."""
        retry_after = error.retry_after or self._get_default_retry_delay(service)
        
        logger.warning(f"Rate limit hit for {service}, waiting {retry_after} seconds")
        
        # Implement exponential backoff
        current_delay = retry_after
        for attempt in range(self._get_retry_attempts(service)):
            logger.info(f"Rate limit retry attempt {attempt + 1} for {service}")
            await asyncio.sleep(current_delay)
            current_delay *= 2  # Exponential backoff
    
    async def _handle_quota_exceeded(self, service: str, error: APIError):
        """Handle quota exceeded errors."""
        logger.error(f"Quota exceeded for {service}: {error.message}")
        
        # For quota exceeded, we typically can't retry immediately
        # Log and alert for cost monitoring
        if self.enable_cost_monitoring:
            self._log_cost_alert(service, error)
    
    async def _handle_authentication_error(self, service: str, error: APIError):
        """Handle authentication errors."""
        logger.error(f"Authentication error for {service}: {error.message}")
        
        # Authentication errors typically require manual intervention
        # Log and potentially alert administrators
        self._log_auth_error(service, error)
    
    def _get_default_retry_delay(self, service: str) -> int:
        """Get default retry delay for a service."""
        if service == 'llamaparse':
            return self.llamaparse_retry_delay
        elif service == 'openai':
            return self.openai_retry_delay
        return 5  # Default 5 seconds
    
    def _get_retry_attempts(self, service: str) -> int:
        """Get retry attempts for a service."""
        if service == 'llamaparse':
            return self.llamaparse_retry_attempts
        elif service == 'openai':
            return self.openai_retry_attempts
        return 3  # Default 3 attempts
    
    def _update_error_tracking(self, service: str, error: APIError):
        """Update error tracking for monitoring and alerting."""
        service_key = f"{service}_{error.error_type.value}"
        
        # Update error count
        self.error_counts[service_key] = self.error_counts.get(service_key, 0) + 1
        
        # Update last error time
        self.last_error_time[service_key] = error.timestamp
        
        # Track retry delays
        if service_key not in self.retry_delays:
            self.retry_delays[service_key] = []
        self.retry_delays[service_key].append(error.timestamp)
    
    def _log_cost_alert(self, service: str, error: APIError):
        """Log cost-related alerts."""
        logger.warning(f"Cost alert for {service}: {error.message}")
        # In a production environment, this would send alerts to monitoring systems
    
    def _log_auth_error(self, service: str, error: APIError):
        """Log authentication errors for administrative attention."""
        logger.error(f"Authentication error requiring attention for {service}: {error.message}")
        # In a production environment, this would send alerts to administrators
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors for monitoring and debugging."""
        return {
            'error_counts': self.error_counts,
            'last_error_time': self.last_error_time,
            'retry_delays': self.retry_delays,
            'total_cost': self.total_cost,
            'cost_alert_threshold': self.cost_alert_threshold
        }
    
    def reset_error_tracking(self):
        """Reset error tracking (useful for testing)."""
        self.error_counts.clear()
        self.last_error_time.clear()
        self.retry_delays.clear()
        self.total_cost = 0.0
    
    async def should_retry(self, service: str, error: APIError) -> bool:
        """Determine if an error should be retried."""
        if error.error_type in [ErrorType.AUTHENTICATION, ErrorType.QUOTA_EXCEEDED]:
            return False  # Don't retry auth or quota errors
        
        if error.error_type == ErrorType.RATE_LIMIT:
            # Check if we've exceeded retry attempts
            service_key = f"{service}_{error.error_type.value}"
            current_attempts = self.error_counts.get(service_key, 0)
            max_attempts = self._get_retry_attempts(service)
            return current_attempts < max_attempts
        
        # Retry other errors up to max attempts
        service_key = f"{service}_{error.error_type.value}"
        current_attempts = self.error_counts.get(service_key, 0)
        max_attempts = self._get_retry_attempts(service)
        return current_attempts < max_attempts
