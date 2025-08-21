# TVDb001 Phase 3.5 Implementation Notes

## Overview
Phase 3.5 focused on implementing job state integration and end-to-end webhook flow testing for the LlamaParse webhook handlers. This phase builds upon the completed webhook endpoint implementation from Phase 3 and integrates it with the existing 003 job state management patterns.

## Implementation Details

### 1. Job State Management Integration

#### Webhook Handler Updates
- **File**: `backend/api/routes/webhooks.py`
- **Changes**: Implemented TODO items in `_handle_parsed_status` and `_handle_failed_status` functions

#### Parsed Status Handler (`_handle_parsed_status`)
```python
# Store parsed content to storage
parsed_path = f"storage://parsed/{webhook_request.document_id}/{webhook_request.job_id}.md"
content_stored = await storage_manager.write_blob(
    parsed_path, 
    markdown_artifact.content, 
    "text/markdown"
)

# Update job status to parsed with database transaction
async with db_manager.get_db_connection() as conn:
    # Update job status and parsed content path
    await conn.execute("""
        UPDATE upload_pipeline.upload_jobs 
        SET status = 'parsed', 
            parsed_path = $1, 
            parsed_sha256 = $2,
            updated_at = now()
        WHERE job_id = $3
    """, parsed_path, markdown_artifact.sha256, webhook_request.job_id)
    
    # Log the state transition event
    event_id = uuid4()
    await conn.execute("""
        INSERT INTO upload_pipeline.events (
            event_id, job_id, document_id, type, severity, code, 
            payload, correlation_id, ts
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
    """, 
        str(event_id),
        webhook_request.job_id,
        webhook_request.document_id,
        "stage_done",  # Event type
        "info",  # Severity
        "parse_completed",  # Event code
        json.dumps({
            "parsed_path": parsed_path,
            "content_sha256": markdown_artifact.sha256,
            "content_length": len(markdown_artifact.content),
            "bytes": markdown_artifact.bytes,
            "parser_name": webhook_request.meta.parser_name,
            "parser_version": webhook_request.meta.parser_version
        }),  # Event payload
        correlation_id
    )
```

#### Failed Status Handler (`_handle_failed_status`)
```python
# Update job status to failed_parse with database transaction
async with db_manager.get_db_connection() as conn:
    # Update job status and error details
    await conn.execute("""
        UPDATE upload_pipeline.upload_jobs 
        SET status = 'failed_parse', 
            last_error = $1,
            updated_at = now()
        WHERE job_id = $2
    """, str(webhook_request.meta.get("error")), webhook_request.job_id)
    
    # Log the error event
    event_id = uuid4()
    await conn.execute("""
        INSERT INTO upload_pipeline.events (
            event_id, job_id, document_id, type, severity, code, 
            payload, correlation_id, ts
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
    """, 
        str(event_id),
        webhook_request.job_id,
        webhook_request.document_id,
        "stage_error",  # Event type
        "error",  # Severity
        "parse_failed",  # Event code
        json.dumps({
            "error": str(webhook_request.meta.get("error")),
            "parse_job_id": webhook_request.parse_job_id,
            "parser_name": webhook_request.meta.parser_name,
            "parser_version": webhook_request.meta.parser_version
        }),  # Event payload
        correlation_id
    )
```

### 2. Database Integration

#### Transaction Management
- **Pattern**: Used `async with db_manager.get_db_connection() as conn:` for atomic operations
- **Benefits**: Automatic rollback on exceptions, consistent with 003 patterns
- **Tables Updated**: 
  - `upload_pipeline.upload_jobs` - Status, parsed_path, parsed_sha256, last_error
  - `upload_pipeline.events` - State transition and error logging

#### Event Logging
- **Event Types**: `stage_done` for successful parsing, `stage_error` for failures
- **Severity Levels**: `info` for success, `error` for failures
- **Event Codes**: `parse_completed`, `parse_failed`
- **Payload**: Structured JSON with relevant metadata

### 3. Storage Integration

#### Parsed Content Storage
- **Path Format**: `storage://parsed/{document_id}/{job_id}.md`
- **Content Type**: `text/markdown`
- **Error Handling**: Raises exception if storage fails, triggers webhook failure

### 4. Schema Updates

