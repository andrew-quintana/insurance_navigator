"""
Comprehensive exception classes for the Insurance Navigator system.

This module provides structured exception handling for all system components,
including service integration, cost control, and configuration management.
"""

import logging
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class InsuranceNavigatorError(Exception):
    """Base exception class for all Insurance Navigator errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        
        # Log the error
        logger.error(f"{self.__class__.__name__}: {message}", extra={
            'error_code': error_code,
            'context': context,
            'timestamp': self.timestamp.isoformat()
        })
        
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }


# User-facing exceptions

class UserFacingError(InsuranceNavigatorError):
    """
    Exception class for user-facing errors with UUID traceability.
    
    This class provides structured error handling for errors that should be
    presented to users, including automatic UUID generation for support
    team traceability.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None, 
                 user_message: Optional[str] = None,
                 support_uuid: Optional[str] = None):
        """
        Initialize UserFacingError.
        
        Args:
            message: Internal error message for logging
            error_code: Error code for categorization
            context: Additional context information
            user_message: User-friendly error message (defaults to message)
            support_uuid: UUID for support team traceability (auto-generated if not provided)
        """
        # Generate support UUID if not provided
        if support_uuid is None:
            support_uuid = str(uuid.uuid4())
        
        # Set user message if not provided
        if user_message is None:
            user_message = message
        
        # Add support UUID to context
        if context is None:
            context = {}
        context['support_uuid'] = support_uuid
        context['user_message'] = user_message
        
        super().__init__(message, error_code, context)
        self.user_message = user_message
        self.support_uuid = support_uuid
    
    def get_user_message(self) -> str:
        """Get user-friendly error message with support UUID."""
        return f"{self.user_message} (Reference: {self.support_uuid})"
    
    def get_support_uuid(self) -> str:
        """Get support UUID for traceability."""
        return self.support_uuid


# Service-related exceptions

class ServiceError(InsuranceNavigatorError):
    """Base exception for service-related errors."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        if service_name:
            context = context or {}
            context['service_name'] = service_name
        
        super().__init__(message, error_code, context)
        self.service_name = service_name


class ServiceUnavailableError(ServiceError):
    """Raised when a service is unavailable."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 retry_after: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        if retry_after:
            context = context or {}
            context['retry_after'] = retry_after
        
        super().__init__(message, service_name, "SERVICE_UNAVAILABLE", context)
        self.retry_after = retry_after


class ServiceExecutionError(ServiceError):
    """Raised when a service operation fails."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 original_error: Optional[Exception] = None, context: Optional[Dict[str, Any]] = None):
        if original_error:
            context = context or {}
            context['original_error'] = str(original_error)
            context['original_error_type'] = type(original_error).__name__
        
        super().__init__(message, service_name, "SERVICE_EXECUTION_FAILED", context)
        self.original_error = original_error


class ServiceConfigurationError(ServiceError):
    """Raised when service configuration is invalid."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        if config_key:
            context = context or {}
            context['config_key'] = config_key
        
        super().__init__(message, None, "SERVICE_CONFIGURATION_ERROR", context)
        self.config_key = config_key


class ServiceTimeoutError(ServiceError):
    """Raised when a service operation times out."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 timeout_seconds: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        if timeout_seconds:
            context = context or {}
            context['timeout_seconds'] = timeout_seconds
        
        super().__init__(message, service_name, "SERVICE_TIMEOUT", context)
        self.timeout_seconds = timeout_seconds


class ServiceRateLimitError(ServiceError):
    """Raised when a service rate limit is exceeded."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 retry_after: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        if retry_after:
            context = context or {}
            context['retry_after'] = retry_after
        
        super().__init__(message, service_name, "SERVICE_RATE_LIMIT", context)
        self.retry_after = retry_after


# Cost-related exceptions

class CostLimitExceededError(InsuranceNavigatorError):
    """Raised when cost limits are exceeded."""
    
    def __init__(self, message: str, current_cost: Optional[float] = None, 
                 cost_limit: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        if current_cost is not None and cost_limit is not None:
            context = context or {}
            context['current_cost'] = current_cost
            context['cost_limit'] = cost_limit
            context['excess_cost'] = current_cost - cost_limit
        
        super().__init__(message, "COST_LIMIT_EXCEEDED", context)
        self.current_cost = current_cost
        self.cost_limit = cost_limit


class DailyCostLimitExceededError(CostLimitExceededError):
    """Raised when daily cost limit is exceeded."""
    
    def __init__(self, message: str, current_cost: Optional[float] = None, 
                 daily_limit: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, current_cost, daily_limit, context)


class HourlyRateLimitExceededError(CostLimitExceededError):
    """Raised when hourly rate limit is exceeded."""
    
    def __init__(self, message: str, current_rate: Optional[float] = None, 
                 hourly_limit: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, current_rate, hourly_limit, context)


# Database-related exceptions

class DatabaseError(InsuranceNavigatorError):
    """Base exception for database-related errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 table: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        if operation or table:
            context = context or {}
            if operation:
                context['operation'] = operation
            if table:
                context['table'] = table
        
        super().__init__(message, "DATABASE_ERROR", context)
        self.operation = operation
        self.table = table


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "connection", None, context)


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""
    
    def __init__(self, message: str, query: Optional[str] = None, 
                 table: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        if query:
            context = context or {}
            context['query'] = query
        
        super().__init__(message, "query", table, context)
        self.query = query


class DatabaseTransactionError(DatabaseError):
    """Raised when a database transaction fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, operation, None, context)


