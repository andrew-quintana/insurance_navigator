"""
Collocated unit tests for InformationRetrievalAgent async patterns.

Addresses: FM-043 - Phase 2 Pattern Modernization
Tests async HTTP client migration and rate limiting integration.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import os

from .agent import InformationRetrievalAgent


class TestAsyncHTTPClientMigration:
    """Test async HTTP client migration."""
    
    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        return InformationRetrievalAgent(use_mock=True)
    
    @pytest.mark.asyncio
    async def test_call_llm_async_with_httpx(self, agent):
        """Test _call_llm_async uses httpx.AsyncClient."""
        # Set up agent with API key
        agent._anthropic_api_key = "test-key"
        agent._anthropic_model = "claude-3-haiku-20240307"
        
        # Mock rate limiter
        mock_limiter = AsyncMock()
        mock_limiter.acquire = AsyncMock()
        agent._anthropic_rate_limiter = mock_limiter
        
        # Mock httpx.AsyncClient
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Test response"}]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            result = await agent._call_llm_async("test prompt")
            
            # Verify httpx.AsyncClient was used
            assert result == "Test response"
            mock_client.post.assert_called_once()
            mock_limiter.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_llm_async_rate_limiting(self, agent):
        """Test rate limiting is applied in async calls."""
        agent._anthropic_api_key = "test-key"
        agent._anthropic_model = "claude-3-haiku-20240307"
        
        mock_limiter = AsyncMock()
        agent._anthropic_rate_limiter = mock_limiter
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": [{"type": "text", "text": "Test"}]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            await agent._call_llm_async("test")
            
            # Verify rate limiter was called
            mock_limiter.acquire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_llm_async_timeout_handling(self, agent):
        """Test timeout handling in async calls."""
        agent._anthropic_api_key = "test-key"
        agent._anthropic_model = "claude-3-haiku-20240307"
        
        mock_limiter = AsyncMock()
        agent._anthropic_rate_limiter = mock_limiter
        
        # Mock timeout exception
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(httpx.TimeoutException):
                await agent._call_llm_async("test")
    
    @pytest.mark.asyncio
    async def test_call_llm_uses_async_client(self, agent):
        """Test _call_llm method uses async client when available."""
        agent._anthropic_api_key = "test-key"
        agent.mock = False  # Ensure not in mock mode
        agent.llm = lambda x: "sync response"  # Set a callable so it doesn't return early
        
        # Mock asyncio.timeout for Python 3.9 compatibility
        with patch('asyncio.timeout', create=True) as mock_timeout:
            mock_timeout.return_value.__aenter__ = AsyncMock(return_value=None)
            mock_timeout.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Mock the async call
            with patch.object(agent, '_call_llm_async', new_callable=AsyncMock) as mock_async:
                mock_async.return_value = "async response"
                
                result = await agent._call_llm("test prompt")
                
                # Should use async client when _anthropic_api_key is set
                assert result == "async response"
                mock_async.assert_called_once_with("test prompt")


class TestAsyncPatterns:
    """Test async patterns in InformationRetrievalAgent."""
    
    @pytest.mark.asyncio
    async def test_get_running_loop_usage(self):
        """Test that get_running_loop() is used instead of get_event_loop()."""
        import inspect
        from . import agent
        
        source = inspect.getsource(agent.InformationRetrievalAgent)
        
        # Should not contain deprecated get_event_loop() (except in comments)
        lines = source.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('#') or '"""' in line:
                continue
            if '.get_event_loop()' in line and 'get_running_loop()' not in line:
                if line.count('"') % 2 == 0 and line.count("'") % 2 == 0:
                    pytest.fail(
                        f"Deprecated get_event_loop() found at line {i}: {line.strip()}"
                    )

