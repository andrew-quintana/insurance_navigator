# TVDb001 Phase 2 Technical Decisions

## Overview
This document captures the key technical decisions made during Phase 2 of the TVDb001 Real API Integration Testing project. Phase 2 focused on implementing upload initiation and flow validation with real service integration, building upon the Phase 1 service router and cost tracking infrastructure.

## Architecture Decisions

### 1. Enhanced Upload Endpoint Design

#### Decision: Service Router Integration Pattern
**Context**: The upload endpoint needed to integrate with the Phase 1 service router while maintaining backward compatibility with existing 003 upload flow.

**Decision**: Implement service router integration through dependency injection pattern with global instances for development.

**Rationale**:
- **Backward Compatibility**: Maintains existing 003 upload flow while adding new capabilities
- **Service Awareness**: Upload endpoint can now make intelligent decisions about service selection
- **Development Simplicity**: Global instances simplify development while maintaining production-ready patterns
- **Testing**: Easy to mock and test with different service configurations

**Alternatives Considered**:
- Direct service instantiation: Would break separation of concerns
- Factory pattern: Overkill for current requirements
- Dependency injection container: Adds complexity without clear benefit

**Implementation Details**:
```python
def get_service_router() -> ServiceRouter:
    """Get or create service router instance"""
    global _service_router
    if _service_router is None:
        config = get_enhanced_config()
        _service_router = ServiceRouter(config.get_service_router_config())
    return _service_router
```

#### Decision: Correlation ID Tracking Throughout Upload Flow
**Context**: Need comprehensive request tracing for debugging and monitoring real service integration.

**Decision**: Generate correlation ID at upload initiation and propagate through all processing stages.

**Rationale**:
- **Debugging**: Enables complete request tracing across all services
- **Monitoring**: Provides visibility into upload processing lifecycle
- **Error Handling**: Correlates errors across different processing stages
- **Performance**: Minimal overhead with significant debugging benefits

**Implementation Details**:
```python
# Generate correlation ID for tracking
correlation_id = uuid4()

# Store in job metadata
job_payload = {
    "correlation_id": str(correlation_id),
    "service_mode": config.service_mode.value,
    # ... other fields
}

# Log all events with correlation ID
await _log_upload_event(
    job_id=job_id,
    document_id=document_id,
    correlation_id=correlation_id,
    event_type="UPLOAD_ACCEPTED",
    payload={...}
)
```

### 2. Enhanced Configuration Management

#### Decision: Extend EnhancedConfig with Missing Fields
**Context**: The upload endpoint needed access to upload, storage, and database configuration that wasn't available in the existing EnhancedConfig.

**Decision**: Add new configuration classes (UploadConfig, StorageConfig, DatabaseConfig) to EnhancedConfig.

**Rationale**:
- **Completeness**: Provides all configuration needed for upload processing
- **Consistency**: Follows existing configuration patterns
- **Validation**: Each config class has its own validation logic
- **Environment Integration**: Supports environment variable configuration

**Implementation Details**:
```python
@dataclass
class UploadConfig:
    """Upload configuration for document processing."""
    max_file_size_bytes: int = 25 * 1024 * 1024  # 25MB
    max_pages: int = 100
    max_concurrent_jobs_per_user: int = 2
    max_uploads_per_day_per_user: int = 30
    supported_mime_types: list = None
    
    @classmethod
    def from_environment(cls) -> 'UploadConfig':
        """Create configuration from environment variables."""
        return cls(
            max_file_size_bytes=int(os.getenv('MAX_FILE_SIZE_BYTES', '26214400')),
            max_pages=int(os.getenv('MAX_PAGES', '100')),
            max_concurrent_jobs_per_user=int(os.getenv('MAX_CONCURRENT_JOBS_PER_USER', '2')),
            max_uploads_per_day_per_user=int(os.getenv('MAX_UPLOADS_PER_DAY_PER_USER', '30'))
        )
```

### 3. Cost-Aware Job Creation

#### Decision: Pre-Validation Cost Checking
**Context**: Need to prevent budget overruns by checking cost limits before job creation.

**Decision**: Implement cost estimation and validation before job creation, with detailed cost breakdown.

**Rationale**:
- **Budget Protection**: Prevents expensive jobs from being created
- **User Experience**: Early failure with clear error messages
- **Cost Transparency**: Users understand processing costs upfront
- **Resource Management**: Better control over API usage

**Implementation Details**:
```python
async def _validate_cost_limits(
    request: UploadRequest, 
    cost_tracker: CostTracker,
    correlation_id: UUID
) -> None:
    """Validate cost limits before job creation"""
    
    # Estimate processing costs
    estimated_cost = await _estimate_processing_cost(request)
    
    # Check daily and hourly limits
    if not await cost_tracker.check_daily_limit(estimated_cost):
        raise CostLimitExceededError("Daily cost limit exceeded")
    
    if not await cost_tracker.check_hourly_limit(estimated_cost):
        raise CostLimitExceededError("Hourly cost limit exceeded")
```

