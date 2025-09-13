"""
Enhanced Error Handling for Worker Services

Implements structured error logging and handling following best practices:
- Appropriate log levels (DEBUG, INFO, WARN, ERROR, FATAL)
- Contextual information (user IDs, request IDs, timestamps, system state)
- Structured logging with JSON format
- Error codes and categorization
- Correlation ID tracking
"""

import json
import logging
import traceback
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import uuid


class ErrorSeverity(Enum):
    """Error severity levels following best practices"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class ErrorCategory(Enum):
    """Error categories for better classification and monitoring"""
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    PROCESSING_ERROR = "PROCESSING_ERROR"
    STORAGE_ERROR = "STORAGE_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


@dataclass
class ErrorContext:
    """Structured error context information"""
    correlation_id: str
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    document_id: Optional[str] = None
    service_name: Optional[str] = None
    operation: Optional[str] = None
    timestamp: str = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class ServiceError:
    """Structured service error with all contextual information"""
    error_code: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    original_exception: Optional[str] = None
    stack_trace: Optional[str] = None
    retry_after: Optional[int] = None
    is_retryable: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for structured logging"""
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": asdict(self.context),
            "original_exception": self.original_exception,
            "stack_trace": self.stack_trace,
            "retry_after": self.retry_after,
            "is_retryable": self.is_retryable,
            "metadata": self.metadata or {}
        }


