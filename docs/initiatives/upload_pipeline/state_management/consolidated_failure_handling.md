# Consolidated Failure Handling - State Management Update

## Overview

This document scopes the refactoring of failure handling in the upload pipeline to consolidate all failure states into a single `state='failed'` instead of using multiple failure statuses (`failed_parse`, `failed_chunking`, `failed_embedding`). The component that failed will be stored in the `last_error` jsonb field.

## Problem Analysis

### Current State

The upload pipeline currently uses **status** field to track processing stage and failure types:

- **Processing Statuses**: `uploaded`, `parse_queued`, `parsed`, `parse_validated`, `chunking`, `chunks_stored`, `embedding_queued`, `embedding_in_progress`, `embeddings_stored`, `complete`, `duplicate`
- **Failure Statuses**: `failed_parse`, `failed_chunking`, `failed_embedding`

The **state** field is used for queue management:
- `queued` - Job waiting to be processed
- `working` - Job currently being processed
- `retryable` - Job failed but can be retried
- `done` - Job completed (success or permanent failure)
- `deadletter` - Job exceeded max retries

### Issues with Current Approach

1. **Status Field Overload**: Status is used for both processing stage AND failure type, mixing concerns
2. **Limited State Semantics**: The `state` field doesn't clearly indicate failure state
3. **Inconsistent Failure Handling**: Different failure statuses require different query patterns
4. **Component Information Loss**: The component that failed isn't explicitly tracked in error details
5. **Query Complexity**: Finding all failed jobs requires checking multiple status values

### Proposed Solution

**Consolidate failures into `state='failed'`**:
- Use `status` field only for **processing stage** (never for failures)
- Use `state='failed'` for **all failures** (regardless of which component failed)
- Store **failed component** in `last_error` jsonb field with structure:
  ```json
  {
    "component": "parse|chunking|embedding|validation|storage",
    "error": "error message",
    "error_type": "ExceptionType",
    "failed_at": "2025-01-15T10:30:00Z",
    "correlation_id": "uuid",
    "retry_count": 0,
    "retryable": true|false
  }
  ```

## Current Failure Points

### 1. Parse Failures
**Location**: `api/upload_pipeline/webhooks.py`, `backend/workers/enhanced_base_worker.py`
- Webhook failure handling sets `status='failed_parse'`
- Worker error handling sets `status='failed_parse'`
- Current `last_error` contains error message only

### 2. Chunking Failures
**Location**: `backend/workers/enhanced_base_worker.py`
- Sets `status='failed_chunking'` on chunking errors
- Current `last_error` contains error details

### 3. Embedding Failures
**Location**: `backend/workers/base_worker.py`, `backend/workers/enhanced_base_worker.py`
- Sets `status='failed_embedding'` on embedding errors
- Current `last_error` contains error details

### 4. Validation Failures
**Location**: `backend/workers/enhanced_base_worker.py`
- Currently may set validation failure status
- Needs component tracking

### 5. Storage Failures
**Location**: Various upload endpoints
- Storage upload failures need component tracking
- Currently may use generic error handling

## Proposed Changes

### 1. Status Field - Remove Failure Statuses

**Remove from valid statuses**:
- `failed_parse`
- `failed_chunking`
- `failed_embedding`

**Keep in valid statuses**:
- All processing statuses remain: `uploaded`, `parse_queued`, `parsed`, `parse_validated`, `chunking`, `chunks_stored`, `embedding_queued`, `embedding_in_progress`, `embeddings_stored`, `complete`, `duplicate`
- Optionally add `pending_upload` (from frontend upload status update initiative)

### 2. State Field - Add 'failed' State

**Add to valid states**:
- `failed` - Job failed (can be retryable or permanent)

**State transitions**:
- `queued` → `working` → `failed` (on error)
- `failed` → `queued` (if retryable)
- `failed` → `deadletter` (if max retries exceeded)
- `failed` → `done` (if permanent failure, no retry)

### 3. last_error JSONB Structure

**Standardized structure**:
```json
{
  "component": "parse|chunking|embedding|validation|storage|unknown",
  "error": "Human-readable error message",
  "error_type": "ExceptionClassName",
  "error_code": "Optional error code",
  "failed_at": "ISO 8601 timestamp",
  "correlation_id": "UUID",
  "retry_count": 0,
  "retryable": true,
  "retry_at": "ISO 8601 timestamp (if retryable)",
  "max_retries": 3,
  "details": {
    "additional_context": "Any component-specific details"
  }
}
```