# Storage-related exceptions

class StorageError(InsuranceNavigatorError):
    """Base exception for storage-related errors."""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 path: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        if operation or path:
            context = context or {}
            if operation:
                context['operation'] = operation
            if path:
                context['path'] = path
        
        super().__init__(message, "STORAGE_ERROR", context)
        self.operation = operation
        self.path = path


class StorageConnectionError(StorageError):
    """Raised when storage connection fails."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "connection", None, context)


class StorageUploadError(StorageError):
    """Raised when file upload fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "upload", file_path, context)


class StorageDownloadError(StorageError):
    """Raised when file download fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "download", file_path, context)


class StorageNotFoundError(StorageError):
    """Raised when a file is not found in storage."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, "not_found", file_path, context)


# Validation-related exceptions

class ValidationError(InsuranceNavigatorError):
    """Base exception for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, context: Optional[Dict[str, Any]] = None):
        if field or value is not None:
            context = context or {}
            if field:
                context['field'] = field
            if value is not None:
                context['value'] = str(value)
        
        super().__init__(message, "VALIDATION_ERROR", context)
        self.field = field
        self.value = value


class RequiredFieldError(ValidationError):
    """Raised when a required field is missing."""
    
    def __init__(self, field: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(f"Required field '{field}' is missing", field, None, context)


class InvalidValueError(ValidationError):
    """Raised when a field has an invalid value."""
    
    def __init__(self, field: str, value: Any, expected: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        message = f"Invalid value for field '{field}': {value}"
        if expected:
            message += f" (expected: {expected})"
        
        super().__init__(message, field, value, context)
        self.expected = expected


class InvalidFormatError(ValidationError):
    """Raised when a field has an invalid format."""
    
    def __init__(self, field: str, value: Any, expected_format: str, 
                 context: Optional[Dict[str, Any]] = None):
        message = f"Invalid format for field '{field}': {value} (expected: {expected_format})"
        super().__init__(message, field, value, context)
        self.expected_format = expected_format


# Network-related exceptions

class NetworkError(InsuranceNavigatorError):
    """Base exception for network-related errors."""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 status_code: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        if url or status_code:
            context = context or {}
            if url:
                context['url'] = url
            if status_code:
                context['status_code'] = status_code
        
        super().__init__(message, "NETWORK_ERROR", context)
        self.url = url
        self.status_code = status_code


class ConnectionError(NetworkError):
    """Raised when a network connection fails."""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, url, None, context)


class TimeoutError(NetworkError):
    """Raised when a network operation times out."""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 timeout_seconds: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        if timeout_seconds:
            context = context or {}
            context['timeout_seconds'] = timeout_seconds
        
        super().__init__(message, url, None, context)
        self.timeout_seconds = timeout_seconds


class HTTPError(NetworkError):
    """Raised when an HTTP request fails."""
    
    def __init__(self, message: str, url: Optional[str] = None, 
                 status_code: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, url, status_code, context)


class WebhookError(NetworkError):
    """Raised when a webhook delivery fails."""
    
    def __init__(self, message: str, webhook_url: Optional[str] = None, 
                 delivery_attempts: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        if webhook_url or delivery_attempts:
            context = context or {}
            if webhook_url:
                context['webhook_url'] = webhook_url
            if delivery_attempts:
                context['delivery_attempts'] = delivery_attempts
        
        super().__init__(message, webhook_url, None, context)
        self.webhook_url = webhook_url
        self.delivery_attempts = delivery_attempts


# Utility functions for exception handling

def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable."""
    retryable_exceptions = (
        ServiceUnavailableError,
        ServiceTimeoutError,
        ServiceRateLimitError,
        ConnectionError,
        NetworkError,
        WebhookError
    )
    
    return isinstance(error, retryable_exceptions)


def get_retry_delay(error: Exception) -> int:
    """Get retry delay in seconds for an error."""
    if isinstance(error, ServiceRateLimitError):
        return error.retry_after or 60
    elif isinstance(error, ServiceUnavailableError):
        return error.retry_after or 30
    elif isinstance(error, (ConnectionError, NetworkError)):
        return 10
    else:
        return 5


def create_user_facing_error(message: str, original_error: Optional[Exception] = None, 
                           error_code: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> UserFacingError:
    """
    Create a UserFacingError with automatic UUID generation.
    
    Args:
        message: Error message
        original_error: Original exception that caused this error
        error_code: Error code for categorization
        context: Additional context information
        
    Returns:
        UserFacingError instance with support UUID
    """
    if original_error:
        context = context or {}
        context['original_error'] = str(original_error)
        context['original_error_type'] = type(original_error).__name__
    
    return UserFacingError(
        message=message,
        error_code=error_code,
        context=context
    )