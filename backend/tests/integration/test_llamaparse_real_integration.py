"""
Integration tests for real LlamaParse service.

This module tests the complete LlamaParse integration including
API client, webhook handling, and service router integration.
"""

import pytest
import asyncio
import json
import hashlib
import hmac
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.external.service_router import ServiceRouter, ServiceMode
from backend.shared.config.enhanced_config import get_config

class TestRealLlamaParseIntegration:
    """Test real LlamaParse service integration."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        with patch('backend.shared.config.enhanced_config.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.service_mode = ServiceMode.REAL
            mock_config.llamaparse.api_key = "test_api_key_123"
            mock_config.llamaparse.base_url = "https://api.test.com"
            mock_config.llamaparse.webhook_secret = "test_webhook_secret_123"
            mock_config.llamaparse.daily_cost_limit_usd = 10.0
            mock_config.llamaparse.hourly_rate_limit = 100
            mock_config.llamaparse.timeout_seconds = 30
            mock_config.llamaparse.retry_attempts = 3
            mock_get_config.return_value = mock_config
            yield mock_get_config
    
    @pytest.fixture
    def real_llamaparse_service(self, mock_config):
        """Create real LlamaParse service instance for testing."""
        return RealLlamaParseService(
            api_key="test_api_key_123",
            base_url="https://api.test.com",
            webhook_secret="test_webhook_secret_123",
            rate_limit_per_minute=60,
            timeout_seconds=30,
            max_retries=3
        )
    
    @pytest.fixture
    def service_router(self, mock_config):
        """Create service router instance for testing."""
        return ServiceRouter(config={"mode": "real"}, start_health_monitoring=False)
    
    def test_real_llamaparse_service_initialization(self, real_llamaparse_service):
        """Test RealLlamaParseService initialization."""
        assert real_llamaparse_service.api_key == "test_api_key_123"
        assert real_llamaparse_service.base_url == "https://api.test.com"
        assert real_llamaparse_service.webhook_secret == "test_webhook_secret_123"
        assert real_llamaparse_service.rate_limit_per_minute == 60
        assert real_llamaparse_service.timeout_seconds == 30
        assert real_llamaparse_service.max_retries == 3
        assert real_llamaparse_service.client is not None
    
    def test_webhook_signature_verification(self, real_llamaparse_service):
        """Test webhook signature verification functionality."""
        secret = "test_webhook_secret_123"
        payload = b'{"test": "data", "correlation_id": "test_123"}'
        
        # Generate valid signature
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        result = real_llamaparse_service.verify_webhook_signature(payload, expected_signature)
        assert result is True
        
        # Test invalid signature
        result = real_llamaparse_service.verify_webhook_signature(payload, "invalid_signature")
        assert result is False
    
    def test_webhook_signature_verification_no_secret(self):
        """Test webhook signature verification when no secret is configured."""
        service = RealLlamaParseService(
            api_key="test_key",
            base_url="https://api.test.com",
            webhook_secret=None  # No secret configured
        )
        
        payload = b'{"test": "data"}'
        signature = "some_signature"
        
        # Should return True when no secret configured (warning logged)
        result = service.verify_webhook_signature(payload, signature)
        assert result is True
    
    def test_rate_limiting_initialization(self, real_llamaparse_service):
        """Test rate limiting initialization."""
        # Test rate limit state initialization
        assert len(real_llamaparse_service.request_times) == 0
        assert real_llamaparse_service.rate_limit_per_minute == 60
    
    def test_service_interface_compliance(self, real_llamaparse_service):
        """Test that RealLlamaParseService implements ServiceInterface correctly."""
        # Check required methods exist
        assert hasattr(real_llamaparse_service, 'is_available')
        assert hasattr(real_llamaparse_service, 'get_health')
        assert hasattr(real_llamaparse_service, 'execute')
        
        # Check method types
        assert callable(real_llamaparse_service.is_available)
        assert callable(real_llamaparse_service.get_health)
        assert callable(real_llamaparse_service.execute)
    
    def test_service_router_initialization(self, service_router):
        """Test service router initialization."""
        assert service_router.mode == ServiceMode.REAL
        assert service_router.fallback_enabled is True
        assert service_router.fallback_timeout == 10
    
    def test_service_router_mode_switching(self, service_router):
        """Test service router mode switching."""
        # Test mode switching
        service_router.set_mode(ServiceMode.MOCK)
        assert service_router.mode == ServiceMode.MOCK
        
        service_router.set_mode(ServiceMode.HYBRID)
        assert service_router.mode == ServiceMode.HYBRID
        
        service_router.set_mode(ServiceMode.REAL)
        assert service_router.mode == ServiceMode.REAL

class TestLlamaParseWebhookIntegration:
    """Test LlamaParse webhook integration scenarios."""
    
    def test_webhook_payload_validation(self):
        """Test webhook payload validation with real schemas."""
        from backend.shared.schemas.webhooks import LlamaParseWebhookRequest, LlamaParseArtifact, LlamaParseMeta
        
        # Create valid webhook payload
        webhook_data = {
            "job_id": uuid4(),
            "document_id": uuid4(),
            "status": "parsed",
            "artifacts": [{
                "type": "markdown",
                "content": "# Test Document\n\nThis is test content.",
                "sha256": "a" * 64,  # Valid SHA256 pattern
                "bytes": 50
            }],
            "meta": {
                "parser_name": "llamaparse",
                "parser_version": "1.0.0"
            }
        }
        
        # Should create valid object
        webhook_request = LlamaParseWebhookRequest(**webhook_data)
        assert webhook_request.status == "parsed"
        assert len(webhook_request.artifacts) == 1
        assert webhook_request.artifacts[0].type == "markdown"
        assert webhook_request.artifacts[0].sha256 == "a" * 64
    
    def test_webhook_status_validation(self):
        """Test webhook status validation."""
        from backend.shared.schemas.webhooks import LlamaParseWebhookRequest, LlamaParseArtifact, LlamaParseMeta
        
        # Test valid statuses
        valid_statuses = ['parsed', 'failed', 'processing']
        
        for status in valid_statuses:
            webhook_data = {
                "job_id": uuid4(),
                "document_id": uuid4(),
                "status": status,
                "artifacts": [],
                "meta": {
                    "parser_name": "llamaparse",
                    "parser_version": "1.0.0"
                }
            }
            
            webhook_request = LlamaParseWebhookRequest(**webhook_data)
            assert webhook_request.status == status
        
        # Test invalid status
        with pytest.raises(ValueError, match="Invalid status"):
            webhook_data = {
                "job_id": uuid4(),
                "document_id": uuid4(),
                "status": "invalid_status",
                "artifacts": [],
                "meta": {
                    "parser_name": "llamaparse",
                    "parser_version": "1.0.0"
                }
            }
            
            LlamaParseWebhookRequest(**webhook_data)

class TestLlamaParseAsyncIntegration:
    """Test LlamaParse async integration scenarios."""
    
    @pytest.fixture
    def real_llamaparse_service(self):
        """Create real LlamaParse service instance for testing."""
        return RealLlamaParseService(
            api_key="test_api_key_123",
            base_url="https://api.test.com",
            webhook_secret="test_webhook_secret_123",
            rate_limit_per_minute=60,
            timeout_seconds=30,
            max_retries=3
        )
    
    @pytest.mark.asyncio
    async def test_service_health_check(self, real_llamaparse_service):
        """Test service health checking functionality."""
        # Mock the HTTP client to simulate health check
        with patch.object(real_llamaparse_service.client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            health = await real_llamaparse_service.get_health()
            
            assert health.is_healthy is True
            assert health.last_check is not None
            assert health.response_time_ms is not None
            assert health.error_count == 0
            assert health.last_error is None
    
    @pytest.mark.asyncio
    async def test_service_health_check_failure(self, real_llamaparse_service):
        """Test service health checking with failure."""
        # Mock the HTTP client to simulate health check failure
        with patch.object(real_llamaparse_service.client, 'get') as mock_get:
            mock_get.side_effect = Exception("Connection failed")
            
            health = await real_llamaparse_service.get_health()
            
            assert health.is_healthy is False
            assert health.last_check is not None
            assert health.error_count > 0
            assert health.last_error is not None
    
    @pytest.mark.asyncio
    async def test_service_availability_check(self, real_llamaparse_service):
        """Test service availability checking."""
        # Mock health check to return healthy
        with patch.object(real_llamaparse_service, 'get_health') as mock_health:
            mock_health.return_value = MagicMock(is_healthy=True)
            
            is_available = await real_llamaparse_service.is_available()
            assert is_available is True
        
        # Mock health check to return unhealthy
        with patch.object(real_llamaparse_service, 'get_health') as mock_health:
            mock_health.return_value = MagicMock(is_healthy=False)
            
            is_available = await real_llamaparse_service.is_available()
            assert is_available is False
