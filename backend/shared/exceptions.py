"""
Comprehensive exception classes for the Insurance Navigator system.

This module provides structured exception handling for all system components,
including service integration, cost control, and configuration management.
"""

import logging
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
            context['retry_after_seconds'] = retry_after
        
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
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 config_key: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        if config_key:
            context = context or {}
            context['config_key'] = config_key
        
        super().__init__(message, service_name, "SERVICE_CONFIGURATION_ERROR", context)
        self.config_key = config_key


class ServiceRateLimitError(ServiceError):
    """Raised when service rate limits are exceeded."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 retry_after: Optional[int] = None, rate_limit_info: Optional[Dict[str, Any]] = None, 
                 context: Optional[Dict[str, Any]] = None):
        if retry_after:
            context = context or {}
            context['retry_after_seconds'] = retry_after
        
        if rate_limit_info:
            context = context or {}
            context['rate_limit_info'] = rate_limit_info
        
        super().__init__(message, service_name, "SERVICE_RATE_LIMIT_EXCEEDED", context)
        self.retry_after = retry_after
        self.rate_limit_info = rate_limit_info


class ServiceTimeoutError(ServiceError):
    """Raised when a service operation times out."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 timeout_seconds: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        if timeout_seconds:
            context = context or {}
            context['timeout_seconds'] = timeout_seconds
        
        super().__init__(message, service_name, "SERVICE_TIMEOUT", context)
        self.timeout_seconds = timeout_seconds


# Cost control exceptions

class CostControlError(InsuranceNavigatorError):
    """Base exception for cost control errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, context)


class CostLimitExceededError(CostControlError):
    """Raised when cost limits are exceeded."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 daily_cost: Optional[float] = None, daily_limit: Optional[float] = None,
                 context: Optional[Dict[str, Any]] = None):
        if service_name:
            context = context or {}
            context['service_name'] = service_name
        
        if daily_cost is not None:
            context = context or {}
            context['daily_cost_usd'] = daily_cost
        
        if daily_limit is not None:
            context = context or {}
            context['daily_limit_usd'] = daily_limit
        
        super().__init__(message, "COST_LIMIT_EXCEEDED", context)
        self.service_name = service_name
        self.daily_cost = daily_cost
        self.daily_limit = daily_limit


class RateLimitExceededError(CostControlError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, service_name: Optional[str] = None, 
                 hourly_requests: Optional[int] = None, hourly_limit: Optional[int] = None,
                 retry_after: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        if service_name:
            context = context or {}
            context['service_name'] = service_name
        
        if hourly_requests is not None:
            context = context or {}
            context['hourly_requests'] = hourly_requests
        
        if hourly_limit is not None:
            context = context or {}
            context['hourly_limit'] = hourly_limit
        
        if retry_after:
            context = context or {}
            context['retry_after_seconds'] = retry_after
        
        super().__init__(message, "RATE_LIMIT_EXCEEDED", context)
        self.service_name = service_name
        self.hourly_requests = hourly_requests
        self.hourly_limit = hourly_limit
        self.retry_after = retry_after


class BudgetExceededError(CostControlError):
    """Raised when total budget is exceeded."""
    
    def __init__(self, message: str, total_cost: Optional[float] = None, 
                 total_limit: Optional[float] = None, context: Optional[Dict[str, Any]] = None):
        if total_cost is not None:
            context = context or {}
            context['total_cost_usd'] = total_cost
        
        if total_limit is not None:
            context = context or {}
            context['total_limit_usd'] = total_limit
        
        super().__init__(message, "BUDGET_EXCEEDED", context)
        self.total_cost = total_cost
        self.total_limit = total_limit


# Configuration exceptions

class ConfigurationError(InsuranceNavigatorError):
    """Raised when configuration validation fails."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, 
                 validation_errors: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None):
        if config_key:
            context = context or {}
            context['config_key'] = config_key
        
        if validation_errors:
            context = context or {}
            context['validation_errors'] = validation_errors
        
        super().__init__(message, "CONFIGURATION_ERROR", context)
        self.config_key = config_key
        self.validation_errors = validation_errors


class EnvironmentVariableError(ConfigurationError):
    """Raised when required environment variables are missing."""
    
    def __init__(self, message: str, missing_variables: Optional[List[str]] = None, 
                 context: Optional[Dict[str, Any]] = None):
        if missing_variables:
            context = context or {}
            context['missing_variables'] = missing_variables
        
        super().__init__(message, "ENVIRONMENT_VARIABLE_ERROR", context)
        self.missing_variables = missing_variables


class CredentialError(ConfigurationError):
    """Raised when credentials are invalid or missing."""
    
    def __init__(self, message: str, credential_type: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        if credential_type:
            context = context or {}
            context['credential_type'] = credential_type
        
        super().__init__(message, "CREDENTIAL_ERROR", context)
        self.credential_type = credential_type


# Database and storage exceptions

class DatabaseError(InsuranceNavigatorError):
    """Base exception for database-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, context)


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, message: str, connection_string: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        if connection_string:
            # Don't log the full connection string for security
            context = context or {}
            context['connection_host'] = connection_string.split('@')[-1].split('/')[0] if '@' in connection_string else 'unknown'
        
        super().__init__(message, "DATABASE_CONNECTION_ERROR", context)
        self.connection_string = connection_string


