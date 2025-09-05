#!/usr/bin/env python3
"""
Phase 2: API Service Unit Tests
Enhanced unit tests for API service components including upload handlers, 
document processing, and authentication flows.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

# Import API components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))

from api.upload_pipeline.main import app
from api.upload_pipeline.upload_handler import UploadHandler
from api.upload_pipeline.document_processor import DocumentProcessor
from api.upload_pipeline.auth_service import AuthService

class TestUploadHandler:
    """Unit tests for UploadHandler component"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing"""
        config = Mock()
        config.supabase_url = "https://test.supabase.co"
        config.supabase_anon_key = "test_anon_key"
        config.supabase_service_role_key = "test_service_key"
        config.storage_bucket = "test-bucket"
        config.max_file_size = 10 * 1024 * 1024  # 10MB
        config.allowed_file_types = [".pdf", ".docx", ".txt"]
        return config
    
    @pytest.fixture
    def upload_handler(self, mock_config):
        """Create UploadHandler instance for testing"""
        return UploadHandler(mock_config)
    
    @pytest.fixture
    def sample_pdf_file(self):
        """Create sample PDF file for testing"""
        content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        return UploadFile(
            file=io.BytesIO(content),
            filename="test_document.pdf",
            content_type="application/pdf"
        )
    
    def test_upload_handler_initialization(self, upload_handler, mock_config):
        """Test UploadHandler initialization"""
        assert upload_handler.config == mock_config
        assert upload_handler.max_file_size == mock_config.max_file_size
        assert upload_handler.allowed_file_types == mock_config.allowed_file_types
    
    def test_validate_file_type_valid(self, upload_handler, sample_pdf_file):
        """Test file type validation with valid file"""
        result = upload_handler.validate_file_type(sample_pdf_file)
        assert result is True
    
    def test_validate_file_type_invalid(self, upload_handler):
        """Test file type validation with invalid file"""
        invalid_file = UploadFile(
            file=io.BytesIO(b"invalid content"),
            filename="test.txt",
            content_type="text/plain"
        )
        result = upload_handler.validate_file_type(invalid_file)
        assert result is False
    
    def test_validate_file_size_valid(self, upload_handler, sample_pdf_file):
        """Test file size validation with valid file"""
        result = upload_handler.validate_file_size(sample_pdf_file)
        assert result is True
    
    def test_validate_file_size_invalid(self, upload_handler):
        """Test file size validation with oversized file"""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = UploadFile(
            file=io.BytesIO(large_content),
            filename="large_file.pdf",
            content_type="application/pdf"
        )
        result = upload_handler.validate_file_size(large_file)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, upload_handler, sample_pdf_file):
        """Test successful file upload"""
        with patch.object(upload_handler, 'upload_to_storage') as mock_upload:
            mock_upload.return_value = {
                "file_id": "test-file-id",
                "file_path": "test/path/test_document.pdf",
                "file_size": 179
            }
            
            result = await upload_handler.upload_file(sample_pdf_file, "test-user-id")
            
            assert result["file_id"] == "test-file-id"
            assert result["file_path"] == "test/path/test_document.pdf"
            assert result["file_size"] == 179
            mock_upload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_validation_error(self, upload_handler):
        """Test file upload with validation error"""
        invalid_file = UploadFile(
            file=io.BytesIO(b"invalid content"),
            filename="test.txt",
            content_type="text/plain"
        )
        
        with pytest.raises(ValueError, match="Invalid file type"):
            await upload_handler.upload_file(invalid_file, "test-user-id")
    
    @pytest.mark.asyncio
    async def test_upload_file_storage_error(self, upload_handler, sample_pdf_file):
        """Test file upload with storage error"""
        with patch.object(upload_handler, 'upload_to_storage') as mock_upload:
            mock_upload.side_effect = Exception("Storage error")
            
            with pytest.raises(Exception, match="Storage error"):
                await upload_handler.upload_file(sample_pdf_file, "test-user-id")