#### Webhook Request Schema
- **File**: `backend/shared/schemas/webhooks.py`
- **Added Fields**:
  - `parse_job_id: str` - LlamaParse parse job ID
  - `correlation_id: Optional[str]` - Correlation ID for job tracking

### 5. Dependency Injection

#### FastAPI Dependencies
- **DatabaseManager**: Injected via `Depends(get_db_manager)`
- **StorageManager**: Injected via `Depends(get_storage_manager)`
- **Benefits**: Clean architecture, testable components, consistent with 003 patterns

## Integration Points

### 1. 003 Job State Management
- **Status Transitions**: `uploaded` → `parsed` or `failed_parse`
- **Event Logging**: Consistent with existing event patterns in `base_worker.py`
- **Correlation ID**: Propagated through all processing stages

### 2. Database Schema
- **upload_jobs**: Status updates, parsed content metadata
- **events**: State transition logging, error tracking
- **Consistency**: Follows existing 003 table structures and patterns

### 3. Storage System
- **Supabase Storage**: Parsed content storage with structured paths
- **Error Handling**: Graceful degradation on storage failures

## Testing Implementation

### 1. End-to-End Test Suite
- **File**: `backend/tests/integration/test_webhook_end_to_end.py`
- **Coverage**: Complete webhook flow, database integration, storage integration
- **Mock Strategy**: Proper async context manager mocking for database operations

### 2. Test Categories
- **Webhook Flow Tests**: Successful parsing, failed parsing
- **Integration Tests**: Storage manager, database manager
- **Security Tests**: Signature verification
- **Real API Tests**: Skipped by default (requires credentials)

### 3. Mock Implementation
- **AsyncContextManagerMock**: Custom class for proper async context manager mocking
- **Database Operations**: Mocked connection and execute methods
- **Storage Operations**: Mocked write_blob method

## Error Handling

### 1. Storage Failures
- **Detection**: `write_blob` returns `False`
- **Response**: Exception raised, caught by webhook handler
- **Result**: HTTP 500 with "Internal server error" detail

### 2. Database Failures
- **Transaction Rollback**: Automatic via async context manager
- **Error Logging**: Events logged before re-raising exceptions
- **Graceful Degradation**: Partial state updates prevented

### 3. Validation Failures
- **Payload Validation**: Pydantic schema validation
- **Signature Verification**: HMAC signature validation
- **Correlation ID**: Required field validation

## Performance Considerations

### 1. Database Operations
- **Transaction Scope**: Minimal scope for atomicity
- **Connection Pooling**: Leverages existing DatabaseManager patterns
- **Index Usage**: Assumes proper indexing on job_id and document_id

### 2. Storage Operations
- **Async Operations**: Non-blocking storage writes
- **Error Handling**: Fast failure detection
- **Path Generation**: Efficient string formatting

## Security Features

### 1. Webhook Authentication
- **HMAC Signatures**: SHA256-based signature verification
- **Secret Management**: Configuration-based webhook secrets
- **Header Validation**: Required signature header presence

### 2. Input Validation
- **Schema Validation**: Pydantic model validation
- **Type Safety**: UUID validation, string pattern matching
- **Content Validation**: Artifact type and content validation

## Next Phase Preparation

### 1. Pipeline Integration
- **TODO Items**: Next processing stage triggering
- **Job Progression**: State machine advancement logic
- **Retry Mechanisms**: Failed job retry logic

### 2. Real API Integration
- **Cost Controls**: API usage monitoring and limits
- **Error Handling**: Real API failure scenarios
- **Performance Testing**: End-to-end latency measurement

## Conclusion

Phase 3.5 successfully implemented the core job state integration requirements for the LlamaParse webhook handlers. The implementation follows 003 patterns consistently, provides comprehensive error handling, and includes a robust test suite for validation. The webhook handlers now properly integrate with the job state management system, update database records, log events, and handle storage operations.

Key achievements:
- ✅ Job state integration with 003 patterns
- ✅ Database transaction management
- ✅ Event logging and correlation ID tracking
- ✅ Storage integration with error handling
- ✅ Comprehensive end-to-end testing
- ✅ Security features (HMAC verification)
- ✅ Clean dependency injection architecture

The foundation is now in place for Phase 4, which will focus on pipeline integration and real API testing.
