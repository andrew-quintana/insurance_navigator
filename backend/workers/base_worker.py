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
from shared.external import LlamaParseClient, OpenAIClient
from shared.external.service_router import ServiceRouter, ServiceMode
from shared.logging import StructuredLogger
from shared.config import WorkerConfig

logger = logging.getLogger(__name__)

class BaseWorker:
    """Enhanced BaseWorker with comprehensive monitoring and state machine processing"""
    
    def __init__(self, config: WorkerConfig):
        self.config = config
        self.worker_id = str(uuid.uuid4())
        self.logger = StructuredLogger(f"base_worker.{self.worker_id}", level=config.log_level)
        self.metrics = ProcessingMetrics()
        self.running = False
        
        # Initialize components
        self.db = None
        self.storage = None
        self.service_router = None
        
        # Processing configuration from config
        self.poll_interval = config.poll_interval
        self.max_retries = config.max_retries
        self.retry_base_delay = config.retry_base_delay
        
        # Circuit breaker state
        self.circuit_open = False
        self.failure_count = 0
        self.last_failure_time = None
        
        self.logger.info(
            "BaseWorker initialized",
            worker_id=self.worker_id,
            config_keys=list(config.to_dict().keys())
        )
    
    async def start(self):
        """Start the worker process"""
        try:
            self.running = True
            self.logger.info("Starting BaseWorker", worker_id=self.worker_id)
            
            # Initialize components
            self.logger.info("🔧 Initializing components...", worker_id=self.worker_id)
            await self._initialize_components()
            self.logger.info("✅ Components initialized successfully", worker_id=self.worker_id)
            
            # Start main processing loop in background
            self.logger.info("🚀 Starting main processing loop in background...", worker_id=self.worker_id)
            try:
                self._processing_task = asyncio.create_task(self.process_jobs_continuously())
                self.logger.info(f"✅ Main processing loop started in background, task: {self._processing_task}", worker_id=self.worker_id)
                
                # Add error handling for the task
                def task_done_callback(task):
                    try:
                        if task.exception():
                            self.logger.error(f"❌ Processing task failed with exception: {task.exception()}", worker_id=self.worker_id)
                            import traceback
                            self.logger.error(f"❌ Full traceback: {traceback.format_exc()}", worker_id=self.worker_id)
                            # Don't set running to False here - let the main loop handle it
                        else:
                            self.logger.info("✅ Processing task completed successfully", worker_id=self.worker_id)
                    except Exception as e:
                        self.logger.error(f"❌ Error in task callback: {e}", worker_id=self.worker_id)
                
                self._processing_task.add_done_callback(task_done_callback)
                
                # Wait a moment to ensure the task starts running
                await asyncio.sleep(0.1)
                
                # Verify the task is running
                if self._processing_task.done():
                    self.logger.error("❌ Processing task completed immediately - this indicates an error", worker_id=self.worker_id)
                    if self._processing_task.exception():
                        raise self._processing_task.exception()
                    else:
                        raise RuntimeError("Processing task completed immediately without exception")
                
                self.logger.info("✅ Processing task verified as running", worker_id=self.worker_id)
                
            except Exception as e:
                self.logger.error(f"❌ Failed to create processing task: {e}", worker_id=self.worker_id)
                self.running = False
                raise
            
            # Add debug logging to confirm method is returning
            self.logger.info("🏁 start() method completing, returning to caller", worker_id=self.worker_id)
            
        except Exception as e:
            self.logger.error("❌ Error starting BaseWorker", error=str(e), worker_id=self.worker_id)
            self.running = False
            import traceback
            self.logger.error(f"❌ Full traceback: {traceback.format_exc()}", worker_id=self.worker_id)
            raise
    
    async def stop(self):
        """Stop the worker process"""
        self.logger.info("Stopping BaseWorker", worker_id=self.worker_id)
        self.running = False
        
        # Cancel processing task if running
        if hasattr(self, '_processing_task') and self._processing_task:
            self.logger.info("Cancelling processing task...", worker_id=self.worker_id)
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                self.logger.info("Processing task cancelled successfully", worker_id=self.worker_id)
        
        # Cleanup components
        await self._cleanup_components()
        
        self.logger.info("🛑 BaseWorker stopped", worker_id=self.worker_id)
    
    async def _initialize_components(self):
        """Initialize worker components"""
        try:
            # Initialize database manager
            self.db = DatabaseManager(self.config.database_url)
            await self.db.initialize()
            self.logger.info("Database manager initialized")
            
            # Initialize storage manager
            storage_config = self.config.get_storage_config()
            
            # Use mock storage for local testing
            if hasattr(self.config, 'use_mock_storage') and self.config.use_mock_storage:
                self.storage = MockStorageManager()
                self.logger.info("Mock storage manager initialized for local testing")
            else:
                self.storage = StorageManager(storage_config)
                self.logger.info("Storage manager initialized")
            
            # Initialize ServiceRouter
            service_router_config = self.config.get_service_router_config()
            self.service_router = ServiceRouter(service_router_config)
            self.logger.info("ServiceRouter initialized")
            
            # Start health monitoring after all components are initialized
            self.service_router.start_health_monitoring()
            self.logger.info("Health monitoring started")
            
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
            
            self.logger.info("Components cleaned up")
            
        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))
    
    async def process_jobs_continuously(self):
        """Main worker loop with enhanced health monitoring"""
        self.logger.info("Starting job processing loop", worker_id=self.worker_id)
        self.logger.info(f"🔍 Initial running flag: {self.running}", worker_id=self.worker_id)
        
        loop_count = 0
        while self.running:
            try:
                loop_count += 1
                self.logger.info(f"🔄 Main loop iteration {loop_count}, running={self.running}")
                
                # Check circuit breaker
                if self.circuit_open:
                    if self._should_attempt_reset():
                        self.logger.info("🔄 Attempting circuit breaker reset", worker_id=self.worker_id)
                        self._reset_circuit()
                    else:
                        self.logger.info("⏸️ Circuit breaker open, waiting...", worker_id=self.worker_id)
                        await asyncio.sleep(10)
                        continue
                
                # Get next job
                self.logger.info("🔍 Calling _get_next_job()...", worker_id=self.worker_id)
                job = await self._get_next_job()
                
                if job:
                    self.logger.info("✅ Job retrieved, processing...", worker_id=self.worker_id)
                    await self._process_single_job_with_monitoring(job)
                else:
                    # No jobs available, wait before next poll
                    self.logger.info(f"⏳ No jobs available, waiting {self.poll_interval}s...", worker_id=self.worker_id)
                    await asyncio.sleep(self.poll_interval)
                    
            except asyncio.CancelledError:
                self.logger.info("Worker loop cancelled", worker_id=self.worker_id)
                break
            except Exception as e:
                self.logger.error("❌ Worker loop error", error=str(e), worker_id=self.worker_id)
                await self._handle_worker_error(e)
                await asyncio.sleep(10)
        
        self.logger.info(f"Job processing loop stopped, final running flag: {self.running}", worker_id=self.worker_id)
    
    async def _get_next_job(self) -> Optional[Dict[str, Any]]:
        """Get next job from queue using FOR UPDATE SKIP LOCKED"""
        try:
            self.logger.info("🔍 _get_next_job() called - attempting to retrieve job")
            
            async with self.db.get_db_connection() as conn:
                self.logger.info("🔍 Database connection acquired")
                
                # Query for next available job with user_id from documents table
                self.logger.info("🔍 Executing job query...")
                job = await conn.fetchrow("""
                    WITH next_job AS (
                        SELECT uj.job_id, uj.document_id, d.user_id, uj.stage, uj.state,
                               uj.payload, uj.retry_count, uj.last_error, uj.created_at
                        FROM upload_pipeline.upload_jobs uj
                        JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
                        WHERE uj.stage IN (
                            'job_validated', 'parsing', 'parsed', 'parse_validated', 'chunking', 'chunks_buffered',
                            'embedding', 'embeddings_buffered'
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
                
                self.logger.info(f"🔍 Query executed, result: {job}")
                
                if job:
                    job_dict = dict(job)
                    self.logger.info(
                        "✅ Retrieved job for processing",
                        job_id=str(job_dict["job_id"]),
                        stage=job_dict["stage"],
                        document_id=str(job_dict["document_id"])
                    )
                    return job_dict
                else:
                    self.logger.info("⚠️ No jobs found in query")
                
                return None
                
        except Exception as e:
            self.logger.error("❌ Failed to retrieve next job", error=str(e), traceback=str(e.__traceback__))
            import traceback
            self.logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            return None
    
    async def _process_single_job_with_monitoring(self, job: Dict[str, Any]):
        """Process a single job with comprehensive monitoring"""
        job_id = job["job_id"]
        status = job["stage"] # Changed from job["status"] to job["stage"]
        correlation_id = job.get("correlation_id") or str(uuid.uuid4())
        
        start_time = datetime.utcnow()
        
        try:
            self.logger.log_processing_stage(
                stage=status,
                job_id=str(job_id),
                correlation_id=correlation_id
            )
            
            # Route to appropriate processor based on stage
            if status == "job_validated":
                await self._process_job_validated(job, correlation_id)
            elif status == "parsing":
                await self._process_parsing(job, correlation_id)
            elif status == "parsed":
                await self._validate_parsed(job, correlation_id)
            elif status == "parse_validated":
                await self._process_chunks(job, correlation_id)
            elif status == "chunks_buffered":
                await self._queue_embeddings(job, correlation_id)
            elif status in ["embedding", "embeddings_buffered"]:
                await self._process_embeddings(job, correlation_id)
            elif status == "embedded":
                await self._finalize_job(job, correlation_id)
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
            
            self.logger.log_error_with_context(
                error=e,
                context={
                    "job_id": str(job_id),
                    "status": status,
                    "duration_seconds": duration,
                    "correlation_id": correlation_id
                }
            )
            
            # Handle error - retry or mark as failed
            await self._handle_processing_error(job, e, correlation_id)
    
    async def _process_queued_job(self, job: Dict[str, Any], correlation_id: str):
        """Process queued job - initial validation and dedupe check"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        try:
            self.logger.info(
                "Processing queued job - initial validation",
                job_id=str(job_id),
                document_id=str(document_id),
                correlation_id=correlation_id
            )
            
            # TODO: Implement initial validation logic (dedupe check, etc.)
            # For now, just advance to job_validated stage
            await self._advance_job_stage(job_id, "job_validated", correlation_id)
            
        except Exception as e:
            await self._handle_processing_error(job, e, correlation_id)
            raise
    
    async def _process_job_validated(self, job: Dict[str, Any], correlation_id: str):
        """Process job_validated stage - prepare for parsing"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        try:
            self.logger.info(
                "Processing job_validated stage",
                job_id=str(job_id),
                document_id=str(document_id),
                correlation_id=correlation_id
            )
            
            # Update job stage to 'parsing' to indicate parsing preparation
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET stage = 'parsing', state = 'working', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.info(
                    "Job advanced to parsing stage",
                    job_id=str(job_id),
                    document_id=str(document_id),
                    correlation_id=correlation_id
                )
                
        except Exception as e:
            self.logger.error(
                "Failed to process job_validated stage",
                job_id=str(job_id),
                document_id=str(document_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _process_parsing(self, job: Dict[str, Any], correlation_id: str):
        """Process parsing stage - submit document to LlamaParse for parsing"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        try:
            self.logger.info(
                "Processing parsing stage",
                job_id=str(job_id),
                document_id=str(document_id),
                correlation_id=correlation_id
            )
            
            # Get document details from payload
            payload = job.get("payload", {})
            storage_path = payload.get("storage_path")
            mime_type = payload.get("mime", "application/pdf")
            
            if not storage_path:
                raise ValueError("No storage_path found in job payload")
            
            # For Phase 3.3 testing, simulate successful parsing by advancing to 'parsed' stage
            # In production, this would involve actual LlamaParse API submission and webhook handling
            self.logger.info(
                "Simulating successful parsing for Phase 3.3 testing",
                job_id=str(job_id),
                document_id=str(document_id),
                storage_path=storage_path,
                mime_type=mime_type,
                correlation_id=correlation_id
            )
            
            # Simulate parsing delay
            await asyncio.sleep(2)
            
            # Advance job to 'parsed' stage
            await self._advance_job_stage(job_id, "parsed", correlation_id)
            
            self.logger.info(
                "Job advanced to parsed stage",
                job_id=str(job_id),
                document_id=str(document_id),
                correlation_id=correlation_id
            )
            
        except Exception as e:
            self.logger.error(
                "Failed to process parsing stage",
                job_id=str(job_id),
                document_id=str(document_id),
                error=str(e),
                correlation_id=correlation_id
            )
            await self._handle_processing_error(job, e, correlation_id)
            raise
    
    async def _validate_parsed(self, job: Dict[str, Any], correlation_id: str):
        """Validate parsed content with comprehensive error checking"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        try:
            # Get parsed content information from documents table
            async with self.db.get_db_connection() as conn:
                doc_info = await conn.fetchrow("""
                    SELECT parsed_path, parsed_sha256 
                    FROM upload_pipeline.documents 
                    WHERE document_id = $1
                """, document_id)
                
                if not doc_info or not doc_info["parsed_path"]:
                    raise ValueError(f"No parsed_path found for document {document_id}")
                
                parsed_path = doc_info["parsed_path"]
                existing_sha256 = doc_info["parsed_sha256"]
            
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
                    SELECT d.document_id, d.parsed_path 
                    FROM upload_pipeline.documents d
                    WHERE d.parsed_sha256 = $1 AND d.document_id != $2
                    LIMIT 1
                """, content_sha, document_id)
                
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
                
                # Update document with validation results
                await conn.execute("""
                    UPDATE upload_pipeline.documents 
                    SET parsed_sha256 = $1, updated_at = now()
                    WHERE document_id = $2
                """, content_sha, document_id)
                
                # Update job stage to parse_validated
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET stage = 'parse_validated', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.log_state_transition(
                    from_status="parsed",
                    to_status="parse_validated",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    "Parse validation completed",
                    job_id=str(job_id),
                    content_sha=content_sha,
                    content_length=len(parsed_content),
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Parse validation failed",
                job_id=str(job_id),
                document_id=str(document_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _process_chunks(self, job: Dict[str, Any], correlation_id: str):
        """Generate chunks with comprehensive validation"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        # Get chunks_version from payload or use default
        chunks_version = job.get("chunks_version") or "markdown-simple@1"
        
        try:
            # Get parsed content information from documents table
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
                
                # Update job progress and status
                progress = job.get("progress", {})
                progress.update({
                    "chunks_total": len(chunks),
                    "chunks_done": len(chunks),
                    "chunks_written": chunks_written
                })
                
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'chunks_stored', progress = $1, updated_at = now()
                    WHERE job_id = $2
                """, json.dumps(progress), job_id)
                
                self.logger.log_state_transition(
                    from_status="parse_validated",
                    to_status="chunks_stored",
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
                    "Chunking completed successfully",
                    job_id=str(job_id),
                    chunks_generated=len(chunks),
                    chunks_written=chunks_written,
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Chunking failed",
                job_id=str(job_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _queue_embeddings(self, job: Dict[str, Any], correlation_id: str):
        """Queue job for embedding processing"""
        job_id = job["job_id"]
        
        try:
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'embedding_queued', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.log_state_transition(
                    from_status="chunks_stored",
                    to_status="embedding_queued",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    "Job queued for embedding",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Failed to queue job for embedding",
                job_id=str(job_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _process_embeddings(self, job: Dict[str, Any], correlation_id: str):
        """Process embeddings with micro-batching"""
        job_id = job["job_id"]
        document_id = job["document_id"]
        
        try:
            # Update status to in progress
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'embedding_in_progress', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.log_state_transition(
                    from_status="embedding_queued",
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
            
            # Generate embeddings with micro-batching
            start_time = datetime.utcnow()
            embeddings = await self.service_router.generate_embeddings(texts, str(job_id))
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
                    SET status = 'embeddings_stored', progress = $1, updated_at = now()
                    WHERE job_id = $2
                """, json.dumps(progress), job_id)
                
                self.logger.log_state_transition(
                    from_status="embedding_in_progress",
                    to_status="embeddings_stored",
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
                    "Embedding processing completed successfully",
                    job_id=str(job_id),
                    chunks_processed=len(chunks),
                    embeddings_generated=len(embeddings),
                    duration_seconds=duration,
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Embedding processing failed",
                job_id=str(job_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _finalize_job(self, job: Dict[str, Any], correlation_id: str):
        """Finalize job processing"""
        job_id = job["job_id"]
        
        try:
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET status = 'complete', updated_at = now()
                    WHERE job_id = $1
                """, job_id)
                
                self.logger.log_state_transition(
                    from_status="embeddings_stored",
                    to_status="complete",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.log_event(
                    event_type="finalized",
                    event_code="JOB_COMPLETED",
                    severity="info",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
                
                self.logger.info(
                    "Job finalized successfully",
                    job_id=str(job_id),
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Job finalization failed",
                job_id=str(job_id),
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _generate_chunks(self, content: str, chunker_version: str) -> List[Dict[str, Any]]:
        """Generate chunks using specified chunker"""
        # Simple markdown chunking for now
        # This could be extended with more sophisticated chunking strategies
        
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        chunk_ord = 0
        
        for line in lines:
            current_chunk.append(line)
            
            # Create chunk on heading or after certain number of lines
            if (line.startswith('#') and current_chunk) or len(current_chunk) >= 20:
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk).strip()
                    if chunk_text:
                        chunks.append({
                            "ord": chunk_ord,
                            "text": chunk_text,
                            "chunker_name": "markdown-simple",
                            "chunker_version": chunker_version,
                            "meta": {
                                "start_line": len(chunks) * 20,
                                "end_line": len(chunks) * 20 + len(current_chunk),
                                "type": "markdown"
                            }
                        })
                        chunk_ord += 1
                    current_chunk = []
        
        # Add final chunk if any content remains
        if current_chunk:
            chunk_text = '\n'.join(current_chunk).strip()
            if chunk_text:
                chunks.append({
                    "ord": chunk_ord,
                    "text": chunk_text,
                    "chunker_name": "markdown-simple",
                    "chunker_version": chunker_version,
                    "meta": {
                        "start_line": len(chunks) * 20,
                        "end_line": len(chunks) * 20 + len(current_chunk),
                        "type": "markdown"
                    }
                })
        
        return chunks
    
    def _generate_chunk_id(self, document_id: str, chunker_name: str, chunker_version: str, chunk_ord: int) -> str:
        """Generate deterministic chunk ID using UUIDv5"""
        # Use the namespace from CONTEXT002.md
        namespace = uuid.UUID('6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42')
        
        # Create canonical string
        canonical_string = f"{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}"
        
        # Generate UUIDv5
        return str(uuid.uuid5(namespace, canonical_string))
    
    def _normalize_markdown(self, content: str) -> str:
        """Normalize markdown content for consistent hashing"""
        # Basic normalization - this could be enhanced
        normalized = content.strip()
        normalized = '\n'.join(line.rstrip() for line in normalized.split('\n'))
        return normalized
    
    def _compute_sha256(self, content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _compute_vector_sha(self, vector: List[float]) -> str:
        """Compute SHA256 hash of vector for integrity verification"""
        # Convert vector to bytes for hashing
        vector_bytes = b''.join(float(x).hex().encode() for x in vector)
        return hashlib.sha256(vector_bytes).hexdigest()
    
    async def _advance_job_stage(self, job_id: str, new_stage: str, correlation_id: str):
        """Advance job to next stage"""
        try:
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs 
                    SET stage = $1, state = 'queued', updated_at = now()
                    WHERE job_id = $2
                """, new_stage, job_id)
                
                self.logger.info(
                    "Job stage advanced",
                    job_id=job_id,
                    new_stage=new_stage,
                    correlation_id=correlation_id
                )
        
        except Exception as e:
            self.logger.error(
                "Failed to advance job stage",
                job_id=job_id,
                new_stage=new_stage,
                error=str(e),
                correlation_id=correlation_id
            )
            raise
    
    async def _handle_processing_error(self, job: Dict[str, Any], error: Exception, correlation_id: str):
        """Handle processing errors with retry logic"""
        job_id = job["job_id"]
        retry_count = job.get("retry_count", 0)
        
        if retry_count >= self.max_retries:
            # Mark as permanently failed
            await self._mark_job_failed(job, error, correlation_id)
        else:
            # Schedule retry
            await self._schedule_job_retry(job, error, correlation_id)
    
    async def _mark_job_failed(self, job: Dict[str, Any], error: Exception, correlation_id: str):
        """Mark job as permanently failed"""
        job_id = job["job_id"]
        status = job["stage"] # Changed from job["status"] to job["stage"]
        
        # Determine failure status based on current stage
        if status == "parsed":
            failure_status = "failed_parse"
        elif status in ["parse_validated", "chunking", "chunks_stored"]:
            failure_status = "failed_chunking"
        elif status in ["embedding_queued", "embedding_in_progress", "embeddings_stored"]:
            failure_status = "failed_embedding"
        else:
            failure_status = "failed_unknown"
        
        try:
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET stage = $1, last_error = $2, updated_at = now()
                    WHERE job_id = $3
                """, failure_status, json.dumps({
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "failed_at": datetime.utcnow().isoformat(),
                    "correlation_id": correlation_id
                }), job_id)
                
                self.logger.log_event(
                    event_type="error",
                    event_code="JOB_FAILED_PERMANENTLY",
                    severity="error",
                    job_id=str(job_id),
                    status=failure_status,
                    error=str(error),
                    correlation_id=correlation_id
                )
                
        except Exception as e:
            self.logger.error(
                "Failed to mark job as failed",
                job_id=str(job_id),
                error=str(e),
                correlation_id=correlation_id
            )
    
    async def _schedule_job_retry(self, job: Dict[str, Any], error: Exception, correlation_id: str):
        """Schedule job for retry with exponential backoff"""
        job_id = job["job_id"]
        retry_count = job.get("retry_count", 0)
        
        # Calculate retry delay
        retry_delay = self.retry_base_delay * (2 ** retry_count)
        retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
        
        try:
            async with self.db.get_db_connection() as conn:
                await conn.execute("""
                    UPDATE upload_pipeline.upload_jobs
                    SET retry_count = $1, last_error = $2, updated_at = now()
                    WHERE job_id = $3
                """, retry_count + 1, json.dumps({
                    "error": str(error),
                    "error_type": type(error).__name__,
                    "retry_count": retry_count + 1,
                    "retry_at": retry_at.isoformat(),
                    "correlation_id": correlation_id
                }), job_id)
                
                self.logger.log_event(
                    event_type="retry",
                    event_code="JOB_RETRY_SCHEDULED",
                    severity="warn",
                    job_id=str(job_id),
                    retry_count=retry_count + 1,
                    retry_delay_seconds=retry_delay,
                    retry_at=retry_at.isoformat(),
                    correlation_id=correlation_id
                )
                
        except Exception as e:
            self.logger.error(
                "Failed to schedule job retry",
                job_id=str(job_id),
                error=str(e),
                correlation_id=correlation_id
            )
    
    async def _handle_worker_error(self, error: Exception):
        """Handle worker-level errors"""
        self.failure_count += 1
        
        if self.failure_count >= 5:  # Worker-level circuit breaker
            self.circuit_open = True
            self.last_failure_time = datetime.utcnow()
            self.logger.warning(
                "Worker circuit breaker opened",
                failure_count=self.failure_count,
                opened_at=self.last_failure_time.isoformat()
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return True
        
        time_since_failure = datetime.utcnow() - self.last_failure_time
        return time_since_failure.total_seconds() >= 60  # 1 minute recovery timeout
    
    def _reset_circuit(self):
        """Reset the circuit breaker"""
        self.circuit_open = False
        self.failure_count = 0
        self.last_failure_time = None
        self.logger.info("Worker circuit breaker reset")
    
    def _record_processing_success(self, status: str, duration: float):
        """Record successful processing metrics"""
        self.metrics.record_job_completion(True, duration)
    
    def _record_processing_error(self, status: str, error: str):
        """Record processing error metrics"""
        self.metrics.record_job_completion(False, 0.0)
    
    async def health_check(self) -> Dict[str, Any]:
        """Worker health check"""
        try:
            # Check component health
            db_health = await self.db.health_check() if self.db else {"status": "unknown"}
            storage_health = await self.storage.health_check() if self.storage else {"status": "unknown"}
            service_router_health = await self.service_router.health_check() if self.service_router else {"status": "unknown"}
            
            return {
                "status": "healthy" if self.running else "stopped",
                "worker_id": self.worker_id,
                "running": self.running,
                "circuit_open": self.circuit_open,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": self.metrics.get_summary(),
                "components": {
                    "database": db_health,
                    "storage": storage_health,
                    "service_router": service_router_health
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "worker_id": self.worker_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

class ProcessingMetrics:
    """Processing metrics collection for monitoring"""
    
    def __init__(self):
        self.jobs_processed = 0
        self.jobs_failed = 0
        self.processing_time_total = 0.0
        self.last_job_time = None
        self.stage_counts = {}
        self.error_counts = {}
    
    def record_job_completion(self, success: bool, processing_time: float):
        """Record job completion metrics"""
        if success:
            self.jobs_processed += 1
        else:
            self.jobs_failed += 1
        
        self.processing_time_total += processing_time
        self.last_job_time = datetime.utcnow()
    
    def record_stage_completion(self, stage: str):
        """Record stage completion"""
        if stage not in self.stage_counts:
            self.stage_counts[stage] = 0
        self.stage_counts[stage] += 1
    
    def record_error(self, error_type: str):
        """Record error occurrence"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        total_jobs = self.jobs_processed + self.jobs_failed
        success_rate = (self.jobs_processed / total_jobs * 100) if total_jobs > 0 else 0
        avg_processing_time = (self.processing_time_total / total_jobs) if total_jobs > 0 else 0
        
        return {
            "jobs_processed": self.jobs_processed,
            "jobs_failed": self.jobs_failed,
            "total_jobs": total_jobs,
            "success_rate": round(success_rate, 2),
            "avg_processing_time": round(avg_processing_time, 2),
            "last_job_time": self.last_job_time.isoformat() if self.last_job_time else None,
            "stage_counts": self.stage_counts,
            "error_counts": self.error_counts
        }
