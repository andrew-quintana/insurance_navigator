"""
Tests for the DocumentParser implementation.
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from langchain_core.documents import Document
from config.parser import DocumentParser

@pytest.fixture
def mock_llama_parse():
    """Mock LlamaParse instance."""
    with patch('config.parser.LlamaParse') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def document_parser(mock_llama_parse):
    """Create DocumentParser instance with mocked LlamaParse."""
    with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
        parser = DocumentParser()
        # Ensure we're using the mocked instance
        parser.parser = mock_llama_parse
        return parser

@pytest.fixture
def real_document_parser():
    """Create DocumentParser instance for real document testing."""
    with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
        return DocumentParser()

def test_init_missing_api_key():
    """Test initialization fails without API key."""
    with pytest.raises(ValueError, match="LLAMA_CLOUD_API_KEY environment variable not set"):
        with patch.dict('os.environ', {}, clear=True):
            DocumentParser()

def test_init_success(document_parser):
    """Test successful initialization."""
    assert document_parser.api_key == 'test_key'
    assert document_parser.parser is not None

@patch('pathlib.Path.exists')
def test_parse_document_success(mock_exists, document_parser, mock_llama_parse):
    """Test successful document parsing with mock."""
    # Mock file existence check
    mock_exists.return_value = True
    
    # Mock parsed document
    mock_doc = Mock()
    mock_doc.text = "Test content"
    mock_doc.page_number = 1
    mock_llama_parse.load_data.return_value = [mock_doc]
    
    # Test parsing
    result = document_parser.parse_document("tests/data/documents/sample_insurance.pdf")
    
    # Verify results
    assert len(result) == 1
    assert isinstance(result[0], Document)
    assert result[0].page_content == "Test content"
    assert result[0].metadata["page_number"] == 1
    assert result[0].metadata["source"] == "tests/data/documents/sample_insurance.pdf"
    
    # Verify LlamaParse was called correctly
    mock_llama_parse.load_data.assert_called_once()

@patch('pathlib.Path.exists')
def test_parse_document_error(mock_exists, document_parser, mock_llama_parse):
    """Test error handling in document parsing."""
    # Mock file existence check
    mock_exists.return_value = True
    
    # Mock error
    mock_llama_parse.load_data.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        document_parser.parse_document("tests/data/documents/sample_insurance.pdf")
    assert str(exc_info.value) == "Error parsing document: Test error"

@patch('pathlib.Path.exists')
def test_parse_documents_multiple(mock_exists, document_parser, mock_llama_parse):
    """Test parsing multiple documents."""
    # Mock file existence check
    mock_exists.return_value = True
    
    # Mock parsed documents
    mock_doc1 = Mock()
    mock_doc1.text = "Content 1"
    mock_doc1.page_number = 1
    
    mock_doc2 = Mock()
    mock_doc2.text = "Content 2"
    mock_doc2.page_number = 1
    
    mock_llama_parse.load_data.side_effect = [[mock_doc1], [mock_doc2]]
    
    # Test parsing multiple documents
    result = document_parser.parse_documents([
        "tests/data/documents/sample_insurance.pdf",
        "tests/data/documents/sample_insurance.docx"
    ])
    
    # Verify results
    assert len(result) == 2
    assert result[0].page_content == "Content 1"
    assert result[1].page_content == "Content 2"
    
    # Verify LlamaParse was called for each document
    assert mock_llama_parse.load_data.call_count == 2

@patch('pathlib.Path.exists')
def test_parse_document_file_not_found(mock_exists, document_parser):
    """Test error handling when file doesn't exist."""
    # Mock file existence check
    mock_exists.return_value = False
    
    with pytest.raises(Exception) as exc_info:
        document_parser.parse_document("nonexistent.pdf")
    assert "File not found: nonexistent.pdf" in str(exc_info.value)

@patch('pathlib.Path.exists')
def test_parse_empty_result(mock_exists, document_parser, mock_llama_parse):
    """Test handling of empty parsing results."""
    # Mock file existence check
    mock_exists.return_value = True
    
    # Mock empty result
    mock_llama_parse.load_data.return_value = []
    
    # Test parsing
    result = document_parser.parse_document("tests/data/documents/sample_insurance.pdf")
    
    # Verify results
    assert len(result) == 1
    assert isinstance(result[0], Document)
    assert result[0].page_content == ""
    assert result[0].metadata["error"] == "No content parsed"
    assert result[0].metadata["source"] == "tests/data/documents/sample_insurance.pdf"