**Component values**:
- `parse` - LlamaParse parsing failed
- `chunking` - Document chunking failed
- `embedding` - Vector embedding generation failed
- `validation` - Document validation failed
- `storage` - Storage upload/download failed
- `unknown` - Unknown/unexpected failure

### 4. Query Pattern Changes

**Current queries** (need updates):
```sql
-- Finding failed jobs (OLD)
SELECT * FROM upload_pipeline.upload_jobs 
WHERE status IN ('failed_parse', 'failed_chunking', 'failed_embedding')

-- Finding retryable failed jobs (OLD)
SELECT * FROM upload_pipeline.upload_jobs 
WHERE status IN ('failed_parse', 'failed_chunking', 'failed_embedding')
AND last_error->>'retryable' = 'true'
```

**New queries**:
```sql
-- Finding all failed jobs (NEW)
SELECT * FROM upload_pipeline.upload_jobs 
WHERE state = 'failed'

-- Finding retryable failed jobs (NEW)
SELECT * FROM upload_pipeline.upload_jobs 
WHERE state = 'failed'
AND last_error->>'retryable' = 'true'

-- Finding jobs by failed component (NEW)
SELECT * FROM upload_pipeline.upload_jobs 
WHERE state = 'failed'
AND last_error->>'component' = 'parse'

-- Finding parse failures (NEW)
SELECT * FROM upload_pipeline.upload_jobs 
WHERE state = 'failed'
AND (last_error->>'component' = 'parse' OR last_error->>'component' IS NULL)
AND status IN ('parse_queued', 'parsed')
```

## Implementation Plan

### Phase 1: Database Schema Updates

#### 1.1 Update Valid States Constraint
**File**: `supabase/migrations/[timestamp]_consolidate_failure_states.sql`

```sql
BEGIN;

-- Add 'failed' to valid states
ALTER TABLE upload_pipeline.upload_jobs
DROP CONSTRAINT IF EXISTS upload_jobs_state_check;

ALTER TABLE upload_pipeline.upload_jobs
ADD CONSTRAINT upload_jobs_state_check 
CHECK (state IN ('queued', 'working', 'retryable', 'done', 'deadletter', 'failed'));

-- Update state transition validation function
CREATE OR REPLACE FUNCTION upload_pipeline.validate_state_transition(
    old_state text,
    new_state text
) RETURNS boolean AS $$
BEGIN
    CASE old_state
        WHEN 'queued' THEN
            RETURN new_state IN ('working', 'done', 'failed');
        WHEN 'working' THEN
            RETURN new_state IN ('done', 'retryable', 'deadletter', 'failed');
        WHEN 'retryable' THEN
            RETURN new_state IN ('queued', 'deadletter', 'failed');
        WHEN 'failed' THEN
            RETURN new_state IN ('queued', 'done', 'deadletter');
        WHEN 'done' THEN
            RETURN new_state = 'done';
        WHEN 'deadletter' THEN
            RETURN new_state = 'deadletter';
        ELSE
            RETURN false;
    END CASE;
END;
$$ LANGUAGE plpgsql;

COMMIT;
```

#### 1.2 Update Valid Statuses Constraint
**File**: Same migration file

```sql
-- Remove failure statuses from valid statuses
ALTER TABLE upload_pipeline.upload_jobs
DROP CONSTRAINT IF EXISTS upload_jobs_status_check;

ALTER TABLE upload_pipeline.upload_jobs
ADD CONSTRAINT upload_jobs_status_check 
CHECK (status IN (
    'pending_upload',
    'uploaded', 
    'parse_queued', 
    'parsed', 
    'parse_validated', 
    'chunking', 
    'chunks_stored', 
    'embedding_queued', 
    'embedding_in_progress', 
    'embeddings_stored', 
    'complete', 
    'duplicate'
));

-- Update status transition validation function
CREATE OR REPLACE FUNCTION upload_pipeline.validate_status_transition(
    old_status text,
    new_status text
) RETURNS boolean AS $$
BEGIN
    -- Status transitions (no failure statuses)
    CASE old_status
        WHEN 'pending_upload' THEN
            RETURN new_status = 'uploaded';
        WHEN 'uploaded' THEN
            RETURN new_status = 'parse_queued';
        WHEN 'parse_queued' THEN
            RETURN new_status = 'parsed';
        WHEN 'parsed' THEN
            RETURN new_status = 'parse_validated';
        WHEN 'parse_validated' THEN
            RETURN new_status = 'chunking';
        WHEN 'chunking' THEN
            RETURN new_status = 'chunks_stored';
        WHEN 'chunks_stored' THEN
            RETURN new_status = 'embedding_queued';
        WHEN 'embedding_queued' THEN
            RETURN new_status = 'embedding_in_progress';
        WHEN 'embedding_in_progress' THEN
            RETURN new_status = 'embeddings_stored';
        WHEN 'embeddings_stored' THEN
            RETURN new_status = 'complete';
        WHEN 'complete' THEN
            RETURN new_status = 'complete'; -- Terminal
        WHEN 'duplicate' THEN
            RETURN new_status = 'duplicate'; -- Terminal
        ELSE
            RETURN false;
    END CASE;
END;
$$ LANGUAGE plpgsql;
```

