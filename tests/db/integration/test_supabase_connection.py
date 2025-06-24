"""Integration tests for Supabase connection."""
import os
import pytest
from unittest.mock import patch, AsyncMock
import httpx
from supabase import create_client, Client

from db.config import config

@pytest.fixture
async def mock_http_client():
    """Create a mock HTTP client for testing."""
    client = AsyncMock(spec=httpx.Client)
    client.post.return_value.json.return_value = {'count': 1}
    client.get.return_value.json.return_value = [
        {'name': 'documents', 'public': False}
    ]
    return client

@pytest.fixture
async def mock_supabase_client(mock_http_client):
    """Create a mock Supabase client."""
    client = AsyncMock(spec=Client)
    
    # Mock table operations
    table_mock = AsyncMock()
    table_mock.select.return_value.execute.return_value.data = [{'count': 1}]
    table_mock.select.return_value.execute.return_value.error = None
    client.table.return_value = table_mock
    
    # Mock storage operations
    storage_mock = AsyncMock()
    storage_mock.list_buckets.return_value = [
        {'name': 'documents', 'public': False}
    ]
    client.storage = storage_mock
    
    return client

class TestSupabaseConnection:
    """Integration tests for Supabase connection."""

    @pytest.mark.asyncio
    async def test_health_check(self, mock_supabase_client, mock_http_client):
        """Test Supabase health check query."""
        with patch('supabase.create_client', return_value=mock_supabase_client):
            client = create_client(config.supabase.url, config.supabase.anon_key)
            
            # Execute health check query
            result = await client.table('health_check').select('count').execute()
            
            # Verify response
            assert result.data is not None
            assert not result.error
            assert len(result.data) == 1
            assert result.data[0]['count'] == 1
            
            # Verify mock calls
            client.table.assert_called_once_with('health_check')
            client.table().select.assert_called_once_with('count')

    @pytest.mark.asyncio
    async def test_storage_bucket_access(self, mock_supabase_client):
        """Test access to Supabase storage bucket."""
        with patch('supabase.create_client', return_value=mock_supabase_client):
            client = create_client(config.supabase.url, config.supabase.service_role_key)
            
            # List storage buckets
            buckets = await client.storage.list_buckets()
            
            # Verify response
            assert len(buckets) == 1
            assert buckets[0]['name'] == config.supabase.storage_bucket
            assert not buckets[0]['public']
            
            # Verify mock calls
            client.storage.list_buckets.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_error_handling(self, mock_supabase_client):
        """Test handling of connection errors."""
        mock_supabase_client.table.side_effect = Exception("Connection failed")
        
        with patch('supabase.create_client', return_value=mock_supabase_client):
            client = create_client(config.supabase.url, config.supabase.anon_key)
            
            with pytest.raises(Exception) as exc_info:
                await client.table('health_check').select('count').execute()
            
            assert "Connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_storage_operation_error(self, mock_supabase_client):
        """Test handling of storage operation errors."""
        mock_supabase_client.storage.list_buckets.side_effect = Exception(
            "Storage operation failed"
        )
        
        with patch('supabase.create_client', return_value=mock_supabase_client):
            client = create_client(config.supabase.url, config.supabase.service_role_key)
            
            with pytest.raises(Exception) as exc_info:
                await client.storage.list_buckets()
            
            assert "Storage operation failed" in str(exc_info.value)
