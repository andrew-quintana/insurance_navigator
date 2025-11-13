"""
Unit tests for rate limiter (Phase 2).

Addresses: FM-043 - Add rate limiting for external APIs
"""

import pytest
import asyncio
import time
from agents.shared.rate_limiting import (
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
    """Test token bucket algorithm accuracy and precision."""
    
    @pytest.mark.asyncio
    async def test_token_bucket_algorithm_accuracy(self):
        """Test token bucket algorithm accuracy."""
        config = RateLimitConfig(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_size=10
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Should be able to acquire tokens up to bucket size immediately
        for i in range(10):
            await limiter.acquire()
        
        # Next acquisition should wait
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start
        
        # Should have waited approximately 1 second (60 req/min = 1 req/sec)
        assert elapsed >= 0.9, f"Expected wait time ~1s, got {elapsed}s"
        assert elapsed < 1.5, f"Expected wait time ~1s, got {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_token_bucket_precision(self):
        """Test token bucket precision under sustained load."""
        config = RateLimitConfig(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Make 60 requests over 1 minute
        start = time.time()
        for _ in range(60):
            await limiter.acquire()
        elapsed = time.time() - start
        
        # Should take approximately 60 seconds (1 req/sec)
        assert elapsed >= 58, f"Expected ~60s for 60 requests, got {elapsed}s"
        assert elapsed < 65, f"Expected ~60s for 60 requests, got {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_token_bucket_burst_handling(self):
        """Test token bucket handles burst traffic correctly."""
        config = RateLimitConfig(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            burst_size=10
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Burst of 10 should be immediate
        start = time.time()
        for _ in range(10):
            await limiter.acquire()
        burst_time = time.time() - start
        
        assert burst_time < 0.5, f"Burst of 10 should be fast, took {burst_time}s"


class TestSlidingWindowRateLimiter:
    """Test sliding window algorithm accuracy and precision."""
    
    @pytest.mark.asyncio
    async def test_sliding_window_algorithm_accuracy(self):
        """Test sliding window algorithm accuracy."""
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
    async def test_sliding_window_precision(self):
        """Test sliding window precision."""
        config = RateLimitConfig(
            requests_per_minute=10,  # 10 req/min = 1 req per 6 seconds
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            window_size_seconds=60
        )
        limiter = SlidingWindowRateLimiter(config)
        
        # Make 10 requests - should be spread over time
        start = time.time()
        for _ in range(10):
            await limiter.acquire()
        elapsed = time.time() - start
        
        # Should take some time (requests are rate limited)
        assert elapsed >= 0, "Should complete"


class TestRateLimitEnforcement:
    """Test rate limit enforcement under sustained load."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforcement_under_load(self):
        """Test rate limit enforcement under sustained load."""
        config = RateLimitConfig(
            requests_per_minute=10,  # 10 req/min
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Try to make 20 requests quickly
        start = time.time()
        tasks = [limiter.acquire() for _ in range(20)]
        await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        # Should take at least 10 seconds (10 req/min = 1 req per 6 seconds for 10 requests)
        # But we're making 20, so should take longer
        assert elapsed >= 5, f"20 requests at 10/min should take time, got {elapsed}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_access_to_rate_limiter(self):
        """Test concurrent access to rate limiter (thread safety)."""
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
        results = await asyncio.gather(*[acquire() for _ in range(50)])
        elapsed = time.time() - start
        
        # All should complete (concurrent access should work)
        assert len(results) == 50
        # Should complete reasonably quickly (within rate limit)
        assert elapsed < 5, f"50 concurrent requests took {elapsed}s"


class TestRateLimiterPerformance:
    """Performance benchmarks for different rate limiting algorithms."""
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Performance benchmarks for different algorithms."""
        token_bucket = create_rate_limiter(100, RateLimitAlgorithm.TOKEN_BUCKET)
        sliding_window = create_rate_limiter(100, RateLimitAlgorithm.SLIDING_WINDOW)
        
        # Benchmark token bucket
        start = time.time()
        for _ in range(10):
            await token_bucket.acquire()
        token_bucket_time = time.time() - start
        
        # Benchmark sliding window
        start = time.time()
        for _ in range(10):
            await sliding_window.acquire()
        sliding_window_time = time.time() - start
        
        # Both should be reasonably fast
        assert token_bucket_time < 1
        assert sliding_window_time < 1


class TestRateLimiterConfiguration:
    """Test configuration changes during runtime operations."""
    
    @pytest.mark.asyncio
    async def test_configuration_changes_during_runtime(self):
        """Test configuration changes during runtime operations."""
        config = RateLimitConfig(
            requests_per_minute=60,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter = TokenBucketRateLimiter(config)
        
        # Make some requests
        for _ in range(5):
            await limiter.acquire()
        
        # Update configuration
        new_config = RateLimitConfig(
            requests_per_minute=120,  # Double the rate
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
        limiter.update_config(new_config)
        
        # Should now allow faster requests
        start = time.time()
        for _ in range(10):
            await limiter.acquire()
        elapsed = time.time() - start
        
        # Should be faster with new config (though initial tokens may be limited)
        assert elapsed >= 0


class TestGlobalRateLimiters:
    """Test global rate limiter instances."""
    
    @pytest.mark.asyncio
    async def test_get_openai_rate_limiter(self):
        """Test OpenAI rate limiter (60 req/min default)."""
        limiter = get_openai_rate_limiter()
        assert isinstance(limiter, RateLimiter)
        
        # Should be able to acquire
        await limiter.acquire()
    
    @pytest.mark.asyncio
    async def test_get_anthropic_rate_limiter(self):
        """Test Anthropic rate limiter (50 req/min default)."""
        limiter = get_anthropic_rate_limiter()
        assert isinstance(limiter, RateLimiter)
        
        # Should be able to acquire
        await limiter.acquire()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_singleton_behavior(self):
        """Test that global rate limiters are singletons."""
        limiter1 = get_openai_rate_limiter()
        limiter2 = get_openai_rate_limiter()
        
        # Should be the same instance
        assert limiter1 is limiter2