#### 1.3 Data Migration - Convert Existing Failures

```sql
-- Migrate existing failed statuses to state='failed'
UPDATE upload_pipeline.upload_jobs
SET 
    state = 'failed',
    last_error = jsonb_build_object(
        'component', CASE 
            WHEN status = 'failed_parse' THEN 'parse'
            WHEN status = 'failed_chunking' THEN 'chunking'
            WHEN status = 'failed_embedding' THEN 'embedding'
            ELSE 'unknown'
        END,
        'error', COALESCE(last_error->>'error', 'Unknown error'),
        'error_type', COALESCE(last_error->>'error_type', 'Unknown'),
        'failed_at', COALESCE(last_error->>'failed_at', NOW()::text),
        'correlation_id', COALESCE(last_error->>'correlation_id', gen_random_uuid()::text),
        'retry_count', COALESCE((last_error->>'retry_count')::int, retry_count),
        'retryable', COALESCE((last_error->>'retryable')::boolean, true),
        'original_status', status -- Preserve for reference
    ),
    status = CASE 
        WHEN status = 'failed_parse' THEN 'parse_queued'
        WHEN status = 'failed_chunking' THEN 'chunking'
        WHEN status = 'failed_embedding' THEN 'embedding_queued'
        ELSE status
    END
WHERE status IN ('failed_parse', 'failed_chunking', 'failed_embedding');
```

### Phase 2: Backend Code Updates

#### 2.1 Update Models
**File**: `api/upload_pipeline/models.py`

```python
# Update valid_statuses
valid_statuses = {
    'pending_upload',
    'uploaded', 
    'parse_queued', 
    'parsed', 
    'parse_validated', 
    'chunking', 
    'chunks_stored', 
    'embedding_queued', 
    'embedding_in_progress', 
    'embeddings_stored', 
    'complete', 
    'duplicate'
}

# Update valid_states
valid_states = {
    'queued', 
    'working', 
    'retryable', 
    'done', 
    'deadletter',
    'failed'  # NEW
}
```

**File**: `backend/shared/db/models.py`

```python
# Update CheckConstraint
__table_args__ = (
    CheckConstraint(
        status.in_([
            'pending_upload',
            'uploaded', 'parse_queued', 'parsed', 'parse_validated',
            'chunking', 'chunks_stored', 'embedding_queued',
            'embedding_in_progress', 'embeddings_stored', 'complete',
            'duplicate'
        ]),
        name='valid_status'
    ),
    CheckConstraint(
        state.in_(['queued', 'working', 'retryable', 'done', 'deadletter', 'failed']),
        name='valid_state'
    ),
)
```

#### 2.2 Create Failure Helper Function
**File**: `backend/workers/failure_handler.py` (NEW)

