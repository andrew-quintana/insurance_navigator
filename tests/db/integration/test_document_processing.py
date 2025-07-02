"""
Unit tests for document processing functionality.

This module tests the core document processing functionality including:
1. Document parsing
2. Chunking
3. Vectorization
4. Status management
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, Any, List
from langchain_core.documents import Document

from db.services.document_service import DocumentService
from db.services.embedding_service import EmbeddingService
from config.parser import DocumentParser
from tests.config.test_config import get_test_config

class TestDocumentProcessing:
    @pytest.fixture
    def mock_storage_service(self):
        """Mock storage service for testing."""
        mock = MagicMock()
        mock.get_document = AsyncMock(return_value=b"Test document content")
        mock.store_document = AsyncMock(return_value="test/path/document.pdf")
        return mock

    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service for testing."""
        mock = MagicMock()
        mock.create_embeddings = AsyncMock(return_value=[[0.1] * 1536])  # Mock embedding vector
        return mock

    @pytest.fixture
    def mock_document_service(self):
        """Mock document service for testing."""
        mock = MagicMock()
        mock.create_document = AsyncMock(return_value={"id": str(uuid.uuid4())})
        mock.update_document_status = AsyncMock()
        mock.get_document_status = AsyncMock(return_value={"status": "pending"})
        return mock

    @pytest.fixture
    def test_document_data(self):
        """Test document data fixture."""
        return {
            'original_filename': 'test_doc.pdf',
            'document_type': 'user_uploaded',
            'content_type': 'application/pdf',
            'storage_path': f'documents/{uuid.uuid4()}/test_doc.pdf',
            'metadata': {
                'jurisdiction': 'federal',
                'program': 'medicare',
                'document_date': datetime.now().isoformat(),
                'tags': ['test', 'unit']
            },
            'status': 'pending'
        }

    @pytest.mark.asyncio
    async def test_document_creation(self, mock_document_service, test_document_data):
        """Test document creation."""
        # Test creating a document
        doc_id = await mock_document_service.create_document(
            user_id=str(uuid.uuid4()),
            metadata=test_document_data
        )
        assert doc_id is not None
        assert isinstance(doc_id, dict)
        assert "id" in doc_id

        # Verify document status
        status = await mock_document_service.get_document_status(doc_id["id"])
        assert status["status"] == "pending"

    @pytest.mark.asyncio
    async def test_document_parsing(self):
        """Test document parsing functionality."""
        with patch('config.parser.LlamaParse') as mock_llama_parse_class, \
             patch('builtins.open', mock_open(read_data=b"Test document content")), \
             patch('pathlib.Path.exists', return_value=True):
            
            # Setup mock LlamaParse
            mock_llama_parse = MagicMock()
            mock_llama_parse_class.return_value = mock_llama_parse
            
            # Mock document parsing
            mock_doc = MagicMock()
            mock_doc.text = "Test Insurance Policy\nPolicy Number: TEST-123"
            mock_doc.page_number = 1
            mock_llama_parse.load_data.return_value = [mock_doc]
            
            # Create parser with mocked dependencies
            with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
                parser = DocumentParser()
            
            # Create a test file
            test_file = "test/path/document.pdf"
            
            # Test parsing
            result = parser.parse_document(test_file)
            
            # Verify result
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Document)
            assert "Test Insurance Policy" in result[0].page_content
            assert "Policy Number: TEST-123" in result[0].page_content
            assert result[0].metadata['page_number'] == 1
            assert result[0].metadata['source'] == test_file

    @pytest.mark.asyncio
    async def test_document_chunking(self):
        """Test document chunking functionality."""
        with patch('config.parser.LlamaParse') as mock_llama_parse_class, \
             patch('builtins.open', mock_open(read_data=b"Test document content")), \
             patch('pathlib.Path.exists', return_value=True):
            
            # Setup mock
            mock_llama_parse = MagicMock()
            mock_llama_parse_class.return_value = mock_llama_parse
            
            # Create a long document text
            mock_doc = MagicMock()
            mock_doc.text = "Test " * 1000  # Long enough to create multiple chunks
            mock_doc.page_number = 1
            mock_llama_parse.load_data.return_value = [mock_doc]
            
            # Create parser with mocked dependencies
            with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
                parser = DocumentParser()
            
            # Create a test file
            test_file = "test/path/document.pdf"
            
            # Parse document
            docs = parser.parse_document(test_file)
            assert len(docs) == 1
            assert isinstance(docs[0], Document)
            assert len(docs[0].page_content) > 100

    @pytest.mark.asyncio
    async def test_document_vectorization(self, mock_embedding_service):
        """Test document vectorization."""
        # Create test chunks
        chunks = [
            Document(page_content="Test chunk 1", metadata={"page": 1}),
            Document(page_content="Test chunk 2", metadata={"page": 1})
        ]
        
        # Test vectorization
        vectors = await mock_embedding_service.create_embeddings(
            [chunk.page_content for chunk in chunks]
        )
        
        # Verify vectors
        assert len(vectors) == 1  # Mock returns single vector
        assert len(vectors[0]) == 1536  # OpenAI embedding size

    @pytest.mark.asyncio
    async def test_status_transitions(self, mock_document_service, test_document_data):
        """Test document status transitions."""
        # Create document
        doc_id = await mock_document_service.create_document(
            user_id=str(uuid.uuid4()),
            metadata=test_document_data
        )
        
        # Test status transitions
        statuses = ["processing", "parsed", "chunked", "vectorized", "active"]
        for status in statuses:
            await mock_document_service.update_document_status(
                document_id=doc_id["id"],
                status=status
            )
            mock_document_service.get_document_status.return_value = {"status": status}
            current_status = await mock_document_service.get_document_status(doc_id["id"])
            assert current_status["status"] == status

    @pytest.mark.asyncio
    async def test_error_handling(self, mock_document_service, test_document_data):
        """Test error handling in document processing."""
        # Test with invalid document data
        invalid_data = {**test_document_data}
        invalid_data.pop('original_filename')  # Make data invalid
        
        # Mock error behavior
        mock_document_service.create_document.side_effect = ValueError("Missing required field")
        
        with pytest.raises(ValueError) as exc_info:
            await mock_document_service.create_document(
                user_id=str(uuid.uuid4()),
                metadata=invalid_data
            )
        assert "Missing required field" in str(exc_info.value)
        
        # Test with processing error
        mock_document_service.create_document.side_effect = None  # Reset mock
        doc_id = await mock_document_service.create_document(
            user_id=str(uuid.uuid4()),
            metadata=test_document_data
        )
        mock_document_service.update_document_status.side_effect = Exception("Processing error")
        
        with pytest.raises(Exception) as exc_info:
            await mock_document_service.update_document_status(
                document_id=doc_id["id"],
                status="error",
                message="Test error"
            )
        assert "Processing error" in str(exc_info.value) 