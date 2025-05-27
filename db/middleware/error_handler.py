from typing import Any, Dict, Optional, Type
import logging
import traceback
from datetime import datetime
from uuid import uuid4
import json

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from asyncpg.exceptions import PostgresError
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class ErrorDetail:
    """Standardized error detail structure."""
    def __init__(
        self,
        message: str,
        error_type: str,
        error_code: str,
        trace_id: str,
        timestamp: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_type = error_type
        self.error_code = error_code
        self.trace_id = trace_id
        self.timestamp = timestamp
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error details to dictionary format."""
        return {
            'message': self.message,
            'error_type': self.error_type,
            'error_code': self.error_code,
            'trace_id': self.trace_id,
            'timestamp': self.timestamp,
            'details': self.details
        }

class APIError(Exception):
    """Base class for API errors."""
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

class ValidationAPIError(APIError):
    """Validation error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code='VALIDATION_ERROR',
            status_code=400,
            details=details
        )

class AuthorizationError(APIError):
    """Authorization error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code='AUTHORIZATION_ERROR',
            status_code=403,
            details=details
        )

class DatabaseError(APIError):
    """Database operation error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code='DATABASE_ERROR',
            status_code=500,
            details=details
        )

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for handling errors and providing consistent error responses."""
    
    ERROR_MAPPINGS = {
        ValidationError: (ValidationAPIError, 400),
        PermissionError: (AuthorizationError, 403),
        PostgresError: (DatabaseError, 500),
    }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        trace_id = str(uuid4())
        request.state.trace_id = trace_id

        try:
            response = await call_next(request)
            return response

        except Exception as e:
            return await self.handle_error(e, trace_id, request)

    async def handle_error(
        self, error: Exception, trace_id: str, request: Request
    ) -> JSONResponse:
        """Handle different types of errors and return appropriate responses."""
        timestamp = datetime.utcnow().isoformat()

        # Get error details based on error type
        error_class, status_code = self._get_error_mapping(error)
        
        if isinstance(error, APIError):
            error_detail = ErrorDetail(
                message=str(error),
                error_type=error.__class__.__name__,
                error_code=error.error_code,
                trace_id=trace_id,
                timestamp=timestamp,
                details=error.details
            )
            status_code = error.status_code
        else:
            # Convert to appropriate API error
            api_error = self._convert_to_api_error(error, error_class)
            error_detail = ErrorDetail(
                message=str(api_error),
                error_type=api_error.__class__.__name__,
                error_code=api_error.error_code,
                trace_id=trace_id,
                timestamp=timestamp,
                details=api_error.details
            )

        # Log error with context
        self._log_error(error, error_detail, request)

        return JSONResponse(
            status_code=status_code,
            content=error_detail.to_dict()
        )

    def _get_error_mapping(
        self, error: Exception
    ) -> tuple[Type[APIError], int]:
        """Get the appropriate API error class and status code for an exception."""
        for error_type, (api_error_class, status_code) in self.ERROR_MAPPINGS.items():
            if isinstance(error, error_type):
                return api_error_class, status_code
        return APIError, 500

    def _convert_to_api_error(
        self, error: Exception, error_class: Type[APIError]
    ) -> APIError:
        """Convert a standard exception to an API error."""
        if isinstance(error, ValidationError):
            return error_class(
                message="Validation error",
                details={'validation_errors': error.errors()}
            )
        elif isinstance(error, PostgresError):
            return error_class(
                message="Database error occurred",
                details={'pg_error': str(error)}
            )
        else:
            return error_class(
                message=str(error),
                details={'error_type': error.__class__.__name__}
            )

    def _log_error(
        self, error: Exception, error_detail: ErrorDetail, request: Request
    ) -> None:
        """Log error with context information."""
        error_context = {
            'trace_id': error_detail.trace_id,
            'timestamp': error_detail.timestamp,
            'request_method': request.method,
            'request_url': str(request.url),
            'error_type': error_detail.error_type,
            'error_code': error_detail.error_code,
            'details': error_detail.details
        }

        if isinstance(error, APIError):
            logger.error(
                f"API Error: {error_detail.message}",
                extra=error_context
            )
        else:
            logger.exception(
                f"Unexpected error: {error_detail.message}",
                exc_info=error,
                extra=error_context
            )


# Create a convenience function that can be imported
def error_handler(request: Request, call_next):
    """
    Convenience function wrapper for ErrorHandlerMiddleware
    This allows importing as: from db.middleware.error_handler import error_handler
    """
    middleware = ErrorHandlerMiddleware(app=None)
    return middleware.dispatch(request, call_next)


# Alternative: Create a middleware instance for direct use
error_handler_middleware = ErrorHandlerMiddleware 