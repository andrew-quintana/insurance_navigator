"""
Test Utilities for Phase 3 Production Validation

This package provides utilities for comprehensive testing and validation
of the Insurance Navigator system's production readiness.
"""

from .auth_helper import create_test_user, authenticate_test_user, validate_token
from .document_helper import create_test_document, upload_test_document, check_document_status
from .validation_helper import (
    validate_response_structure,
    validate_performance_metrics,
    validate_error_handling,
    calculate_success_rate,
    validate_production_readiness
)

__all__ = [
    'create_test_user',
    'authenticate_test_user', 
    'validate_token',
    'create_test_document',
    'upload_test_document',
    'check_document_status',
    'validate_response_structure',
    'validate_performance_metrics',
    'validate_error_handling',
    'calculate_success_rate',
    'validate_production_readiness'
]
