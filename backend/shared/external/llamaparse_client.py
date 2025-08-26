import httpx
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json
import hashlib
import hmac
import secrets

logger = logging.getLogger(__name__)

class LlamaParseClient:
    """LlamaParse API client with comprehensive error handling and webhook support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("api_url", "https://api.llamaindex.ai")
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 120)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 5)
        
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
        
        logger.info(f"LlamaParse client initialized for {self.base_url}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def submit_parse_job(
        self, 
        job_id: str, 
        source_url: str, 
        webhook_url: str,
        webhook_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit a parse job with webhook callback"""
        try:
            if self.circuit_open:
                if self._should_attempt_reset():
                    self._reset_circuit()
                else:
                    raise Exception("Circuit breaker is open")
            
            # Prepare webhook payload with HMAC signature if secret provided
            webhook_payload = {
                "url": webhook_url,
                "headers": {}
            }
            
            if webhook_secret:
                timestamp = str(int(datetime.utcnow().timestamp()))
                payload = f"{job_id}:{timestamp}"
                signature = hmac.new(
                    webhook_secret.encode(),
                    payload.encode(),
                    hashlib.sha256
                ).hexdigest()
                
                webhook_payload["headers"] = {
                    "X-LlamaParse-Signature": signature,
                    "X-LlamaParse-Timestamp": timestamp
                }
            
            # Submit parse job
            response = await self.client.post(
                f"{self.base_url}/v1/parse",
                json={
                    "source_url": source_url,
                    "webhook": webhook_payload,
                    "metadata": {
                        "job_id": job_id,
                        "submitted_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Reset failure count on success
            self.failure_count = 0
            
            logger.info(
                "Parse job submitted successfully",
                job_id=job_id,
                parse_job_id=result.get("parse_job_id"),
                status=result.get("status")
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e, job_id)
            raise
        except Exception as e:
            await self._handle_general_error(e, job_id)
            raise
    
    async def check_parse_status(self, parse_job_id: str) -> Dict[str, Any]:
        """Check the status of a parse job"""
        try:
            if self.circuit_open:
                if self._should_attempt_reset():
                    self._reset_circuit()
                else:
                    raise Exception("Circuit breaker is open")
            
            response = await self.client.get(
                f"{self.base_url}/v1/parse/{parse_job_id}"
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Reset failure count on success
            self.failure_count = 0
            
            logger.info(
                "Parse status retrieved",
                parse_job_id=parse_job_id,
                status=result.get("status")
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            await self._handle_http_error(e, parse_job_id)
            raise
        except Exception as e:
            await self._handle_general_error(e, parse_job_id)
            raise
    
    async def _handle_http_error(self, error: httpx.HTTPStatusError, job_id: str):
        """Handle HTTP errors with appropriate logging and circuit breaker logic"""
        self.failure_count += 1
        
        if error.response.status_code in [429, 500, 502, 503, 504]:
            # Retryable error
            logger.warning(
                "Retryable HTTP error in LlamaParse API",
                job_id=job_id,
                status_code=error.response.status_code,
                error=str(error),
                failure_count=self.failure_count
            )
        else:
            # Non-retryable error
            logger.error(
                "Non-retryable HTTP error in LlamaParse API",
                job_id=job_id,
                status_code=error.response.status_code,
                error=str(error)
            )
        
        # Check if circuit should be opened
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    async def _handle_general_error(self, error: Exception, job_id: str):
        """Handle general errors with circuit breaker logic"""
        self.failure_count += 1
        
        logger.error(
            "General error in LlamaParse API",
            job_id=job_id,
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
            "Circuit breaker opened for LlamaParse API",
            failure_count=self.failure_count,
            opened_at=self.last_failure_time.isoformat()
        )
    
    def _reset_circuit(self):
        """Reset the circuit breaker"""
        self.circuit_open = False
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker reset for LlamaParse API")
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.recovery_timeout
    
    async def is_available(self) -> bool:
        """Check if the LlamaParse service is available"""
        try:
            # Use health check to determine availability
            health_result = await self.health_check()
            return health_result["status"] == "healthy" and not self.circuit_open
        except Exception:
            return False
    
    async def get_health(self) -> Dict[str, Any]:
        """Get service health information (alias for health_check for compatibility)"""
        return await self.health_check()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on LlamaParse API"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            return {
                "status": "healthy",
                "service": "llamaparse",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "circuit_status": "closed" if not self.circuit_open else "open"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "llamaparse",
                "error": str(e),
                "circuit_status": "closed" if not self.circuit_open else "open"
            }