```python
"""Centralized failure handling for upload pipeline."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import uuid


class FailureHandler:
    """Handles job failures with consistent error structure."""
    
    # Component definitions
    COMPONENT_PARSE = "parse"
    COMPONENT_CHUNKING = "chunking"
    COMPONENT_EMBEDDING = "embedding"
    COMPONENT_VALIDATION = "validation"
    COMPONENT_STORAGE = "storage"
    COMPONENT_UNKNOWN = "unknown"
    
    @staticmethod
    def create_error_details(
        component: str,
        error: Exception,
        correlation_id: str,
        retryable: bool = True,
        retry_count: int = 0,
        max_retries: int = 3,
        additional_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create standardized error details structure.
        
        Args:
            component: Component that failed (parse, chunking, embedding, etc.)
            error: Exception that occurred
            correlation_id: Correlation ID for tracing
            retryable: Whether this error is retryable
            retry_count: Current retry count
            max_retries: Maximum retry attempts
            additional_details: Any component-specific details
            
        Returns:
            Dictionary with standardized error structure
        """
        error_details = {
            "component": component,
            "error": str(error),
            "error_type": type(error).__name__,
            "failed_at": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
            "retry_count": retry_count,
            "retryable": retryable,
            "max_retries": max_retries,
        }
        
        # Add retry timing if retryable
        if retryable and retry_count < max_retries:
            # Exponential backoff: 2^retry_count minutes
            retry_delay_minutes = 2 ** retry_count
            retry_at = datetime.utcnow() + timedelta(minutes=retry_delay_minutes)
            error_details["retry_at"] = retry_at.isoformat()
        
        # Add component-specific details
        if additional_details:
            error_details["details"] = additional_details
            
        return error_details
    
    @staticmethod
    def get_component_from_status(status: str) -> str:
        """Map status to component for failure tracking."""
        status_to_component = {
            "parse_queued": FailureHandler.COMPONENT_PARSE,
            "parsed": FailureHandler.COMPONENT_PARSE,
            "parse_validated": FailureHandler.COMPONENT_VALIDATION,
            "chunking": FailureHandler.COMPONENT_CHUNKING,
            "chunks_stored": FailureHandler.COMPONENT_CHUNKING,
            "embedding_queued": FailureHandler.COMPONENT_EMBEDDING,
            "embedding_in_progress": FailureHandler.COMPONENT_EMBEDDING,
            "embeddings_stored": FailureHandler.COMPONENT_EMBEDDING,
        }
        return status_to_component.get(status, FailureHandler.COMPONENT_UNKNOWN)
```

#### 2.3 Update Worker Error Handling
**Files**: 
- `backend/workers/enhanced_base_worker.py`
- `backend/workers/base_worker.py`
- `api/upload_pipeline/webhooks.py`

**Pattern to replace**:
```python
# OLD
await conn.execute("""
    UPDATE upload_pipeline.upload_jobs
    SET status = 'failed_parse', state = 'done', 
        last_error = $1, updated_at = now()
    WHERE job_id = $2
""", json.dumps({"error": error_message}), job_id)
```

**New pattern**:
```python
# NEW
from backend.workers.failure_handler import FailureHandler

error_details = FailureHandler.create_error_details(
    component=FailureHandler.COMPONENT_PARSE,
    error=exception,
    correlation_id=correlation_id,
    retryable=is_retryable,
    retry_count=retry_count
)

await conn.execute("""
    UPDATE upload_pipeline.upload_jobs
    SET state = 'failed', 
        last_error = $1, 
        updated_at = now()
    WHERE job_id = $2
""", json.dumps(error_details), job_id)
```

#### 2.4 Update Query Patterns

**File**: `backend/workers/enhanced_base_worker.py`

```python
# OLD
async def _get_next_job(self):
    jobs = await conn.fetch("""
        SELECT * FROM upload_pipeline.upload_jobs
        WHERE state = 'queued' 
        AND status = 'uploaded'
        AND (last_error IS NULL 
             OR (last_error->>'retry_at')::timestamp <= now())
    """)
    
    # Also check for retryable failed jobs
    failed_jobs = await conn.fetch("""
        SELECT * FROM upload_pipeline.upload_jobs
        WHERE status IN ('failed_parse', 'failed_chunking', 'failed_embedding')
        AND state = 'retryable'
        AND (last_error->>'retry_at')::timestamp <= now()
    """)
```

**NEW**:
```python
async def _get_next_job(self):
    jobs = await conn.fetch("""
        SELECT * FROM upload_pipeline.upload_jobs
        WHERE (
            (state = 'queued' AND status = 'uploaded')
            OR (state = 'failed' 
                AND last_error->>'retryable' = 'true'
                AND (last_error->>'retry_at')::timestamp <= now())
        )
        AND (last_error IS NULL 
             OR (last_error->>'retry_at')::timestamp <= now())
        ORDER BY created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    """)
```

#### 2.5 Update Retry Logic

**File**: `backend/workers/enhanced_base_worker.py`

```python
# OLD
async def _retry_failed_parse(self, job, correlation_id):
    if job["status"] != "failed_parse":
        return
    # ... retry logic
    await conn.execute("""
        UPDATE upload_pipeline.upload_jobs
        SET status = 'uploaded', state = 'queued', 
            last_error = NULL, retry_count = retry_count + 1
        WHERE job_id = $1
    """, job_id)
```