class TransactionError(DatabaseError):
    """Raised when database transaction fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        if operation:
            context = context or {}
            context['operation'] = operation
        
        super().__init__(message, "DATABASE_TRANSACTION_ERROR", context)
        self.operation = operation


class StorageError(InsuranceNavigatorError):
    """Base exception for storage-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, context)


class FileNotFoundError(StorageError):
    """Raised when a file is not found in storage."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        if file_path:
            context = context or {}
            context['file_path'] = file_path
        
        super().__init__(message, "FILE_NOT_FOUND", context)
        self.file_path = file_path


class StorageQuotaExceededError(StorageError):
    """Raised when storage quota is exceeded."""
    
    def __init__(self, message: str, current_usage: Optional[int] = None, 
                 quota_limit: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        if current_usage is not None:
            context = context or {}
            context['current_usage_bytes'] = current_usage
        
        if quota_limit is not None:
            context = context or {}
            context['quota_limit_bytes'] = quota_limit
        
        super().__init__(message, "STORAGE_QUOTA_EXCEEDED", context)
        self.current_usage = current_usage
        self.quota_limit = quota_limit


# Processing pipeline exceptions

class ProcessingError(InsuranceNavigatorError):
    """Base exception for document processing errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, context)


class DocumentValidationError(ProcessingError):
    """Raised when document validation fails."""
    
    def __init__(self, message: str, document_id: Optional[str] = None, 
                 validation_errors: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None):
        if document_id:
            context = context or {}
            context['document_id'] = document_id
        
        if validation_errors:
            context = context or {}
            context['validation_errors'] = validation_errors
        
        super().__init__(message, "DOCUMENT_VALIDATION_ERROR", context)
        self.document_id = document_id
        self.validation_errors = validation_errors


class ValidationError(InsuranceNavigatorError):
    """Raised when general validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, 
                 validation_errors: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None):
        if field_name:
            context = context or {}
            context['field_name'] = field_name
        
        if validation_errors:
            context = context or {}
            context['validation_errors'] = validation_errors
        
        super().__init__(message, "VALIDATION_ERROR", context)
        self.field_name = field_name
        self.validation_errors = validation_errors


class ProcessingTimeoutError(ProcessingError):
    """Raised when document processing times out."""
    
    def __init__(self, message: str, document_id: Optional[str] = None, 
                 processing_stage: Optional[str] = None, timeout_seconds: Optional[int] = None,
                 context: Optional[Dict[str, Any]] = None):
        if document_id:
            context = context or {}
            context['document_id'] = document_id
        
        if processing_stage:
            context = context or {}
            context['processing_stage'] = processing_stage
        
        if timeout_seconds:
            context = context or {}
            context['timeout_seconds'] = timeout_seconds
        
        super().__init__(message, "PROCESSING_TIMEOUT", context)
        self.document_id = document_id
        self.processing_stage = processing_stage
        self.timeout_seconds = timeout_seconds


class StateTransitionError(ProcessingError):
    """Raised when state machine transition fails."""
    
    def __init__(self, message: str, document_id: Optional[str] = None, 
                 current_state: Optional[str] = None, target_state: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        if document_id:
            context = context or {}
            context['document_id'] = document_id
        
        if current_state:
            context = context or {}
            context['current_state'] = current_state
        
        if target_state:
            context = context or {}
            context['target_state'] = target_state
        
        super().__init__(message, "STATE_TRANSITION_ERROR", context)
        self.document_id = document_id
        self.current_state = current_state
        self.target_state = target_state


# Authentication and authorization exceptions

class AuthenticationError(InsuranceNavigatorError):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, context)


class AuthorizationError(InsuranceNavigatorError):
    """Raised when authorization fails."""
    
    def __init__(self, message: str, required_permissions: Optional[List[str]] = None, 
                 context: Optional[Dict[str, Any]] = None):
        if required_permissions:
            context = context or {}
            context['required_permissions'] = required_permissions
        
        super().__init__(message, "AUTHORIZATION_ERROR", context)
        self.required_permissions = required_permissions


# Network and communication exceptions

class NetworkError(InsuranceNavigatorError):
    """Base exception for network-related errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_code, context)


class WebhookError(NetworkError):
    """Raised when webhook delivery fails."""
    
    def __init__(self, message: str, webhook_url: Optional[str] = None, 
                 delivery_attempts: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        if webhook_url:
            context = context or {}
            context['webhook_url'] = webhook_url
        
        if delivery_attempts is not None:
            context = context or {}
            context['delivery_attempts'] = delivery_attempts
        
        super().__init__(message, "WEBHOOK_DELIVERY_ERROR", context)
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
    if isinstance(error, ServiceRateLimitError) and error.retry_after:
        return error.retry_after
    
    if isinstance(error, ServiceTimeoutError):
        return 30  # 30 seconds for timeout errors
    
    if isinstance(error, ConnectionError):
        return 60  # 1 minute for connection errors
    
    if isinstance(error, ServiceUnavailableError):
        return 300  # 5 minutes for service unavailable
    
    # Default retry delay
    return 10


def format_error_context(error: Exception) -> Dict[str, Any]:
    """Format error context for logging and debugging."""
    if isinstance(error, InsuranceNavigatorError):
        return error.to_dict()
    else:
        return {
            'error_type': type(error).__name__,
            'message': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }


def log_exception_with_context(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an exception with additional context."""
    error_context = format_error_context(error)
    if context:
        error_context['additional_context'] = context
    
    logger.error(f"Exception occurred: {error_context['error_type']}", extra=error_context)
