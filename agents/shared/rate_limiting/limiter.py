"""
Rate limiting implementation for external API calls.

Addresses: FM-043 - Phase 2 Pattern Modernization
Implements configurable rate limiting for OpenAI and Anthropic APIs.
"""

import asyncio
import os
import time
import logging
from typing import Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithm types."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    burst_size: Optional[int] = None  # For token bucket
    window_size_seconds: int = 60  # For sliding window


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""
    
    @abstractmethod
    async def acquire(self) -> None:
        """Acquire permission to make a request. Blocks until available."""
        pass
    
    @abstractmethod
    def get_available_requests(self) -> int:
        """Get number of available requests in current window."""
        pass


class TokenBucketRateLimiter(RateLimiter):
    """
    Token bucket rate limiter implementation.
    
    Allows burst traffic up to bucket size while maintaining average rate.
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize token bucket rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.requests_per_minute = config.requests_per_minute
        self.bucket_size = config.burst_size or config.requests_per_minute
        self.tokens = float(self.bucket_size)
        self.last_refill = time.time()
        self.refill_rate = self.requests_per_minute / 60.0  # tokens per second
        self._lock = asyncio.Lock()
        
        logger.info(
            f"TokenBucketRateLimiter initialized: "
            f"{self.requests_per_minute} req/min, "
            f"bucket_size={self.bucket_size}, "
            f"refill_rate={self.refill_rate:.2f} tokens/sec"
        )
    
    async def acquire(self) -> None:
        """Acquire a token from the bucket. Blocks until token available."""
        async with self._lock:
            await self._refill_tokens()
            
            # Wait until we have at least one token
            while self.tokens < 1.0:
                # Calculate wait time for next token
                tokens_needed = 1.0 - self.tokens
                wait_time = tokens_needed / self.refill_rate
                
                # Release lock and wait
                await asyncio.sleep(wait_time)
                
                # Refill again after wait
                await self._refill_tokens()
            
            # Consume one token
            self.tokens -= 1.0
            logger.debug(f"Token acquired. Remaining tokens: {self.tokens:.2f}")
    
    async def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed > 0:
            # Add tokens based on refill rate
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
            self.last_refill = now
    
    def get_available_requests(self) -> int:
        """Get number of available requests (tokens)."""
        return int(self.tokens)
    
    def update_config(self, config: RateLimitConfig) -> None:
        """Update rate limit configuration at runtime."""
        async def _update():
            async with self._lock:
                self.config = config
                self.requests_per_minute = config.requests_per_minute
                self.bucket_size = config.burst_size or config.requests_per_minute
                self.refill_rate = self.requests_per_minute / 60.0
                # Don't exceed bucket size when updating
                self.tokens = min(self.bucket_size, self.tokens)
                logger.info(f"Rate limiter config updated: {self.requests_per_minute} req/min")
        
        # Schedule update (in real async context, this would be awaited)
        asyncio.create_task(_update())


class SlidingWindowRateLimiter(RateLimiter):
    """
    Sliding window rate limiter implementation.
    
    Tracks requests in a time window and enforces strict rate limits.
    """
    
    def __init__(self, config: RateLimitConfig):
        """
        Initialize sliding window rate limiter.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.requests_per_minute = config.requests_per_minute
        self.window_size_seconds = config.window_size_seconds
        self.request_times: list[float] = []
        self._lock = asyncio.Lock()
        
        logger.info(
            f"SlidingWindowRateLimiter initialized: "
            f"{self.requests_per_minute} req/min, "
            f"window_size={self.window_size_seconds}s"
        )
    
    async def acquire(self) -> None:
        """Acquire permission to make a request. Blocks until available."""
        async with self._lock:
            now = time.time()
            
            # Remove requests outside the window
            cutoff_time = now - self.window_size_seconds
            self.request_times = [t for t in self.request_times if t > cutoff_time]
            
            # Calculate max requests allowed in window
            max_requests = (self.requests_per_minute * self.window_size_seconds) / 60.0
            
            # Wait if we're at the limit
            while len(self.request_times) >= max_requests:
                # Calculate wait time until oldest request expires
                if self.request_times:
                    oldest_time = min(self.request_times)
                    wait_time = (oldest_time + self.window_size_seconds) - now + 0.01
                    wait_time = max(0, wait_time)
                else:
                    wait_time = self.window_size_seconds / max_requests
                
                # Release lock and wait
                await asyncio.sleep(wait_time)
                
                # Update window after wait
                now = time.time()
                cutoff_time = now - self.window_size_seconds
                self.request_times = [t for t in self.request_times if t > cutoff_time]
            
            # Record this request
            self.request_times.append(now)
            logger.debug(f"Request acquired. Requests in window: {len(self.request_times)}")
    
    def get_available_requests(self) -> int:
        """Get number of available requests in current window."""
        now = time.time()
        cutoff_time = now - self.window_size_seconds
        current_requests = len([t for t in self.request_times if t > cutoff_time])
        max_requests = int((self.requests_per_minute * self.window_size_seconds) / 60.0)
        return max(0, max_requests - current_requests)
    
    def update_config(self, config: RateLimitConfig) -> None:
        """Update rate limit configuration at runtime."""
        async def _update():
            async with self._lock:
                self.config = config
                self.requests_per_minute = config.requests_per_minute
                self.window_size_seconds = config.window_size_seconds
                logger.info(f"Rate limiter config updated: {self.requests_per_minute} req/min")
        
        # Schedule update
        asyncio.create_task(_update())


def create_rate_limiter(
    requests_per_minute: int,
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET,
    **kwargs
) -> RateLimiter:
    """
    Factory function to create rate limiters.
    
    Args:
        requests_per_minute: Maximum requests per minute
        algorithm: Rate limiting algorithm to use
        **kwargs: Additional algorithm-specific parameters
        
    Returns:
        RateLimiter instance
    """
    config = RateLimitConfig(
        requests_per_minute=requests_per_minute,
        algorithm=algorithm,
        burst_size=kwargs.get("burst_size"),
        window_size_seconds=kwargs.get("window_size_seconds", 60)
    )
    
    if algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
        return TokenBucketRateLimiter(config)
    elif algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
        return SlidingWindowRateLimiter(config)
    else:
        raise ValueError(f"Unknown rate limit algorithm: {algorithm}")


# Global rate limiters for common APIs
_openai_limiter: Optional[RateLimiter] = None
_anthropic_limiter: Optional[RateLimiter] = None


def get_openai_rate_limiter() -> RateLimiter:
    """Get or create OpenAI rate limiter (60 req/min)."""
    global _openai_limiter
    if _openai_limiter is None:
        requests_per_min = int(os.getenv("OPENAI_RATE_LIMIT", "60"))
        _openai_limiter = create_rate_limiter(
            requests_per_minute=requests_per_min,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
    return _openai_limiter


def get_anthropic_rate_limiter() -> RateLimiter:
    """Get or create Anthropic rate limiter (50 req/min)."""
    global _anthropic_limiter
    if _anthropic_limiter is None:
        requests_per_min = int(os.getenv("ANTHROPIC_RATE_LIMIT", "50"))
        _anthropic_limiter = create_rate_limiter(
            requests_per_minute=requests_per_min,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET
        )
    return _anthropic_limiter

