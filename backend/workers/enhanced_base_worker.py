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
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import traceback

from shared.db import DatabaseManager
from shared.storage import StorageManager
from shared.storage.mock_storage import MockStorageManager
from shared.external import RealLlamaParseService, OpenAIClient
from shared.external.service_router import ServiceRouter, ServiceMode, ServiceUnavailableError, ServiceExecutionError
from shared.exceptions import UserFacingError
from shared.logging import StructuredLogger
from shared.config import WorkerConfig
from shared.external.error_handler import (
    WorkerErrorHandler,
    ErrorContext,
    ErrorSeverity,
    ErrorCategory,
    create_correlation_id,
    create_error_context
)
from shared.external.enhanced_service_client import EnhancedServiceClient

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
            self.db = DatabaseManager(self.config.database_url)
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
            async with self.db.get_db_connection() as conn:
                job = await conn.fetchrow("""
                    WITH next_job AS (
                        SELECT uj.job_id, uj.document_id, d.user_id, uj.status, uj.state,
                               uj.progress, uj.retry_count, uj.last_error, uj.created_at,
                               d.storage_path, d.mime_type
                        FROM upload_pipeline.upload_jobs uj
                        JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                        WHERE uj.status IN (
                            'uploaded', 'parse_queued', 'parsed', 'parse_validated', 
                            'chunking', 'chunks_stored', 'embedding_queued', 'embedding_in_progress', 'embeddings_stored'
                        )
                        AND uj.state IN ('queued', 'working', 'retryable')
                        AND (
                            uj.last_error IS NULL 
                            OR (uj.last_error->>'retry_at')::timestamp <= now()
                        )
                        ORDER BY uj.created_at
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
            
            # Update job state to working
            await self._update_job_state(job_id, "working", correlation_id)
            
            # Process based on status
            if status == "uploaded":
                await self._process_parsing_real(job, correlation_id)
            elif status == "parsed":
                await self._process_validation_real(job, correlation_id)
            elif status == "parse_validated":
                await self._process_chunking_real(job, correlation_id)
            elif status == "chunks_stored":
                await self._process_embeddings_real(job, correlation_id)
            else:
                raise ValueError(f"Unknown job status: {status}")
            
            # Mark job as completed
            await self._update_job_state(job_id, "completed", correlation_id)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(
                "Job processed successfully",
                correlation_id=correlation_id,
                job_id=str(job_id),
                processing_time_seconds=processing_time
            )
            
        except UserFacingError as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._record_processing_error(status, str(e))
            
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
            await self._update_job_state(job_id, "failed", correlation_id, str(e))
            raise
    
    async def _process_parsing_real(self, job: Dict[str, Any], correlation_id: str):
        """Process document parsing using real LlamaParse service"""
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
                "Processing document parsing with real LlamaParse service",
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
            
            # Call real LlamaParse service
            parsed_result = await self.enhanced_service_client.call_llamaparse_service(
                document_path=storage_path,
                user_id=user_id,
                        job_id=str(job_id),
                document_id=str(document_id),
                        correlation_id=correlation_id
                    )
                    
            # Store parsed content
            parsed_path = f"files/user/{user_id}/parsed/{document_id}.md"
            await self.storage.write_blob(parsed_path, parsed_result["content"])
            
            # Update document with parsed content info
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET parsed_path = $1, parsed_sha256 = $2, processing_status = 'parsed',
                        updated_at = now()
                    WHERE document_id = $3
                """, parsed_path, parsed_result.get("sha256", ""), document_id)
                
                # Update job status
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET status = 'parsed', state = 'queued', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
<<<<<<< HEAD
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET parsed_path = $1, processing_status = 'parsed', updated_at = now()
                    WHERE document_id = $2
                """, parsed_path, document_id)
                
                self.logger.info("Document parsed successfully", 
                               job_id=str(job_id), 
                               document_id=str(document_id),
                               parsed_path=parsed_path)
                
            except UserFacingError as e:
                # Log user-facing error with support UUID
                self.logger.error("Document parsing failed with user-facing error", 
                                job_id=str(job_id), 
                                document_id=str(document_id),
                                error=str(e),
                                support_uuid=e.get_support_uuid(),
                                error_code=e.error_code)
                
                # Update job status to failed with user message
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'failed', state = 'error', error_message = $1, updated_at = now()
                    WHERE job_id = $2
                """, e.get_user_message(), job_id)
                
                # Update document status
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET processing_status = 'failed', error_message = $1, updated_at = now()
                    WHERE document_id = $2
                """, e.get_user_message(), document_id)
                
                # Re-raise the error for upstream handling
                raise
            except Exception as e:
                self.logger.error("Parsing failed", 
                                job_id=str(job_id), 
                                document_id=str(document_id),
                                error=str(e))
                raise
=======
                self.logger.info(
                "Document parsing completed successfully",
                correlation_id=correlation_id,
                    job_id=str(job_id),
                document_id=str(document_id),
                parsed_path=parsed_path
                )
        
        except Exception as e:
            error = self.error_handler.create_error(
                error_code="DOCUMENT_PARSING_FAILED",
                error_message="Failed to parse document with LlamaParse service",
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PROCESSING_ERROR,
                context=context,
                original_exception=e
            )
            self.error_handler.log_error(error)
            raise
>>>>>>> 17059bea829e425cbc75d16d069994640a564c4c
    
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
            async with self.db.get_db_connection() as conn:
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
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'parse_validated', state = 'queued', updated_at = now()
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
            async with self.db.get_db_connection() as conn:
                doc_info = await conn.fetchrow("""
                    SELECT parsed_path, parsed_sha256 
                    FROM upload_pipeline.documents 
                    WHERE document_id = $1
                """, document_id)
            
                if not doc_info or not doc_info["parsed_path"]:
                    raise ValueError(f"No parsed_path found for document {document_id}")
                
                parsed_path = doc_info["parsed_path"]
            
            # Read parsed content
            parsed_content = await self.storage.read_blob(parsed_path)
            
            if not parsed_content or len(parsed_content.strip()) == 0:
                raise ValueError("Parsed content is empty")
            
            # Generate chunks (simplified chunking for now)
            chunks = self._generate_chunks(parsed_content, document_id)
            
            # Store chunks in database
            async with self.db.get_db_connection() as conn:
                for i, chunk in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())
                    await conn.execute("""
                        INSERT INTO upload_pipeline.document_chunks 
                        (chunk_id, document_id, chunk_ord, text, created_at)
                        VALUES ($1, $2, $3, $4, now())
                    """, chunk_id, document_id, i, chunk)
                
                # Update job status
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'chunks_stored', state = 'queued', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.info(
                "Document chunking completed successfully",
                correlation_id=correlation_id,
                    job_id=str(job_id),
                    document_id=str(document_id),
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
        """Process embeddings using real OpenAI service"""
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
            async with self.db.get_db_connection() as conn:
                chunks = await conn.fetch("""
                    SELECT chunk_id, text 
                    FROM upload_pipeline.document_chunks 
                    WHERE document_id = $1
                    ORDER BY chunk_ord
                """, document_id)
                
                if not chunks:
                    raise ValueError(f"No chunks found for document {document_id}")
                
                chunk_texts = [chunk["text"] for chunk in chunks]
            
            # Call real OpenAI service for embeddings
            embeddings = await self.enhanced_service_client.call_openai_service(
                texts=chunk_texts,
                user_id=user_id,
                job_id=str(job_id),
                document_id=str(document_id),
                correlation_id=correlation_id
            )
            
            # Store embeddings in database
            async with self.db.get_db_connection() as conn:
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    await conn.execute("""
                        UPDATE upload_pipeline.document_chunks 
                        SET embedding = $1, updated_at = now()
                        WHERE chunk_id = $2
                    """, embedding, chunk["chunk_id"])
                
                # Update job status
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'embeddings_stored', state = 'completed', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
            self.logger.info(
                "Embeddings processing completed successfully",
                correlation_id=correlation_id,
                job_id=str(job_id), 
                document_id=str(document_id),
                embedding_count=len(embeddings)
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
        """Update job state in database"""
        try:
            async with self.db.get_db_connection() as conn:
                if error_message:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs
                        SET state = $1, last_error = $2, updated_at = now()
                        WHERE job_id = $3
                    """, state, json.dumps({"error": error_message, "timestamp": datetime.utcnow().isoformat()}), job_id)
                else:
                    await conn.execute("""
                        UPDATE upload_pipeline.upload_jobs
                        SET state = $1, updated_at = now()
                        WHERE job_id = $2
                    """, state, job_id)
        except Exception as e:
<<<<<<< HEAD
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
            await self._schedule_job_retry(job, f"{error_type}: {error_message}", correlation_id)
        else:
            await self._mark_job_failed(job, f"{error_type}: {error_message}", correlation_id)
    
    async def _handle_worker_error(self, error: Exception):
        """Handle worker-level errors with circuit breaker logic"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        # Check if circuit should be opened
        if self.failure_count >= 5:  # Open circuit after 5 failures
            self.circuit_open = True
=======
>>>>>>> 17059bea829e425cbc75d16d069994640a564c4c
            self.logger.error(
                "Failed to update job state",
                correlation_id=correlation_id,
                job_id=job_id,
                state=state,
                error=str(e)
            )
            raise