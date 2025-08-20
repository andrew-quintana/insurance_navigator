# TVDb001 Phase 1 Architectural Decisions

## Overview
This document outlines the key architectural decisions made during Phase 1 of the TVDb001 Real API Integration Testing project. These decisions establish the foundation for the service integration infrastructure and guide future development phases.

## 1. Service Router Architecture

### Decision: Configuration-Driven Service Registration
**Context**: Need to automatically register services based on configuration without manual intervention.

**Decision**: Implement automatic service registration in the ServiceRouter constructor based on configuration parameters.

**Rationale**:
- Reduces boilerplate code in BaseWorker
- Ensures consistent service registration
- Simplifies configuration management
- Enables easy addition of new services

**Implementation**:
```python
def _auto_register_services(self, config: Dict[str, Any]) -> None:
    """Automatically register services based on configuration"""
    if "llamaparse_config" in config:
        # Register LlamaParse service
    if "openai_config" in config:
        # Register OpenAI service
```

**Alternatives Considered**:
- Manual service registration in BaseWorker
- Service discovery via reflection/introspection
- Configuration file-based registration

### Decision: Mock Service Implementation Strategy
**Context**: Need to provide reliable fallback services when real APIs are unavailable.

**Decision**: Implement dedicated mock service classes that implement the same interface as real services.

**Rationale**:
- Ensures consistent behavior between mock and real services
- Provides deterministic test results
- Enables comprehensive testing without external dependencies
- Maintains service contract compliance

**Implementation**:
```python
class MockLlamaParseService(MockService):
    async def parse_document(self, file_path: str, correlation_id: str = None) -> Dict[str, Any]:
        # Deterministic mock implementation

class MockOpenAIService(MockService):
    async def generate_embeddings(self, texts: List[str], correlation_id: str = None) -> List[List[float]]:
        # Deterministic mock implementation
```

**Alternatives Considered**:
- Generic mock service with dynamic method generation
- Service stubbing via dependency injection
- External mock service containers

## 2. Configuration Management

### Decision: Hierarchical Configuration Structure
**Context**: Need to manage complex configuration for multiple services with different requirements.

**Decision**: Implement hierarchical configuration classes that inherit from a base configuration class.

**Rationale**:
- Provides clear separation of concerns
- Enables service-specific validation
- Supports inheritance and composition
- Maintains type safety and validation

**Implementation**:
```python
@dataclass
class LlamaParseConfig(BaseServiceConfig):
    api_key: str
    base_url: str
    daily_cost_limit: float = 10.0
    hourly_rate_limit: int = 100

@dataclass
class OpenAIConfig(BaseServiceConfig):
    api_key: str
    base_url: str
    model: str = "text-embedding-3-small"
    max_batch_size: int = 256
```

**Alternatives Considered**:
- Flat configuration dictionary
- Environment variable-only configuration
- External configuration files (YAML, JSON)

### Decision: Environment-Based Configuration Loading
**Context**: Need to support different environments (development, staging, production) with appropriate configurations.

**Decision**: Use environment-specific `.env.{environment}` files for configuration loading.

**Rationale**:
- Follows existing project patterns
- Provides environment isolation
- Supports secure credential management
- Enables easy environment switching

**Implementation**:
```python
@classmethod
def from_environment(cls) -> 'EnhancedConfig':
    """Create configuration from environment variables"""
    return cls(
        service_mode=os.getenv("SERVICE_MODE", "HYBRID"),
        # ... other configuration parameters
    )
```

**Alternatives Considered**:
- Configuration management service
- Database-stored configuration
- Kubernetes ConfigMaps/Secrets

## 3. Cost Tracking System

### Decision: Time-Based Cost Aggregation
**Context**: Need to track costs across different time periods for budgeting and monitoring.

**Decision**: Implement both daily and hourly cost aggregation with configurable limits.

**Rationale**:
- Provides flexible cost control
- Enables both short-term and long-term budgeting
- Supports different business requirements
- Enables detailed cost analysis

**Implementation**:
```python
@dataclass
class CostLimit:
    daily_limit: float
    hourly_rate_limit: int
    alert_threshold: float = 0.8
    retention_days: int = 30

def check_cost_limit(self, service: str, cost: float, tokens: int) -> bool:
    # Check both daily and hourly limits
```

