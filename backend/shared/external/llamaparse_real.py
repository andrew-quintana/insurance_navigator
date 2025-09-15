"""
Real LlamaParse API client implementation.

This module provides a real LlamaParse API client with authentication,
rate limiting, cost tracking, and comprehensive error handling.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

from .service_router import ServiceInterface, ServiceHealth, ServiceUnavailableError, ServiceExecutionError
from ..exceptions import UserFacingError

logger = logging.getLogger(__name__)


class LlamaParseParseRequest(BaseModel):
    """LlamaParse parse request model."""
    file_path: str = Field(..., description="Path to the file to parse")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for callback")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    parse_options: Optional[Dict[str, Any]] = Field(None, description="Additional parse options")


class LlamaParseParseResponse(BaseModel):
    """LlamaParse parse response model."""
    parse_job_id: str = Field(..., description="Unique parse job ID")
    status: str = Field(..., description="Parse job status")
    message: Optional[str] = Field(None, description="Additional message")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class LlamaParseWebhookPayload(BaseModel):
    """LlamaParse webhook payload model."""
    parse_job_id: str = Field(..., description="Parse job ID")
    status: str = Field(..., description="Parse job status")
    artifacts: List[Dict[str, Any]] = Field(..., description="Parse artifacts")
    meta: Dict[str, Any] = Field(..., description="Metadata")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class RealLlamaParseService(ServiceInterface):
    """Real LlamaParse API service implementation."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.cloud.llamaindex.ai",
        webhook_secret: Optional[str] = None,
        rate_limit_per_minute: int = 60,
        timeout_seconds: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.webhook_secret = webhook_secret
        self.rate_limit_per_minute = rate_limit_per_minute
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        
        # Rate limiting state
        self.request_times: List[datetime] = []
        self.last_health_check = None
        self.health_status = ServiceHealth(
            is_healthy=True,
            last_check=datetime.utcnow(),
            response_time_ms=None,
            error_count=0,
            last_error=None
        )
        
        # HTTP client
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Set up HTTP client with proper headers and configuration."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Accessa-Insurance-Navigator/1.0"
        }
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(self.timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def is_available(self) -> bool:
        """Check if the LlamaParse service is available."""
        try:
            health = await self.get_health()
            return health.is_healthy
        except Exception as e:
            logger.warning(f"LlamaParse availability check failed: {e}")
            return False
    
    async def get_health(self) -> ServiceHealth:
        """Get current service health status."""
        now = datetime.utcnow()
        
        # Cache health check for 30 seconds
        if (self.last_health_check and 
            (now - self.last_health_check).total_seconds() < 30):
            return self.health_status
        
        try:
            start_time = datetime.utcnow()
            
            # Test API connectivity with a simple request
            # LlamaParse doesn't have a simple health endpoint, so we'll test with parsing upload
            response = await self.client.post(f"{self.base_url}/parsing/upload", json={})
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update health status
            # 400 means API is working but needs proper parameters, 401/403 means auth issues but API is up
            self.health_status = ServiceHealth(
                is_healthy=response.status_code in [200, 400, 401, 403],  # 400/401/403 means API is up
                last_check=now,
                response_time_ms=response_time,
                error_count=0 if response.status_code in [200, 400, 401, 403] else 1,
                last_error=None if response.status_code in [200, 400, 401, 403] else f"HTTP {response.status_code}"
            )
            
            self.last_health_check = now
            
        except Exception as e:
            error_msg = str(e)
            self.health_status = ServiceHealth(
                is_healthy=False,
                last_check=now,
                response_time_ms=None,
                error_count=self.health_status.error_count + 1,
                last_error=error_msg
            )
            self.last_health_check = now
            
            logger.error(f"LlamaParse health check failed: {error_msg}")
        
        return self.health_status
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        now = datetime.utcnow()
        
        # Remove requests older than 1 minute
        cutoff = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff]
        
        if len(self.request_times) >= self.rate_limit_per_minute:
            wait_time = 60 - (now - self.request_times[0]).total_seconds()
            if wait_time > 0:
                logger.warning(f"Rate limit exceeded, waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        self.request_times.append(now)
    
    async def parse_document(
        self, 
        file_path: str, 
        webhook_url: Optional[str] = None,
        correlation_id: Optional[str] = None,
        parse_options: Optional[Dict[str, Any]] = None
    ) -> LlamaParseParseResponse:
        """
        Submit a document for parsing via LlamaParse API.
        
        Args:
            file_path: Path to the file to parse
            webhook_url: Optional webhook URL for callback
            correlation_id: Optional correlation ID for tracking
            parse_options: Optional additional parse options
            
        Returns:
            LlamaParseParseResponse with parse job details
            
        Raises:
            ServiceExecutionError: If parsing fails
            ServiceUnavailableError: If service is unavailable
        """
        # Note: We don't check availability here to allow the actual API call
        # to determine the specific error type (auth, rate limit, etc.)
        
        await self._check_rate_limit()
        
        try:
            # Prepare request payload
            payload = {
                "file_path": file_path,
                "parse_options": parse_options or {}
            }
            
            if webhook_url:
                payload["webhook_url"] = webhook_url
            
            if correlation_id:
                payload["correlation_id"] = correlation_id
            
            # Add correlation ID to headers for tracking
            headers = {}
            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id
            
            logger.info(
                f"Submitting document for parsing",
                extra={
                    "file_path": file_path,
                    "correlation_id": correlation_id,
                    "webhook_url": webhook_url
                }
            )
            
            # Submit parse request
            response = await self.client.post(
                f"{self.base_url}/v1/parse",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                logger.info(
                    f"Document parse request submitted successfully",
                    extra={
                        "parse_job_id": data.get("parse_job_id"),
                        "correlation_id": correlation_id,
                        "status": data.get("status")
                    }
                )
                
                return LlamaParseParseResponse(
                    parse_job_id=data.get("parse_job_id", ""),
                    status=data.get("status", "queued"),
                    message=data.get("message"),
                    correlation_id=correlation_id
                )
            
            elif response.status_code == 401:
                raise UserFacingError(
                    "Document processing service authentication failed. Please contact support.",
                    error_code="LLAMAPARSE_AUTH_ERROR",
                    context={
                        "status_code": response.status_code,
                        "service": "llamaparse",
                        "operation": "parse_document"
                    }
                )
            elif response.status_code == 403:
                raise UserFacingError(
                    "Document processing service access denied. Please contact support.",
                    error_code="LLAMAPARSE_PERMISSION_ERROR",
                    context={
                        "status_code": response.status_code,
                        "service": "llamaparse",
                        "operation": "parse_document"
                    }
                )
            elif response.status_code == 429:
                raise UserFacingError(
                    "Document processing service is currently busy. Please try again in a few minutes.",
                    error_code="LLAMAPARSE_RATE_LIMIT_ERROR",
                    context={
                        "status_code": response.status_code,
                        "service": "llamaparse",
                        "operation": "parse_document"
                    }
                )
            elif response.status_code >= 500:
                raise UserFacingError(
                    "Document processing service is temporarily unavailable. Please try again later.",
                    error_code="LLAMAPARSE_SERVER_ERROR",
                    context={
                        "status_code": response.status_code,
                        "service": "llamaparse",
                        "operation": "parse_document"
                    }
                )
            else:
                error_detail = response.text or f"HTTP {response.status_code}"
                raise UserFacingError(
                    "Document processing failed due to an unexpected error. Please try again later.",
                    error_code="LLAMAPARSE_UNKNOWN_ERROR",
                    context={
                        "status_code": response.status_code,
                        "error_detail": error_detail,
                        "service": "llamaparse",
                        "operation": "parse_document"
                    }
                )
                
        except httpx.TimeoutException:
            raise UserFacingError(
                "Document processing request timed out. Please try again later.",
                error_code="LLAMAPARSE_TIMEOUT_ERROR",
                context={
                    "service": "llamaparse",
                    "operation": "parse_document",
                    "timeout_seconds": self.timeout_seconds
                }
            )
        except httpx.RequestError as e:
            raise UserFacingError(
                "Document processing service is temporarily unavailable. Please try again later.",
                error_code="LLAMAPARSE_NETWORK_ERROR",
                context={
                    "service": "llamaparse",
                    "operation": "parse_document",
                    "original_error": str(e)
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in LlamaParse parse request: {e}")
            raise UserFacingError(
                "Document processing failed due to an unexpected error. Please try again later.",
                error_code="LLAMAPARSE_UNEXPECTED_ERROR",
                context={
                    "service": "llamaparse",
                    "operation": "parse_document",
                    "original_error": str(e)
                }
            )
    
    async def get_parse_status(self, parse_job_id: str) -> Dict[str, Any]:
        """
        Get the status of a parse job.
        
        Args:
            parse_job_id: The parse job ID to check
            
        Returns:
            Dict with parse job status and details
        """
        if not await self.is_available():
            raise ServiceUnavailableError("LlamaParse service is unavailable")
        
        try:
            response = await self.client.get(f"{self.base_url}/v1/parse/{parse_job_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise ServiceExecutionError(f"Parse job {parse_job_id} not found")
            else:
                error_detail = response.text or f"HTTP {response.status_code}"
                raise ServiceExecutionError(f"Failed to get parse status: {error_detail}")
                
        except httpx.TimeoutException:
            raise ServiceExecutionError("LlamaParse API request timed out")
        except httpx.RequestError as e:
            raise ServiceExecutionError(f"LlamaParse API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting parse status: {e}")
            raise ServiceExecutionError(f"Unexpected error: {e}")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature header
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True
        
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute service operation (implements ServiceInterface)."""
        return await self.parse_document(*args, **kwargs)
    
    async def close(self):
        """Close the service and cleanup resources."""
        if self.client:
            await self.client.aclose()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
