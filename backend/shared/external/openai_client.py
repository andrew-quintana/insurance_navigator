import httpx
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import time
import hashlib

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI API client with micro-batch processing and comprehensive rate limiting"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("api_url", "https://api.openai.com")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "text-embedding-3-small")
        self.timeout = config.get("timeout", 60)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1)
        
        # Rate limiting configuration
        self.requests_per_minute = config.get("requests_per_minute", 3500)
        self.tokens_per_minute = config.get("tokens_per_minute", 90000)
        self.max_batch_size = config.get("max_batch_size", 256)
        
        # Rate limiting state
        self.request_times = []
        self.token_counts = []
        self.last_reset = datetime.utcnow()
        
        # Circuit breaker configuration
        self.failure_threshold = config.get("failure_threshold", 5)
        self.recovery_timeout = config.get("recovery_timeout", 60)
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        
        # HTTP client configuration
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        
        logger.info(f"OpenAI client initialized for {self.base_url} with model {self.model}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def generate_embeddings(
        self, 
        texts: List[str], 
        job_id: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for a list of texts with micro-batching"""
        if not texts:
            return []
        
        # Split into micro-batches
        batches = self._create_micro_batches(texts)
        all_embeddings = []
        
        for i, batch in enumerate(batches):
            try:
                # Check rate limits before processing batch
                await self._wait_for_rate_limit(len(batch))
                
                # Process batch
                batch_embeddings = await self._process_batch(batch, job_id, i + 1, len(batches))
                all_embeddings.extend(batch_embeddings)
                
                # Record successful batch processing
                self._record_batch_success(len(batch))
                
                logger.info(
                    "Batch processed successfully",
                    job_id=job_id,
                    batch_number=i + 1,
                    total_batches=len(batches),
                    batch_size=len(batch),
                    total_processed=len(all_embeddings)
                )
                
            except Exception as e:
                logger.error(
                    "Batch processing failed",
                    job_id=job_id,
                    batch_number=i + 1,
                    batch_size=len(batch),
                    error=str(e)
                )
                raise
        
        return all_embeddings
    
    def _create_micro_batches(self, texts: List[str]) -> List[List[str]]:
        """Create micro-batches based on size and token limits"""
        batches = []
        current_batch = []
        current_tokens = 0
        
        for text in texts:
            # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
            estimated_tokens = len(text) // 4
            
            # Check if adding this text would exceed batch limits
            if (len(current_batch) >= self.max_batch_size or 
                current_tokens + estimated_tokens > 8000):  # OpenAI limit
                
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 0
            
            current_batch.append(text)
            current_tokens += estimated_tokens
        
        # Add final batch
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    async def _wait_for_rate_limit(self, batch_size: int):
        """Wait for rate limit if necessary"""
        now = datetime.utcnow()
        
        # Reset counters if minute has passed
        if (now - self.last_reset).total_seconds() >= 60:
            self.request_times = []
            self.token_counts = []
            self.last_reset = now
        
        # Check request rate limit
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = 60 - (now - self.request_times[0]).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                return await self._wait_for_rate_limit(batch_size)
        
        # Check token rate limit
        total_tokens = sum(self.token_counts) + (batch_size * 100)  # Approximate tokens per text
        if total_tokens >= self.tokens_per_minute:
            wait_time = 60 - (now - self.last_reset).total_seconds()
            if wait_time > 0:
                logger.info(f"Token rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                return await self._wait_for_rate_limit(batch_size)
    
    async def _process_batch(
        self, 
        texts: List[str], 
        job_id: Optional[str], 
        batch_num: int, 
        total_batches: int
    ) -> List[List[float]]:
        """Process a single batch of texts"""
        try:
            if self.circuit_open:
                if self._should_attempt_reset():
                    self._reset_circuit()
                else:
                    raise Exception("Circuit breaker is open")
            
            # Prepare request payload
            payload = {
                "model": self.model,
                "input": texts,
                "encoding_format": "float"
            }
            
            # Make API request
            response = await self.client.post(
                f"{self.base_url}/v1/embeddings",
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract embeddings
            embeddings = [data["embedding"] for data in result["data"]]
            
            # Validate embeddings
            if len(embeddings) != len(texts):
                raise ValueError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")
            
            # Validate embedding dimensions
            expected_dim = 1536 if self.model == "text-embedding-3-small" else 1536
            for i, embedding in enumerate(embeddings):
                if len(embedding) != expected_dim:
                    raise ValueError(f"Embedding {i} has wrong dimension: {len(embedding)} != {expected_dim}")
            
            # Reset failure count on success
            self.failure_count = 0
            
            # Record rate limit usage
            self.request_times.append(datetime.utcnow())
            self.token_counts.append(len(texts) * 100)  # Approximate tokens
            
            logger.info(
                "Batch embeddings generated successfully",
                job_id=job_id,
                batch_number=batch_num,
                total_batches=total_batches,
                batch_size=len(texts),
                embedding_dimension=len(embeddings[0]) if embeddings else 0
            )
            
            return embeddings
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e, job_id, batch_num)
            raise
        except Exception as e:
            await self._handle_general_error(e, job_id, batch_num)
            raise
    
    def _record_batch_success(self, batch_size: int):
        """Record successful batch processing for metrics"""
        # This could be extended to track more detailed metrics
        pass
    
    async def _handle_http_error(self, error: httpx.HTTPStatusError, job_id: Optional[str], batch_num: int):
        """Handle HTTP errors with appropriate logging and circuit breaker logic"""
        self.failure_count += 1
        
        if error.response.status_code in [429, 500, 502, 503, 504]:
            # Retryable error
            logger.warning(
                "Retryable HTTP error in OpenAI API",
                job_id=job_id,
                batch_number=batch_num,
                status_code=error.response.status_code,
                error=str(error),
                failure_count=self.failure_count
            )
        else:
            # Non-retryable error
            logger.error(
                "Non-retryable HTTP error in OpenAI API",
                job_id=job_id,
                batch_number=batch_num,
                status_code=error.response.status_code,
                error=str(error)
            )
        
        # Check if circuit should be opened
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    async def _handle_general_error(self, error: Exception, job_id: Optional[str], batch_num: int):
        """Handle general errors with circuit breaker logic"""
        self.failure_count += 1
        
        logger.error(
            "General error in OpenAI API",
            job_id=job_id,
            batch_number=batch_num,
            error=str(error),
            failure_count=self.failure_count
        )
        
        # Check if circuit should be opened
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    def _open_circuit(self):
        """Open the circuit breaker"""
        self.circuit_open = True
        self.last_failure_time = datetime.utcnow()
        logger.warning(
            "Circuit breaker opened for OpenAI API",
            failure_count=self.failure_count,
            opened_at=self.last_failure_time.isoformat()
        )
    
    def _reset_circuit(self):
        """Reset the circuit breaker"""
        self.circuit_open = False
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker reset for OpenAI API")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on OpenAI API"""
        try:
            # Simple health check using a minimal embedding request
            response = await self.client.post(
                f"{self.base_url}/v1/embeddings",
                json={
                    "model": self.model,
                    "input": ["test"],
                    "encoding_format": "float"
                }
            )
            
            response.raise_for_status()
            
            return {
                "status": "healthy",
                "service": "openai",
                "model": self.model,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "circuit_status": "closed" if not self.circuit_open else "open",
                "rate_limit_status": {
                    "requests_this_minute": len(self.request_times),
                    "tokens_this_minute": sum(self.token_counts)
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "openai",
                "model": self.model,
                "error": str(e),
                "circuit_status": "closed" if not self.circuit_open else "open"
            }

