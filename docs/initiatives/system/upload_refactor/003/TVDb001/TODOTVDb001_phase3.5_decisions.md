# TVDb001 Phase 3.5 Technical Decisions

## Overview
This document outlines the key technical decisions made during Phase 3.5 implementation of job state integration and end-to-end webhook flow testing for the LlamaParse webhook handlers.

## Architecture Decisions

### 1. Dependency Injection Pattern

#### Decision
Use FastAPI's `Depends` system for injecting `DatabaseManager` and `StorageManager` into webhook handlers.

#### Rationale
- **Testability**: Enables easy mocking of dependencies in unit tests
- **Separation of Concerns**: Keeps webhook handlers focused on business logic
- **Consistency**: Follows existing 003 patterns used in other route handlers
- **Flexibility**: Allows for different implementations in different environments

#### Alternatives Considered
- **Direct Instantiation**: Would make testing difficult and create tight coupling
- **Global Singletons**: Would violate dependency injection principles and make testing harder
- **Service Locator Pattern**: More complex than necessary for this use case

#### Implementation
```python
async def llamaparse_webhook(
    request: Request,
    service_router: ServiceRouter = Depends(get_service_router),
    llamaparse_service: RealLlamaParseService = Depends(get_llamaparse_service),
    db_manager: DatabaseManager = Depends(get_db_manager),
    storage_manager: StorageManager = Depends(get_storage_manager)
):
```

### 2. Database Transaction Management

#### Decision
Use async context managers (`async with db_manager.get_db_connection() as conn:`) for database operations.

#### Rationale
- **Atomicity**: Ensures all database operations within a webhook handler succeed or fail together
- **Automatic Rollback**: Exceptions automatically trigger transaction rollback
- **Resource Management**: Automatic connection cleanup and return to pool
- **Consistency**: Follows existing 003 patterns in `base_worker.py` and other components

#### Alternatives Considered
- **Manual Transaction Control**: Would require explicit commit/rollback logic and error handling
- **Connection Pooling Without Transactions**: Would not guarantee data consistency
- **Separate Database Calls**: Could lead to partial state updates

#### Implementation
```python
async with db_manager.get_db_connection() as conn:
    # Update job status
    await conn.execute("""
        UPDATE upload_pipeline.upload_jobs 
        SET status = 'parsed', parsed_path = $1, parsed_sha256 = $2
        WHERE job_id = $3
    """, parsed_path, markdown_artifact.sha256, webhook_request.job_id)
    
    # Log event
    await conn.execute("""
        INSERT INTO upload_pipeline.events (...)
        VALUES (...)
    """, ...)
```

### 3. Event Logging Strategy

#### Decision
Log all state transitions and errors to the `events` table with structured payloads.

#### Rationale
- **Audit Trail**: Complete history of job processing for debugging and compliance
- **Correlation**: `correlation_id` enables tracing across all processing stages
- **Structured Data**: JSON payloads provide rich context for analysis
- **Consistency**: Follows existing 003 event logging patterns

#### Alternatives Considered
- **Simple Status Updates**: Would lose valuable context and debugging information
- **Log Files Only**: Would not integrate with the existing event system
- **Minimal Logging**: Would make troubleshooting difficult

#### Implementation
```python
# Event structure
{
    "event_id": str(uuid4()),
    "job_id": webhook_request.job_id,
    "document_id": webhook_request.document_id,
    "type": "stage_done",  # or "stage_error"
    "severity": "info",    # or "error"
    "code": "parse_completed",  # or "parse_failed"
    "payload": json.dumps({
        "parsed_path": parsed_path,
        "content_sha256": markdown_artifact.sha256,
        # ... other metadata
    }),
    "correlation_id": correlation_id
}
```

### 4. Storage Path Strategy

#### Decision
Use structured storage paths: `storage://parsed/{document_id}/{job_id}.md`

#### Rationale
- **Organization**: Clear separation of parsed content by document and job
- **Uniqueness**: Guarantees unique paths for each parsing operation
- **Retrieval**: Easy to locate and retrieve parsed content for downstream processing
- **Scalability**: Supports multiple parsing attempts and document versions

#### Alternatives Considered
- **Flat Structure**: Would make organization and retrieval difficult
- **Date-based Paths**: Would not provide clear document/job association
- **Hash-based Paths**: Would not maintain human-readable organization

#### Implementation
```python
parsed_path = f"storage://parsed/{webhook_request.document_id}/{webhook_request.job_id}.md"
```

### 5. Error Handling Strategy

#### Decision
Catch all exceptions in webhook handlers and re-raise as `HTTPException` with status code 500.

#### Rationale
- **Consistency**: Provides uniform error responses to webhook callers
- **Security**: Prevents internal error details from leaking to external systems
- **Logging**: Enables comprehensive error logging before re-raising
- **Client Handling**: Allows webhook callers to implement retry logic

#### Alternatives Considered
- **Pass-through Exceptions**: Would expose internal implementation details
- **Custom Error Types**: Would add complexity without significant benefit
- **Silent Failures**: Would make debugging and monitoring difficult

#### Implementation
```python
try:
    # Webhook processing logic
    pass
except HTTPException:
    # Re-raise HTTP exceptions
    raise
except Exception as e:
    logger.error(f"Unexpected error processing webhook: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Internal server error")
```

## Testing Decisions

### 1. Mock Strategy for Async Context Managers

#### Decision
Create a custom `AsyncContextManagerMock` class instead of using `AsyncMock` for database connections.