@patch('config.parser.LlamaParse')
def test_parse_real_documents(mock_llama_parse_class):
    """Test parsing real PDF and DOCX documents."""
    # Mock LlamaParse instance
    mock_llama_parse = Mock()
    mock_llama_parse_class.return_value = mock_llama_parse
    
    # Create parser with mocked LlamaParse
    with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
        parser = DocumentParser()
    
    # Mock PDF parsing
    mock_pdf_doc = Mock()
    mock_pdf_doc.text = "Sample Insurance Policy\nPolicy Number: INS-12345"
    mock_pdf_doc.page_number = 1
    mock_llama_parse.load_data.return_value = [mock_pdf_doc]
    
    # Test PDF parsing
    pdf_path = "tests/data/documents/sample_insurance.pdf"
    with patch('pathlib.Path.exists', return_value=True):
        pdf_result = parser.parse_document(pdf_path)
    
    # Verify PDF results
    assert len(pdf_result) > 0
    assert isinstance(pdf_result[0], Document)
    assert "Sample Insurance Policy" in pdf_result[0].page_content
    assert "Policy Number: INS-12345" in pdf_result[0].page_content
    assert pdf_result[0].metadata["source"] == pdf_path
    
    # Mock DOCX parsing
    mock_docx_doc = Mock()
    mock_docx_doc.text = "Sample Insurance Policy\nPolicy Number: INS-12345"
    mock_docx_doc.page_number = 1
    mock_llama_parse.load_data.return_value = [mock_docx_doc]
    
    # Test DOCX parsing
    docx_path = "tests/data/documents/sample_insurance.docx"
    with patch('pathlib.Path.exists', return_value=True):
        docx_result = parser.parse_document(docx_path)
    
    # Verify DOCX results
    assert len(docx_result) > 0
    assert isinstance(docx_result[0], Document)
    assert "Sample Insurance Policy" in docx_result[0].page_content
    assert "Policy Number: INS-12345" in docx_result[0].page_content
    assert docx_result[0].metadata["source"] == docx_path

@patch('config.parser.LlamaParse')
def test_parse_real_multiple_documents(mock_llama_parse_class):
    """Test parsing multiple real documents."""
    # Mock LlamaParse instance
    mock_llama_parse = Mock()
    mock_llama_parse_class.return_value = mock_llama_parse
    
    # Create parser with mocked LlamaParse
    with patch.dict('os.environ', {'LLAMA_CLOUD_API_KEY': 'test_key'}):
        parser = DocumentParser()
    
    # Mock document parsing
    mock_doc = Mock()
    mock_doc.text = "Sample Insurance Policy\nPolicy Number: INS-12345"
    mock_doc.page_number = 1
    mock_llama_parse.load_data.return_value = [mock_doc]
    
    file_paths = [
        "tests/data/documents/sample_insurance.pdf",
        "tests/data/documents/sample_insurance.docx"
    ]
    
    with patch('pathlib.Path.exists', return_value=True):
        results = parser.parse_documents(file_paths)
    
    # Verify results
    assert len(results) > 0
    for doc in results:
        assert isinstance(doc, Document)
        assert "Sample Insurance Policy" in doc.page_content
        assert "Policy Number: INS-12345" in doc.page_content

@patch('pathlib.Path.exists')
def test_parse_documents_error_handling(mock_exists, document_parser, mock_llama_parse):
    """Test error handling when one document fails to parse in parse_documents."""
    # Mock file existence check
    mock_exists.return_value = True
    
    # Mock first document success
    mock_doc1 = Mock()
    mock_doc1.text = "Content 1"
    mock_doc1.page_number = 1
    
    # Mock second document failure
    mock_llama_parse.load_data.side_effect = [
        [mock_doc1],  # First call succeeds
        Exception("Test error")  # Second call fails
    ]
    
    # Test parsing multiple documents with one failure
    with pytest.raises(Exception) as exc_info:
        document_parser.parse_documents([
            "tests/data/documents/sample_insurance.pdf",
            "tests/data/documents/sample_insurance.docx"
        ])
    
    # Verify error message
    assert "Error parsing document: Test error" in str(exc_info.value)
    
    # Verify LlamaParse was called for each document
    assert mock_llama_parse.load_data.call_count == 2 