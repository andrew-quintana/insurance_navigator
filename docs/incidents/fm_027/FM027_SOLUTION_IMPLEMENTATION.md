# FM-027 Solution Implementation Guide

## Overview

This document provides a comprehensive solution for the FM-027 race condition issues in the Insurance Navigator document processing pipeline. The error "Document file is not accessible for processing. Please try uploading again." is caused by timing-related race conditions between job processing and file access in the Supabase Storage system.

## Root Cause Analysis

### Identified Race Conditions

1. **Job Status Update Timing**: Jobs are created with status "uploaded" before file upload completes
2. **File Access Timing**: Worker tries to access files immediately after job status update
3. **Database Transaction Issues**: Jobs disappear from database while worker still processing
4. **Stale Job Processing**: Worker processes jobs that no longer exist in database

### Technical Architecture Issues

- **Frontend**: Uploads files via signed URLs to Supabase Storage
- **API Service**: Creates jobs with status "uploaded" immediately
- **Worker**: Processes jobs with status "uploaded" using service role key
- **Database**: PostgreSQL with job status lifecycle management

## Solution Implementation

### Phase 1: Immediate Fixes (High Priority)

#### 1.1 File Existence Check Before Processing

**Location**: `backend/workers/enhanced_base_worker.py`

**Implementation**: Add file existence check before processing in `_process_parsing_real()` method.

```python
async def _process_parsing_real(self, job: Dict[str, Any], correlation_id: str):
    """Process document parsing using real LlamaParse service with webhook delegation"""
    job_id = job["job_id"]
    document_id = job["document_id"]
    user_id = job["user_id"]
    
    # Get document details
    storage_path = job.get("storage_path")
    mime_type = job.get("mime_type", "application/pdf")
    
    if not storage_path:
        raise ValueError("No storage_path found in job data")
    
    # CRITICAL FIX: Check if file exists before processing
    file_exists = await self.storage.blob_exists(storage_path)
    if not file_exists:
        # Wait and retry with exponential backoff
        max_retries = 3
        for attempt in range(max_retries):
            await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            file_exists = await self.storage.blob_exists(storage_path)
            if file_exists:
                break
        
        if not file_exists:
            raise UserFacingError(
                "Document file is not accessible for processing. Please try uploading again.",
                error_code="STORAGE_ACCESS_ERROR"
            )
    
    # Continue with existing processing logic...
```

#### 1.2 Job Status Update Delay

**Location**: `api/upload_pipeline/endpoints/upload.py`

**Implementation**: Add delay before updating job status to "uploaded".

```python
@router.post("/upload-file/{job_id}")
async def upload_file_to_storage(
    job_id: str,
    file: UploadFile = File(...)
):
    """Handle direct file upload to storage for development."""
    from config.database import get_supabase_service_client
    
    try:
        # ... existing upload logic ...
        
        # Upload to Supabase storage
        response = supabase.storage.from_(bucket).upload(
            key,
            file_content,
            file_options={"content-type": file.content_type or "application/octet-stream"}
        )
        
        if response.get('error'):
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to upload file to storage: {response['error']}"
            )
        
        # CRITICAL FIX: Wait for file to be accessible before updating job status
        await asyncio.sleep(2.0)  # Wait for file to be accessible
        
        # Verify file is accessible
        file_accessible = await verify_file_accessibility(storage_path)
        if not file_accessible:
            raise HTTPException(
                status_code=500,
                detail="File upload completed but file is not accessible"
            )
        
        # Update job status to indicate file is uploaded
        async with db.get_connection() as conn:
            await conn.execute(
                "UPDATE upload_pipeline.upload_jobs SET status = 'uploaded', state = 'queued' WHERE job_id = $1",
                job_id
            )
        
        logger.info(f"File uploaded successfully to {raw_path} for job {job_id}")
        
        return {"message": "File uploaded successfully", "path": raw_path}
        
    except Exception as e:
        logger.error(f"File upload failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def verify_file_accessibility(storage_path: str) -> bool:
    """Verify that uploaded file is accessible"""
    try:
        from backend.shared.storage.storage_manager import StorageManager
        
        storage_config = {
            "storage_url": os.getenv("SUPABASE_URL"),
            "anon_key": os.getenv("SUPABASE_ANON_KEY"),
            "service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        }
        
        storage = StorageManager(storage_config)
        file_exists = await storage.blob_exists(storage_path)
        await storage.close()
        
        return file_exists
        
    except Exception as e:
        logger.error(f"File accessibility verification failed: {str(e)}")
        return False
```