class TestDocumentProcessor:
    """Unit tests for DocumentProcessor component"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing"""
        config = Mock()
        config.llamaparse_api_key = "test_llamaparse_key"
        config.llamaparse_base_url = "https://api.cloud.llamaindex.ai"
        config.openai_api_key = "test_openai_key"
        config.openai_model = "text-embedding-3-small"
        return config
    
    @pytest.fixture
    def document_processor(self, mock_config):
        """Create DocumentProcessor instance for testing"""
        return DocumentProcessor(mock_config)
    
    @pytest.fixture
    def sample_document_data(self):
        """Create sample document data for testing"""
        return {
            "file_id": "test-file-id",
            "file_path": "test/path/test_document.pdf",
            "file_type": "application/pdf",
            "file_size": 179,
            "user_id": "test-user-id"
        }
    
    def test_document_processor_initialization(self, document_processor, mock_config):
        """Test DocumentProcessor initialization"""
        assert document_processor.config == mock_config
        assert document_processor.llamaparse_api_key == mock_config.llamaparse_api_key
        assert document_processor.openai_api_key == mock_config.openai_api_key
    
    @pytest.mark.asyncio
    async def test_parse_document_success(self, document_processor, sample_document_data):
        """Test successful document parsing"""
        mock_parsed_content = {
            "content": "This is a test insurance document with policy details.",
            "metadata": {
                "title": "Test Insurance Policy",
                "pages": 1,
                "language": "en"
            }
        }
        
        with patch.object(document_processor, 'call_llamaparse_api') as mock_llamaparse:
            mock_llamaparse.return_value = mock_parsed_content
            
            result = await document_processor.parse_document(sample_document_data)
            
            assert result["content"] == mock_parsed_content["content"]
            assert result["metadata"] == mock_parsed_content["metadata"]
            assert result["status"] == "parsed"
            mock_llamaparse.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_document_api_error(self, document_processor, sample_document_data):
        """Test document parsing with API error"""
        with patch.object(document_processor, 'call_llamaparse_api') as mock_llamaparse:
            mock_llamaparse.side_effect = Exception("LlamaParse API error")
            
            with pytest.raises(Exception, match="LlamaParse API error"):
                await document_processor.parse_document(sample_document_data)
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, document_processor):
        """Test successful embedding generation"""
        content = "This is a test insurance document with policy details."
        mock_embeddings = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        with patch.object(document_processor, 'call_openai_api') as mock_openai:
            mock_openai.return_value = mock_embeddings
            
            result = await document_processor.generate_embeddings(content)
            
            assert result == mock_embeddings
            mock_openai.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_embeddings_api_error(self, document_processor):
        """Test embedding generation with API error"""
        content = "This is a test insurance document with policy details."
        
        with patch.object(document_processor, 'call_openai_api') as mock_openai:
            mock_openai.side_effect = Exception("OpenAI API error")
            
            with pytest.raises(Exception, match="OpenAI API error"):
                await document_processor.generate_embeddings(content)
    
    @pytest.mark.asyncio
    async def test_process_document_complete_workflow(self, document_processor, sample_document_data):
        """Test complete document processing workflow"""
        mock_parsed_content = {
            "content": "This is a test insurance document with policy details.",
            "metadata": {"title": "Test Insurance Policy", "pages": 1}
        }
        mock_embeddings = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        with patch.object(document_processor, 'parse_document') as mock_parse, \
             patch.object(document_processor, 'generate_embeddings') as mock_embeddings_func, \
             patch.object(document_processor, 'save_to_database') as mock_save:
            
            mock_parse.return_value = mock_parsed_content
            mock_embeddings_func.return_value = mock_embeddings
            mock_save.return_value = {"document_id": "test-doc-id"}
            
            result = await document_processor.process_document(sample_document_data)
            
            assert result["document_id"] == "test-doc-id"
            assert result["status"] == "processed"
            assert result["content"] == mock_parsed_content["content"]
            assert result["embeddings"] == mock_embeddings
            
            mock_parse.assert_called_once()
            mock_embeddings_func.assert_called_once()
            mock_save.assert_called_once()

