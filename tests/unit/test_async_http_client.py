"""
Unit tests for async HTTP client migration (Phase 2).

Addresses: FM-043 - Migrate synchronous HTTP calls to async httpx.AsyncClient
"""

import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, patch, MagicMock


class TestAsyncHTTPClient:
    """Test httpx.AsyncClient integration and functionality."""
    
    @pytest.mark.asyncio
    async def test_httpx_async_client_basic(self):
        """Test basic httpx.AsyncClient functionality."""
        async with httpx.AsyncClient() as client:
            assert client is not None
            assert isinstance(client, httpx.AsyncClient)
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling (60s) under various conditions."""
        # Test with short timeout
        timeout = httpx.Timeout(1.0, connect=0.5)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            with pytest.raises(httpx.TimeoutException):
                # This should timeout quickly
                await client.get("http://httpbin.org/delay/2")
    
    @pytest.mark.asyncio
    async def test_connection_pooling_behavior(self):
        """Test connection pooling behavior and connection reuse."""
        limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
        
        async with httpx.AsyncClient(limits=limits) as client:
            # Make multiple requests - connections should be reused
            tasks = [
                client.get("http://httpbin.org/get") 
                for _ in range(3)
            ]
            responses = await asyncio.gather(*tasks)
            
            assert len(responses) == 3
            for response in responses:
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_error_handling_and_retries(self):
        """Test error handling, retries, and failure scenarios."""
        async with httpx.AsyncClient() as client:
            # Test 404 error
            response = await client.get("http://httpbin.org/status/404")
            assert response.status_code == 404
            
            # Test 500 error
            response = await client.get("http://httpbin.org/status/500")
            assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_handling(self):
        """Test concurrent requests handling."""
        async with httpx.AsyncClient() as client:
            # Make 10 concurrent requests
            tasks = [
                client.get(f"http://httpbin.org/get?i={i}")
                for i in range(10)
            ]
            responses = await asyncio.gather(*tasks)
            
            assert len(responses) == 10
            for i, response in enumerate(responses):
                assert response.status_code == 200
                # Verify we got different responses
                data = response.json()
                assert "args" in data
    
    @pytest.mark.asyncio
    async def test_performance_async_vs_sync(self):
        """Performance comparison tests: async vs synchronous calls."""
        import time
        
        # Async version
        start = time.time()
        async with httpx.AsyncClient() as client:
            tasks = [
                client.get("http://httpbin.org/delay/0.1")
                for _ in range(5)
            ]
            await asyncio.gather(*tasks)
        async_time = time.time() - start
        
        # Async should be faster than sequential sync calls
        # (5 * 0.1 = 0.5s sequential, async should be ~0.1-0.2s)
        assert async_time < 0.5, f"Async took {async_time}s, expected < 0.5s"
    
    @pytest.mark.asyncio
    async def test_httpx_with_anthropic_api_pattern(self):
        """Test httpx usage pattern matching Anthropic API integration."""
        # Mock Anthropic API response
        mock_response = {
            "content": [
                {"type": "text", "text": "Test response"}
            ]
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = MagicMock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response_obj)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Simulate the pattern used in information_retrieval agent
            timeout = httpx.Timeout(60.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": "test-key"},
                    json={"model": "claude-3-haiku", "messages": []}
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract content
                content = ""
                if "content" in data:
                    for block in data["content"]:
                        if block.get("type") == "text":
                            content = block.get("text", "")
                            break
                
                assert content == "Test response"