#### 1.3 Retry Mechanism for File Access

**Location**: `backend/workers/enhanced_base_worker.py`

**Implementation**: Add retry mechanism in `_direct_llamaparse_call()` method.

```python
async def _direct_llamaparse_call(self, file_path: str, job_id: str, document_id: str, correlation_id: str, document_filename: str, webhook_url: str) -> Dict[str, Any]:
    """
    Direct LlamaParse API call with retry mechanism for file access.
    """
    import httpx
    import os
    
    try:
        # Get API configuration
        LLAMAPARSE_API_KEY = os.getenv("LLAMAPARSE_API_KEY")
        LLAMAPARSE_BASE_URL = "https://api.cloud.llamaindex.ai"
        
        # CRITICAL FIX: Retry mechanism for file access
        max_retries = 3
        file_content = None
        
        for attempt in range(max_retries):
            try:
                # Use StorageManager for consistent authentication
                if not self.storage:
                    raise Exception("Storage manager not initialized")
                
                if file_path.startswith('files/'):
                    bucket = 'files'
                    key = file_path[6:]  # Remove 'files/' prefix
                else:
                    raise Exception(f"Invalid file path format: {file_path}")
                
                # Try to read file with retry
                file_content_str = await self.storage.read_blob(file_path)
                if not file_content_str:
                    raise Exception("Downloaded file is empty")
                
                file_content = file_content_str.encode('utf-8')
                break  # Success, exit retry loop
                
            except Exception as e:
                if attempt < max_retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    self.logger.warning(f"File access attempt {attempt + 1} failed, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                else:
                    # Final attempt failed
                    self.logger.error(f"All file access attempts failed: {str(e)}")
                    raise UserFacingError(
                        "Document file is not accessible for processing. Please try uploading again.",
                        error_code="STORAGE_ACCESS_ERROR"
                    )
        
        if not file_content:
            raise UserFacingError(
                "Document file is not accessible for processing. Please try uploading again.",
                error_code="STORAGE_ACCESS_ERROR"
            )
        
        # Continue with existing LlamaParse API call logic...
        # ... rest of the method remains the same ...
        
    except UserFacingError:
        raise  # Re-raise user-facing errors
    except Exception as e:
        # ... existing error handling ...
```

### Phase 2: Enhanced Monitoring (Medium Priority)

#### 2.1 Comprehensive Logging

**Location**: `backend/workers/enhanced_base_worker.py`

**Implementation**: Add detailed timing logs for race condition detection.