**Alternatives Considered**:
- Single cost limit per service
- Rolling window cost tracking
- Request-based cost limits

### Decision: Token-Based Rate Limiting
**Context**: Need to enforce rate limits for API services that charge per token.

**Decision**: Implement token-based rate limiting in addition to request-based limits.

**Rationale**:
- Aligns with actual API billing models
- Provides more accurate cost control
- Enables fair usage policies
- Supports different service pricing models

**Implementation**:
```python
def check_rate_limit(self, service: str, tokens: int) -> bool:
    """Check if request exceeds hourly token rate limit"""
    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    hourly_usage = self.get_hourly_usage(service, current_hour)
    return hourly_usage.total_tokens + tokens <= self.limits[service].hourly_rate_limit
```

**Alternatives Considered**:
- Request-based rate limiting only
- Time-based rate limiting
- Dynamic rate limiting based on costs

## 4. Exception Handling

### Decision: Hierarchical Exception Structure
**Context**: Need to provide structured error handling that can be used for logging, monitoring, and user feedback.

**Decision**: Implement a hierarchical exception structure with base classes and specific exception types.

**Rationale**:
- Enables catch-all error handling
- Provides specific error types for different scenarios
- Supports error categorization and filtering
- Enables rich error context and metadata

**Implementation**:
```python
class InsuranceNavigatorError(Exception):
    """Base exception for all Insurance Navigator errors"""
    def __init__(self, message: str, correlation_id: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        self.correlation_id = correlation_id
        self.context = context or {}
        super().__init__(message)

class ServiceError(InsuranceNavigatorError):
    """Base exception for service-related errors"""

class ServiceUnavailableError(ServiceError):
    """Raised when a service is unavailable"""

class ServiceExecutionError(ServiceError):
    """Raised when a service operation fails"""
```

**Alternatives Considered**:
- Single exception class with error codes
- Generic exception handling
- External error handling library

### Decision: Rich Error Context
**Context**: Need to provide sufficient information for debugging and monitoring without exposing sensitive data.

**Decision**: Include correlation IDs, context data, and structured error information in exceptions.

**Rationale**:
- Enables request tracing across services
- Provides debugging context
- Supports monitoring and alerting
- Maintains security by avoiding sensitive data exposure

**Implementation**:
```python
def to_dict(self) -> Dict[str, Any]:
    """Convert exception to dictionary for logging/monitoring"""
    return {
        "error_type": self.__class__.__name__,
        "message": str(self),
        "correlation_id": self.correlation_id,
        "context": self.context,
        "timestamp": datetime.utcnow().isoformat()
    }
```

**Alternatives Considered**:
- Simple error messages only
- Full stack trace inclusion
- External error tracking service

## 5. Health Monitoring

### Decision: Configurable Health Check Intervals
**Context**: Need to balance monitoring frequency with system performance and resource usage.

**Decision**: Implement configurable health check intervals with sensible defaults.

**Rationale**:
- Enables environment-specific tuning
- Balances monitoring overhead with responsiveness
- Supports different deployment scenarios
- Provides operational flexibility

**Implementation**:
```python
@dataclass
class ServiceHealthConfig:
    check_interval: int = 30  # seconds
    fallback_timeout: int = 10  # seconds
    health_check_timeout: int = 5  # seconds
    max_consecutive_failures: int = 3
```

**Alternatives Considered**:
- Fixed health check intervals
- Dynamic health check intervals
- Event-driven health monitoring

### Decision: Comprehensive Health Status
**Context**: Need to provide detailed health information for monitoring and debugging.

**Decision**: Include multiple health metrics in health status responses.

**Rationale**:
- Enables proactive monitoring
- Provides debugging information
- Supports health-based routing
- Enables trend analysis

**Implementation**:
```python
@dataclass
class ServiceHealth:
    is_healthy: bool
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_count: int = 0
    last_error: Optional[str] = None
```

**Alternatives Considered**:
- Simple healthy/unhealthy status
- External health monitoring service
- Health check aggregation only

## 6. Testing Strategy