#### Decision: Sophisticated Cost Estimation
**Context**: Need accurate cost estimation for different file sizes and processing requirements.

**Decision**: Implement file size-based cost estimation with service-specific pricing models.

**Rationale**:
- **Accuracy**: Better cost prediction for user planning
- **Transparency**: Users understand cost drivers
- **Service Awareness**: Different services have different cost models
- **Scalability**: Handles various file sizes and processing requirements

**Implementation Details**:
```python
async def _estimate_processing_cost(request: UploadRequest) -> float:
    """Estimate processing cost for the upload request"""
    
    # LlamaParse costs: $0.003 per page (estimated 1 page per 50KB)
    estimated_pages = max(1, request.bytes_len // (50 * 1024))
    llamaparse_cost = estimated_pages * 0.003
    
    # OpenAI costs: $0.00002 per 1K tokens (estimated 1 token per 4 characters)
    estimated_tokens = max(100, request.bytes_len // 4)
    openai_cost = (estimated_tokens / 1000) * 0.00002
    
    total_cost = llamaparse_cost + openai_cost
    return total_cost
```

### 4. Service Availability Validation

#### Decision: Pre-Job Creation Health Checking
**Context**: Need to ensure services are available before creating jobs that depend on them.

**Decision**: Check service health before job creation and log warnings for unhealthy services.

**Rationale**:
- **Proactive Detection**: Identifies service issues before job creation
- **Fallback Preparation**: Logs warnings to prepare for fallback scenarios
- **User Experience**: Better error messages when services are unavailable
- **Monitoring**: Provides visibility into service health during upload processing

**Implementation Details**:
```python
async def _validate_service_availability(
    service_router: ServiceRouter, 
    correlation_id: UUID
) -> Dict[str, Any]:
    """Validate service availability before job creation"""
    
    # Check service health
    health_status = await service_router.get_health_status()
    
    # Validate required services are available
    required_services = ['llamaparse', 'openai']
    for service in required_services:
        if not health_status.get(service, {}).get('healthy', False):
            logger.warning(
                f"Service {service} unhealthy, will use fallback",
                correlation_id=str(correlation_id),
                service=service,
                health_status=health_status.get(service, {})
            )
    
    return health_status
```

### 5. Enhanced Job Metadata

#### Decision: Store Service Integration Data in Job Progress
**Context**: Need to track service mode, correlation ID, and service health status throughout job lifecycle.

**Decision**: Store enhanced metadata in the existing `progress` JSON field to avoid schema changes.

**Rationale**:
- **Backward Compatibility**: No database schema changes required
- **Flexibility**: JSON field can store any additional metadata
- **Extensibility**: Easy to add new fields without migration
- **Performance**: No additional database queries for metadata

**Implementation Details**:
```python
# Create enhanced job payload
job_payload = {
    "user_id": str(user_id),
    "document_id": str(document_id),
    "file_sha256": request.sha256,
    "bytes_len": request.bytes_len,
    "mime": request.mime,
    "storage_path": raw_path,
    "service_mode": config.service_mode.value,
    "correlation_id": str(correlation_id),
    "service_router_config": service_router_config,
    "service_health_status": health_status,
    "cost_tracking_enabled": True,
    "processing_priority": 0
}

# Store in progress field
await tx.execute("""
    INSERT INTO upload_pipeline.upload_jobs (
        job_id, document_id, user_id, status, raw_path, 
        chunks_version, embed_model, embed_version, progress, 
        retry_count, correlation_id, created_at, updated_at
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())
""", job_id, document_id, user_id, "uploaded", raw_path,
    "markdown-simple@1", "text-embedding-3-small", "1", 
    job_payload, 0, correlation_id)
```

## Integration Decisions

### 1. Service Router Integration

#### Decision: Seamless Service Mode Switching
**Context**: Upload endpoint needs to work with all service modes (MOCK, REAL, HYBRID) without code changes.

**Decision**: Use service router configuration to determine service behavior automatically.

**Rationale**:
- **Transparency**: Upload endpoint doesn't need to know about service modes
- **Consistency**: Same code path works for all service configurations
- **Maintainability**: Single code path reduces maintenance overhead
- **Testing**: Easy to test different service modes

### 2. Cost Tracker Integration

#### Decision: Early Cost Validation
**Context**: Need to prevent expensive jobs from being created.

**Decision**: Validate cost limits before any expensive operations.

**Rationale**:
- **Efficiency**: Fail fast before creating jobs
- **User Experience**: Clear error messages about cost limits
- **Resource Protection**: Prevents budget overruns
- **Transparency**: Users understand cost constraints upfront

### 3. Storage Manager Integration

#### Decision: Reuse Existing Storage Manager
**Context**: Need signed URL generation for document uploads.

**Decision**: Use existing StorageManager from 003 implementation.

**Rationale**:
- **Reuse**: Leverages existing, tested storage functionality
- **Consistency**: Same storage patterns across the system
- **Testing**: Already validated in 003 implementation
- **Maintenance**: Single storage implementation to maintain