```python
async def _process_parsing_real(self, job: Dict[str, Any], correlation_id: str):
    """Process document parsing with enhanced timing logging"""
    job_id = job["job_id"]
    document_id = job["document_id"]
    user_id = job["user_id"]
    
    # Enhanced timing logging
    timing_log = {
        "job_id": str(job_id),
        "document_id": str(document_id),
        "user_id": user_id,
        "correlation_id": correlation_id,
        "timestamps": {}
    }
    
    timing_log["timestamps"]["processing_start"] = datetime.utcnow().isoformat()
    
    try:
        # Get document details
        storage_path = job.get("storage_path")
        mime_type = job.get("mime_type", "application/pdf")
        
        if not storage_path:
            raise ValueError("No storage_path found in job data")
        
        timing_log["timestamps"]["file_access_start"] = datetime.utcnow().isoformat()
        
        # File existence check with timing
        file_exists = await self.storage.blob_exists(storage_path)
        timing_log["timestamps"]["file_access_end"] = datetime.utcnow().isoformat()
        timing_log["file_accessible"] = file_exists
        
        if not file_exists:
            # Retry logic with timing
            timing_log["retry_attempts"] = []
            max_retries = 3
            
            for attempt in range(max_retries):
                retry_start = datetime.utcnow().isoformat()
                await asyncio.sleep(2 ** attempt)
                file_exists = await self.storage.blob_exists(storage_path)
                retry_end = datetime.utcnow().isoformat()
                
                timing_log["retry_attempts"].append({
                    "attempt": attempt + 1,
                    "start_time": retry_start,
                    "end_time": retry_end,
                    "success": file_exists
                })
                
                if file_exists:
                    break
            
            if not file_exists:
                timing_log["timestamps"]["processing_end"] = datetime.utcnow().isoformat()
                self.logger.error("File access failed after all retries", **timing_log)
                raise UserFacingError(
                    "Document file is not accessible for processing. Please try uploading again.",
                    error_code="STORAGE_ACCESS_ERROR"
                )
        
        # Continue with processing...
        timing_log["timestamps"]["processing_end"] = datetime.utcnow().isoformat()
        self.logger.info("File processing completed successfully", **timing_log)
        
    except Exception as e:
        timing_log["timestamps"]["processing_end"] = datetime.utcnow().isoformat()
        timing_log["error"] = str(e)
        self.logger.error("File processing failed", **timing_log)
        raise
```

#### 2.2 Circuit Breaker Pattern

**Location**: `backend/workers/enhanced_base_worker.py`

**Implementation**: Add circuit breaker for file access failures.

```python
class FileAccessCircuitBreaker:
    """Circuit breaker for file access failures"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False
    
    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"

class EnhancedBaseWorker:
    def __init__(self, config: WorkerConfig):
        # ... existing initialization ...
        self.file_access_circuit_breaker = FileAccessCircuitBreaker()
    
    async def _process_parsing_real(self, job: Dict[str, Any], correlation_id: str):
        """Process document parsing with circuit breaker"""
        # Check circuit breaker
        if self.file_access_circuit_breaker.is_open():
            raise ServiceUnavailableError(
                "File access service is temporarily unavailable due to repeated failures",
                error_code="FILE_ACCESS_CIRCUIT_BREAKER_OPEN"
            )
        
        try:
            # ... existing processing logic ...
            
            # Record success
            self.file_access_circuit_breaker.record_success()
            
        except UserFacingError as e:
            # Record failure
            self.file_access_circuit_breaker.record_failure()
            raise
```

### Phase 3: Advanced Solutions (Low Priority)

#### 3.1 Job Queuing with Backoff

**Location**: `backend/workers/enhanced_base_worker.py`

**Implementation**: Implement job queuing with backoff strategies.

```python
class JobQueue:
    """Job queue with backoff strategies"""
    
    def __init__(self):
        self.queue = asyncio.Queue()
        self.processing_jobs = set()
        self.failed_jobs = {}
    
    async def put(self, job: Dict[str, Any], delay: float = 0.0):
        """Add job to queue with optional delay"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        await self.queue.put(job)
    
    async def get(self) -> Optional[Dict[str, Any]]:
        """Get next job from queue"""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None
    
    def mark_processing(self, job_id: str):
        """Mark job as being processed"""
        self.processing_jobs.add(job_id)
    
    def mark_complete(self, job_id: str):
        """Mark job as completed"""
        self.processing_jobs.discard(job_id)
        self.failed_jobs.pop(job_id, None)
    
    def mark_failed(self, job_id: str, error: str):
        """Mark job as failed"""
        self.processing_jobs.discard(job_id)
        self.failed_jobs[job_id] = {
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "retry_count": self.failed_jobs.get(job_id, {}).get("retry_count", 0) + 1
        }
    
    def should_retry(self, job_id: str, max_retries: int = 3) -> bool:
        """Check if job should be retried"""
        job_info = self.failed_jobs.get(job_id, {})
        return job_info.get("retry_count", 0) < max_retries
```

