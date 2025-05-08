"""
Tests for the VectorStore implementation.
"""
import pytest
from unittest.mock import Mock, patch
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from config.vectorstore import VectorStore

class MockEmbeddings(Embeddings):
    """Mock embeddings for testing."""
    def embed_documents(self, texts):
        return [[0.1] * 1536] * len(texts)
    
    def embed_query(self, text):
        return [0.1] * 1536

@pytest.fixture
def mock_pgvector():
    """Mock PGVector instance."""
    with patch('langchain_community.vectorstores.PGVector', autospec=True) as mock:
        yield mock

@pytest.fixture
def vector_store(mock_pgvector):
    """Create VectorStore instance with mocked PGVector."""
    with patch.dict('os.environ', {'DATABASE_URL': 'postgresql://test:test@localhost/test'}):
        return VectorStore(MockEmbeddings())

def test_init_missing_db_url():
    """Test initialization fails without database URL."""
    with pytest.raises(ValueError, match="DATABASE_URL environment variable not set"):
        with patch.dict('os.environ', {}, clear=True):
            VectorStore(MockEmbeddings())

def test_init_success(vector_store):
    """Test successful initialization."""
    assert vector_store.connection_string == 'postgresql://test:test@localhost/test'
    assert vector_store.embeddings is not None
    assert vector_store.collection_name == "insurance_documents"

def test_init_store_success(vector_store, mock_pgvector):
    """Test successful store initialization."""
    store = vector_store.init_store()
    
    # Verify PGVector was initialized correctly
    mock_pgvector.assert_called_once_with(
        connection_string='postgresql://test:test@localhost/test',
        embedding_function=vector_store.embeddings,
        collection_name="insurance_documents"
    )
    assert store == mock_pgvector.return_value

def test_init_store_error(vector_store, mock_pgvector):
    """Test error handling in store initialization."""
    mock_pgvector.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        vector_store.init_store()
    assert str(exc_info.value) == "Error initializing vector store: Test error"

def test_add_documents_success(vector_store, mock_pgvector):
    """Test successful document addition."""
    docs = [
        Document(page_content="Test content 1"),
        Document(page_content="Test content 2")
    ]
    
    vector_store.add_documents(docs)
    
    # Verify documents were added
    mock_pgvector.return_value.add_documents.assert_called_once_with(docs)

def test_add_documents_error(vector_store, mock_pgvector):
    """Test error handling in document addition."""
    mock_pgvector.return_value.add_documents.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        vector_store.add_documents([Document(page_content="Test")])
    assert str(exc_info.value) == "Error adding documents to vector store: Test error"

def test_similarity_search_success(vector_store, mock_pgvector):
    """Test successful similarity search."""
    mock_docs = [Document(page_content="Test result")]
    mock_pgvector.return_value.similarity_search.return_value = mock_docs
    
    result = vector_store.similarity_search("test query", k=2)
    
    # Verify search was performed correctly
    assert result == mock_docs
    mock_pgvector.return_value.similarity_search.assert_called_once_with("test query", k=2)

def test_similarity_search_error(vector_store, mock_pgvector):
    """Test error handling in similarity search."""
    mock_pgvector.return_value.similarity_search.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        vector_store.similarity_search("test query")
    assert str(exc_info.value) == "Error performing similarity search: Test error"

def test_delete_collection_success(vector_store, mock_pgvector):
    """Test successful collection deletion."""
    vector_store.delete_collection()
    
    # Verify collection was deleted
    mock_pgvector.return_value.delete_collection.assert_called_once()

def test_delete_collection_error(vector_store, mock_pgvector):
    """Test error handling in collection deletion."""
    mock_pgvector.return_value.delete_collection.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        vector_store.delete_collection()
    assert str(exc_info.value) == "Error deleting collection: Test error" 