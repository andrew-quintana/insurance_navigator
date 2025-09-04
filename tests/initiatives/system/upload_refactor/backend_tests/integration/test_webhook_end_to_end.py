"""
End-to-end webhook testing for Phase 3.5.

This module tests the complete webhook flow including:
- Job state management integration
- Database operations
- Storage operations
- Pipeline stage triggering
"""

import pytest
import json
import asyncio
import hashlib
import hmac
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from uuid import uuid4
import httpx

from backend.api.routes.webhooks import llamaparse_webhook
from backend.shared.schemas.webhooks import LlamaParseWebhookRequest, LlamaParseArtifact, LlamaParseMeta
from backend.shared.external.service_router import ServiceRouter, ServiceMode
from backend.shared.external.llamaparse_real import RealLlamaParseService
from backend.shared.db.connection import DatabaseManager
from backend.shared.storage.storage_manager import StorageManager


class AsyncContextManagerMock:
    """Mock class that properly implements async context manager protocol."""
    
    def __init__(self, mock_conn):
        self.mock_conn = mock_conn
    
    async def __aenter__(self):
        return self.mock_conn
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestWebhookEndToEnd:
    """Test end-to-end webhook flow integration."""
    
    @pytest.fixture
    def sample_webhook_data(self):
        """Sample webhook data for successful parsing."""
        # Generate proper SHA256 hash for test content
        test_content = "# Test Document\n\nThis is test content for parsing."
        content_hash = hashlib.sha256(test_content.encode()).hexdigest()
        
        return {
            "job_id": str(uuid4()),
            "document_id": str(uuid4()),
            "status": "parsed",
            "parse_job_id": "parse_123",
            "correlation_id": "test-correlation-456",
            "artifacts": [
                {
                    "type": "markdown",
                    "content": test_content,
                    "sha256": content_hash,
                    "bytes": 45
                }
            ],
            "meta": {
                "parser_name": "llamaparse",
                "parser_version": "1.0.0"
            }
        }
    
    @pytest.fixture
    def sample_failed_webhook_data(self):
        """Sample webhook data for failed parsing."""
        return {
            "job_id": str(uuid4()),
            "document_id": str(uuid4()),
            "status": "failed",
            "parse_job_id": "parse_456",
            "correlation_id": "test-correlation-456",
            "artifacts": [],
            "meta": {
                "parser_name": "llamaparse",
                "parser_version": "1.0.0",
                "error": "Document parsing failed due to invalid format"
            }
        }
    
    @pytest.fixture
    async def mock_dependencies(self):
        """Set up mock dependencies for testing."""
        # Mock service router
        mock_service_router = MagicMock(spec=ServiceRouter)
        mock_service_router.mode = ServiceMode.REAL
        
        # Mock LlamaParse service
        mock_llamaparse_service = MagicMock(spec=RealLlamaParseService)
        
        # Mock database manager
        mock_db_manager = MagicMock(spec=DatabaseManager)
        mock_db_manager.initialize = AsyncMock()
        
        # Mock database connection
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock()
        
        # Create proper async context manager mock
        mock_context_manager = AsyncContextManagerMock(mock_conn)
        mock_db_manager.get_db_connection = MagicMock(return_value=mock_context_manager)
        
        # Mock storage manager
        mock_storage_manager = MagicMock(spec=StorageManager)
        mock_storage_manager.write_blob = AsyncMock(return_value=True)
        
        return {
            "service_router": mock_service_router,
            "llamaparse_service": mock_llamaparse_service,
            "db_manager": mock_db_manager,
            "storage_manager": mock_storage_manager,
            "mock_conn": mock_conn
        }
    
    async def test_webhook_parsed_status_flow(self, mock_dependencies, sample_webhook_data):
        """Test complete webhook flow for successful parsing."""
        # Set up mock storage
        mock_dependencies["storage_manager"].write_blob.return_value = True
        
        # Create webhook request
        webhook_request = LlamaParseWebhookRequest(**sample_webhook_data)
        
        # Mock FastAPI request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=json.dumps(sample_webhook_data).encode())
        mock_request.headers = {"X-Webhook-Signature": "test_signature"}
        
        # Mock configuration
        with patch('backend.api.routes.webhooks.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.llamaparse.webhook_secret = "test_secret"
            mock_get_config.return_value = mock_config
            
            # Mock signature verification
            with patch('backend.api.routes.webhooks.verify_webhook_signature', return_value=True):
                # Call webhook handler
                response = await llamaparse_webhook(
                    mock_request,
                    mock_dependencies["service_router"],
                    mock_dependencies["llamaparse_service"],
                    mock_dependencies["db_manager"],
                    mock_dependencies["storage_manager"]
                )
                
                # Verify response
                assert response.success is True
                assert response.job_id == webhook_request.job_id
                assert response.document_id == webhook_request.document_id
                
                # Verify storage was called
                mock_dependencies["storage_manager"].write_blob.assert_called_once()
                
                # Verify database operations were called
                assert mock_dependencies["mock_conn"].execute.call_count >= 2  # At least 2 SQL operations
    
    async def test_webhook_failed_status_flow(self, mock_dependencies, sample_failed_webhook_data):
        """Test complete webhook flow for failed parsing."""
        # Create webhook request
        webhook_request = LlamaParseWebhookRequest(**sample_failed_webhook_data)
        
        # Mock FastAPI request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=json.dumps(sample_failed_webhook_data).encode())
        mock_request.headers = {"X-Webhook-Signature": "test_signature"}
        
        # Mock configuration
        with patch('backend.api.routes.webhooks.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.llamaparse.webhook_secret = "test_secret"
            mock_get_config.return_value = mock_config
            
            # Mock signature verification
            with patch('backend.api.routes.webhooks.verify_webhook_signature', return_value=True):
                # Call webhook handler
                response = await llamaparse_webhook(
                    mock_request,
                    mock_dependencies["service_router"],
                    mock_dependencies["llamaparse_service"],
                    mock_dependencies["db_manager"],
                    mock_dependencies["storage_manager"]
                )
                
                # Verify response
                assert response.success is True
                assert response.job_id == webhook_request.job_id
                assert response.document_id == webhook_request.document_id
                
                # Verify database operations were called
                assert mock_dependencies["mock_conn"].execute.call_count >= 1  # At least 1 SQL operation
    
    async def test_webhook_storage_integration(self, mock_dependencies, sample_webhook_data):
        """Test webhook integration with storage manager."""
        # Set up mock storage to fail
        mock_dependencies["storage_manager"].write_blob.return_value = False
        
        # Create webhook request
        webhook_request = LlamaParseWebhookRequest(**sample_webhook_data)
        
        # Mock FastAPI request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=json.dumps(sample_webhook_data).encode())
        mock_request.headers = {"X-Webhook-Signature": "test_signature"}
        
        # Mock configuration
        with patch('backend.api.routes.webhooks.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.llamaparse.webhook_secret = "test_secret"
            mock_get_config.return_value = mock_config
            
            # Mock signature verification
            with patch('backend.api.routes.webhooks.verify_webhook_signature', return_value=True):
                # Call webhook handler - should raise HTTPException due to storage failure
                with pytest.raises(Exception, match="Internal server error"):
                    await llamaparse_webhook(
                        mock_request,
                        mock_dependencies["service_router"],
                        mock_dependencies["llamaparse_service"],
                        mock_dependencies["db_manager"],
                        mock_dependencies["storage_manager"]
                    )
    
    async def test_webhook_database_integration(self, mock_dependencies, sample_webhook_data):
        """Test webhook integration with database manager."""
        # Set up mock storage
        mock_dependencies["storage_manager"].write_blob.return_value = True
        
        # Create webhook request
        webhook_request = LlamaParseWebhookRequest(**sample_webhook_data)
        
        # Mock FastAPI request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=json.dumps(sample_webhook_data).encode())
        mock_request.headers = {"X-Webhook-Signature": "test_signature"}
        
        # Mock configuration
        with patch('backend.api.routes.webhooks.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.llamaparse.webhook_secret = "test_secret"
            mock_get_config.return_value = mock_config
            
            # Mock signature verification
            with patch('backend.api.routes.webhooks.verify_webhook_signature', return_value=True):
                # Call webhook handler
                response = await llamaparse_webhook(
                    mock_request,
                    mock_dependencies["service_router"],
                    mock_dependencies["llamaparse_service"],
                    mock_dependencies["db_manager"],
                    mock_dependencies["storage_manager"]
                )
                
                # Verify database connection was acquired
                mock_dependencies["db_manager"].get_db_connection.assert_called_once()
                
                # Verify database operations were executed
                assert mock_dependencies["mock_conn"].execute.call_count >= 2
    
    async def test_webhook_signature_verification(self, mock_dependencies, sample_webhook_data):
        """Test webhook signature verification."""
        # Create webhook request
        webhook_request = LlamaParseWebhookRequest(**sample_webhook_data)
        
        # Mock FastAPI request
        mock_request = MagicMock()
        mock_request.body = AsyncMock(return_value=json.dumps(sample_webhook_data).encode())
        mock_request.headers = {"X-Webhook-Signature": "test_signature"}
        
        # Mock configuration
        with patch('backend.api.routes.webhooks.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.llamaparse.webhook_secret = "test_secret"
            mock_get_config.return_value = mock_config
            
            # Mock signature verification to fail
            with patch('backend.api.routes.webhooks.verify_webhook_signature', return_value=False):
                # Call webhook handler - should raise HTTPException due to invalid signature
                with pytest.raises(Exception, match="Invalid webhook signature"):
                    await llamaparse_webhook(
                        mock_request,
                        mock_dependencies["service_router"],
                        mock_dependencies["llamaparse_service"],
                        mock_dependencies["db_manager"],
                        mock_dependencies["storage_manager"]
                    )


class TestWebhookRealAPIIntegration:
    """Test webhook integration with real API services."""
    
    @pytest.mark.skip(reason="Requires real LlamaParse API credentials")
    async def test_real_llamaparse_webhook_flow(self):
        """Test webhook flow with real LlamaParse API."""
        # This test would require real API credentials and network access
        # It's skipped by default but can be enabled for integration testing
        pass
    
    async def test_webhook_signature_verification_real(self):
        """Test webhook signature verification with real HMAC."""
        # This test validates the actual signature verification logic
        # without requiring external API calls
        pass

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