### Decision: Comprehensive Unit Testing
**Context**: Need to ensure reliability and maintainability of the infrastructure components.

**Decision**: Implement comprehensive unit tests covering all major functionality and edge cases.

**Rationale**:
- Ensures code quality and reliability
- Enables safe refactoring
- Provides documentation of expected behavior
- Catches regressions early

**Implementation**:
- Service Router: 33 tests covering all modes and scenarios
- Cost Tracker: 35 tests covering all tracking and limit scenarios
- Enhanced Config: 69 tests covering all configuration scenarios
- Exceptions: 9 tests covering all exception types

**Alternatives Considered**:
- Minimal testing for core functionality only
- Integration testing only
- Manual testing only

### Decision: Mock Service Testing
**Context**: Need to test service integration without external dependencies.

**Decision**: Use mock services for comprehensive testing of service interactions.

**Rationale**:
- Enables reliable and fast testing
- Provides deterministic test results
- Avoids external service dependencies
- Supports comprehensive test coverage

**Implementation**:
```python
class MockService(ServiceInterface):
    def __init__(self, name: str, is_available: bool = True, 
                 fail_on_execute: bool = False):
        self.name = name
        self._is_available = is_available
        self._fail_on_execute = fail_on_execute
```

**Alternatives Considered**:
- External test services
- Real service testing in CI/CD
- Service virtualization tools

## 7. Backward Compatibility

### Decision: Maintain Existing Interfaces
**Context**: Need to integrate new infrastructure without breaking existing BaseWorker functionality.

**Decision**: Maintain all existing public interfaces while enhancing internal implementation.

**Rationale**:
- Minimizes disruption to existing code
- Enables gradual migration
- Reduces integration risk
- Maintains existing test coverage

**Implementation**:
- BaseWorker public methods unchanged
- Service behavior identical to existing implementation
- Configuration loading patterns preserved
- Error handling patterns maintained

**Alternatives Considered**:
- Breaking changes with migration guide
- Parallel implementation with feature flags
- Complete rewrite of BaseWorker

### Decision: Transparent Service Integration
**Context**: Need to integrate service router without changing how services are used.

**Decision**: Implement convenience methods in ServiceRouter that match existing service interfaces.

**Rationale**:
- Maintains existing code patterns
- Enables seamless integration
- Reduces migration effort
- Preserves existing functionality

**Implementation**:
```python
async def generate_embeddings(self, texts: List[str], correlation_id: str = None) -> List[List[float]]:
    """Generate embeddings using the OpenAI service."""
    service = await self.get_service("openai")
    return await service.generate_embeddings(texts, correlation_id)
```

**Alternatives Considered**:
- New service interface patterns
- Service factory pattern
- Dependency injection container

## Impact and Trade-offs

### Positive Impacts
1. **Reliability**: Comprehensive error handling and health monitoring
2. **Flexibility**: Configurable service modes and cost controls
3. **Maintainability**: Clear separation of concerns and comprehensive testing
4. **Scalability**: Modular architecture supporting future service additions
5. **Security**: Secure configuration management and service isolation

### Trade-offs
1. **Complexity**: More complex architecture than direct service usage
2. **Performance**: Small overhead for service routing and health monitoring
3. **Testing**: More comprehensive test suite required
4. **Configuration**: More configuration parameters to manage
5. **Learning Curve**: New concepts for developers to understand

## Future Considerations

### Extensibility
- Service router architecture supports easy addition of new services
- Configuration system can accommodate new service types
- Exception hierarchy can be extended for new error types
- Cost tracking can be extended for new billing models

### Performance Optimization
- Health monitoring intervals can be tuned based on requirements
- Service selection caching can be implemented if needed
- Cost tracking can be optimized for high-volume scenarios
- Configuration loading can be optimized for production environments

### Monitoring and Observability
- Health check endpoints can be exposed for external monitoring
- Cost tracking can be integrated with external monitoring systems
- Exception handling can be integrated with error tracking services
- Service router can provide metrics for operational monitoring

---

**Document Version**: 1.0  
**Last Updated**: August 20, 2025  
**Phase**: Phase 1 - Foundation Infrastructure  
**Status**: ✅ COMPLETED
