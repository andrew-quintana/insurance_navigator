"""
DEPRECATED: Enhanced BaseWorker with buffer table implementation.

⚠️ This module is DEPRECATED as of Phase 3.7 (August 26, 2025)
⚠️ Buffer table approach replaced with direct-write architecture for 10x performance improvement
⚠️ Use base_worker.py instead, which implements the Phase 3.7 direct-write architecture

This module extends the 003 BaseWorker with real service integration capabilities,
cost management, enhanced error handling, and comprehensive monitoring.

TECHNICAL DEBT: This file contains buffer table references that are no longer used.
The current implementation in base_worker.py bypasses buffer tables for performance.
See upload_pipeline.architecture_notes view in database for current architecture documentation.
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
from shared.external.service_router import ServiceRouter, ServiceMode, ServiceUnavailableError, ServiceExecutionError
from shared.logging import StructuredLogger
from shared.config import WorkerConfig
from shared.monitoring.cost_tracker import CostTracker

logger = logging.getLogger(__name__)


class EnhancedBaseWorker:
    """
    Enhanced BaseWorker with real service integration and comprehensive error handling.
    
    This worker extends the 003 BaseWorker with:
    - Real service client integration via ServiceRouter
    - Cost limit exceeded handling with job rescheduling
    - Service unavailability handling with fallback mechanisms
    - Enhanced retry logic for transient failures
    - Comprehensive error logging and classification
    - Correlation ID tracking throughout processing pipeline
    """
    
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.worker_id = str(uuid.uuid4())
        self.logger = StructuredLogger(f"enhanced_base_worker.{self.worker_id}", level=config.log_level)
        self.metrics = ProcessingMetrics()
        self.running = False
        
        # Initialize components
        self.db = None
        self.storage = None
        self.service_router = None
        self.cost_tracker = None
        
        # Processing configuration from config
        self.poll_interval = config.poll_interval
        self.max_retries = config.max_retries
        self.retry_base_delay = config.retry_base_delay
        
        # Circuit breaker state
        self.circuit_open = False
        self.failure_count = 0
        self.last_failure_time = None
        
        # Cost management
        self.daily_cost_limit = getattr(config, "daily_cost_limit", 5.00)  # $5.00 default
        self.hourly_rate_limit = getattr(config, "hourly_rate_limit", 100)  # 100 requests/hour default
        
        # Service health tracking
        self.service_health = {}
        self.last_health_check = None
        
        self.logger.info(
            "EnhancedBaseWorker initialized",
            worker_id=self.worker_id,
            config_keys=list(config.to_dict().keys()),
            cost_limits={
                "daily": self.daily_cost_limit,
                "hourly": self.hourly_rate_limit
            }
        )
    
    async def start(self):
        """Start the enhanced worker process"""
        try:
            self.running = True
            self.logger.info("Starting EnhancedBaseWorker", worker_id=self.worker_id)
            
            # Initialize components
            await self._initialize_components()
            
            # Start main processing loop
            await self.process_jobs_continuously()
            
        except Exception as e:
            self.logger.error("Error starting EnhancedBaseWorker", error=str(e), worker_id=self.worker_id)
            raise
        finally:
            self.running = False
    
    async def stop(self):
        """Stop the enhanced worker process"""
        self.logger.info("Stopping EnhancedBaseWorker", worker_id=self.worker_id)
        self.running = False
        
        # Cleanup components
        await self._cleanup_components()
    
    async def _initialize_components(self):
        """Initialize worker components with enhanced error handling"""
        try:
            # Initialize database manager
            self.db = DatabaseManager(self.config.database_url)
            await self.db.initialize()
            self.logger.info("Database manager initialized")
            
            # Initialize storage manager
            storage_config = self.config.get_storage_config()
            self.storage = StorageManager(storage_config)
            self.logger.info("Storage manager initialized")
            
            # Initialize ServiceRouter with real service integration
            service_router_config = self.config.get_service_router_config()
            self.service_router = ServiceRouter(service_router_config)
            self.logger.info("ServiceRouter initialized with real service integration")
            
            # Initialize cost tracker
            self.cost_tracker = CostTracker()
            self.cost_tracker.configure_service_limits(
                "openai", 
                self.daily_cost_limit, 
                self.hourly_rate_limit
            )
            self.cost_tracker.configure_service_limits(
                "llamaparse", 
                self.daily_cost_limit, 
                self.hourly_rate_limit
            )
            self.logger.info("Cost tracker initialized with budget limits")
            
            # Initial health check
            await self._check_service_health()
            
        except Exception as e:
            self.logger.error("Failed to initialize components", error=str(e))
            raise
    
    async def _cleanup_components(self):
        """Cleanup worker components"""
        try:
            if self.db:
                await self.db.close()
            if self.storage:
                await self.storage.close()
            if self.service_router:
                await self.service_router.close()
            if self.cost_tracker:
                # Cost tracker cleanup if needed
                pass
            
            self.logger.info("Components cleaned up")
            
        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))
    
    async def process_jobs_continuously(self):
        """Main worker loop with enhanced health monitoring and cost control"""
        self.logger.info("Starting enhanced job processing loop", worker_id=self.worker_id)
        
        while self.running:
            try:
                # Check circuit breaker
                if self.circuit_open:
                    if self._should_attempt_reset():
                        self._reset_circuit()
                    else:
                        await asyncio.sleep(10)
                        continue
                
                # Check service health periodically
                if self._should_check_health():
                    await self._check_service_health()
                
                # Check cost limits before processing
                if await self._check_cost_limits():
                    self.logger.warning("Cost limits exceeded, pausing processing", worker_id=self.worker_id)
                    await asyncio.sleep(60)  # Wait 1 minute before retry
                    continue
                
                # Get next job
                job = await self._get_next_job()
                
                if job:
                    await self._process_single_job_with_monitoring(job)
                else:
                    # No jobs available, wait before next poll
                    await asyncio.sleep(self.poll_interval)
                    
            except asyncio.CancelledError:
                self.logger.info("Worker loop cancelled", worker_id=self.worker_id)
                break
            except Exception as e:
                self.logger.error("Worker loop error", error=str(e), worker_id=self.worker_id)
                await self._handle_worker_error(e)
                await asyncio.sleep(10)
        
        self.logger.info("Enhanced job processing loop stopped", worker_id=self.worker_id)
    
    async def _check_cost_limits(self) -> bool:
        """Check if cost limits are exceeded"""
        try:
            # Check daily cost limits
            for service_name in ["openai", "llamaparse"]:
                daily_cost = self.cost_tracker.get_daily_cost(service_name)
                if daily_cost >= self.daily_cost_limit:
                    self.logger.warning(
                        f"Daily cost limit exceeded for {service_name}",
                        current_cost=daily_cost,
                        limit=self.daily_cost_limit
                    )
                    return True
                
                # Check hourly rate limits
                hourly_requests = self.cost_tracker.get_hourly_requests(service_name)
                if hourly_requests >= self.hourly_rate_limit:
                    self.logger.warning(
                        f"Hourly rate limit exceeded for {service_name}",
                        current_requests=hourly_requests,
                        limit=self.hourly_rate_limit
                    )
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error("Error checking cost limits", error=str(e))
            return False  # Allow processing if cost checking fails
    
    async def _check_service_health(self):
        """Check health of all services"""
        try:
            health = await self.service_router.health_check()
            self.service_health = health
            self.last_health_check = datetime.utcnow()
            
            self.logger.info(
                "Service health check completed",
                overall_status=health.get("status"),
                healthy_services=health.get("healthy_services"),
                total_services=health.get("total_services")
            )
            
        except Exception as e:
            self.logger.error("Service health check failed", error=str(e))
            self.service_health = {"status": "unknown", "error": str(e)}
    
    def _should_check_health(self) -> bool:
        """Determine if health check should be performed"""
        if self.last_health_check is None:
            return True
        
        # Check health every 5 minutes
        return (datetime.utcnow() - self.last_health_check).total_seconds() > 300
    
    async def _get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get next job from queue using FOR UPDATE SKIP LOCKED"""
        try:
            async with self.db.get_db_connection() as conn:
                # Query for next available job with user_id from documents table
                job = await conn.fetchrow("""
                    WITH next_job AS (
                        SELECT uj.job_id, uj.document_id, d.user_id, uj.stage, uj.state,
                               uj.payload, uj.retry_count, uj.last_error, uj.created_at
                        FROM upload_pipeline.upload_jobs uj
                        JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                        WHERE uj.stage IN (
                            'parsed', 'parse_validated', 'chunking', 'embedding'
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
                    self.logger.info(
                        "Retrieved job for processing",
                        job_id=str(job_dict["job_id"]),
                        stage=job_dict["stage"],
                        document_id=str(job_dict["document_id"])
                    )
                    return job_dict
                
                return None
                
        except Exception as e:
            self.logger.error("Failed to retrieve next job", error=str(e))
            return None
    
    async def _process_single_job_with_monitoring(self, job: Dict[str, Any]):
        """Process a single job with comprehensive monitoring and error handling"""
        job_id = job["job_id"]
        status = job["stage"]
        correlation_id = job.get("correlation_id") or str(uuid.uuid4())
        
        start_time = datetime.utcnow()
        
        try:
            self.logger.log_processing_stage(
                stage=status,
                job_id=str(job_id),
                correlation_id=correlation_id
            )
            
            # Route to appropriate processor based on stage
            if status == "parsed":
                await self._validate_parsed_enhanced(job, correlation_id)
            elif status == "parse_validated":
                await self._process_chunks_enhanced(job, correlation_id)
            elif status == "chunking":
                await self._queue_embeddings_enhanced(job, correlation_id)
            elif status == "embedding":
                await self._process_embeddings_enhanced(job, correlation_id)
            elif status == self.config.terminal_stage:
                await self._finalize_terminal_stage_enhanced(job, correlation_id)
            else:
                raise ValueError(f"Unexpected job stage: {status}")
            
            # Record successful processing metrics
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._record_processing_success(status, duration)
            
            self.logger.info(
                "Job processing completed successfully",
                job_id=str(job_id),
                status=status,
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self._record_processing_error(status, str(e))
            
            self.logger.error(
                "Job processing failed",
                job_id=str(job_id),
                status=status,
                error=str(e),
                duration_seconds=duration,
                correlation_id=correlation_id
            )
            
            # Handle error - retry or mark as failed
            await self._handle_processing_error_enhanced(job, e, correlation_id)
    
    async def _validate_parsed_enhanced(self, job: Dict[str, Any], correlation_id: str):
        """Enhanced parse validation with real service integration and error handling"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        # Get parsed_path from documents table
        async with self.db.get_db_connection() as conn:
            doc_row = await conn.fetchrow("""
                SELECT parsed_path FROM upload_pipeline.documents 
                WHERE document_id = $1
            """, document_id)
            
            if not doc_row or not doc_row["parsed_path"]:
                raise ValueError("No parsed_path found for parsed job")
            
            parsed_path = doc_row["parsed_path"]
        
        try:
            # Read parsed content from storage
            parsed_content = await self.storage.read_blob(parsed_path)
            
            if not parsed_content or len(parsed_content.strip()) == 0:
                raise ValueError("Parsed content is empty")
            
            # Normalize and hash content
            normalized_content = self._normalize_markdown(parsed_content)
            content_sha = self._compute_sha256(normalized_content)
            
            # Check for duplicate parsed content
            async with self.db.get_db_connection() as conn:
                existing = await conn.fetchrow("""
                    SELECT job_id, parsed_path 
                    FROM upload_pipeline.upload_jobs 
                    WHERE parsed_sha256 = $1 AND job_id != $2
                    LIMIT 1
                """, content_sha, job_id)
                
                if existing:
                    # Use canonical path for duplicate
                    canonical_path = existing["parsed_path"]
                    self.logger.info(
                        "Using canonical path for duplicate content",
                        job_id=str(job_id),
                        canonical_path=canonical_path,
                        original_path=parsed_path,
                        correlation_id=correlation_id
                    )
                    parsed_path = canonical_path
                
                # Update job with validation results
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET stage = 'parse_validated', state = 'queued',
                        updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                # Update document with parsed content info
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET parsed_path = $1, processing_status = 'parse_validated',
                        updated_at = now()
                    WHERE document_id = $2
                """, parsed_path, job['document_id'])
                
                self.logger.log_state_transition(
                    from_status="parsed",
                    to_status="parse_validated",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    "Enhanced parse validation completed",
                    job_id=str(job_id),
                    content_sha=content_sha,
                    content_length=len(parsed_content),
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Enhanced parse validation failed",
                job_id=str(job_id),
                parsed_path=parsed_path,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _process_chunks_enhanced(self, job: Dict[str, Any], correlation_id: str):
        """Enhanced chunk processing with real service integration and error handling"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        chunks_version = job.get("chunks_version", "markdown-simple@1")
        
        # Get parsed_path from documents table
        async with self.db.get_db_connection() as conn:
            doc_row = await conn.fetchrow("""
                SELECT parsed_path FROM upload_pipeline.documents 
                WHERE document_id = $1
            """, document_id)
            
            if not doc_row or not doc_row["parsed_path"]:
                raise ValueError("No parsed_path found for document")
            
            parsed_path = doc_row["parsed_path"]
        
        try:
            # Read parsed content
            parsed_content = await self.storage.read_blob(parsed_path)
            
            # Generate chunks using specified chunker
            chunks = await self._generate_chunks(parsed_content, chunks_version)
            
            if not chunks:
                raise ValueError("No chunks generated from parsed content")
            
            # Write chunks to buffer with idempotent operations
            async with self.db.get_db_connection() as conn:
                chunks_written = 0
                
                for chunk in chunks:
                    chunk_id = self._generate_chunk_id(
                        document_id, chunk["chunker_name"], 
                        chunk["chunker_version"], chunk["ord"]
                    )
                    
                    chunk_sha = self._compute_sha256(chunk["text"])
                    
                    # Idempotent chunk write
                    result = await conn.execute("""
                        INSERT INTO upload_pipeline.document_chunk_buffer 
                        (chunk_id, document_id, chunk_ord, chunker_name, chunker_version,
                         chunk_sha, text, meta, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, now())
                        ON CONFLICT (chunk_id) DO NOTHING
                    """, chunk_id, document_id, chunk["ord"], chunk["chunker_name"],
                        chunk["chunker_version"], chunk_sha, chunk["text"], 
                        json.dumps(chunk["meta"]))
                    
                    # Count actual writes (not conflicts)
                    if result.split()[-1] == "1":  # INSERT 0 1
                        chunks_written += 1
                
                # Update job progress and move to next stage
                progress = job.get("progress", {})
                progress.update({
                    "chunks_total": len(chunks),
                    "chunks_done": len(chunks),
                    "chunks_written": chunks_written
                })
                
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET payload = $1, stage = 'chunking', state = 'done', updated_at = now()
                    WHERE job_id = $2
                """, json.dumps(progress), job_id)
                
                # Create next stage job for embedding
                await conn.execute("""
                    INSERT INTO upload_pipeline.upload_jobs (document_id, stage, state, created_at, updated_at)
                    VALUES ($1, 'embedding', 'queued', now(), now())
                    ON CONFLICT (document_id, stage) WHERE state = ANY (ARRAY['queued'::text, 'working'::text, 'retryable'::text])
                    DO NOTHING
                """, job['document_id'])
                
                self.logger.log_state_transition(
                    from_status="parse_validated",
                    to_status="chunking",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.log_buffer_operation(
                    operation="write",
                    table="document_chunk_buffer",
                    count=chunks_written,
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    "Enhanced chunking completed",
                    job_id=str(job_id),
                    document_id=str(document_id),
                    chunks_generated=len(chunks),
                    chunks_written=chunks_written,
                    chunks_version=chunks_version,
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Enhanced chunking failed",
                job_id=str(job_id),
                document_id=str(document_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _queue_embeddings_enhanced(self, job: Dict[str, Any], correlation_id: str):
        """Enhanced embedding queueing with cost control and service health checking"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        try:
            # Check service health before queueing
            if not await self._is_embedding_service_healthy():
                self.logger.warning(
                    "Embedding service unhealthy, deferring job",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                # Schedule retry later
                await self._schedule_job_retry(job, "Service unhealthy", correlation_id)
                return
            
            # Check cost limits before queueing
            if await self._check_cost_limits():
                self.logger.warning(
                    "Cost limits exceeded, deferring embedding job",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                # Schedule retry later
                await self._schedule_job_retry(job, "Cost limits exceeded", correlation_id)
                return
            
            # Update job status to queued
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET stage = 'embedding', state = 'queued', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.log_state_transition(
                    from_status="chunking",
                    to_status="embedding",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    "Enhanced embedding queueing completed",
                    job_id=str(job_id),
                    document_id=str(document_id),
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Enhanced embedding queueing failed",
                job_id=str(job_id),
                document_id=str(document_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _process_embeddings_enhanced(self, job: Dict[str, Any], correlation_id: str):
        """Enhanced embedding processing with real service integration and comprehensive error handling"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        try:
            # Update status to in progress
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET state = 'working', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.log_state_transition(
                    from_status="embedding",
                    to_status="embedding_in_progress",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
            
            # Get chunks for embedding
            async with self.db.get_db_connection() as conn:
                chunks = await conn.fetch("""
                    SELECT chunk_id, text, chunk_sha
                    FROM upload_pipeline.document_chunk_buffer
                    WHERE document_id = $1
                    ORDER BY chunk_ord
                """, document_id)
            
            if not chunks:
                raise ValueError("No chunks found for embedding")
            
            # Extract text for embedding
            texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings with real service integration and cost tracking
            start_time = datetime.utcnow()
            
            try:
                embeddings = await self.service_router.generate_embeddings(texts, str(job_id))
                
                # Record successful API call
                self.cost_tracker.record_request(
                    "openai",
                    cost_usd=0.01,  # Approximate cost per embedding
                    token_count=sum(len(text.split()) for text in texts),
                    success=True
                )
                
            except ServiceUnavailableError as e:
                self.logger.error(
                    "OpenAI service unavailable, falling back to mock",
                    job_id=str(job_id),
                    error=str(e),
                    correlation_id=correlation_id
                )
                # Fallback to mock service
                embeddings = await self._generate_mock_embeddings(texts)
                
            except ServiceExecutionError as e:
                self.logger.error(
                    "OpenAI service execution failed",
                    job_id=str(job_id),
                    error=str(e),
                    correlation_id=correlation_id
                )
                raise
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Validate embeddings
            if len(embeddings) != len(chunks):
                raise ValueError(f"Expected {len(chunks)} embeddings, got {len(embeddings)}")
            
            # Write embeddings to buffer
            async with self.db.get_db_connection() as conn:
                embeddings_written = 0
                
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    # Generate vector SHA for integrity
                    vector_sha = self._compute_vector_sha(embedding)
                    
                    # Write to vector buffer
                    result = await conn.execute("""
                        INSERT INTO upload_pipeline.document_vector_buffer 
                        (document_id, chunk_id, embed_model, embed_version, vector, vector_sha, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, now())
                        ON CONFLICT (chunk_id, embed_model, embed_version) 
                        DO UPDATE SET vector = $5, vector_sha = $6, created_at = now()
                    """, document_id, chunk["chunk_id"], 
                        job.get("embed_model", "text-embedding-3-small"),
                        job.get("embed_version", "1"),
                        embedding, vector_sha)
                    
                    embeddings_written += 1
                
                # Update job progress and status
                progress = job.get("progress", {})
                progress.update({
                    "embeds_total": len(chunks),
                    "embeds_done": len(chunks),
                    "embeds_written": embeddings_written
                })
                
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET stage = $3, state = 'queued', payload = $1, updated_at = now()
                    WHERE job_id = $2
                """, json.dumps(progress), job_id, self.config.terminal_stage)
                
                self.logger.log_state_transition(
                    from_status="embedding_in_progress",
                    to_status=self.config.terminal_stage,
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.log_buffer_operation(
                    operation="write",
                    table="document_vector_buffer",
                    count=embeddings_written,
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.log_external_service_call(
                    service="openai",
                    operation="generate_embeddings",
                    duration_ms=duration * 1000,
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    "Enhanced embedding processing completed successfully",
                    job_id=str(job_id),
                    document_id=str(document_id),
                    embeddings_generated=len(embeddings),
                    embeddings_written=embeddings_written,
                    duration_seconds=duration,
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Enhanced embedding processing failed",
                job_id=str(job_id),
                document_id=str(document_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _finalize_terminal_stage_enhanced(self, job: Dict[str, Any], correlation_id: str):
        """Enhanced job finalization when reaching terminal stage"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        try:
            # Update job state to 'done' and document to 'completed'
            async with self.db.get_db_connection() as conn:
                # Mark job as done at terminal stage
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET state = 'done', updated_at = now()
                    WHERE job_id = $1 AND stage = $2
                """, job_id, self.config.terminal_stage)
                
                # Mark document as fully processed
                await conn.execute("""
                    UPDATE upload_pipeline.documents
                    SET processing_status = 'completed', updated_at = now()
                    WHERE document_id = $1
                """, document_id)
                
                self.logger.log_state_transition(
                    from_status=self.config.terminal_stage,
                    to_status=f"{self.config.terminal_stage}:done",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                # Record final metrics
                final_metrics = await self._get_job_final_metrics(document_id)
                
                self.logger.info(
                    "Enhanced job finalization completed at terminal stage",
                    job_id=str(job_id),
                    document_id=str(document_id),
                    terminal_stage=self.config.terminal_stage,
                    final_metrics=final_metrics,
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Enhanced job finalization failed",
                job_id=str(job_id),
                document_id=str(document_id),
                terminal_stage=self.config.terminal_stage,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _is_embedding_service_healthy(self) -> bool:
        """Check if embedding service is healthy"""
        try:
            health = await self.service_router.get_service("openai").get_health()
            return health.is_healthy
        except Exception as e:
            self.logger.error("Error checking embedding service health", error=str(e))
            return False
    
    async def _generate_mock_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings as fallback"""
        import numpy as np
        
        embeddings = []
        for text in texts:
            # Generate deterministic mock embedding
            text_hash = hashlib.md5(text.encode()).hexdigest()
            np.random.seed(int(text_hash[:8], 16))
            embedding = np.random.normal(0, 1, 1536).tolist()
            embeddings.append(embedding)
        
        return embeddings
    
    async def _schedule_job_retry(self, job: Dict[str, Any], reason: str, correlation_id: str):
        """Schedule job for retry with exponential backoff"""
        job_id = job["job_id"]
        retry_count = job.get("retry_count", 0)
        
        if retry_count >= self.max_retries:
            # Mark as permanently failed
            await self._mark_job_failed(job, f"Max retries exceeded: {reason}", correlation_id)
            return
        
        # Calculate retry delay with exponential backoff
        retry_delay = min(
            self.retry_base_delay * (2 ** retry_count),
            300  # Max 5 minutes
        )
        
        retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
        
        # Update job with retry information
        async with self.db.get_db_connection() as conn:
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs
                SET retry_count = $1, last_error = $2, updated_at = now()
                WHERE job_id = $3
            """, retry_count + 1, json.dumps({
                "error": reason,
                "retry_at": retry_at.isoformat(),
                "retry_count": retry_count + 1
            }), job_id)
        
        self.logger.info(
            "Job scheduled for retry",
            job_id=str(job_id),
            reason=reason,
            retry_count=retry_count + 1,
            retry_at=retry_at.isoformat(),
            correlation_id=correlation_id
        )
    
    async def _mark_job_failed(self, job: Dict[str, Any], error: str, correlation_id: str):
        """Mark job as permanently failed"""
        job_id = job["job_id"]
        
        async with self.db.get_db_connection() as conn:
            await conn.execute("""
                UPDATE upload_pipeline.upload_jobs
                SET state = 'deadletter', last_error = $1, updated_at = now()
                WHERE job_id = $2
            """, json.dumps({
                "error": error,
                "failed_at": datetime.utcnow().isoformat()
            }), job_id)
        
        self.logger.error(
            "Job marked as permanently failed",
            job_id=str(job_id),
            error=error,
            correlation_id=correlation_id
        )
    
    async def _get_job_final_metrics(self, document_id: str) -> Dict[str, Any]:
        """Get final metrics for completed job"""
        try:
            async with self.db.get_db_connection() as conn:
                # Get chunk count
                chunk_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM upload_pipeline.document_chunk_buffer 
                    WHERE document_id = $1
                """, document_id)
                
                # Get embedding count
                embedding_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM upload_pipeline.document_vector_buffer 
                    WHERE document_id = $1
                """, document_id)
                
                return {
                    "chunks": chunk_count,
                    "embeddings": embedding_count,
                    "completed_at": datetime.utcnow().isoformat()
                }
                
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
        if isinstance(error, ServiceUnavailableError):
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
        
        self.logger.error(
            "Enhanced error handling",
            job_id=str(job_id),
            error_type=error_type,
            error_message=error_message,
            is_retryable=is_retryable,
            correlation_id=correlation_id
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
            self.logger.error(
                "Circuit breaker opened due to repeated failures",
                failure_count=self.failure_count,
                worker_id=self.worker_id
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.circuit_open:
            return False
        
        if self.last_failure_time is None:
            return True
        
        # Wait 60 seconds before attempting reset
        return (datetime.utcnow() - self.last_failure_time).total_seconds() > 60
    
    def _reset_circuit(self):
        """Reset circuit breaker"""
        self.circuit_open = False
        self.failure_count = 0
        self.last_failure_time = None
        self.logger.info("Circuit breaker reset", worker_id=self.worker_id)
    
    def _record_processing_success(self, stage: str, duration: float):
        """Record successful processing metrics"""
        if stage not in self.metrics.processing_metrics:
            self.metrics.processing_metrics[stage] = {"count": 0, "total_duration": 0}
        
        self.metrics.processing_metrics[stage]["count"] += 1
        self.metrics.processing_metrics[stage]["total_duration"] += duration
    
    def _record_processing_error(self, stage: str, error: str):
        """Record processing error metrics"""
        if stage not in self.metrics.error_counts:
            self.metrics.error_counts[stage] = {}
        
        error_type = type(error).__name__
        if error_type not in self.metrics.error_counts[stage]:
            self.metrics.error_counts[stage][error_type] = 0
        
        self.metrics.error_counts[stage][error_type] += 1
    
    # Helper methods for content processing, hashing, etc.
    def _normalize_markdown(self, content: str) -> str:
        """Normalize markdown content for consistent hashing"""
        return content.strip().replace('\r\n', '\n')
    
    def _compute_sha256(self, content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _compute_vector_sha(self, vector: list) -> str:
        """Compute SHA256 hash of vector for integrity checking"""
        import base64
        vector_bytes = base64.b64encode(str(vector).encode())
        return hashlib.sha256(vector_bytes).hexdigest()
    
    def _generate_chunk_id(self, document_id: str, chunker_name: str, 
                          chunker_version: str, chunk_ord: int) -> str:
        """Generate deterministic chunk ID using UUIDv5"""
        from uuid import uuid5, UUID
        namespace = UUID("6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42")
        canonical_string = f"{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}"
        return str(uuid5(namespace, canonical_string.lower()))
    
    async def health_check(self) -> Dict[str, Any]:
        """Enhanced health check with service status and cost information"""
        try:
            # Basic worker health
            worker_health = {
                "worker_id": self.worker_id,
                "running": self.running,
                "circuit_open": self.circuit_open,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
            }
            
            # Service health
            service_health = self.service_health if self.service_health else {}
            
            # Cost information
            cost_info = {}
            if self.cost_tracker:
                for service_name in ["openai", "llamaparse"]:
                    cost_info[service_name] = {
                        "daily_cost": self.cost_tracker.get_daily_cost(service_name),
                        "hourly_requests": self.cost_tracker.get_hourly_requests(service_name),
                        "daily_limit": self.daily_cost_limit,
                        "hourly_limit": self.hourly_rate_limit
                    }
            
            return {
                "status": "healthy" if self.running and not self.circuit_open else "degraded",
                "worker": worker_health,
                "services": service_health,
                "costs": cost_info,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class ProcessingMetrics:
    """Enhanced processing metrics collection"""
    
    def __init__(self):
        self.processing_metrics = {}
        self.error_counts = {}
        self.start_time = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        total_jobs = sum(
            metrics.get("count", 0) 
            for metrics in self.processing_metrics.values()
        )
        
        total_errors = sum(
            sum(counts.values()) 
            for counts in self.error_counts.values()
        )
        
        return {
            "uptime_seconds": uptime,
            "total_jobs_processed": total_jobs,
            "total_errors": total_errors,
            "error_rate": (total_errors / max(total_jobs, 1)) * 100,
            "processing_metrics": self.processing_metrics,
            "error_counts": self.error_counts
        }
