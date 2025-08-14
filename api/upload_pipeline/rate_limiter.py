"""
Rate limiting for the upload pipeline API.
"""

import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass

from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    max_requests: int
    window_seconds: int
    endpoint: str


class RateLimiter:
    """Rate limiter for API endpoints."""
    
    def __init__(self):
        self.config = get_config()
        self.rate_limits: Dict[str, RateLimitConfig] = {}
        self.user_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.endpoint_requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.initialized = False
    
    def initialize(self):
        """Initialize rate limit configurations."""
        # Upload rate limits per user
        self.rate_limits["/api/v2/upload"] = RateLimitConfig(
            max_requests=self.config.max_uploads_per_day_per_user,
            window_seconds=86400,  # 24 hours
            endpoint="upload"
        )
        
        # Job status polling rate limits per job
        self.rate_limits["/api/v2/jobs/{job_id}"] = RateLimitConfig(
            max_requests=self.config.max_polls_per_minute_per_job,
            window_seconds=60,  # 1 minute
            endpoint="job_status"
        )
        
        # General API rate limits
        self.rate_limits["/api/v2"] = RateLimitConfig(
            max_requests=1000,  # 1000 requests per hour
            window_seconds=3600,  # 1 hour
            endpoint="general"
        )
        
        self.initialized = True
        logger.info("Rate limiter initialized with configurations")
    
    def check_rate_limit(self, endpoint: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a request is within rate limits.
        
        Args:
            endpoint: API endpoint path
            user_id: Optional user ID for user-specific limits
            
        Returns:
            True if request is allowed, False if rate limited
        """
        if not self.initialized:
            logger.warning("Rate limiter not initialized, allowing request")
            return True
        
        current_time = time.time()
        
        # Clean up old requests
        self._cleanup_old_requests(current_time)
        
        # Check endpoint-specific rate limits
        endpoint_config = self._get_endpoint_config(endpoint)
        if endpoint_config:
            if not self._check_endpoint_limit(endpoint, endpoint_config, current_time):
                return False
        
        # Check user-specific rate limits
        if user_id and endpoint_config and endpoint_config.endpoint == "upload":
            if not self._check_user_limit(user_id, endpoint_config, current_time):
                return False
        
        return True
    
    def get_retry_after(self, endpoint: str, user_id: Optional[str] = None) -> int:
        """
        Get retry-after time in seconds for rate-limited requests.
        
        Args:
            endpoint: API endpoint path
            user_id: Optional user ID for user-specific limits
            
        Returns:
            Seconds to wait before retrying
        """
        current_time = time.time()
        
        # Check endpoint-specific limits
        endpoint_config = self._get_endpoint_config(endpoint)
        if endpoint_config:
            retry_after = self._get_endpoint_retry_after(endpoint, endpoint_config, current_time)
            if retry_after > 0:
                return retry_after
        
        # Check user-specific limits
        if user_id and endpoint_config and endpoint_config.endpoint == "upload":
            retry_after = self._get_user_retry_after(user_id, endpoint_config, current_time)
            if retry_after > 0:
                return retry_after
        
        return 0
    
    def _get_endpoint_config(self, endpoint: str) -> Optional[RateLimitConfig]:
        """Get rate limit configuration for an endpoint."""
        # Find matching endpoint configuration
        for path, config in self.rate_limits.items():
            if endpoint.startswith(path):
                return config
        
        return None
    
    def _check_endpoint_limit(self, endpoint: str, config: RateLimitConfig, current_time: float) -> bool:
        """Check if endpoint rate limit is exceeded."""
        requests = self.endpoint_requests[endpoint]
        
        # Remove old requests outside the window
        while requests and current_time - requests[0] > config.window_seconds:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= config.max_requests:
            logger.warning(
                "Endpoint rate limit exceeded",
                endpoint=endpoint,
                current_requests=len(requests),
                max_requests=config.max_requests
            )
            return False
        
        # Add current request
        requests.append(current_time)
        return True
    
    def _check_user_limit(self, user_id: str, config: RateLimitConfig, current_time: float) -> bool:
        """Check if user rate limit is exceeded."""
        requests = self.user_requests[user_id]
        
        # Remove old requests outside the window
        while requests and current_time - requests[0] > config.window_seconds:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= config.max_requests:
            logger.warning(
                "User rate limit exceeded",
                user_id=user_id,
                endpoint=config.endpoint,
                current_requests=len(requests),
                max_requests=config.max_requests
            )
            return False
        
        # Add current request
        requests.append(current_time)
        return True
    
    def _get_endpoint_retry_after(self, endpoint: str, config: RateLimitConfig, current_time: float) -> int:
        """Get retry-after time for endpoint rate limit."""
        requests = self.endpoint_requests[endpoint]
        
        if len(requests) >= config.max_requests:
            # Find when the oldest request will expire
            oldest_request = requests[0]
            return max(0, int(oldest_request + config.window_seconds - current_time))
        
        return 0
    
    def _get_user_retry_after(self, user_id: str, config: RateLimitConfig, current_time: float) -> int:
        """Get retry-after time for user rate limit."""
        requests = self.user_requests[user_id]
        
        if len(requests) >= config.max_requests:
            # Find when the oldest request will expire
            oldest_request = requests[0]
            return max(0, int(oldest_request + config.window_seconds - current_time))
        
        return 0
    
    def _cleanup_old_requests(self, current_time: float):
        """Clean up old requests to prevent memory leaks."""
        # Clean up endpoint requests
        for endpoint, requests in self.endpoint_requests.items():
            config = self._get_endpoint_config(endpoint)
            if config:
                while requests and current_time - requests[0] > config.window_seconds:
                    requests.popleft()
        
        # Clean up user requests
        for user_id, requests in self.user_requests.items():
            # Use upload rate limit config for user cleanup
            config = self.rate_limits.get("/api/v2/upload")
            if config:
                while requests and current_time - requests[0] > config.window_seconds:
                    requests.popleft()
        
        # Remove empty user entries
        empty_users = [user_id for user_id, requests in self.user_requests.items() if not requests]
        for user_id in empty_users:
            del self.user_requests[user_id]
        
        # Remove empty endpoint entries
        empty_endpoints = [endpoint for endpoint, requests in self.endpoint_requests.items() if not requests]
        for endpoint in empty_endpoints:
            del self.endpoint_requests[endpoint]
    
    def get_rate_limit_info(self, endpoint: str, user_id: Optional[str] = None) -> Dict[str, any]:
        """Get current rate limit information for debugging."""
        current_time = time.time()
        info = {
            "endpoint": endpoint,
            "user_id": user_id,
            "current_time": current_time
        }
        
        # Endpoint rate limit info
        endpoint_config = self._get_endpoint_config(endpoint)
        if endpoint_config:
            requests = self.endpoint_requests[endpoint]
            info["endpoint_limits"] = {
                "max_requests": endpoint_config.max_requests,
                "window_seconds": endpoint_config.window_seconds,
                "current_requests": len(requests),
                "remaining_requests": max(0, endpoint_config.max_requests - len(requests))
            }
        
        # User rate limit info
        if user_id and endpoint_config and endpoint_config.endpoint == "upload":
            requests = self.user_requests[user_id]
            info["user_limits"] = {
                "max_requests": endpoint_config.max_requests,
                "window_seconds": endpoint_config.window_seconds,
                "current_requests": len(requests),
                "remaining_requests": max(0, endpoint_config.max_requests - len(requests))
            }
        
        return info