## Testing Decisions

### 1. Mock Service Testing

#### Decision: Mock Dependencies for Unit Testing
**Context**: Need to test upload endpoint without real external services.

**Decision**: Create mock implementations of ServiceRouter and CostTracker for testing.

**Rationale**:
- **Isolation**: Tests focus on upload endpoint logic
- **Reliability**: Tests don't depend on external service availability
- **Speed**: Fast test execution without network calls
- **Control**: Predictable test behavior

**Implementation Details**:
```python
class MockServiceRouter:
    """Mock service router for testing"""
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Mock health status"""
        return {
            "llamaparse": {"healthy": True, "response_time": 50},
            "openai": {"healthy": True, "response_time": 30}
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Mock configuration"""
        return {
            "mode": "hybrid",
            "fallback_enabled": True
        }
```

### 2. Test Coverage Strategy

#### Decision: Comprehensive Function Testing
**Context**: Need to validate all upload endpoint functionality.

**Decision**: Test individual functions and complete upload flow.

**Rationale**:
- **Functionality**: Ensures each component works correctly
- **Integration**: Validates components work together
- **Edge Cases**: Tests various file sizes and scenarios
- **Error Handling**: Validates error scenarios and recovery

## Security Decisions

### 1. API Key Management

#### Decision: Environment Variable Configuration
**Context**: Need secure storage of API keys for real services.

**Decision**: Use environment variables with enhanced configuration validation.

**Rationale**:
- **Security**: API keys not stored in code
- **Flexibility**: Easy to change keys without code changes
- **Validation**: Configuration validation ensures required keys are present
- **Environment Support**: Different keys for different environments

### 2. Input Validation

#### Decision: Comprehensive Request Validation
**Context**: Need to prevent malicious or invalid upload requests.

**Decision**: Implement comprehensive validation including file size, MIME type, and content hash.

**Rationale**:
- **Security**: Prevents abuse and malicious uploads
- **Data Integrity**: Ensures uploaded files meet requirements
- **User Experience**: Clear error messages for validation failures
- **Resource Protection**: Prevents resource exhaustion attacks

## Performance Decisions

### 1. Asynchronous Processing

#### Decision: Async Upload Processing
**Context**: Upload endpoint needs to handle multiple concurrent requests efficiently.

**Decision**: Use async/await pattern throughout the upload flow.

**Rationale**:
- **Concurrency**: Handle multiple uploads simultaneously
- **Efficiency**: Non-blocking I/O operations
- **Scalability**: Better resource utilization
- **Responsiveness**: Fast response times for users

### 2. Database Connection Management

#### Decision: Reuse Database Connections
**Context**: Need efficient database access for upload processing.

**Decision**: Use global database manager instance with connection pooling.

**Rationale**:
- **Efficiency**: Reuse database connections
- **Performance**: Avoid connection overhead
- **Resource Management**: Better connection pool utilization
- **Reliability**: Consistent database access patterns

## Future Considerations

### 1. Schema Evolution

#### Decision: Use JSON Fields for Flexibility
**Context**: Need to store additional metadata without schema changes.

**Decision**: Store enhanced metadata in existing JSON fields.

**Future Impact**:
- **Migration**: May need schema changes for better performance
- **Indexing**: JSON fields may need specialized indexing
- **Querying**: Complex queries on JSON data may be needed
- **Validation**: JSON schema validation may be beneficial

### 2. Service Discovery

#### Decision: Static Service Configuration
**Context**: Services are configured statically in environment variables.

**Future Enhancement**:
- **Dynamic Discovery**: Service discovery for dynamic environments
- **Health Monitoring**: Real-time service health monitoring
- **Load Balancing**: Intelligent service selection based on load
- **Circuit Breaking**: Advanced failure handling and recovery

### 3. Cost Optimization

#### Decision: Basic Cost Estimation
**Context**: Simple cost estimation based on file size.

**Future Enhancement**:
- **Machine Learning**: ML-based cost prediction
- **Batch Optimization**: Optimize batch sizes for cost efficiency
- **Service Selection**: Choose services based on cost and performance
- **Cost Analytics**: Advanced cost analysis and reporting

## Conclusion

Phase 2 has successfully implemented upload initiation and flow validation with real service integration. The key technical decisions focus on:

1. **Service Integration**: Seamless integration with Phase 1 service router
2. **Cost Control**: Comprehensive cost estimation and validation
3. **Monitoring**: Correlation ID tracking and enhanced logging
4. **Configuration**: Extended configuration management for all components
5. **Testing**: Comprehensive testing with mock dependencies

These decisions provide a solid foundation for Phase 3, which will focus on LlamaParse real integration and complete pipeline validation.

---

**Decision Date**: August 20, 2025  
**Phase**: Phase 2 - Upload Initiation & Flow Validation  
**Status**: ✅ IMPLEMENTED  
**Next Phase**: Phase 3 - LlamaParse Real Integration