**NEW**:
```python
async def _retry_failed_job(self, job, correlation_id):
    if job["state"] != "failed":
        return
    
    error_details = job.get("last_error", {})
    if error_details.get("retryable") != True:
        return
    
    retry_count = error_details.get("retry_count", 0)
    max_retries = error_details.get("max_retries", 3)
    
    if retry_count >= max_retries:
        # Move to deadletter
        await conn.execute("""
            UPDATE upload_pipeline.upload_jobs
            SET state = 'deadletter', updated_at = now()
            WHERE job_id = $1
        """, job["job_id"])
        return
    
    # Determine status to retry from based on component
    component = error_details.get("component", "unknown")
    retry_status = self._get_retry_status_for_component(component)
    
    await conn.execute("""
        UPDATE upload_pipeline.upload_jobs
        SET status = $1, 
            state = 'queued',
            last_error = jsonb_set(
                last_error,
                '{retry_count}',
                to_jsonb((last_error->>'retry_count')::int + 1)
            ),
            updated_at = now()
        WHERE job_id = $2
    """, retry_status, job["job_id"])

def _get_retry_status_for_component(self, component: str) -> str:
    """Get the status to retry from based on failed component."""
    component_to_status = {
        "parse": "uploaded",
        "chunking": "parse_validated",
        "embedding": "chunks_stored",
        "validation": "parsed",
    }
    return component_to_status.get(component, "uploaded")
```

### Phase 3: API Updates

#### 3.1 Update Job Status Response
**File**: `api/upload_pipeline/endpoints/jobs.py`

```python
def _format_error_details(error_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format error details for API response."""
    if not error_data:
        return None
    
    return {
        "component": error_data.get("component", "unknown"),
        "code": error_data.get("error_code", "unknown_error"),
        "message": error_data.get("error", "An error occurred"),
        "timestamp": error_data.get("failed_at"),
        "retryable": error_data.get("retryable", False),
        "retry_count": error_data.get("retry_count", 0),
        "max_retries": error_data.get("max_retries", 3),
        "details": error_data.get("details")
    }

def _calculate_job_progress(status: str, state: str) -> Dict[str, float]:
    """Calculate progress based on status and state."""
    # Remove failure status weights
    status_weights = {
        "pending_upload": 5,
        "uploaded": 10,
        "parse_queued": 20,
        "parsed": 30,
        "parse_validated": 35,
        "chunking": 45,
        "chunks_stored": 50,
        "embedding_queued": 60,
        "embedding_in_progress": 70,
        "embeddings_stored": 80,
        "complete": 100,
        "duplicate": -1,
    }
    
    # If failed, return negative progress
    if state == "failed":
        return {
            "status_pct": -1,
            "total_pct": -1
        }
    
    status_pct = status_weights.get(status, 0)
    return {
        "status_pct": status_pct,
        "total_pct": status_pct
    }
```

### Phase 4: Testing Updates

#### 4.1 Update Test Queries
**Files**: All test files that query for failed jobs

```python
# OLD
jobs = await conn.fetch("""
    SELECT * FROM upload_pipeline.upload_jobs
    WHERE status IN ('failed_parse', 'failed_chunking', 'failed_embedding')
""")

# NEW
jobs = await conn.fetch("""
    SELECT * FROM upload_pipeline.upload_jobs
    WHERE state = 'failed'
""")
```

#### 4.2 Update Assertions

```python
# OLD
assert job["status"] == "failed_parse"
assert job["state"] == "done"

# NEW
assert job["state"] == "failed"
assert job["last_error"]["component"] == "parse"
assert job["status"] in ["parse_queued", "parsed"]  # Status preserved
```

## Migration Strategy

### Step 1: Pre-Migration Validation

1. **Audit current failures**:
   ```sql
   SELECT status, COUNT(*) 
   FROM upload_pipeline.upload_jobs 
   WHERE status LIKE 'failed_%'
   GROUP BY status;
   ```

2. **Backup existing data**:
   ```sql
   CREATE TABLE upload_pipeline.upload_jobs_backup AS 
   SELECT * FROM upload_pipeline.upload_jobs;
   ```

### Step 2: Deploy Database Migration

