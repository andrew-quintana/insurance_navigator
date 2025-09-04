"""
Pytest configuration and common fixtures for BaseWorker tests
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from backend.workers.base_worker import BaseWorker
from backend.shared.config import WorkerConfig
from backend.shared.db.connection import DatabaseManager

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_config():
    """Create test configuration"""
    return WorkerConfig(
        database_url="postgresql://test:test@localhost:5432/test",
        supabase_url="http://localhost:5000",
        supabase_anon_key="test_anon_key",
        supabase_service_role_key="test_service_key",
        llamaparse_api_url="http://localhost:8001",
        llamaparse_api_key="test_llamaparse_key",
        openai_api_url="http://localhost:8002",
        openai_api_key="test_openai_key",
        openai_model="text-embedding-3-small",
        poll_interval=0.1,
        max_retries=3,
        retry_base_delay=0.1
    )

@pytest.fixture
def mock_components():
    """Create mock components for testing"""
    db = AsyncMock()
    storage = AsyncMock()
    llamaparse = AsyncMock()
    openai = AsyncMock()
    
    return db, storage, llamaparse, openai

@pytest.fixture
def base_worker(test_config, mock_components):
    """Create BaseWorker instance with mock components"""
    db, storage, llamaparse, openai = mock_components
    
    worker = BaseWorker(test_config)
    worker.db = db
    worker.storage = storage
    worker.llamaparse = llamaparse
    worker.openai = openai
    
    return worker

@pytest.fixture
def sample_job():
    """Create a sample job for testing"""
    return {
        "job_id": str(uuid.uuid4()),
        "document_id": str(uuid.uuid4()),
        "status": "parsed",
        "parsed_path": "storage://parsed/test/test.md",
        "chunks_version": "markdown-simple@1",
        "embed_model": "text-embedding-3-small",
        "embed_version": "1",
        "retry_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing"""
    return [
        {
            "ord": 0,
            "text": "# Test Document\n\nThis is the first paragraph.",
            "chunker_name": "markdown-simple",
            "chunker_version": "1",
            "meta": {"section": "header"}
        },
        {
            "ord": 1,
            "text": "## Section 1\n\nContent for section 1.",
            "chunker_name": "markdown-simple",
            "chunker_version": "1",
            "meta": {"section": "content"}
        },
        {
            "ord": 2,
            "text": "## Section 2\n\nContent for section 2.",
            "chunker_name": "markdown-simple",
            "chunker_version": "1",
            "meta": {"section": "content"}
        }
    ]

@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing"""
    return [
        [0.1] * 1536,  # 1536-dimensional vector
        [0.2] * 1536,
        [0.3] * 1536
    ]

@pytest.fixture
def mock_database_connection():
    """Create a mock database connection"""
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.execute = AsyncMock(return_value="INSERT 0 1")
    
    return mock_conn

@pytest.fixture
def mock_storage_responses():
    """Create mock storage responses"""
    return {
        "parsed": "# Test Document\n\nContent here.\n\n## Section 1\nMore content.",
        "empty": "",
        "large": "# Large Document\n\n" + "Content paragraph. " * 1000
    }

@pytest.fixture
def correlation_id():
    """Create a correlation ID for testing"""
    return f"test-{uuid.uuid4()}"

# Test markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location"""
    for item in items:
        # Mark tests based on file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # Mark slow tests based on test name
        if "performance" in item.name or "load" in item.name:
            item.add_marker(pytest.mark.slow)

@pytest.fixture(autouse=True)
def patch_db_initialize(monkeypatch):
    """Auto-patch DatabaseManager.initialize to prevent real DB connections"""
    monkeypatch.setattr(DatabaseManager, "initialize", AsyncMock())