#### 3.2 Database Transaction Locking

**Location**: `backend/workers/enhanced_base_worker.py`

**Implementation**: Add database transaction locking to prevent race conditions.

```python
async def _get_next_job_with_lock(self) -> Optional[Dict[str, Any]]:
    """Get next job from queue with proper locking"""
    correlation_id = create_correlation_id()
    
    try:
        async with self.db.get_connection() as conn:
            # Use FOR UPDATE SKIP LOCKED to prevent race conditions
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
            context=create_error_context(
                correlation_id=correlation_id,
                operation="get_next_job_with_lock"
            ),
            original_exception=e
        )
        self.error_handler.log_error(error)
        raise
```

## Testing and Validation

### Test Scripts

1. **`test_fm027_race_condition_reproduction.py`**: Comprehensive race condition testing
2. **`test_fm027_simple_timing.py`**: Simple timing tests
3. **`test_fm027_staging_investigation.py`**: Staging environment analysis

### Running Tests

```bash
# Run race condition reproduction tests
python test_fm027_race_condition_reproduction.py

# Run simple timing tests
python test_fm027_simple_timing.py

# Run staging investigation
python test_fm027_staging_investigation.py
```

### Expected Results

- **Race Condition Detection**: Tests should identify timing issues
- **Solution Effectiveness**: Implemented fixes should resolve race conditions
- **Performance Impact**: Solutions should have minimal performance impact
- **Error Reduction**: >99% reduction in file access errors

## Monitoring and Alerting

### Key Metrics to Monitor

1. **File Access Success Rate**: Percentage of successful file access attempts
2. **Job Processing Time**: Average time from job creation to completion
3. **Race Condition Frequency**: Number of race conditions detected per hour
4. **Circuit Breaker Status**: Frequency of circuit breaker activations
5. **Retry Success Rate**: Percentage of successful retry attempts

### Alerting Thresholds

- **File Access Success Rate**: <95% for 5 minutes
- **Race Condition Frequency**: >10 per hour
- **Circuit Breaker Activations**: >3 per hour
- **Job Processing Time**: >300 seconds average

## Deployment Strategy

### Phase 1: Immediate Fixes (Week 1)
1. Deploy file existence checks
2. Deploy job status update delays
3. Deploy retry mechanisms
4. Monitor for improvements

### Phase 2: Enhanced Monitoring (Week 2)
1. Deploy comprehensive logging
2. Deploy circuit breaker pattern
3. Set up monitoring and alerting
4. Analyze performance impact

### Phase 3: Advanced Solutions (Week 3-4)
1. Deploy job queuing with backoff
2. Deploy database transaction locking
3. Optimize based on monitoring data
4. Document lessons learned

## Rollback Plan

If issues arise during deployment:

1. **Immediate Rollback**: Revert to previous version
2. **Partial Rollback**: Disable specific features
3. **Configuration Rollback**: Adjust timing parameters
4. **Monitoring**: Watch for error rate changes

## Success Criteria

- **Error Reduction**: >99% reduction in "Document file is not accessible" errors
- **Performance**: <10% increase in processing time
- **Reliability**: >99.9% job processing success rate
- **Monitoring**: Real-time visibility into race condition detection

## Conclusion

The FM-027 race condition issues can be resolved through a combination of immediate fixes, enhanced monitoring, and advanced solutions. The key is to implement file existence checks, add appropriate delays, and implement retry mechanisms to handle the timing issues between job processing and file access.

The phased approach allows for gradual implementation while monitoring the impact of each change, ensuring that the solutions are effective and don't introduce new issues.