1. Run migration during maintenance window
2. Verify constraint updates
3. Verify data migration results
4. Verify no failed jobs lost in migration

### Step 3: Deploy Backend Updates

1. Deploy backend code with new failure handling
2. Deploy API updates
3. Verify workers can process jobs correctly
4. Monitor for any regressions

### Step 4: Update Queries and Scripts

1. Update all administrative scripts
2. Update monitoring/alerting queries
3. Update dashboard queries
4. Update documentation

### Step 5: Post-Migration Validation

1. Verify no jobs stuck in old failure statuses
2. Verify new failures use `state='failed'`
3. Verify component information captured correctly
4. Verify retry logic works with new structure

## Impact Analysis

### Files Requiring Updates

**Database**:
- Migration file (NEW)
- State transition validation functions
- Status transition validation functions

**Backend Models**:
- `api/upload_pipeline/models.py`
- `backend/shared/db/models.py`
- `backend/shared/schemas/jobs.py`

**Workers**:
- `backend/workers/enhanced_base_worker.py`
- `backend/workers/base_worker.py`
- `backend/workers/failure_handler.py` (NEW)

**API**:
- `api/upload_pipeline/webhooks.py`
- `api/upload_pipeline/endpoints/jobs.py`

**Scripts**:
- `scripts/reset_failed_jobs.py`
- `scripts/retry_job.py`
- `scripts/simple_worker.py`
- `scripts/real_worker.py`

**Tests**:
- All test files that check for failure statuses
- Integration tests for failure scenarios

### Breaking Changes

1. **Query Changes**: All queries checking `status IN ('failed_*')` must change to `state = 'failed'`
2. **API Responses**: Job status responses will show `state='failed'` instead of failure statuses
3. **Retry Logic**: Retry logic must check `state='failed'` and component from `last_error`
4. **Monitoring**: Dashboards and alerts must be updated

### Backward Compatibility

- Migration preserves original status in `last_error->'original_status'` for reference
- Migration can be reversed if needed (restore from backup)
- Gradual rollout possible: update queries first, then code

## Benefits

### 1. Clear Separation of Concerns
- `status` = processing stage (what step are we on?)
- `state` = queue/job state (what's the job's queue status?)

### 2. Simplified Queries
- Single query for all failures: `WHERE state = 'failed'`
- Component filtering: `WHERE state = 'failed' AND last_error->>'component' = 'parse'`

### 3. Better Error Tracking
- Component information explicitly stored
- Consistent error structure across all failures
- Easier debugging and monitoring

### 4. Flexible Retry Logic
- Retry logic based on component, not status
- Can retry from appropriate stage based on component
- Better retry strategies per component

### 5. Improved Analytics
- Track failure rates by component
- Identify problematic components
- Better failure pattern analysis

## Risks and Mitigation

### Risk 1: Data Loss During Migration
**Mitigation**: 
- Full backup before migration
- Test migration on staging first
- Verify row counts match

### Risk 2: Breaking Existing Queries
**Mitigation**:
- Comprehensive audit of all queries
- Update all scripts and tools
- Provide migration guide for teams

### Risk 3: Worker Compatibility
**Mitigation**:
- Deploy database migration first
- Deploy workers with backward compatibility check
- Gradual rollout with monitoring

### Risk 4: Retry Logic Breaking
**Mitigation**:
- Thorough testing of retry scenarios
- Verify retry paths for each component
- Monitor retry success rates

## Success Criteria

1. ✅ All failures use `state='failed'` (no `failed_*` statuses)
2. ✅ Component information captured in `last_error` for all failures
3. ✅ Retry logic works correctly with new structure
4. ✅ All queries updated and working
5. ✅ No data loss during migration
6. ✅ Monitoring and alerts updated
7. ✅ Documentation updated

## Timeline Estimate

- **Phase 1 (Database)**: 2-3 days
- **Phase 2 (Backend)**: 3-4 days
- **Phase 3 (API)**: 1-2 days
- **Phase 4 (Testing)**: 2-3 days
- **Migration Execution**: 1 day
- **Validation & Monitoring**: 2-3 days

**Total**: ~2-3 weeks including testing and validation

## Next Steps

1. Review and approve this scope document
2. Create detailed implementation tasks
3. Set up staging environment for testing
4. Begin Phase 1 implementation
5. Schedule migration window

---

**Status**: Ready for Review  
**Last Updated**: 2025-01-15  
**Author**: AI Assistant  
**Reviewers**: [To be assigned]

