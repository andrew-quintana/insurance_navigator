"""
Enhanced BaseWorker with Proper Error Handling and Real Service Integration

This worker implements proper error handling following best practices:
- Structured logging with appropriate log levels
- Contextual information (user IDs, request IDs, timestamps, system state)
- Error codes and categorization
- No silent fallbacks to mock data
- Proper service failure handling
- Correlation ID tracking
"""

import asyncio
import logging
import uuid
import hashlib
import json
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import traceback

from core.database import DatabaseManager
from .database_config import create_database_config
from backend.shared.storage.storage_manager import StorageManager
from backend.shared.storage.mock_storage import MockStorageManager
from backend.shared.external import RealLlamaParseService, OpenAIClient
from backend.shared.external.service_router import ServiceRouter, ServiceMode, ServiceUnavailableError, ServiceExecutionError
from backend.shared.exceptions import UserFacingError
from backend.shared.logging import StructuredLogger
from backend.shared.config import WorkerConfig
from backend.shared.external.error_handler import (
    WorkerErrorHandler,
    ErrorContext,
    ErrorSeverity,
    ErrorCategory,
    create_correlation_id,
    create_error_context
)
from backend.shared.external.enhanced_service_client import EnhancedServiceClient

logger = logging.getLogger(__name__)


class EnhancedBaseWorker:
    """
    Enhanced BaseWorker with proper error handling and real service integration.
    
    Features:
    - Structured error logging with appropriate log levels
    - Contextual information in all log messages
    - Error codes and categorization
    - No silent fallbacks to mock data
    - Proper service failure handling
    - Correlation ID tracking throughout processing pipeline
    - Health monitoring and alerting
    """
    
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.worker_id = str(uuid.uuid4())
        self.logger = StructuredLogger(f"enhanced_base_worker.{self.worker_id}", level=config.log_level)
        self.error_handler = WorkerErrorHandler(f"enhanced_base_worker.{self.worker_id}")
        self.running = False
        
        # Initialize components
        self.db = None
        self.storage = None
        self.service_router = None
        self.enhanced_service_client = None
        
        # Processing configuration from config
        self.poll_interval = config.poll_interval
        self.max_retries = config.max_retries
        self.retry_base_delay = config.retry_base_delay
        
        # Circuit breaker state
        self.circuit_open = False
        self.failure_count = 0
        self.last_failure_time = None
        
        self.logger.info(
            "Enhanced BaseWorker initialized",
            worker_id=self.worker_id,
            config_keys=list(config.to_dict().keys())
        )
    
    async def initialize(self):
        """Initialize all components with proper error handling"""
        correlation_id = create_correlation_id()
        context = create_error_context(
            correlation_id=correlation_id,
            operation="worker_initialization"
        )
        
        try:
            self.logger.info(
                "Initializing Enhanced BaseWorker components",
                correlation_id=correlation_id,
                worker_id=self.worker_id
            )
            
            # Initialize database
            db_config = create_database_config()
            self.db = DatabaseManager(db_config)
            await self.db.initialize()
            
            # Initialize storage
            if self.config.use_mock_storage:
                self.storage = MockStorageManager()
                self.logger.warning(
                    "Using mock storage - this should not be used in production",
                    correlation_id=correlation_id
                )
            else:
                self.storage = StorageManager(
                    config={
                        "storage_url": self.config.supabase_url,
                        "anon_key": self.config.supabase_anon_key,
                        "service_role_key": self.config.supabase_service_role_key
                    }
                )
            
            # Initialize service router
            self.service_router = ServiceRouter(
                config={
                    "mode": os.getenv("SERVICE_MODE", "hybrid").lower(),
                    "fallback_enabled": os.getenv("ENVIRONMENT", "development") != "production",
                    "llamaparse_config": {
                        "api_key": self.config.llamaparse_api_key,
                        "api_url": self.config.llamaparse_api_url
                    },
                    "openai_config": {
                        "api_key": self.config.openai_api_key,
                        "api_url": self.config.openai_api_url,
                        "requests_per_minute": self.config.openai_requests_per_minute,
                        "tokens_per_minute": self.config.openai_tokens_per_minute
                    }
                },
                start_health_monitoring=True
            )
            
            # Initialize enhanced service client
            self.enhanced_service_client = EnhancedServiceClient(
                service_router=self.service_router,
                logger_name=f"enhanced_base_worker.{self.worker_id}"
            )
            
            self.logger.info(
                "Enhanced BaseWorker initialization completed successfully",
                correlation_id=correlation_id,
                worker_id=self.worker_id
            )
            
        except Exception as e:
            error = self.error_handler.create_error(
                error_code="WORKER_INITIALIZATION_FAILED",
                error_message="Failed to initialize Enhanced BaseWorker",
                severity=ErrorSeverity.FATAL,
                category=ErrorCategory.CONFIGURATION_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            raise
    
    async def start(self):
        """Start the worker with proper error handling"""
        correlation_id = create_correlation_id()
        context = create_error_context(
            correlation_id=correlation_id,
            operation="worker_start"
        )
        
        try:
            self.logger.info(
                "Starting Enhanced BaseWorker",
                correlation_id=correlation_id,
                worker_id=self.worker_id
            )
            
            # Initialize components if not already done
            if self.db is None:
                await self.initialize()
            
            self.running = True
            await self.process_jobs_continuously()
            
        except Exception as e:
            error = self.error_handler.create_error(
                error_code="WORKER_START_FAILED",
                error_message="Failed to start Enhanced BaseWorker",
                severity=ErrorSeverity.FATAL,
                category=ErrorCategory.PROCESSING_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            raise
    
    async def stop(self):
        """Stop the worker gracefully"""
        correlation_id = create_correlation_id()
        context = create_error_context(
            correlation_id=correlation_id,
            operation="worker_stop"
        )
        
        try:
            self.logger.info(
                "Stopping Enhanced BaseWorker",
                correlation_id=correlation_id,
                worker_id=self.worker_id
            )
            
            self.running = False
            
            # Close database connections
            if self.db:
                await self.db.close()
            
            self.logger.info(
                "Enhanced BaseWorker stopped successfully",
                correlation_id=correlation_id,
                worker_id=self.worker_id
            )
            
        except Exception as e:
            error = self.error_handler.create_error(
                error_code="WORKER_STOP_FAILED",
                error_message="Failed to stop Enhanced BaseWorker",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PROCESSING_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            raise
    
    async def process_jobs_continuously(self):
        """Main worker loop with enhanced error handling"""
        correlation_id = create_correlation_id()
        context = create_error_context(
            correlation_id=correlation_id,
            operation="job_processing_loop"
        )
        
        self.logger.info(
            "Starting job processing loop",
            correlation_id=correlation_id,
            worker_id=self.worker_id
        )
        
        loop_count = 0
        while self.running:
            try:
                loop_count += 1
                
                # Get next job
                job = await self._get_next_job()
                if job:
                    await self._process_single_job_with_monitoring(job)
                else:
                    # No jobs available, wait before next poll
                    await asyncio.sleep(self.poll_interval)
                    
            except asyncio.CancelledError:
                self.logger.info(
                    "Worker loop cancelled",
                    correlation_id=correlation_id,
                    worker_id=self.worker_id
                )
                break
            except Exception as e:
                error = self.error_handler.create_error(
                    error_code="JOB_PROCESSING_LOOP_ERROR",
                    error_message="Error in job processing loop",
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.PROCESSING_ERROR,
                    context=context,
                    original_exception=e
                )
                self.error_handler.log_error(error)
                await asyncio.sleep(10)  # Wait before retrying
        
        self.logger.info(
            "Job processing loop stopped",
            correlation_id=correlation_id,
            worker_id=self.worker_id
        )
    
    async def _get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get next job from queue with proper error handling"""
        correlation_id = create_correlation_id()
        context = create_error_context(
            correlation_id=correlation_id,
            operation="get_next_job"
        )
        
        try:
            async with self.db.get_connection() as conn:
                job = await conn.fetchrow("""
                    WITH next_job AS (
                        SELECT uj.job_id, uj.document_id, d.user_id, uj.status, uj.state,
                               uj.progress, uj.retry_count, uj.last_error, uj.created_at,
                               d.raw_path as storage_path, d.mime as mime_type
                        FROM upload_pipeline.upload_jobs uj
                        JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                        WHERE uj.status IN (
                            'uploaded', 'parse_queued', 'parsed', 'parse_validated', 
                            'chunking', 'chunks_stored', 'embedding_queued', 'embedding_in_progress', 'embeddings_stored'
                        )
                        AND (
                            uj.last_error IS NULL 
                            OR (uj.last_error->>'retry_at')::timestamp <= now()
                            OR (uj.last_error->>'retry_at') IS NULL
                        )
                        ORDER BY 
                            CASE uj.status
                                WHEN 'parsed' THEN 1
                                WHEN 'parse_validated' THEN 2
                                WHEN 'chunking' THEN 3
                                WHEN 'chunks_stored' THEN 4
                                WHEN 'embedding_queued' THEN 5
                                WHEN 'embedding_in_progress' THEN 6
                                WHEN 'embeddings_stored' THEN 7
                                WHEN 'uploaded' THEN 8
                                WHEN 'parse_queued' THEN 9
                                WHEN 'complete' THEN 10
                                WHEN 'duplicate' THEN 11
                                ELSE 12
                            END,
                            uj.created_at
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    )
                    SELECT * FROM next_job
                """)
                
                if job:
                    job_dict = dict(job)
                    job_dict["correlation_id"] = correlation_id
                    return job_dict
                
                return None
                
        except Exception as e:
            error = self.error_handler.create_error(
                error_code="GET_NEXT_JOB_FAILED",
                error_message="Failed to get next job from queue",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.DATABASE_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            raise
    
    async def _process_single_job_with_monitoring(self, job: Dict[str, Any]):
        """Process a single job with comprehensive error handling"""
        job_id = job["job_id"]
        status = job["status"]
        correlation_id = job.get("correlation_id") or create_correlation_id()
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id=job.get("user_id"),
            job_id=str(job_id),
            document_id=str(job.get("document_id")),
            operation=f"process_job_{status}"
        )
        
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(
                "Processing job with enhanced error handling",
                correlation_id=correlation_id,
                job_id=str(job_id),
                status=status,
                user_id=job.get("user_id"),
                document_id=str(job.get("document_id"))
            )
            
            # Process based on status (don't override the current status)
            if status == "uploaded":
                await self._process_parsing_real(job, correlation_id)
                # Job status will be updated to "parse_queued" by _process_parsing_real
            elif status == "parse_queued":
                # Job is queued for external processing (LamaParse), no action needed
                self.logger.info(
                    "Job is queued for external processing, waiting for webhook completion",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    status=status,
                    user_id=job.get("user_id"),
                    document_id=str(job.get("document_id"))
                )
                # No processing action - just acknowledge and continue polling
            elif status == "parsed":
                await self._process_validation_real(job, correlation_id)
                # Job status will be updated to "parse_validated" by _process_validation_real
            elif status == "failed_parse":
                # Retry failed parsing jobs
                await self._retry_failed_parse(job, correlation_id)
            elif status == "parse_validated":
                await self._process_chunking_real(job, correlation_id)
                # Job status will be updated to "chunks_stored" by _process_chunking_real
            elif status == "chunking":
                await self._process_chunking_real(job, correlation_id)
                # Job status will be updated to "chunks_stored" by _process_chunking_real
            elif status == "chunks_stored":
                await self._process_embeddings_real(job, correlation_id)
                # Job status will be updated to "embeddings_stored" by _process_embeddings_real
            elif status == "embedding_queued":
                await self._process_embeddings_real(job, correlation_id)
                # Job status will be updated to "embeddings_stored" by _process_embeddings_real
            elif status == "embedding_in_progress":
                await self._process_embeddings_real(job, correlation_id)
                # Job status will be updated to "embeddings_stored" by _process_embeddings_real
            elif status == "embeddings_stored":
                # Job is complete, mark as done
                await self._update_job_state(job_id, "complete", correlation_id)
                self.logger.info(
                    "Job completed successfully",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    status=status
                )
            elif status in ["complete", "duplicate"]:
                # Job is already complete or duplicate, skip processing
                self.logger.info(
                    "Job already complete or duplicate, skipping",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    status=status
                )
            elif status.startswith("failed_"):
                # Job has failed, skip processing
                self.logger.warning(
                    "Job has failed status, skipping",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    status=status
                )
            else:
                raise ValueError(f"Unknown job status: {status}")
            
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                "Job processed successfully",
                correlation_id=correlation_id,
                job_id=str(job_id),
                processing_time_seconds=processing_time
            )
            
        except UserFacingError as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            # Record processing error metrics (placeholder for monitoring)
            logger.warning(f"Processing error recorded for status {status}: {str(e)}")
            
            self.logger.error(
                "Job processing failed with user-facing error",
                job_id=str(job_id),
                status=status,
                error=str(e),
                support_uuid=e.get_support_uuid(),
                error_code=e.error_code,
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            
            # Handle error - retry or mark as failed
            await self._handle_processing_error_enhanced(job, e, correlation_id)
        except Exception as e:
            error = self.error_handler.create_error(
                error_code=f"JOB_PROCESSING_FAILED_{status.upper()}",
                error_message=f"Failed to process job in {status} stage",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PROCESSING_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            
            # Mark job as failed
            await self._update_job_state(job_id, "failed_parse", correlation_id, str(e))
            raise
    
    async def _process_parsing_real(self, job: Dict[str, Any], correlation_id: str):
        """Process document parsing using real LlamaParse service with webhook delegation"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        user_id = job["user_id"]
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id=user_id,
            job_id=str(job_id),
            document_id=str(document_id),
            service_name="llamaparse",
            operation="parse_document"
        )
        
        try:
            self.logger.info(
                "Delegating document parsing to LlamaParse service",
                correlation_id=correlation_id,
                job_id=str(job_id),
                document_id=str(document_id),
                user_id=user_id
            )
            
            # Get document details
            storage_path = job.get("storage_path")
            mime_type = job.get("mime_type", "application/pdf")
            
            if not storage_path:
                raise ValueError("No storage_path found in job data")
            
            # Get document filename from database
            async with self.db.get_connection() as conn:
                doc_result = await conn.fetchrow("""
                    SELECT filename FROM upload_pipeline.documents 
                    WHERE document_id = $1
                """, document_id)
                document_filename = doc_result["filename"] if doc_result else "document.pdf"
            
            # Log storage path for debugging
            logger.info(f"Processing document with storage path: {storage_path}")
            
            # Generate webhook URL for LlamaParse callback
            # Use environment-appropriate base URL
            environment = os.getenv("ENVIRONMENT", "development")
            webhook_base_url = os.getenv("WEBHOOK_BASE_URL")
            
            # Debug logging for environment variables
            self.logger.info(f"Environment detection: ENVIRONMENT={environment}, WEBHOOK_BASE_URL={webhook_base_url}")
            
            # Webhook URL resolution hierarchy:
            # 1. WEBHOOK_BASE_URL (highest priority - overrides everything)
            # 2. Environment-specific variables (STAGING_WEBHOOK_BASE_URL, PRODUCTION_WEBHOOK_BASE_URL)
            # 3. Default URLs based on environment (fallback)
            
            # Always respect WEBHOOK_BASE_URL when explicitly set (overrides all environment-specific logic)
            if webhook_base_url:
                base_url = webhook_base_url
                self.logger.info(f"Using explicit WEBHOOK_BASE_URL: {base_url}")
            elif environment == "development":
                # For development, try to get ngrok URL dynamically
                try:
                    # Import ngrok_discovery only in development
                    import sys
                    import importlib
                    ngrok_module = importlib.import_module("backend.shared.utils.ngrok_discovery")
                    
                    # Check if ngrok is available
                    if not ngrok_module.is_ngrok_available():
                        raise RuntimeError("Ngrok is required for development but not available. Please start ngrok first.")
                    
                    base_url = ngrok_module.get_webhook_base_url()
                    self.logger.info(f"Using ngrok URL: {base_url}")
                    
                    # Validate the URL is accessible
                    try:
                        import requests
                        response = requests.head(f"{base_url}/health", timeout=5)
                        if response.status_code >= 500:
                            raise RuntimeError(f"Ngrok URL {base_url} is not accessible (status: {response.status_code})")
                    except Exception as e:
                        raise RuntimeError(f"Ngrok URL {base_url} validation failed: {e}")
                        
                except (ImportError, Exception) as e:
                    # No fallback - fail fast if ngrok is not available
                    self.logger.error(f"Ngrok discovery failed: {e}")
                    raise RuntimeError(f"Development environment requires ngrok: {e}")
            else:
                # For staging/production, use environment-specific URLs with fallbacks
                if environment == "staging":
                    base_url = os.getenv(
                        "STAGING_WEBHOOK_BASE_URL", 
                        "https://insurance-navigator-staging-api.onrender.com"
                    )
                    self.logger.info(f"Using staging webhook base URL: {base_url}")
                else:
                    base_url = os.getenv(
                        "PRODUCTION_WEBHOOK_BASE_URL", 
                        "https://insurance-navigator-api.onrender.com"
                    )
                    self.logger.info(f"Using production webhook base URL: {base_url}")
            
            webhook_url = f"{base_url}/api/upload-pipeline/webhook/llamaparse/{job_id}"
            webhook_secret = str(uuid.uuid4())  # Generate webhook secret
            
            # Debug logging for final webhook URL
            self.logger.info(f"Generated webhook URL: {webhook_url}")
            
            # DIRECT LlamaParse call (bypassing service layers to avoid rate limiting)
            parse_result = await self._direct_llamaparse_call(
                file_path=storage_path,
                job_id=str(job_id),
                document_id=str(document_id),
                correlation_id=correlation_id,
                document_filename=document_filename,
                webhook_url=webhook_url
            )
            
            # Store webhook secret in job for verification
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET webhook_secret = $1, status = 'parse_queued', updated_at = now()
                    WHERE job_id = $2
                """, webhook_secret, job_id)
            
            self.logger.info(
                "Document parsing job submitted to LlamaParse",
                job_id=str(job_id),
                document_id=str(document_id),
                parse_job_id=parse_result.get("parse_job_id"),
                webhook_url=webhook_url
            )
            
            # Note: Job will be updated via webhook when parsing completes
            # The webhook will handle storing parsed content and updating status
            
        except UserFacingError as e:
            # Log user-facing error with support UUID
            self.logger.error("Document parsing job submission failed with user-facing error", 
                            job_id=str(job_id), 
                            document_id=str(document_id),
                            error=str(e),
                            support_uuid=e.get_support_uuid(),
                            error_code=e.error_code)
            
            # Update job status to failed with user message
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'failed_parse', last_error = $1, updated_at = now()
                    WHERE job_id = $2
                """, json.dumps({"error": e.get_user_message(), "timestamp": datetime.utcnow().isoformat()}), job_id)
                
                # Update document status (error details are stored in upload_jobs.last_error)
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET processing_status = 'failed', updated_at = now()
                    WHERE document_id = $1
                """, document_id)
            
            # Re-raise the error for upstream handling
            raise
        except Exception as e:
            self.logger.error("Parsing job submission failed", 
                            job_id=str(job_id), 
                            document_id=str(document_id),
                            error=str(e))
            raise
    
    async def _retry_failed_parse(self, job: Dict[str, Any], correlation_id: str):
        """Retry failed parsing jobs with retry limits"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        user_id = job["user_id"]
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id=user_id,
            job_id=str(job_id),
            document_id=str(document_id),
            operation="retry_failed_parse"
        )
        
        try:
            # Check retry count
            async with self.db.get_connection() as conn:
                retry_info = await conn.fetchrow("""
                    SELECT retry_count, last_error
                    FROM upload_pipeline.upload_jobs 
                    WHERE job_id = $1
                """, job_id)
                
                if not retry_info:
                    self.logger.error(f"Job not found for retry: {job_id}")
                    return
                
                retry_count = retry_info.get("retry_count", 0)
                max_retries = self.config.max_retries
                
                if retry_count >= max_retries:
                    self.logger.warning(
                        f"Job {job_id} has exceeded max retries ({max_retries}), marking as permanently failed",
                        correlation_id=correlation_id,
                        job_id=str(job_id),
                        retry_count=retry_count
                    )
                    await self._update_job_state(job_id, "permanently_failed", correlation_id, 
                                               f"Exceeded max retries ({max_retries})")
                    return
                
                # Increment retry count
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET retry_count = retry_count + 1, 
                        status = 'parse_queued',
                        last_error = NULL,
                        updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.info(
                    f"Retrying failed parse job {job_id} (attempt {retry_count + 1}/{max_retries})",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    retry_count=retry_count + 1
                )
                
                # Process the job again
                await self._process_parsing_real(job, correlation_id)
                
        except Exception as e:
            self.logger.error(
                f"Failed to retry job {job_id}: {str(e)}",
                correlation_id=correlation_id,
                job_id=str(job_id),
                error=str(e)
            )
            # Mark as permanently failed if retry mechanism itself fails
            await self._update_job_state(job_id, "permanently_failed", correlation_id, 
                                       f"Retry mechanism failed: {str(e)}")

    async def _process_validation_real(self, job: Dict[str, Any], correlation_id: str):
        """Process document validation with real content"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        user_id = job["user_id"]
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id=user_id,
                    job_id=str(job_id),
            document_id=str(document_id),
            operation="validate_parsed_content"
        )
        
        try:
            self.logger.info(
                "Processing document validation with real content",
                correlation_id=correlation_id,
                job_id=str(job_id),
                document_id=str(document_id),
                user_id=user_id
            )
            
            # Get parsed content from storage
            async with self.db.get_connection() as conn:
                doc_info = await conn.fetchrow("""
                    SELECT parsed_path, parsed_sha256 
                    FROM upload_pipeline.documents 
                    WHERE document_id = $1
                """, document_id)
                
                if not doc_info or not doc_info["parsed_path"]:
                    raise ValueError(f"No parsed_path found for document {document_id}")
                
                parsed_path = doc_info["parsed_path"]
            
            # Read and validate parsed content
            parsed_content = await self.storage.read_blob(parsed_path)
            
            if not parsed_content or len(parsed_content.strip()) == 0:
                raise ValueError("Parsed content is empty")
            
            # Validate content quality
            if len(parsed_content) < 100:
                self.logger.warning(
                    "Parsed content is very short, may indicate parsing issues",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    document_id=str(document_id),
                    content_length=len(parsed_content)
                )
            
            # Update job status
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'parse_validated', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.info(
                "Document validation completed successfully",
                correlation_id=correlation_id,
                    job_id=str(job_id),
                    document_id=str(document_id),
                content_length=len(parsed_content)
                )
        
        except Exception as e:
            error = self.error_handler.create_error(
                error_code="DOCUMENT_VALIDATION_FAILED",
                error_message="Failed to validate parsed document content",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PROCESSING_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            raise
    
    async def _process_chunking_real(self, job: Dict[str, Any], correlation_id: str):
        """Process document chunking with real content"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        user_id = job["user_id"]
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id=user_id,
            job_id=str(job_id),
            document_id=str(document_id),
            operation="chunk_document"
        )
        
        try:
            self.logger.info(
                "Processing document chunking with real content",
                correlation_id=correlation_id,
                    job_id=str(job_id),
                document_id=str(document_id),
                user_id=user_id
                )
            
            # Get parsed content
            async with self.db.get_connection() as conn:
                doc_info = await conn.fetchrow("""
                    SELECT raw_path, parsed_path, parsed_sha256 
                    FROM upload_pipeline.documents 
                    WHERE document_id = $1
                """, document_id)
            
                if not doc_info:
                    raise ValueError(f"No document found for document_id {document_id}")
                
                # Use raw_path for reading the original file
                file_path = doc_info["raw_path"]
                if not file_path:
                    raise ValueError(f"No raw_path found for document {document_id}")
            
            # Read actual file content from blob storage
            self.logger.info(f"Reading file from storage: {file_path}")
            
            # Extract bucket and key from file_path
            if file_path.startswith("files/user/"):
                key = file_path[6:]  # Remove "files/" prefix
                bucket = "files"
            else:
                raise ValueError(f"Invalid file_path format: {file_path}")
            
            # Read parsed content from storage (not raw file)
            try:
                # Get parsed content path from database
                async with self.db.get_connection() as conn:
                    parsed_info = await conn.fetchrow("""
                        SELECT parsed_path FROM upload_pipeline.documents 
                        WHERE document_id = $1
                    """, document_id)
                    
                    if not parsed_info or not parsed_info["parsed_path"]:
                        raise ValueError(f"No parsed content found for document {document_id}")
                    
                    parsed_path = parsed_info["parsed_path"]
                
                # Read parsed content from storage
                parsed_content = await self.storage.read_blob(parsed_path)
                
                if not parsed_content or len(parsed_content.strip()) == 0:
                    raise ValueError("Parsed content is empty or not found")
                
                self.logger.info(f"Successfully read {len(parsed_content)} characters of parsed content from storage")
                    
            except Exception as e:
                self.logger.error(f"Failed to read parsed content from storage: {str(e)}")
                raise ValueError(f"Cannot proceed with chunking - parsed content not available: {str(e)}")
            
            if not parsed_content or len(parsed_content.strip()) == 0:
                raise ValueError("Parsed content is empty")
            
            # Generate chunks (simplified chunking for now)
            chunks = await self._generate_chunks(parsed_content, "1")
            
            # Store chunks in database
            import hashlib
            async with self.db.get_connection() as conn:
                # Check if chunks already exist for this document
                existing_chunks = await conn.fetchval("""
                    SELECT COUNT(*) FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1 AND chunker_name = $2
                """, document_id, chunks[0]["chunker_name"] if chunks else "markdown-simple")
                
                if existing_chunks > 0:
                    self.logger.info(
                        f"Chunks already exist for document {document_id}, skipping chunking and continuing pipeline",
                        correlation_id=correlation_id,
                        job_id=str(job_id),
                        document_id=str(document_id),
                        existing_chunks=existing_chunks
                    )
                    # Chunks already exist, continue to next stage without error
                else:
                    # Insert chunks only if they don't exist
                    for i, chunk in enumerate(chunks):
                        chunk_id = str(uuid.uuid4())
                        chunk_sha = hashlib.sha256(chunk["text"].encode('utf-8')).hexdigest()
                        try:
                            await conn.execute("""
                                INSERT INTO upload_pipeline.document_chunks 
                                (chunk_id, document_id, chunker_name, chunker_version, chunk_ord, text, chunk_sha, 
                                 embed_model, embed_version, vector_dim, embedding, created_at, updated_at)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, now(), now())
                            """, chunk_id, document_id, chunk["chunker_name"], chunk["chunker_version"], 
                                i, chunk["text"], chunk_sha, "text-embedding-3-small", "1", 1536, 
                                "[" + ",".join(["0.0"] * 1536) + "]")  # Placeholder embedding vector as string
                        except Exception as e:
                            if "duplicate key value violates unique constraint" in str(e):
                                self.logger.info(
                                    f"Chunk {i} already exists for document {document_id}, skipping",
                                    correlation_id=correlation_id,
                                    job_id=str(job_id),
                                    document_id=str(document_id),
                                    chunk_ord=i
                                )
                                continue  # Skip this chunk and continue with the next one
                            else:
                                raise  # Re-raise if it's a different error
                
                # Update job status to chunks_stored (whether chunks were inserted or already existed)
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'chunks_stored', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.info(
                    f"Chunking stage completed for document {document_id}",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    document_id=str(document_id),
                    existing_chunks=existing_chunks,
                    chunk_count=len(chunks)
                )
        
        except Exception as e:
            error = self.error_handler.create_error(
                error_code="DOCUMENT_CHUNKING_FAILED",
                error_message="Failed to chunk document content",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PROCESSING_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            raise
    
    async def _process_embeddings_real(self, job: Dict[str, Any], correlation_id: str):
        """Process embeddings using real OpenAI service with batch processing"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        user_id = job["user_id"]
        
        context = create_error_context(
            correlation_id=correlation_id,
            user_id=user_id,
            job_id=str(job_id), 
            document_id=str(document_id),
            service_name="openai",
            operation="generate_embeddings"
        )
        
        try:
            self.logger.info(
                "Processing embeddings with real OpenAI service",
                correlation_id=correlation_id,
                job_id=str(job_id),
                document_id=str(document_id),
                user_id=user_id
            )
            
            # Get chunks from database
            async with self.db.get_connection() as conn:
                chunks = await conn.fetch("""
                    SELECT chunk_id, text 
                    FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                    ORDER BY chunk_ord
                """, document_id)
                
                if not chunks:
                    raise ValueError(f"No chunks found for document {document_id}")
                
                chunk_texts = [chunk["text"] for chunk in chunks]
                total_chunks = len(chunk_texts)
            
            # Process embeddings in batches to avoid OpenAI batch size limits
            batch_size = 256  # OpenAI's maximum batch size
            all_embeddings = []
            
            # Initialize embedding quality monitor
            try:
                from backend.shared.validation.embedding_validator import EmbeddingValidator
                from backend.shared.monitoring.embedding_monitor import EmbeddingQualityMonitor
                
                validator = EmbeddingValidator()
                monitor = EmbeddingQualityMonitor(validator=validator)
                
                self.logger.info("Embedding quality monitoring enabled")
            except ImportError:
                validator = None
                monitor = None
                self.logger.warning("Embedding quality monitoring not available - validation modules not found")
            
            self.logger.info(
                f"Processing {total_chunks} chunks in batches of {batch_size}",
                correlation_id=correlation_id,
                job_id=str(job_id),
                document_id=str(document_id),
                total_chunks=total_chunks,
                batch_size=batch_size
            )
            
            for i in range(0, total_chunks, batch_size):
                batch_end = min(i + batch_size, total_chunks)
                batch_texts = chunk_texts[i:batch_end]
                batch_chunks = chunks[i:batch_end]
                
                self.logger.info(
                    f"Processing batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} "
                    f"(chunks {i+1}-{batch_end})",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    document_id=str(document_id),
                    batch_start=i+1,
                    batch_end=batch_end,
                    batch_size=len(batch_texts)
                )
                
                # Call OpenAI service for this batch
                batch_embeddings = await self.enhanced_service_client.call_openai_service(
                    texts=batch_texts,
                    user_id=user_id,
                    job_id=str(job_id),
                    document_id=str(document_id),
                    correlation_id=correlation_id
                )
                
                # Validate and store embeddings for this batch
                async with self.db.get_connection() as conn:
                    for chunk_idx, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                        # Validate embedding quality if monitor is available
                        if monitor:
                            try:
                                source_info = {
                                    "user_id": user_id,
                                    "job_id": str(job_id),
                                    "document_id": str(document_id),
                                    "chunk_id": str(chunk["chunk_id"]),
                                    "batch_index": i // batch_size,
                                    "chunk_index_in_batch": chunk_idx,
                                    "correlation_id": correlation_id,
                                    "text_length": len(chunk.get("text", "")),
                                    "text_preview": chunk.get("text", "")[:100]
                                }
                                
                                # Validate embedding - this will raise an exception for critical issues
                                validation_result = await monitor.validate_embedding(
                                    embedding, 
                                    source_info, 
                                    raise_on_critical=True
                                )
                                
                                # Log validation success with quality metrics
                                if validation_result.is_valid:
                                    self.logger.debug(
                                        f"Embedding validation successful for chunk {chunk['chunk_id']}",
                                        extra={
                                            "chunk_id": str(chunk["chunk_id"]),
                                            "validation_metrics": validation_result.metrics,
                                            "correlation_id": correlation_id
                                        }
                                    )
                                
                            except Exception as validation_error:
                                # Critical embedding validation failure
                                self.logger.error(
                                    f"CRITICAL_EMBEDDING_VALIDATION_FAILURE: {str(validation_error)}",
                                    extra={
                                        "chunk_id": str(chunk["chunk_id"]),
                                        "embedding_preview": embedding[:5] if len(embedding) >= 5 else embedding,
                                        "embedding_stats": {
                                            "length": len(embedding),
                                            "min_value": min(embedding) if embedding else None,
                                            "max_value": max(embedding) if embedding else None,
                                            "zero_count": sum(1 for x in embedding if abs(x) < 1e-10) if embedding else None
                                        },
                                        "source_info": source_info,
                                        "correlation_id": correlation_id,
                                        "error": str(validation_error)
                                    }
                                )
                                
                                # For critical issues like zero embeddings, fail the entire job
                                if "ZERO_EMBEDDING_DETECTED" in str(validation_error) or "MOSTLY_ZERO_EMBEDDING_DETECTED" in str(validation_error):
                                    raise RuntimeError(
                                        f"Critical embedding quality failure: {str(validation_error)}. "
                                        f"Job {job_id} cannot proceed with invalid embeddings."
                                    )
                                else:
                                    # For less critical issues, log but continue
                                    self.logger.warning(f"Embedding validation warning for chunk {chunk['chunk_id']}: {str(validation_error)}")
                        
                        # Convert embedding list to string format for PostgreSQL vector type
                        embedding_str = "[" + ",".join([str(x) for x in embedding]) + "]"
                        
                        # Store embedding in database
                        await conn.execute("""
                            UPDATE upload_pipeline.document_chunks 
                            SET embedding = $1, updated_at = now()
                            WHERE chunk_id = $2
                        """, embedding_str, chunk["chunk_id"])
                
                all_embeddings.extend(batch_embeddings)
                
                self.logger.info(
                    f"Batch {i//batch_size + 1} processed successfully",
                    correlation_id=correlation_id,
                    job_id=str(job_id),
                    document_id=str(document_id),
                    batch_embeddings=len(batch_embeddings),
                    total_processed=len(all_embeddings)
                )
                
                # Add small delay between batches to respect rate limits
                if i + batch_size < total_chunks:
                    await asyncio.sleep(0.1)  # 100ms delay between batches
            
            # Update job status
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'embeddings_stored', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
            self.logger.info(
                "Embeddings processing completed successfully",
                correlation_id=correlation_id,
                job_id=str(job_id), 
                document_id=str(document_id),
                embedding_count=len(all_embeddings),
                total_chunks=total_chunks
            )
            
        except Exception as e:
            error = self.error_handler.create_error(
                error_code="EMBEDDINGS_PROCESSING_FAILED",
                error_message="Failed to generate embeddings with OpenAI service",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PROCESSING_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            raise
    
    def _generate_chunks(self, content: str, document_id: str) -> List[str]:
        """Generate chunks from content (simplified implementation)"""
        # Simple chunking by paragraphs
        paragraphs = content.split('\n\n')
        chunks = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                chunks.append(paragraph.strip())
        
        return chunks
    
    async def _update_job_state(self, job_id: str, state: str, correlation_id: str, error_message: Optional[str] = None):
        """Update job status in database"""
        try:
            async with self.db.get_connection() as conn:
                if error_message:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs
                        SET status = $1, last_error = $2, updated_at = now()
                        WHERE job_id = $3
                    """, state, json.dumps({"error": error_message, "timestamp": datetime.utcnow().isoformat()}), job_id)
                else:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs
                        SET status = $1, updated_at = now()
                        WHERE job_id = $2
                    """, state, job_id)
        except Exception as e:
            self.logger.error("Error getting final metrics", error=str(e))
            return {"error": str(e)}
    
    async def _generate_chunks(self, content: str, chunker_version: str) -> List[Dict[str, Any]]:
        """Generate chunks from content using specified chunker"""
        try:
            # Simple markdown chunking for now
            # This can be enhanced with more sophisticated chunking strategies
            lines = content.split('\n')
            chunks = []
            current_chunk = []
            chunk_ord = 0
            
            for line in lines:
                current_chunk.append(line)
                
                # Create chunk on headers or after certain number of lines
                if (line.startswith('#') and current_chunk) or len(current_chunk) >= 10:
                    if current_chunk:
                        chunk_text = '\n'.join(current_chunk).strip()
                        if chunk_text:
                            chunks.append({
                                "text": chunk_text,
                                "ord": chunk_ord,
                                "chunker_name": "markdown-simple",
                                "chunker_version": chunker_version,
                                "meta": {
                                    "line_count": len(current_chunk),
                                    "chunk_type": "markdown"
                                }
                            })
                            chunk_ord += 1
                        current_chunk = []
            
            # Add remaining content as final chunk
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "ord": chunk_ord,
                        "chunker_name": "markdown-simple",
                        "chunker_version": chunker_version,
                        "meta": {
                            "line_count": len(current_chunk),
                            "chunk_type": "markdown"
                        }
                    })
            
            return chunks
            
        except Exception as e:
            self.logger.error("Error generating chunks", error=str(e))
            raise
    
    async def _handle_processing_error_enhanced(self, job: Dict[str, Any], error: Exception, correlation_id: str):
        """Enhanced error handling with classification and recovery strategies"""
        job_id = job["job_id"]
        error_message = str(error)
        
        # Classify error type
        if isinstance(error, UserFacingError):
            error_type = "user_facing_error"
            is_retryable = False  # User-facing errors should not be retried
            error_message = error.get_user_message()  # Use user-friendly message
        elif isinstance(error, ServiceUnavailableError):
            error_type = "service_unavailable"
            is_retryable = True
        elif isinstance(error, ServiceExecutionError):
            error_type = "service_execution_error"
            is_retryable = True
        elif "cost limit" in error_message.lower():
            error_type = "cost_limit_exceeded"
            is_retryable = True
        elif "rate limit" in error_message.lower():
            error_type = "rate_limit_exceeded"
            is_retryable = True
        else:
            error_type = "unknown_error"
            is_retryable = False
        
        # Prepare error logging context
        log_context = {
            "job_id": str(job_id),
            "error_type": error_type,
            "error_message": error_message,
            "is_retryable": is_retryable,
            "correlation_id": correlation_id
        }
        
        # Add support UUID for UserFacingError
        if isinstance(error, UserFacingError):
            log_context["support_uuid"] = error.get_support_uuid()
            log_context["error_code"] = error.error_code
        
        self.logger.error(
            "Enhanced error handling",
            **log_context
        )
        
        if is_retryable:
            # Schedule retry with exponential backoff
            retry_delay = min(300, 5 * (2 ** min(job.get("retry_count", 0), 6)))  # Max 5 minutes
            retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
            
            retry_context = {
                "error_type": error_type,
                "error_message": error_message,
                "retry_count": job.get("retry_count", 0) + 1,
                "retry_at": retry_at.isoformat(),
                "retry_delay_seconds": retry_delay,
                "timestamp": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id
            }
            
            await self._update_job_state(job["job_id"], "failed_parse", correlation_id, json.dumps(retry_context))
            
            self.logger.info(
                f"Job {job_id} scheduled for retry in {retry_delay} seconds",
                correlation_id=correlation_id,
                job_id=str(job_id),
                retry_count=retry_context["retry_count"],
                retry_delay_seconds=retry_delay,
                error_type=error_type
            )
        else:
            # Mark job as permanently failed
            await self._update_job_state(job["job_id"], "failed_parse", correlation_id, f"Non-retryable error: {error_type}: {error_message}")
    
    async def _direct_llamaparse_call(self, file_path: str, job_id: str, document_id: str, correlation_id: str, document_filename: str, webhook_url: str) -> Dict[str, Any]:
        """
        Direct LlamaParse API call bypassing all service layers.
        Matches the reference script implementation exactly.
        """
        import httpx
        import os
        
        try:
            # Get API configuration
            LLAMAPARSE_API_KEY = os.getenv("LLAMAPARSE_API_KEY")
            LLAMAPARSE_BASE_URL = "https://api.cloud.llamaindex.ai"
            
            # Read file (try storage first, fallback to local)
            try:
                # Try to read from storage
                storage_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
                # Use development key for local development
                environment = os.getenv("ENVIRONMENT", "development")
                if environment == "development":
                    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
                else:
                    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", os.getenv("SERVICE_ROLE_KEY", ""))
                if not service_role_key:
                    raise Exception("SUPABASE_SERVICE_ROLE_KEY environment variable not set")
                
                if file_path.startswith('files/'):
                    bucket = 'files'
                    key = file_path[6:]  # Remove 'files/' prefix
                else:
                    raise Exception(f"Invalid file path format: {file_path}")
                
                async with httpx.AsyncClient() as storage_client:
                    response = await storage_client.get(
                        f"{storage_url}/storage/v1/object/{bucket}/{key}",
                        headers={
                            "apikey": service_role_key,
                            "Authorization": f"Bearer {service_role_key}",
                            "Content-Type": "application/json",
                            "User-Agent": "Insurance-Navigator/1.0"
                        }
                    )
                    response.raise_for_status()
                    file_content = response.content
                
                if not file_content:
                    raise Exception(f"Downloaded file is empty")
                    
                self.logger.info(f"Downloaded file from storage: {len(file_content)} bytes")
                    
            except Exception as e:
                # Storage download failed - cannot proceed without file
                self.logger.error(f"Storage download failed, cannot process document: {str(e)}")
                raise UserFacingError(
                    "Document file is not accessible for processing. Please try uploading again.",
                    error_code="STORAGE_ACCESS_ERROR"
                )
            
            # Make direct API call exactly like reference script (fresh client, no custom config)
            async with httpx.AsyncClient(timeout=300) as client:
                # Prepare multipart form data for file upload
                files = {
                    'file': (document_filename, file_content, 'application/pdf')
                }
                
                # Prepare form data (primitive types only for multipart)
                form_data = {
                    'parsingInstructions': 'Extract the complete text content from this PDF document exactly as it appears. Do not summarize, analyze, or modify the content. Return the raw text with all details, numbers, and specific information preserved.',
                    'result_type': 'markdown',
                    'webhook_url': webhook_url  # Use simple webhook_url parameter
                }
                
                headers = {
                    'Authorization': f'Bearer {LLAMAPARSE_API_KEY}'
                }
                
                self.logger.info(f"Making direct LlamaParse API call for job {job_id}")
                self.logger.info(f"LlamaParse API form_data: {form_data}")
                
                response = await client.post(
                    f'{LLAMAPARSE_BASE_URL}/api/parsing/upload',
                    files=files,
                    data=form_data,
                    headers=headers
                )
                
                self.logger.info(f"LlamaParse API response: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    parse_job_id = result.get("id", "")
                    
                    self.logger.info(f"LlamaParse job submitted successfully: {parse_job_id}")
                    
                    # Update job status to parse_queued (waiting for webhook completion)
                    async with self.db.get_connection() as conn:
                        await conn.execute("""
                            UPDATE upload_pipeline.upload_jobs
                            SET status = 'parse_queued', state = 'queued', updated_at = now()
                            WHERE job_id = $1
                        """, job_id)
                    
                    self.logger.info(f"Job status updated to parse_queued, waiting for webhook completion")
                    
                    return {
                        "parse_job_id": parse_job_id,
                        "status": "submitted",
                        "message": "Direct API call successful"
                    }
                elif response.status_code == 429:
                    self.logger.error(
                        f"LlamaParse rate limited: {response.status_code}",
                        job_id=job_id,
                        document_id=document_id,
                        api_status_code=response.status_code,
                        api_response_body=response.text,
                        api_response_headers=dict(response.headers)
                    )
                    # Rate limit errors are retryable
                    raise ServiceUnavailableError(
                        "Document processing service is currently busy. Please try again in a few minutes.",
                        error_code="LLAMAPARSE_RATE_LIMIT_ERROR"
                    )
                else:
                    # Enhanced error logging with full context
                    self.logger.error(
                        f"LlamaParse API error: {response.status_code} - {response.text}",
                        job_id=job_id,
                        document_id=document_id,
                        api_status_code=response.status_code,
                        api_response_body=response.text,
                        api_response_headers=dict(response.headers),
                        request_url=f'{LLAMAPARSE_BASE_URL}/api/parsing/upload',
                        request_headers=headers,
                        form_data_keys=list(form_data.keys()),
                        file_size=len(file_content),
                        document_filename=document_filename,
                        webhook_url=webhook_url
                    )
                    
                    # Store detailed error context in database
                    error_context = {
                        "api_status_code": response.status_code,
                        "api_response_body": response.text,
                        "api_response_headers": dict(response.headers),
                        "request_url": f'{LLAMAPARSE_BASE_URL}/api/parsing/upload',
                        "file_size": len(file_content),
                        "document_filename": document_filename,
                        "webhook_url": webhook_url,
                        "timestamp": datetime.utcnow().isoformat(),
                        "correlation_id": correlation_id
                    }
                    
                    # Classify error as retryable or non-retryable
                    if response.status_code in [500, 502, 503, 504]:
                        # Server errors are retryable
                        self.logger.warning(f"LlamaParse server error {response.status_code}, marking as retryable")
                        raise ServiceUnavailableError(
                            "Document processing service is temporarily unavailable. Please try again later.",
                            error_code="LLAMAPARSE_SERVER_ERROR"
                        )
                    elif response.status_code in [400, 401, 403, 422]:
                        # Client errors are non-retryable
                        self.logger.error(f"LlamaParse client error {response.status_code}, marking as non-retryable")
                        
                        # Update job with detailed error context
                        async with self.db.get_connection() as conn:
                            await conn.execute("""
                                UPDATE upload_pipeline.upload_jobs
                                SET status = 'failed_parse', last_error = $1, updated_at = now()
                                WHERE job_id = $2
                            """, json.dumps(error_context), job_id)
                        
                        raise UserFacingError(
                            "Document processing failed due to an invalid request. Please check your document and try again.",
                            error_code="LLAMAPARSE_CLIENT_ERROR"
                        )
                    else:
                        # Unknown errors are non-retryable
                        self.logger.error(f"LlamaParse unknown error {response.status_code}, marking as non-retryable")
                        
                        # Update job with detailed error context
                        async with self.db.get_connection() as conn:
                            await conn.execute("""
                                UPDATE upload_pipeline.upload_jobs
                                SET status = 'failed_parse', last_error = $1, updated_at = now()
                                WHERE job_id = $2
                            """, json.dumps(error_context), job_id)
                        
                        raise UserFacingError(
                            "Document processing failed. Please try again later.",
                            error_code="LLAMAPARSE_API_ERROR"
                        )
                    
        except UserFacingError:
            raise  # Re-raise user-facing errors
        except Exception as e:
            # Enhanced exception logging with full context
            self.logger.error(
                f"Direct LlamaParse call failed: {str(e)}",
                job_id=job_id,
                document_id=document_id,
                exception_type=type(e).__name__,
                exception_message=str(e),
                file_size=len(file_content) if 'file_content' in locals() else 0,
                document_filename=document_filename,
                webhook_url=webhook_url,
                correlation_id=correlation_id,
                exc_info=True
            )
            
            # Store detailed error context in database
            error_context = {
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "file_size": len(file_content) if 'file_content' in locals() else 0,
                "document_filename": document_filename,
                "webhook_url": webhook_url,
                "timestamp": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id
            }
            
            # Update job with detailed error context
            async with self.db.get_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'failed_parse', last_error = $1, updated_at = now()
                    WHERE job_id = $2
                """, json.dumps(error_context), job_id)
            
            raise UserFacingError(
                "Document processing failed due to an unexpected error. Please try again later.",
                error_code="LLAMAPARSE_UNEXPECTED_ERROR"
            )

    async def _handle_worker_error(self, error: Exception):
        """Handle worker-level errors with circuit breaker logic"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        # Check if circuit should be opened
        if self.failure_count >= 5:  # Open circuit after 5 failures
            self.circuit_open = True
            self.logger.error(
                "Circuit breaker opened due to excessive failures"
            )
            raise