class TestAuthService:
    """Unit tests for AuthService component"""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration for testing"""
        config = Mock()
        config.supabase_url = "https://test.supabase.co"
        config.supabase_anon_key = "test_anon_key"
        config.supabase_service_role_key = "test_service_key"
        config.jwt_secret = "test_jwt_secret"
        return config
    
    @pytest.fixture
    def auth_service(self, mock_config):
        """Create AuthService instance for testing"""
        return AuthService(mock_config)
    
    def test_auth_service_initialization(self, auth_service, mock_config):
        """Test AuthService initialization"""
        assert auth_service.config == mock_config
        assert auth_service.supabase_url == mock_config.supabase_url
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service):
        """Test successful user authentication"""
        mock_user_data = {
            "id": "test-user-id",
            "email": "test@example.com",
            "role": "user"
        }
        
        with patch.object(auth_service, 'verify_token') as mock_verify:
            mock_verify.return_value = mock_user_data
            
            result = await auth_service.authenticate_user("valid-token")
            
            assert result["user_id"] == "test-user-id"
            assert result["email"] == "test@example.com"
            assert result["role"] == "user"
            mock_verify.assert_called_once_with("valid-token")
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_token(self, auth_service):
        """Test user authentication with invalid token"""
        with patch.object(auth_service, 'verify_token') as mock_verify:
            mock_verify.return_value = None
            
            with pytest.raises(ValueError, match="Invalid token"):
                await auth_service.authenticate_user("invalid-token")
    
    @pytest.mark.asyncio
    async def test_authorize_user_success(self, auth_service):
        """Test successful user authorization"""
        user_data = {
            "user_id": "test-user-id",
            "role": "user"
        }
        
        result = await auth_service.authorize_user(user_data, "upload")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_authorize_user_insufficient_permissions(self, auth_service):
        """Test user authorization with insufficient permissions"""
        user_data = {
            "user_id": "test-user-id",
            "role": "viewer"
        }
        
        result = await auth_service.authorize_user(user_data, "admin")
        assert result is False

class TestAPIEndpoints:
    """Unit tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client for API"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_upload_endpoint_unauthorized(self, client):
        """Test upload endpoint without authentication"""
        response = client.post("/upload")
        assert response.status_code == 401
    
    def test_upload_endpoint_authorized(self, client):
        """Test upload endpoint with authentication"""
        # Mock authentication
        with patch('api.upload_pipeline.main.auth_service') as mock_auth:
            mock_auth.authenticate_user.return_value = {
                "user_id": "test-user-id",
                "email": "test@example.com"
            }
            
            # Mock file upload
            with patch('api.upload_pipeline.main.upload_handler') as mock_upload:
                mock_upload.upload_file.return_value = {
                    "file_id": "test-file-id",
                    "file_path": "test/path/test.pdf"
                }
                
                files = {"file": ("test.pdf", b"test content", "application/pdf")}
                headers = {"Authorization": "Bearer valid-token"}
                
                response = client.post("/upload", files=files, headers=headers)
                assert response.status_code == 200
                
                data = response.json()
                assert data["file_id"] == "test-file-id"
                assert data["status"] == "uploaded"
    
    def test_document_status_endpoint(self, client):
        """Test document status endpoint"""
        with patch('api.upload_pipeline.main.document_processor') as mock_processor:
            mock_processor.get_document_status.return_value = {
                "document_id": "test-doc-id",
                "status": "processed",
                "progress": 100
            }
            
            response = client.get("/documents/test-doc-id/status")
            assert response.status_code == 200
            
            data = response.json()
            assert data["document_id"] == "test-doc-id"
            assert data["status"] == "processed"
    
    def test_document_retrieve_endpoint(self, client):
        """Test document retrieval endpoint"""
        with patch('api.upload_pipeline.main.document_processor') as mock_processor:
            mock_processor.get_document.return_value = {
                "document_id": "test-doc-id",
                "content": "Test document content",
                "metadata": {"title": "Test Document"}
            }
            
            response = client.get("/documents/test-doc-id")
            assert response.status_code == 200
            
            data = response.json()
            assert data["document_id"] == "test-doc-id"
            assert data["content"] == "Test document content"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
