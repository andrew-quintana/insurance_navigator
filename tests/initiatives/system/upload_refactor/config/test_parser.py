"""
Tests for the DocumentParser implementation.
"""
import os
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import List, Dict, Any

from config.parser import DocumentParser, Document
from config.storage import StorageService

@pytest.fixture
def mock_storage_service():
    """Mock storage service for testing."""
    return Mock(spec=StorageService)

@pytest.fixture
def mock_llama_parse():
    """Mock LlamaParse instance for testing."""
    mock = Mock()
    mock_doc = Mock()
    mock_doc.text = "Sample Insurance Policy\nPolicy Number: INS-12345"
    mock_doc.page_number = 1
    mock.load_data.return_value = [mock_doc]
    return mock

@pytest.fixture
def test_document_data():
    """Test document data for unified schema."""
    return {
        'original_filename': 'sample_insurance.pdf',
        'storage_path': 'test/path/sample_insurance.pdf',
        'document_type': 'user_uploaded',
        'jurisdiction': 'United States',
        'program': ['Healthcare', 'General'],
        'source_url': None,
        'source_last_checked': datetime.now().isoformat(),
        'priority_score': 1.0,
        'metadata': {
            'processing_timestamp': datetime.now().isoformat(),
            'source_method': 'test',
            'content_length': 100,
            'extraction_method': 'test'
        },
        'tags': ['test'],
        'status': 'pending'
    }

@patch('config.parser.LlamaParse')
def test_parse_single_document(mock_llama_parse_class, mock_storage_service, test_document_data):
    """Test parsing a single document."""
    # Mock LlamaParse instance
    mock_llama_parse = Mock()
    mock_llama_parse_class.return_value = mock_llama_parse
    
    # Create parser with mocked dependencies
    with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
        parser = DocumentParser(storage_service=mock_storage_service)
    
    # Mock document parsing
    mock_doc = Mock()
    mock_doc.text = "Sample Insurance Policy\nPolicy Number: INS-12345"
    mock_doc.page_number = 1
    mock_llama_parse.load_data.return_value = [mock_doc]
    
    # Test parsing
    result = parser.parse_document(
        file_path="tests/data/documents/sample_insurance.pdf",
        document_data=test_document_data
    )
    
    # Verify result
    assert isinstance(result, Document)
    assert "Sample Insurance Policy" in result.page_content
    assert "Policy Number: INS-12345" in result.page_content
    assert result.metadata['document_type'] == 'user_uploaded'
    assert result.metadata['jurisdiction'] == 'United States'
    assert result.metadata['program'] == ['Healthcare', 'General']

@patch('config.parser.LlamaParse')
def test_parse_real_multiple_documents(mock_llama_parse_class, mock_storage_service, test_document_data):
    """Test parsing multiple real documents."""
    # Mock LlamaParse instance
    mock_llama_parse = Mock()
    mock_llama_parse_class.return_value = mock_llama_parse
    
    # Create parser with mocked dependencies
    with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
        parser = DocumentParser(storage_service=mock_storage_service)
    
    # Mock document parsing
    mock_doc = Mock()
    mock_doc.text = "Sample Insurance Policy\nPolicy Number: INS-12345"
    mock_doc.page_number = 1
    mock_llama_parse.load_data.return_value = [mock_doc]
    
    file_paths = [
        "tests/data/documents/sample_insurance.pdf",
        "tests/data/documents/sample_insurance.docx"
    ]
    
    # Test parsing multiple documents
    with patch('pathlib.Path.exists', return_value=True):
        results = parser.parse_documents(
            file_paths=file_paths,
            document_data=[test_document_data, test_document_data]
        )
    
    # Verify results
    assert len(results) > 0
    for doc in results:
        assert isinstance(doc, Document)
        assert "Sample Insurance Policy" in doc.page_content
        assert "Policy Number: INS-12345" in doc.page_content
        assert doc.metadata['document_type'] == 'user_uploaded'
        assert doc.metadata['jurisdiction'] == 'United States'
        assert doc.metadata['program'] == ['Healthcare', 'General']

@patch('config.parser.LlamaParse')
def test_error_handling(mock_llama_parse_class, mock_storage_service, test_document_data):
    """Test error handling during parsing."""
    # Mock LlamaParse instance to raise an exception
    mock_llama_parse = Mock()
    mock_llama_parse.load_data.side_effect = Exception("Test error")
    mock_llama_parse_class.return_value = mock_llama_parse
    
    # Create parser with mocked dependencies
    with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
        parser = DocumentParser(storage_service=mock_storage_service)
    
    # Test error handling
    with pytest.raises(Exception) as exc_info:
        parser.parse_document(
            file_path="tests/data/documents/sample_insurance.pdf",
            document_data=test_document_data
        )
    
    assert "Test error" in str(exc_info.value)

@patch('config.parser.LlamaParse')
def test_metadata_handling(mock_llama_parse_class, mock_storage_service, test_document_data):
    """Test handling of document metadata."""
    # Mock LlamaParse instance
    mock_llama_parse = Mock()
    mock_llama_parse_class.return_value = mock_llama_parse
    
    # Create parser with mocked dependencies
    with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
        parser = DocumentParser(storage_service=mock_storage_service)
    
    # Mock document parsing with metadata
    mock_doc = Mock()
    mock_doc.text = "Sample Insurance Policy\nPolicy Number: INS-12345"
    mock_doc.page_number = 1
    mock_doc.metadata = {
        'title': 'Sample Insurance',
        'author': 'Test Author',
        'creation_date': '2024-01-01'
    }
    mock_llama_parse.load_data.return_value = [mock_doc]
    
    # Test parsing with metadata
    result = parser.parse_document(
        file_path="tests/data/documents/sample_insurance.pdf",
        document_data=test_document_data
    )
    
    # Verify metadata handling
    assert isinstance(result, Document)
    assert result.metadata['document_type'] == 'user_uploaded'
    assert result.metadata['jurisdiction'] == 'United States'
    assert result.metadata['program'] == ['Healthcare', 'General']
    assert result.metadata['title'] == 'Sample Insurance'
    assert result.metadata['author'] == 'Test Author'
    assert result.metadata['creation_date'] == '2024-01-01'