#### Rationale
- **Proper Protocol Implementation**: Correctly implements `__aenter__` and `__aexit__` methods
- **Test Reliability**: Avoids issues with `AsyncMock` not properly simulating async context managers
- **Clear Intent**: Makes the test setup more explicit and maintainable
- **Realistic Behavior**: Closer to actual async context manager behavior

#### Alternatives Considered
- **AsyncMock with __aenter__/__aexit__**: Complex setup and prone to errors
- **MagicMock with AsyncMock**: Inconsistent behavior and harder to debug
- **Real Database Connections**: Would require test database setup and slow down tests

#### Implementation
```python
class AsyncContextManagerMock:
    """Mock class that properly implements async context manager protocol."""
    
    def __init__(self, mock_conn):
        self.mock_conn = mock_conn
    
    async def __aenter__(self):
        return self.mock_conn
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
```

### 2. Test Data Generation

#### Decision
Generate realistic test data with proper SHA256 hashes and valid UUIDs.

#### Rationale
- **Validation Testing**: Ensures Pydantic schema validation works correctly
- **Realistic Scenarios**: Tests closer to actual production data
- **Error Prevention**: Avoids test failures due to invalid data
- **Maintainability**: Clear relationship between test content and expected hashes

#### Alternatives Considered
- **Static Test Data**: Would not test dynamic content scenarios
- **Random Data**: Would make tests non-deterministic
- **Minimal Data**: Would not exercise full validation logic

#### Implementation
```python
# Generate proper SHA256 hash for test content
test_content = "# Test Document\n\nThis is test content for parsing."
content_hash = hashlib.sha256(test_content.encode()).hexdigest()

return {
    "artifacts": [{
        "type": "markdown",
        "content": test_content,
        "sha256": content_hash,
        "bytes": 45
    }],
    # ... other fields
}
```

## Schema Decisions

### 1. Webhook Request Schema Extensions

#### Decision
Add `parse_job_id` and `correlation_id` fields to `LlamaParseWebhookRequest`.

#### Rationale
- **Parse Job Tracking**: Enables correlation with LlamaParse internal job IDs
- **End-to-End Tracing**: `correlation_id` supports complete request lifecycle tracking
- **Integration Requirements**: Fields needed for proper job state management
- **Future Extensibility**: Provides foundation for advanced tracking features

#### Alternatives Considered
- **Optional Fields**: Would not enforce required tracking
- **Separate Schemas**: Would add complexity without clear benefit
- **Metadata Fields**: Would not provide type safety and validation

#### Implementation
```python
class LlamaParseWebhookRequest(BaseModel):
    # ... existing fields
    parse_job_id: str = Field(..., description="LlamaParse parse job ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for job tracking")
```

## Security Decisions

### 1. HMAC Signature Verification

#### Decision
Maintain existing HMAC signature verification for webhook authentication.

#### Rationale
- **Security**: Prevents unauthorized webhook calls and replay attacks
- **Standards Compliance**: Follows webhook security best practices
- **Existing Implementation**: Leverages proven security infrastructure
- **Configuration Flexibility**: Supports different secrets per environment

#### Alternatives Considered
- **No Authentication**: Would leave webhooks vulnerable to attacks
- **API Key Authentication**: Would require changes to LlamaParse webhook configuration
- **JWT Tokens**: Would add complexity without significant security benefit

## Performance Decisions

### 1. Database Operation Batching

#### Decision
Execute multiple database operations within a single transaction rather than separate calls.

#### Rationale
- **Atomicity**: Ensures data consistency across related operations
- **Performance**: Single transaction is more efficient than multiple separate calls
- **Connection Efficiency**: Minimizes connection pool usage
- **Error Handling**: Simpler rollback logic for failures

#### Alternatives Considered
- **Separate Transactions**: Would not guarantee atomicity
- **Batch SQL**: Would require more complex SQL generation
- **Async Operations**: Would not provide transaction guarantees

## Integration Decisions

### 1. 003 Pattern Consistency

#### Decision
Follow existing 003 patterns for job state management, event logging, and database operations.

#### Rationale
- **Consistency**: Maintains architectural coherence across the system
- **Maintainability**: Developers familiar with existing patterns
- **Testing**: Leverages existing test infrastructure and patterns
- **Documentation**: Builds on established architectural documentation

#### Alternatives Considered
- **Custom Patterns**: Would create inconsistency and increase maintenance burden
- **External Libraries**: Would add dependencies without clear benefit
- **Hybrid Approach**: Would create confusion about which patterns to follow

## Future Considerations

### 1. Pipeline Integration
- **Decision Point**: How to trigger next processing stages from webhook callbacks
- **Options**: Direct function calls, message queues, event-driven architecture
- **Recommendation**: Event-driven approach for loose coupling and scalability

### 2. Retry Mechanisms
- **Decision Point**: How to handle transient failures and implement retry logic
- **Options**: Exponential backoff, circuit breakers, dead letter queues
- **Recommendation**: Exponential backoff with circuit breaker pattern

### 3. Real API Testing
- **Decision Point**: How to implement cost-controlled real API integration testing
- **Options**: Sandbox environments, rate limiting, budget monitoring
- **Recommendation**: Multi-layered approach with cost controls and monitoring

## Conclusion

The technical decisions made in Phase 3.5 prioritize:
1. **Consistency** with existing 003 patterns
2. **Testability** through proper dependency injection and mocking
3. **Reliability** through transaction management and error handling
4. **Security** through signature verification and input validation
5. **Maintainability** through clean architecture and structured logging

These decisions provide a solid foundation for Phase 4 implementation while maintaining the architectural principles established in the 003 system.
