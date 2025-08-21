"""
Real OpenAI API client implementation.

This module provides a real OpenAI API client with authentication,
rate limiting, cost tracking, and comprehensive error handling.
"""

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field

from .service_router import ServiceInterface, ServiceHealth, ServiceUnavailableError, ServiceExecutionError

logger = logging.getLogger(__name__)


class OpenAIEmbeddingRequest(BaseModel):
    """OpenAI embedding request model."""
    input: Union[str, List[str]] = Field(..., description="Text or list of texts to embed")
    model: str = Field(default="text-embedding-3-small", description="Embedding model to use")
    encoding_format: Optional[str] = Field(default="float", description="Encoding format")
    user: Optional[str] = Field(None, description="User identifier for tracking")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class OpenAIEmbeddingResponse(BaseModel):
    """OpenAI embedding response model."""
    object: str = Field(..., description="Response object type")
    data: List[Dict[str, Any]] = Field(..., description="Embedding data")
    model: str = Field(..., description="Model used for embedding")
    usage: Dict[str, Any] = Field(..., description="Usage statistics")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")


class RealOpenAIService(ServiceInterface):
    """Real OpenAI API service implementation."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com",
        organization: Optional[str] = None,
        rate_limit_per_minute: int = 3500,  # OpenAI's default rate limit
        timeout_seconds: int = 30,
        max_retries: int = 3,
        max_batch_size: int = 256  # OpenAI's max batch size
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.organization = organization
        self.rate_limit_per_minute = rate_limit_per_minute
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.max_batch_size = max_batch_size
        
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
        
        # Cost tracking (approximate costs per 1K tokens)
        self.cost_per_1k_tokens = {
            "text-embedding-3-small": 0.00002,  # $0.00002 per 1K tokens
            "text-embedding-3-large": 0.00013,  # $0.00013 per 1K tokens
        }
        
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
        
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(self.timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def is_available(self) -> bool:
        """Check if the OpenAI service is available."""
        try:
            health = await self.get_health()
            return health.is_healthy
        except Exception as e:
            logger.warning(f"OpenAI availability check failed: {e}")
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
            
            # Test API connectivity with models endpoint
            response = await self.client.get(f"{self.base_url}/v1/models")
            
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update health status
            self.health_status = ServiceHealth(
                is_healthy=response.status_code in [200, 401, 403],  # 401/403 means API is up
                last_check=now,
                response_time_ms=response_time,
                error_count=0 if response.status_code in [200, 401, 403] else 1,
                last_error=None if response.status_code in [200, 401, 403] else f"HTTP {response.status_code}"
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
            
            logger.error(f"OpenAI health check failed: {error_msg}")
        
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
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (approximate)."""
        # Rough estimation: 1 token ≈ 4 characters for English text
        return math.ceil(len(text) / 4)
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate estimated cost for token usage."""
        cost_per_1k = self.cost_per_1k_tokens.get(model, 0.00002)  # Default to small model cost
        return (tokens / 1000) * cost_per_1k
    
    async def create_embeddings(
        self,
        input_texts: Union[str, List[str]],
        model: str = "text-embedding-3-small",
        encoding_format: str = "float",
        user: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> OpenAIEmbeddingResponse:
        """
        Create embeddings using OpenAI API.
        
        Args:
            input_texts: Text or list of texts to embed
            model: Embedding model to use
            encoding_format: Encoding format (float or base64)
            user: Optional user identifier
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            OpenAIEmbeddingResponse with embeddings and usage data
            
        Raises:
            ServiceExecutionError: If embedding creation fails
            ServiceUnavailableError: If service is unavailable
        """
        if not await self.is_available():
            raise ServiceUnavailableError("OpenAI service is unavailable")
        
        await self._check_rate_limit()
        
        # Normalize input to list
        if isinstance(input_texts, str):
            input_texts = [input_texts]
        
        if not input_texts:
            raise ServiceExecutionError("No input texts provided")
        
        # Validate batch size
        if len(input_texts) > self.max_batch_size:
            raise ServiceExecutionError(f"Batch size {len(input_texts)} exceeds maximum {self.max_batch_size}")
        
        try:
            # Prepare request payload
            payload = {
                "input": input_texts,
                "model": model,
                "encoding_format": encoding_format
            }
            
            if user:
                payload["user"] = user
            
            # Add correlation ID to headers for tracking
            headers = {}
            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id
            
            # Estimate tokens for cost tracking
            total_tokens = sum(self._estimate_tokens(text) for text in input_texts)
            estimated_cost = self._calculate_cost(model, total_tokens)
            
            logger.info(
                f"Creating embeddings with OpenAI",
                extra={
                    "model": model,
                    "batch_size": len(input_texts),
                    "total_tokens": total_tokens,
                    "estimated_cost": estimated_cost,
                    "correlation_id": correlation_id
                }
            )
            
            # Submit embedding request
            response = await self.client.post(
                f"{self.base_url}/v1/embeddings",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Add correlation ID to response
                data["correlation_id"] = correlation_id
                
                logger.info(
                    f"Embeddings created successfully",
                    extra={
                        "model": model,
                        "batch_size": len(input_texts),
                        "usage": data.get("usage", {}),
                        "correlation_id": correlation_id
                    }
                )
                
                return OpenAIEmbeddingResponse(**data)
            
            elif response.status_code == 401:
                raise ServiceExecutionError("Invalid OpenAI API key")
            elif response.status_code == 403:
                raise ServiceExecutionError("Insufficient OpenAI API permissions")
            elif response.status_code == 429:
                raise ServiceExecutionError("OpenAI API rate limit exceeded")
            elif response.status_code >= 500:
                raise ServiceExecutionError(f"OpenAI API server error: {response.status_code}")
            else:
                error_detail = response.text or f"HTTP {response.status_code}"
                raise ServiceExecutionError(f"OpenAI API request failed: {error_detail}")
                
        except httpx.TimeoutException:
            raise ServiceExecutionError("OpenAI API request timed out")
        except httpx.RequestError as e:
            raise ServiceExecutionError(f"OpenAI API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI embedding request: {e}")
            raise ServiceExecutionError(f"Unexpected error: {e}")
    
    async def create_embeddings_batch(
        self,
        input_texts: List[str],
        model: str = "text-embedding-3-small",
        batch_size: Optional[int] = None,
        correlation_id: Optional[str] = None
    ) -> List[List[float]]:
        """
        Create embeddings for a large batch of texts, automatically chunking into smaller batches.
        
        Args:
            input_texts: List of texts to embed
            model: Embedding model to use
            batch_size: Optional custom batch size (defaults to max_batch_size)
            correlation_id: Optional correlation ID for tracking
            
        Returns:
            List of embedding vectors
        """
        if not input_texts:
            return []
        
        batch_size = batch_size or self.max_batch_size
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(input_texts), batch_size):
            batch = input_texts[i:i + batch_size]
            batch_correlation_id = f"{correlation_id}-batch-{i//batch_size + 1}" if correlation_id else None
            
            try:
                response = await self.create_embeddings(
                    batch,
                    model=model,
                    correlation_id=batch_correlation_id
                )
                
                # Extract embeddings from response
                batch_embeddings = [item["embedding"] for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.info(
                    f"Batch {i//batch_size + 1} processed successfully",
                    extra={
                        "batch_size": len(batch),
                        "total_processed": len(all_embeddings),
                        "correlation_id": batch_correlation_id
                    }
                )
                
            except Exception as e:
                logger.error(f"Batch {i//batch_size + 1} failed: {e}")
                # For failed batches, add empty embeddings to maintain index alignment
                all_embeddings.extend([[] for _ in batch])
        
        return all_embeddings
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """
        Get available OpenAI models.
        
        Returns:
            List of available models
        """
        if not await self.is_available():
            raise ServiceUnavailableError("OpenAI service is unavailable")
        
        try:
            response = await self.client.get(f"{self.base_url}/v1/models")
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                error_detail = response.text or f"HTTP {response.status_code}"
                raise ServiceExecutionError(f"Failed to get models: {error_detail}")
                
        except httpx.TimeoutException:
            raise ServiceExecutionError("OpenAI API request timed out")
        except httpx.RequestError as e:
            raise ServiceExecutionError(f"OpenAI API request failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error getting models: {e}")
            raise ServiceExecutionError(f"Unexpected error: {e}")
    
    async def execute(self, *args, **kwargs) -> Any:
        """Execute service operation (implements ServiceInterface)."""
        return await self.create_embeddings(*args, **kwargs)
    
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
