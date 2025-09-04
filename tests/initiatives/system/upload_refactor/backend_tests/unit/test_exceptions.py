"""
Unit tests for the custom exception classes.

Tests basic exception functionality and inheritance.
"""

import pytest
from datetime import datetime

from backend.shared.exceptions import (
    InsuranceNavigatorError,
    ServiceError, ServiceUnavailableError, ServiceExecutionError,
    CostControlError, CostLimitExceededError,
    ConfigurationError, DatabaseError, StorageError
)


class TestInsuranceNavigatorError:
    """Test cases for the base exception class."""
    
    def test_initialization_with_minimal_params(self):
        """Test initialization with minimal parameters."""
        error = InsuranceNavigatorError("Test error message")
        
        assert error.message == "Test error message"
        assert error.error_code is None
        assert error.context == {}
        assert isinstance(error.timestamp, datetime)
    
    def test_initialization_with_all_params(self):
        """Test initialization with all parameters."""
        context = {"user_id": "123", "operation": "test"}
        error = InsuranceNavigatorError(
            message="Test error message",
            error_code="TEST_001",
            context=context
        )
        
        assert error.message == "Test error message"
        assert error.error_code == "TEST_001"
        assert error.context == context
        assert isinstance(error.timestamp, datetime)
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        context = {"user_id": "123", "operation": "test"}
        error = InsuranceNavigatorError(
            message="Test error message",
            error_code="TEST_001",
            context=context
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["message"] == "Test error message"
        assert error_dict["error_code"] == "TEST_001"
        assert error_dict["context"] == context
        assert "timestamp" in error_dict
        assert "error_type" in error_dict


class TestServiceError:
    """Test cases for service-related exceptions."""
    
    def test_service_error_initialization(self):
        """Test ServiceError initialization."""
        error = ServiceError("Service error", "test_service")
        
        assert error.message == "Service error"
        assert error.service_name == "test_service"
    
    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError initialization."""
        error = ServiceUnavailableError("Service unavailable", "test_service")
        
        assert error.message == "Service unavailable"
        assert error.service_name == "test_service"
    
    def test_service_execution_error(self):
        """Test ServiceExecutionError initialization."""
        error = ServiceExecutionError("Execution failed", "test_service")
        
        assert error.message == "Execution failed"
        assert error.service_name == "test_service"


class TestCostControlError:
    """Test cases for cost control exceptions."""
    
    def test_cost_control_error_initialization(self):
        """Test CostControlError initialization."""
        error = CostControlError("Cost control error")
        
        assert error.message == "Cost control error"
    
    def test_cost_limit_exceeded_error(self):
        """Test CostLimitExceededError initialization."""
        error = CostLimitExceededError(
            "Daily cost limit exceeded",
            "test_service",
            daily_cost=25.50,
            daily_limit=20.00
        )
        
        assert error.message == "Daily cost limit exceeded"
        assert error.service_name == "test_service"
        assert error.daily_cost == 25.50
        assert error.daily_limit == 20.00


class TestConfigurationError:
    """Test cases for configuration exceptions."""
    
    def test_configuration_error_initialization(self):
        """Test ConfigurationError initialization."""
        error = ConfigurationError("Configuration error")
        
        assert error.message == "Configuration error"


class TestDatabaseError:
    """Test cases for database exceptions."""
    
    def test_database_error_initialization(self):
        """Test DatabaseError initialization."""
        error = DatabaseError("Database error")
        
        assert error.message == "Database error"


class TestStorageError:
    """Test cases for storage exceptions."""
    
    def test_storage_error_initialization(self):
        """Test StorageError initialization."""
        error = StorageError("Storage error")
        
        assert error.message == "Storage error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
