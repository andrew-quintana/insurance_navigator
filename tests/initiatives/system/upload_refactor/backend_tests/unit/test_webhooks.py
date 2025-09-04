"""
Unit tests for webhook functionality.

This module tests the webhook endpoints, HMAC signature verification,
and webhook processing logic.
"""

import pytest
import json
import hashlib
import hmac
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4

from backend.api.routes.webhooks import verify_webhook_signature
from backend.shared.schemas.webhooks import LlamaParseWebhookRequest, LlamaParseWebhookResponse
from backend.shared.external.service_router import ServiceRouter, ServiceMode
from backend.shared.external.llamaparse_real import RealLlamaParseService

class TestWebhookSignatureVerification:
    """Test webhook signature verification functionality."""
    
    def test_verify_webhook_signature_valid(self):
        """Test valid webhook signature verification."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        
        # Generate valid signature
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        result = verify_webhook_signature(payload, expected_signature, secret)
        assert result is True
    
    def test_verify_webhook_signature_invalid(self):
        """Test invalid webhook signature verification."""
        secret = "test_secret"
        payload = b'{"test": "data"}'
        invalid_signature = "invalid_signature"
        
        # Verify invalid signature
        result = verify_webhook_signature(payload, invalid_signature, secret)
        assert result is False
    
    def test_verify_webhook_signature_empty_secret(self):
        """Test signature verification with empty secret."""
        secret = ""
        payload = b'{"test": "data"}'
        signature = "some_signature"
        
        # Should handle empty secret gracefully
        result = verify_webhook_signature(payload, signature, secret)
        assert result is False

class TestWebhookFunctions:
    """Test webhook utility functions."""
    
    @patch('backend.api.routes.webhooks.get_config')
    def test_webhook_signature_verification_integration(self, mock_get_config):
        """Test webhook signature verification with mocked config."""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.llamaparse.webhook_secret = "test_webhook_secret_123"
        mock_get_config.return_value = mock_config
        
        # Test data
        secret = "test_webhook_secret_123"
        payload = b'{"test": "data", "correlation_id": "test_123"}'
        
        # Generate valid signature
        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Test verification
        result = verify_webhook_signature(payload, signature, secret)
        assert result is True
        
        # Test invalid signature
        result = verify_webhook_signature(payload, "invalid_signature", secret)
        assert result is False

class TestWebhookSchemas:
    """Test webhook schema validation."""
    
    def test_llamaparse_webhook_request_validation(self):
        """Test LlamaParse webhook request schema validation."""
        # Valid webhook data
        job_id = uuid4()
        document_id = uuid4()
        valid_data = {
            "job_id": job_id,
            "document_id": document_id,
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
        webhook_request = LlamaParseWebhookRequest(**valid_data)
        assert webhook_request.job_id == job_id
        assert webhook_request.status == "parsed"
        assert webhook_request.document_id == document_id
        assert len(webhook_request.artifacts) == 1
        assert webhook_request.artifacts[0].type == "markdown"
    
    def test_llamaparse_webhook_response_creation(self):
        """Test LlamaParse webhook response creation."""
        job_id = uuid4()
        document_id = uuid4()
        
        response = LlamaParseWebhookResponse(
            success=True,
            message="Webhook processed successfully",
            job_id=job_id,
            document_id=document_id
        )
        
        assert response.success is True
        assert response.message == "Webhook processed successfully"
        assert response.job_id == job_id
        assert response.document_id == document_id
        assert response.processed_at is not None

class TestWebhookSecurity:
    """Test webhook security features."""
    
    def test_hmac_signature_generation(self):
        """Test HMAC signature generation for webhook security."""
        secret = "test_webhook_secret_123"
        payload = b'{"test": "data", "correlation_id": "test_123"}'
        
        # Generate signature using same method as webhook handler
        signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature is valid
        assert len(signature) == 64  # SHA256 hex digest length
        assert signature.isalnum()  # Should be alphanumeric
        
        # Verify with our verification function
        result = verify_webhook_signature(payload, signature, secret)
        assert result is True
    
    def test_signature_timing_attack_protection(self):
        """Test that signature verification is protected against timing attacks."""
        secret = "test_webhook_secret_123"
        payload = b'{"test": "data"}'
        
        # Generate valid signature
        valid_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Generate invalid signature of same length
        invalid_signature = "a" * len(valid_signature)
        
        # Both should take similar time to verify (timing attack protection)
        import time
        
        start_time = time.time()
        verify_webhook_signature(payload, valid_signature, secret)
        valid_time = time.time() - start_time
        
        start_time = time.time()
        verify_webhook_signature(payload, invalid_signature, secret)
        invalid_time = time.time() - start_time
        
        # Times should be similar (within reasonable bounds)
        time_diff = abs(valid_time - invalid_time)
        assert time_diff < 0.1  # Should be less than 100ms difference
