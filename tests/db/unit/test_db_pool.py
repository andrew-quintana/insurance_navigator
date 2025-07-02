"""Unit tests for database pool functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os
from supabase import Client

from db.services.db_pool import (
    get_db_pool,
    close_db_pool,
    get_connection_status,
    _should_retry,
    _create_client
)

@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    client = MagicMock(spec=Client)
    client.auth = MagicMock()
    client.auth.get_session = MagicMock()
    return client

@pytest.fixture
def mock_env_vars():
    """Set up mock environment variables."""
    with patch.dict('os.environ', {
        'SUPABASE_DB_URL': 'https://test.supabase.co',
        'SUPABASE_SERVICE_ROLE_KEY': 'test_service_key',
        'SUPABASE_ANON_KEY': 'test_anon_key'
    }):
        yield

class TestDatabasePool:
    """Test cases for the database pool."""

    def test_should_retry(self):
        """Test retry decision logic."""
        # Test retryable errors
        retryable_errors = [
            Exception("connection refused"),
            Exception("timeout occurred"),
            Exception("network unreachable"),
            Exception("connection reset"),
            Exception("too many connections")
        ]
        for error in retryable_errors:
            assert _should_retry(error) is True

        # Test non-retryable errors
        non_retryable_errors = [
            Exception("invalid credentials"),
            Exception("permission denied"),
            Exception("table not found")
        ]
        for error in non_retryable_errors:
            assert _should_retry(error) is False

    @patch('db.services.db_pool.create_client')
    def test_create_client_success(self, mock_create_client, mock_env_vars, mock_supabase_client):
        """Test successful client creation."""
        mock_create_client.return_value = mock_supabase_client

        client = _create_client()
        assert client is not None
        assert client == mock_supabase_client
        mock_create_client.assert_called_once_with(
            'https://test.supabase.co',
            'test_service_key'
        )

    @patch('db.services.db_pool.create_client')
    def test_create_client_missing_config(self, mock_create_client):
        """Test client creation with missing configuration."""
        with patch.dict('os.environ', {}, clear=True):
            client = _create_client()
            assert client is None
            mock_create_client.assert_not_called()

    @patch('db.services.db_pool.create_client')
    def test_create_client_retry(self, mock_create_client, mock_env_vars):
        """Test client creation with retries."""
        # Make the first two attempts fail, third succeeds
        mock_create_client.side_effect = [
            Exception("connection refused"),
            Exception("timeout"),
            mock_supabase_client
        ]

        client = _create_client()
        assert client == mock_supabase_client
        assert mock_create_client.call_count == 3

    @patch('db.services.db_pool._create_client')
    def test_get_db_pool(self, mock_create_client, mock_supabase_client):
        """Test getting database pool."""
        mock_create_client.return_value = mock_supabase_client

        # First call should create new client
        client1 = get_db_pool()
        assert client1 == mock_supabase_client
        mock_create_client.assert_called_once()

        # Second call should return existing client
        client2 = get_db_pool()
        assert client2 == mock_supabase_client
        assert mock_create_client.call_count == 1

        # Test error handling
        mock_create_client.side_effect = Exception("Failed to create client")
        client3 = get_db_pool()
        assert client3 is None

    def test_close_db_pool(self, mock_supabase_client):
        """Test closing database pool."""
        # Set up initial state
        with patch('db.services.db_pool._client', mock_supabase_client):
            close_db_pool()
            status = get_connection_status()
            assert status['is_connected'] is False
            assert status['last_error'] is None
            assert status['retry_count'] == 0

    def test_get_connection_status(self, mock_supabase_client):
        """Test getting connection status."""
        # Test initial status
        status = get_connection_status()
        assert 'is_connected' in status
        assert 'last_error' in status
        assert 'retry_count' in status
        assert 'max_retries' in status

        # Test status after successful connection
        with patch('db.services.db_pool._client', mock_supabase_client):
            with patch('db.services.db_pool._connection_status', {
                'is_connected': True,
                'last_error': None,
                'retry_count': 0,
                'max_retries': 3
            }):
                status = get_connection_status()
                assert status['is_connected'] is True
                assert status['last_error'] is None
                assert status['retry_count'] == 0
                assert status['max_retries'] == 3

        # Test status after failed connection
        with patch('db.services.db_pool._connection_status', {
            'is_connected': False,
            'last_error': 'Connection failed',
            'retry_count': 2,
            'max_retries': 3
        }):
            status = get_connection_status()
            assert status['is_connected'] is False
            assert status['last_error'] == 'Connection failed'
            assert status['retry_count'] == 2
            assert status['max_retries'] == 3 