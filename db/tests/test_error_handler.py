import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from datetime import datetime
import json
from unittest.mock import patch, MagicMock
from asyncpg.exceptions import PostgresError
from pydantic import BaseModel, ValidationError

from db.middleware.error_handler import (
    ErrorHandlerMiddleware,
    APIError,
    ValidationAPIError,
    AuthorizationError,
    DatabaseError
)

@pytest.fixture
def app():
    app = FastAPI()
    app.add_middleware(ErrorHandlerMiddleware)
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

class TestModel(BaseModel):
    name: str
    age: int

def test_validation_error(app, client):
    """Test handling of pydantic validation errors."""
    @app.post("/test-validation")
    async def validation_endpoint(model: TestModel):
        return {"message": "success"}

    response = client.post(
        "/test-validation",
        json={"name": "test", "age": "not_an_integer"}
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error_type"] == "ValidationAPIError"
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "validation_errors" in data["details"]
    assert "trace_id" in data
    assert "timestamp" in data

def test_authorization_error(app, client):
    """Test handling of authorization errors."""
    @app.get("/test-auth")
    async def auth_endpoint():
        raise PermissionError("Unauthorized access")

    response = client.get("/test-auth")

    assert response.status_code == 403
    data = response.json()
    assert data["error_type"] == "AuthorizationError"
    assert data["error_code"] == "AUTHORIZATION_ERROR"
    assert data["message"] == "Unauthorized access"

def test_database_error(app, client):
    """Test handling of database errors."""
    @app.get("/test-db")
    async def db_endpoint():
        raise PostgresError("Database connection failed")

    response = client.get("/test-db")

    assert response.status_code == 500
    data = response.json()
    assert data["error_type"] == "DatabaseError"
    assert data["error_code"] == "DATABASE_ERROR"
    assert "pg_error" in data["details"]

def test_custom_api_error(app, client):
    """Test handling of custom API errors."""
    @app.get("/test-custom")
    async def custom_endpoint():
        raise APIError(
            message="Custom error",
            error_code="CUSTOM_ERROR",
            status_code=422,
            details={"custom_field": "custom_value"}
        )

    response = client.get("/test-custom")

    assert response.status_code == 422
    data = response.json()
    assert data["error_type"] == "APIError"
    assert data["error_code"] == "CUSTOM_ERROR"
    assert data["details"]["custom_field"] == "custom_value"

def test_unexpected_error(app, client):
    """Test handling of unexpected errors."""
    @app.get("/test-unexpected")
    async def unexpected_endpoint():
        raise ValueError("Unexpected error occurred")

    response = client.get("/test-unexpected")

    assert response.status_code == 500
    data = response.json()
    assert data["error_type"] == "APIError"
    assert "error_type" in data["details"]
    assert data["message"] == "Unexpected error occurred"

@pytest.mark.asyncio
async def test_error_logging(app, client):
    """Test that errors are properly logged."""
    with patch('logging.getLogger') as mock_logger:
        mock_logger_instance = MagicMock()
        mock_logger.return_value = mock_logger_instance

        @app.get("/test-logging")
        async def logging_endpoint():
            raise ValueError("Test error for logging")

        response = client.get("/test-logging")
        
        # Verify logger was called with correct context
        mock_logger_instance.exception.assert_called_once()
        call_args = mock_logger_instance.exception.call_args
        assert "Test error for logging" in call_args[0][0]
        assert "trace_id" in call_args[1]["extra"]
        assert "timestamp" in call_args[1]["extra"]
        assert "request_method" in call_args[1]["extra"]
        assert "request_url" in call_args[1]["extra"]

def test_trace_id_generation(app, client):
    """Test that unique trace IDs are generated for each request."""
    trace_ids = set()

    @app.get("/test-trace")
    async def trace_endpoint(request: Request):
        trace_ids.add(request.state.trace_id)
        raise ValueError("Test error")

    # Make multiple requests
    for _ in range(3):
        response = client.get("/test-trace")
        data = response.json()
        assert "trace_id" in data
        trace_ids.add(data["trace_id"])

    # Verify all trace IDs are unique
    assert len(trace_ids) == 6  # 3 from requests + 3 from responses

def test_error_response_structure(app, client):
    """Test the structure of error responses."""
    @app.get("/test-structure")
    async def structure_endpoint():
        raise APIError(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"test": "value"}
        )

    response = client.get("/test-structure")
    data = response.json()

    # Verify all required fields are present
    required_fields = {
        "message",
        "error_type",
        "error_code",
        "trace_id",
        "timestamp",
        "details"
    }
    assert all(field in data for field in required_fields)

    # Verify timestamp format
    datetime.fromisoformat(data["timestamp"])  # Should not raise error

    # Verify details structure
    assert isinstance(data["details"], dict)
    assert data["details"]["test"] == "value" 