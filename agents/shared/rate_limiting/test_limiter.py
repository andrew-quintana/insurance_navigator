"""
Collocated unit tests for rate limiter.

Addresses: FM-043 - Phase 2 Pattern Modernization
"""

import pytest
import asyncio
import time
import os
from .limiter import (
    RateLimiter,
    TokenBucketRateLimiter,
    SlidingWindowRateLimiter,
    RateLimitConfig,
    RateLimitAlgorithm,
    create_rate_limiter,
    get_openai_rate_limiter,
    get_anthropic_rate_limiter
)


class TestTokenBucketRateLimiter:
    """Test token bucket algorithm."""
    
    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality."""
        config = RateLimitConfig(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_size=10
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Should be able to acquire tokens up to bucket size
        for i in range(10):
            await limiter.acquire()
        
        # Next acquisition should wait
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start
        
        # Should have waited approximately 1 second
        assert elapsed >= 0.9, f"Expected wait time ~1s, got {elapsed}s"
        assert elapsed < 1.5, f"Expected wait time ~1s, got {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_get_available_requests(self):
        """Test getting available requests."""
        config = RateLimitConfig(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_size=10
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Initially should have bucket_size tokens
        available = limiter.get_available_requests()
        assert available == 10
        
        # After acquiring, should decrease
        await limiter.acquire()
        available = limiter.get_available_requests()
        assert available == 9


class TestSlidingWindowRateLimiter:
    """Test sliding window algorithm."""
    
    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality."""
        config = RateLimitConfig(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            window_size_seconds=60
        )
        limiter = SlidingWindowRateLimiter(config)
        
        # Should allow 60 requests in 60 second window
        start = time.time()
        for i in range(60):
            await limiter.acquire()
        elapsed = time.time() - start
        
        # Should complete quickly (all within window)
        assert elapsed < 2, f"60 requests should complete quickly, took {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_get_available_requests(self):
        """Test getting available requests."""
        config = RateLimitConfig(
            requests_per_minute=10,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            window_size_seconds=60
        )
        limiter = SlidingWindowRateLimiter(config)
        
        # Make some requests
        for _ in range(5):
            await limiter.acquire()
        
        # Should have 5 remaining (10 - 5 = 5)
        available = limiter.get_available_requests()
        assert available == 5


class TestRateLimiterFactory:
    """Test rate limiter factory functions."""
    
    @pytest.mark.asyncio
    async def test_create_token_bucket_limiter(self):
        """Test creating token bucket limiter."""
        limiter = create_rate_limiter(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        assert isinstance(limiter, TokenBucketRateLimiter)
        await limiter.acquire()  # Should work
    
    @pytest.mark.asyncio
    async def test_create_sliding_window_limiter(self):
        """Test creating sliding window limiter."""
        limiter = create_rate_limiter(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )
        assert isinstance(limiter, SlidingWindowRateLimiter)
        await limiter.acquire()  # Should work
    
    @pytest.mark.asyncio
    async def test_get_openai_rate_limiter(self):
        """Test OpenAI rate limiter singleton."""
        limiter1 = get_openai_rate_limiter()
        limiter2 = get_openai_rate_limiter()
        
        # Should be the same instance (singleton)
        assert limiter1 is limiter2
        assert isinstance(limiter1, RateLimiter)
    
    @pytest.mark.asyncio
    async def test_get_anthropic_rate_limiter(self):
        """Test Anthropic rate limiter singleton."""
        limiter1 = get_anthropic_rate_limiter()
        limiter2 = get_anthropic_rate_limiter()
        
        # Should be the same instance (singleton)
        assert limiter1 is limiter2
        assert isinstance(limiter1, RateLimiter)


class TestConcurrentRateLimiting:
    """Test concurrent access to rate limiters."""
    
    @pytest.mark.asyncio
    async def test_concurrent_acquire(self):
        """Test concurrent acquisitions."""
        config = RateLimitConfig(
            requests_per_minute=100,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Concurrent acquisitions
        async def acquire():
            await limiter.acquire()
            return time.time()
        
        start = time.time()
        results = await asyncio.gather(*[acquire() for _ in range(20)])
        elapsed = time.time() - start
        
        # All should complete
        assert len(results) == 20
        # Should complete reasonably quickly
        assert elapsed < 5, f"20 concurrent requests took {elapsed}s"

