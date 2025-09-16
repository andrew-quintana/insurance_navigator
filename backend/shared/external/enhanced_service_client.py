"""
Enhanced Service Client with Proper Error Handling

This client implements proper error handling instead of silent fallbacks to mock data.
It follows best practices for error logging and service failure handling.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .error_handler import (
    WorkerErrorHandler, 
    ErrorContext, 
    ErrorSeverity, 
    ErrorCategory,
    create_correlation_id,
    create_error_context
)
from .service_router import ServiceRouter, ServiceMode
from ..logging.structured_logger import StructuredLogger


class EnhancedServiceClient:
    """
    Enhanced service client that properly handles errors instead of falling back to mock data.
    
    Features:
    - Structured error logging
    - Proper error propagation
    - Service health monitoring
    - Retry logic with exponential backoff
    - Correlation ID tracking
    """
    
    def __init__(self, service_router: ServiceRouter, logger_name: str = "enhanced_service_client"):
        self.service_router = service_router
        self.error_handler = WorkerErrorHandler(logger_name)
        self.logger = StructuredLogger(logger_name)
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "exponential_base": 2.0
        }
    
    async def call_llamaparse_service(
        self,
        document_path: str,
        user_id: str,
        job_id: str,
        document_id: str,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call LlamaParse service with proper error handling.
        
        Args:
            document_path: Path to the document to parse
            user_id: User ID for context
            job_id: Job ID for tracking
            document_id: Document ID for tracking
            correlation_id: Correlation ID for request tracking
            
        Returns:
            Parsed document content and metadata
            
        Raises:
            ServiceUnavailableError: If service is unavailable and fallback is disabled
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            ProcessingError: If document processing fails
        """
        if correlation_id is None:
            correlation_id = create_correlation_id()
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id=user_id,
            job_id=job_id,
            document_id=document_id,
            service_name="llamaparse",
            operation="parse_document"
        )
        
        try:
            # Get the service (this will raise an error if unavailable and fallback disabled)
            service = await self.service_router.get_service("llamaparse")
            
            # Check if we're in mock mode (this should not happen in production)
            if hasattr(service, 'name') and 'mock' in service.name.lower():
                error = self.error_handler.create_error(
                    error_code="MOCK_SERVICE_DETECTED",
                    error_message="Mock service detected in production environment",
                    severity=ErrorSeverity.FATAL,
                    category=ErrorCategory.CONFIGURATION_ERROR,
                    context=context,
                    metadata={"service_name": "llamaparse", "detected_mode": "mock"}
                )
                self.error_handler.log_error(error)
                raise RuntimeError("Mock service detected in production - this should not happen")
            
            # Call the service with retry logic
            result = await self._call_with_retry(
                service.parse_document,
                document_path,
                context=context,
                service_name="llamaparse"
            )
            
            self.logger.info(
                "LlamaParse service call successful",
                correlation_id=correlation_id,
                job_id=job_id,
                document_id=document_id,
                result_size=len(str(result))
            )
            
            return result
            
        except Exception as e:
            # Log the error and re-raise instead of falling back to mock
            error = self.error_handler.handle_processing_error(
                operation="llamaparse_parse",
                context=context,
                original_exception=e,
                is_retryable=True
            )
            self.error_handler.log_error(error)
            raise
    
    async def submit_llamaparse_job(
        self,
        job_id: str,
        document_id: str,
        source_url: str,
        webhook_url: str,
        webhook_secret: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit a LlamaParse job with webhook callback.
        
        Args:
            job_id: Job ID for tracking
            document_id: Document ID for tracking
            source_url: URL of the document to parse
            webhook_url: Webhook URL for callback
            webhook_secret: Secret for webhook verification
            correlation_id: Correlation ID for request tracking
            
        Returns:
            Parse job submission result with job ID
            
        Raises:
            ServiceUnavailableError: If service is unavailable
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
        """
        if correlation_id is None:
            correlation_id = create_correlation_id()
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id="",  # Not available at job submission time
            job_id=job_id,
            document_id=document_id,
            service_name="llamaparse",
            operation="submit_parse_job"
        )
        
        try:
            # Get the service (this will raise an error if unavailable and fallback disabled)
            service = await self.service_router.get_service("llamaparse")
            
            # Check if we're in mock mode (this should not happen in production)
            if hasattr(service, 'name') and 'mock' in service.name.lower():
                error = self.error_handler.create_error(
                    error_code="MOCK_SERVICE_DETECTED",
                    error_message="Mock service detected in production environment",
                    severity=ErrorSeverity.FATAL,
                    category=ErrorCategory.CONFIGURATION_ERROR,
                    context=context,
                    metadata={"service_name": "llamaparse", "detected_mode": "mock"}
                )
                self.error_handler.log_error(error)
                raise RuntimeError("Mock service detected in production - this should not happen")
            
            # Call the service with retry logic
            result = await self._call_with_retry(
                service.submit_parse_job,
                job_id,
                source_url,
                webhook_url,
                webhook_secret,
                context=context,
                service_name="llamaparse"
            )
            
            self.logger.info(
                "LlamaParse job submitted successfully",
                correlation_id=correlation_id,
                job_id=job_id,
                document_id=document_id,
                parse_job_id=result.get("parse_job_id")
            )
            
            return result
            
        except Exception as e:
            # Log the error and re-raise instead of falling back to mock
            error = self.error_handler.handle_processing_error(
                operation="llamaparse_submit_job",
                context=context,
                original_exception=e,
                is_retryable=True
            )
            raise
    
    async def call_openai_service(
        self,
        texts: List[str],
        user_id: str,
        job_id: str,
        document_id: str,
        correlation_id: Optional[str] = None
    ) -> List[List[float]]:
        """
        Call OpenAI service for embeddings with proper error handling.
        
        Args:
            texts: List of texts to embed
            user_id: User ID for context
            job_id: Job ID for tracking
            document_id: Document ID for tracking
            correlation_id: Correlation ID for request tracking
            
        Returns:
            List of embedding vectors
            
        Raises:
            ServiceUnavailableError: If service is unavailable and fallback is disabled
            AuthenticationError: If authentication fails
            RateLimitError: If rate limit is exceeded
            ProcessingError: If embedding generation fails
        """
        if correlation_id is None:
            correlation_id = create_correlation_id()
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id=user_id,
            job_id=job_id,
            document_id=document_id,
            service_name="openai",
            operation="generate_embeddings"
        )
        
        try:
            # Get the service (this will raise an error if unavailable and fallback disabled)
            service = await self.service_router.get_service("openai")
            
            # Check if we're in mock mode (this should not happen in production)
            if hasattr(service, 'name') and 'mock' in service.name.lower():
                error = self.error_handler.create_error(
                    error_code="MOCK_SERVICE_DETECTED",
                    error_message="Mock service detected in production environment",
                    severity=ErrorSeverity.FATAL,
                    category=ErrorCategory.CONFIGURATION_ERROR,
                    context=context,
                    metadata={"service_name": "openai", "detected_mode": "mock"}
                )
                self.error_handler.log_error(error)
                raise RuntimeError("Mock service detected in production - this should not happen")
            
            # Call the service with retry logic
            result = await self._call_with_retry(
                service.generate_embeddings,
                texts,
                context=context,
                service_name="openai"
            )
            
            self.logger.info(
                "OpenAI service call successful",
                correlation_id=correlation_id,
                job_id=job_id,
                document_id=document_id,
                embedding_count=len(result)
            )
            
            return result
            
        except Exception as e:
            # Log the error and re-raise instead of falling back to mock
            error = self.error_handler.handle_processing_error(
                operation="openai_embeddings",
                context=context,
                original_exception=e,
                is_retryable=True
            )
            raise
    
    async def _call_with_retry(
        self,
        service_func,
        *args,
        context: ErrorContext,
        service_name: str,
        **kwargs
    ) -> Any:
        """
        Call service function with retry logic and proper error handling.
        
        Args:
            service_func: The service function to call
            *args: Arguments to pass to the service function
            context: Error context for logging
            service_name: Name of the service for error reporting
            **kwargs: Keyword arguments to pass to the service function
            
        Returns:
            Result from the service function
            
        Raises:
            Various service errors based on the failure type
        """
        last_exception = None
        
        for attempt in range(self.retry_config["max_retries"] + 1):
            try:
                # Call the service function
                result = await service_func(*args, **kwargs)
                
                if attempt > 0:
                    self.logger.info(
                        f"Service call succeeded on attempt {attempt + 1}",
                        correlation_id=context.correlation_id,
                        service_name=service_name,
                        attempt=attempt + 1
                    )
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Log the attempt
                self.logger.warning(
                    f"Service call failed on attempt {attempt + 1}",
                    correlation_id=context.correlation_id,
                    service_name=service_name,
                    attempt=attempt + 1,
                    error=str(e)
                )
                
                # Check if this is the last attempt
                if attempt >= self.retry_config["max_retries"]:
                    break
                
                # Calculate delay for next attempt
                delay = min(
                    self.retry_config["base_delay"] * (self.retry_config["exponential_base"] ** attempt),
                    self.retry_config["max_delay"]
                )
                
                self.logger.info(
                    f"Retrying service call in {delay} seconds",
                    correlation_id=context.correlation_id,
                    service_name=service_name,
                    delay=delay
                )
                
                await asyncio.sleep(delay)
        
        # All retries failed, raise the last exception
        if last_exception:
            # Create appropriate error based on exception type
            if "rate limit" in str(last_exception).lower():
                error = self.error_handler.handle_rate_limit_exceeded(
                    service_name=service_name,
                    context=context,
                    retry_after=60,  # Default retry after 60 seconds
                    original_exception=last_exception
                )
            elif "auth" in str(last_exception).lower() or "unauthorized" in str(last_exception).lower():
                error = self.error_handler.handle_authentication_failed(
                    service_name=service_name,
                    context=context,
                    original_exception=last_exception
                )
            else:
                error = self.error_handler.handle_service_unavailable(
                    service_name=service_name,
                    context=context,
                    original_exception=last_exception
                )
            
            raise last_exception
    
    def get_service_health(self) -> Dict[str, Any]:
        """Get current service health status"""
        return {
            "error_summary": self.error_handler.get_error_summary(),
            "retry_config": self.retry_config,
            "timestamp": datetime.utcnow().isoformat()
        }