class WorkerErrorHandler:
    """
    Enhanced error handler for worker services following best practices.
    
    Features:
    - Structured logging with JSON format
    - Error categorization and severity levels
    - Correlation ID tracking
    - Contextual information inclusion
    - Retry logic and error recovery
    - Alerting and monitoring integration
    """
    
    def __init__(self, logger_name: str = "worker_error_handler"):
        self.logger = logging.getLogger(logger_name)
        self._setup_structured_logging()
        self.error_counts: Dict[str, int] = {}
        self.alert_thresholds = {
            ErrorSeverity.ERROR: 10,  # Alert after 10 errors
            ErrorSeverity.FATAL: 1    # Alert immediately on fatal errors
        }
    
    def _setup_structured_logging(self):
        """Setup structured logging with JSON format"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def create_error(
        self,
        error_code: str,
        error_message: str,
        severity: ErrorSeverity,
        category: ErrorCategory,
        context: ErrorContext,
        original_exception: Optional[Exception] = None,
        retry_after: Optional[int] = None,
        is_retryable: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceError:
        """Create a structured service error"""
        
        # Extract stack trace if exception provided
        stack_trace = None
        if original_exception:
            stack_trace = traceback.format_exc()
        
        error = ServiceError(
            error_code=error_code,
            error_message=error_message,
            severity=severity,
            category=category,
            context=context,
            original_exception=str(original_exception) if original_exception else None,
            stack_trace=stack_trace,
            retry_after=retry_after,
            is_retryable=is_retryable,
            metadata=metadata or {}
        )
        
        return error
    
    def log_error(self, error: ServiceError) -> None:
        """Log structured error with appropriate level"""
        
        # Update error counts for monitoring
        error_key = f"{error.category.value}_{error.severity.value}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log with appropriate level
        log_data = error.to_dict()
        log_message = json.dumps(log_data, indent=2)
        
        if error.severity == ErrorSeverity.DEBUG:
            self.logger.debug(log_message)
        elif error.severity == ErrorSeverity.INFO:
            self.logger.info(log_message)
        elif error.severity == ErrorSeverity.WARN:
            self.logger.warning(log_message)
        elif error.severity == ErrorSeverity.ERROR:
            self.logger.error(log_message)
        elif error.severity == ErrorSeverity.FATAL:
            self.logger.critical(log_message)
        
        # Check for alerting thresholds
        self._check_alert_thresholds(error)
    
    def _check_alert_thresholds(self, error: ServiceError) -> None:
        """Check if error counts exceed alerting thresholds"""
        error_key = f"{error.category.value}_{error.severity.value}"
        current_count = self.error_counts.get(error_key, 0)
        threshold = self.alert_thresholds.get(error.severity, float('inf'))
        
        if current_count >= threshold:
            self.logger.critical(
                f"ALERT: Error threshold exceeded for {error_key}",
                extra={
                    "alert_type": "error_threshold_exceeded",
                    "error_category": error.category.value,
                    "error_severity": error.severity.value,
                    "current_count": current_count,
                    "threshold": threshold,
                    "correlation_id": error.context.correlation_id
                }
            )
    
    def handle_service_unavailable(
        self,
        service_name: str,
        context: ErrorContext,
        original_exception: Optional[Exception] = None,
        retry_after: Optional[int] = None
    ) -> ServiceError:
        """Handle service unavailable errors"""
        
        error = self.create_error(
            error_code=f"SERVICE_UNAVAILABLE_{service_name.upper()}",
            error_message=f"Service '{service_name}' is unavailable",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.SERVICE_UNAVAILABLE,
            context=context,
            original_exception=original_exception,
            retry_after=retry_after,
            is_retryable=True,
            metadata={"service_name": service_name}
        )
        
        self.log_error(error)
        return error
    
    def handle_authentication_failed(
        self,
        service_name: str,
        context: ErrorContext,
        original_exception: Optional[Exception] = None
    ) -> ServiceError:
        """Handle authentication failures"""
        
        error = self.create_error(
            error_code=f"AUTH_FAILED_{service_name.upper()}",
            error_message=f"Authentication failed for service '{service_name}'",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.AUTHENTICATION_FAILED,
            context=context,
            original_exception=original_exception,
            is_retryable=False,
            metadata={"service_name": service_name}
        )
        
        self.log_error(error)
        return error
    
    def handle_rate_limit_exceeded(
        self,
        service_name: str,
        context: ErrorContext,
        retry_after: int,
        original_exception: Optional[Exception] = None
    ) -> ServiceError:
        """Handle rate limit exceeded errors"""
        
        error = self.create_error(
            error_code=f"RATE_LIMIT_{service_name.upper()}",
            error_message=f"Rate limit exceeded for service '{service_name}'",
            severity=ErrorSeverity.WARN,
            category=ErrorCategory.RATE_LIMIT_EXCEEDED,
            context=context,
            original_exception=original_exception,
            retry_after=retry_after,
            is_retryable=True,
            metadata={"service_name": service_name, "retry_after_seconds": retry_after}
        )
        
        self.log_error(error)
        return error
    
    def handle_processing_error(
        self,
        operation: str,
        context: ErrorContext,
        original_exception: Optional[Exception] = None,
        is_retryable: bool = False
    ) -> ServiceError:
        """Handle document processing errors"""
        
        error = self.create_error(
            error_code=f"PROCESSING_ERROR_{operation.upper()}",
            error_message=f"Processing error in operation '{operation}'",
            severity=ErrorSeverity.ERROR,
            category=ErrorCategory.PROCESSING_ERROR,
            context=context,
            original_exception=original_exception,
            is_retryable=is_retryable,
            metadata={"operation": operation}
        )
        
        self.log_error(error)
        return error
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary for monitoring"""
        return {
            "error_counts": self.error_counts,
            "total_errors": sum(self.error_counts.values()),
            "timestamp": datetime.utcnow().isoformat()
        }


# Convenience functions for common error scenarios
def create_correlation_id() -> str:
    """Create a new correlation ID for request tracking"""
    return str(uuid.uuid4())


def create_error_context(
    correlation_id: str,
    user_id: Optional[str] = None,
    job_id: Optional[str] = None,
    document_id: Optional[str] = None,
    service_name: Optional[str] = None,
    operation: Optional[str] = None
) -> ErrorContext:
    """Create error context with correlation ID"""
    return ErrorContext(
        correlation_id=correlation_id,
        user_id=user_id,
        job_id=job_id,
        document_id=document_id,
        service_name=service_name,
        operation=operation
    )
