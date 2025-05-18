"""
Error Handling Utilities

This module defines a standardized exception hierarchy for the Insurance Navigator system.
All agents should use these exceptions for consistent error handling.
"""

from typing import Optional, Dict, Any


class AgentError(Exception):
    """Base exception for all agent errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for logging or serialization."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ValidationError(AgentError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        details = kwargs.get("details", {})
        details.update({
            "field": field,
            "value": value
        })
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class SecurityError(AgentError):
    """Raised when security checks fail."""
    
    def __init__(self, message: str, threat_type: str = None, threat_severity: str = None, **kwargs):
        details = kwargs.get("details", {})
        details.update({
            "threat_type": threat_type,
            "threat_severity": threat_severity
        })
        super().__init__(message, error_code="SECURITY_ERROR", details=details)


class ProcessingError(AgentError):
    """Raised when data processing fails."""
    
    def __init__(self, message: str, stage: str = None, **kwargs):
        details = kwargs.get("details", {})
        details.update({
            "stage": stage
        })
        super().__init__(message, error_code="PROCESSING_ERROR", details=details)


class ConfigurationError(AgentError):
    """Raised when configuration loading or validation fails."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        details = kwargs.get("details", {})
        details.update({
            "config_key": config_key
        })
        super().__init__(message, error_code="CONFIG_ERROR", details=details)


class ExternalServiceError(AgentError):
    """Raised when an external service call fails."""
    
    def __init__(self, message: str, service_name: str = None, **kwargs):
        details = kwargs.get("details", {})
        details.update({
            "service_name": service_name
        })
        super().__init__(message, error_code="EXTERNAL_SERVICE_ERROR", details=details)


class DocumentError(AgentError):
    """Raised when document processing fails."""
    
    def __init__(self, message: str, document_id: str = None, **kwargs):
        details = kwargs.get("details", {})
        details.update({
            "document_id": document_id
        })
        super().__init__(message, error_code="DOCUMENT_ERROR", details=details) 