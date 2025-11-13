# pytest configuration for concurrency validation tests
# Addresses: FM-043 - Test configuration for Phase 1 validation

import pytest
import asyncio
import sys
import os

# Add the project root to Python path for imports
project_root = os.path.join(os.path.dirname(__file__), '../../..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_global_state():
    """Reset global state between tests to avoid interference."""
    # Reset global pool manager
    from agents.tooling.rag import database_manager
    database_manager._pool_manager = None
    
    # Reset global monitor
    from agents.shared.monitoring import concurrency_monitor
    concurrency_monitor._monitor = None
    
    yield
    
    # Clean up after test
    database_manager._pool_manager = None
    concurrency_monitor._monitor = None


@pytest.fixture
def mock_env():
    """Provide mock environment variables for testing."""
    return {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/testdb',
        'SUPABASE_DB_HOST': 'localhost',
        'SUPABASE_DB_PORT': '5432',
        'SUPABASE_DB_USER': 'test',
        'SUPABASE_DB_PASSWORD': 'test',
        'SUPABASE_DB_NAME': 'testdb'
    }