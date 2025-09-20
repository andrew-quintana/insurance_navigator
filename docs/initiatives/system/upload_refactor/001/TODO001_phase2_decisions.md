# Phase 2 Architectural Decisions: Core API & Job Queue Implementation

## Overview
This document captures the key architectural decisions made during Phase 2 of the Insurance Navigator insurance document ingestion pipeline refactor. These decisions focus on the API layer design, authentication strategy, rate limiting approach, and job management patterns.

## API Architecture Decisions

### D2.1: FastAPI Application Structure
**Decision**: Implement monolithic FastAPI application with modular endpoint organization

**Alternatives Considered**:
1. **Microservices**: Separate services for upload, jobs, and processing
2. **Monolithic**: Single FastAPI application with modular endpoints (chosen)
3. **Hybrid**: API gateway with separate service instances

**Chosen Approach**: Monolithic FastAPI application with modular endpoints

**Rationale**:
- **Simplicity**: Single deployment unit for MVP phase
- **Shared State**: Rate limiting and authentication benefit from shared context
- **Development Speed**: Faster development and testing cycles
- **Resource Efficiency**: Single process for moderate scale workloads
- **Future Flexibility**: Can be split into microservices later if needed

**Implementation**: 
- Single `main.py` with modular endpoint routers
- Shared middleware stack (CORS, auth, rate limiting, logging)
- Centralized configuration and database management
- Endpoint modules: `upload.py`, `jobs.py`

### D2.2: Authentication Strategy
**Decision**: JWT-based authentication with Supabase integration

**Alternatives Considered**:
1. **Session-based**: Traditional session cookies and server-side storage
2. **API Keys**: Simple API key authentication
3. **JWT with Supabase**: JWT validation using Supabase service role (chosen)
4. **OAuth 2.0**: Full OAuth flow with external provider

**Chosen Approach**: JWT with Supabase integration

**Rationale**:
- **Supabase Integration**: Leverages existing Supabase authentication
- **Stateless**: No server-side session storage required
- **Scalability**: JWT tokens work across multiple API instances
- **Security**: Supabase handles secure token generation and validation
- **User Context**: Automatic user ID extraction for authorization

**Implementation**:
- JWT validation in `auth.py` module
- Service role key for token validation
- User context extraction and dependency injection
- `require_user()` and `optional_user()` decorators

### D2.3: Rate Limiting Implementation
**Decision**: Multi-level rate limiting with in-memory storage

**Alternatives Considered**:
1. **Redis-based**: Distributed rate limiting with Redis
2. **Database-based**: Rate limiting stored in database
3. **In-memory**: Application-level rate limiting (chosen)
4. **External service**: Third-party rate limiting service

**Chosen Approach**: Multi-level in-memory rate limiting

**Rationale**:
- **Simplicity**: No additional infrastructure dependencies
- **Performance**: Fast in-memory lookups for rate limit checks
- **Flexibility**: Multiple rate limit levels (global, user, endpoint)
- **MVP Appropriate**: Sufficient for initial deployment scale
- **Future Migration**: Can migrate to Redis for distributed deployment

**Implementation**:
- `RateLimiter` class with sliding window approach
- Multiple rate limit configurations (upload, polling, general)
- Automatic cleanup of expired rate limit data
- Configurable limits via environment variables

### D2.4: Database Connection Management
**Decision**: AsyncPG connection pool with automatic schema management

**Alternatives Considered**:
1. **SQLAlchemy**: Full ORM with async support
2. **Raw asyncpg**: Direct database driver (chosen)
3. **Database proxy**: Connection through Supabase client
4. **Connection per request**: No connection pooling

**Chosen Approach**: AsyncPG connection pool with schema management

**Rationale**:
- **Performance**: Direct database access without ORM overhead
- **Async Support**: Native async/await support for FastAPI
- **Connection Pooling**: Efficient connection reuse and management
- **Schema Control**: Automatic schema selection for upload_pipeline
- **Simplicity**: Direct SQL queries without abstraction layers

**Implementation**:
- `DatabaseManager` class with connection pool
- 5-20 connection pool with proper timeouts
- Automatic schema setting for upload_pipeline
- Health check and monitoring capabilities

## Endpoint Design Decisions

### D2.5: Upload Endpoint Architecture
**Decision**: Single upload endpoint with comprehensive validation and deduplication

**Alternatives Considered**:
1. **Multi-step upload**: Separate endpoints for validation, upload, and processing
2. **Single endpoint**: Complete upload flow in one request (chosen)
3. **WebSocket upload**: Real-time upload progress via WebSocket
4. **Chunked upload**: Support for large file chunking

**Chosen Approach**: Single upload endpoint with comprehensive validation

**Rationale**:
- **User Experience**: Single request for complete upload initiation
- **Efficiency**: Reduces round-trips and simplifies frontend logic
- **Validation**: Comprehensive validation before job creation
- **Deduplication**: Early duplicate detection prevents unnecessary processing
- **Consistency**: Aligns with CONTEXT.md API contract specifications

**Implementation**:
- `POST /api/v2/upload` endpoint
- File validation (size, MIME type, filename)
- SHA256-based deduplication
- Job creation in `queued` state
- Signed URL generation for file upload

### D2.6: Job Status Endpoint Design
**Decision**: RESTful job status endpoint with progress calculation

**Alternatives Considered**:
1. **WebSocket updates**: Real-time status updates via WebSocket
2. **Polling-based**: REST endpoint for status queries (chosen)
3. **Server-sent events**: One-way real-time updates
4. **Status webhooks**: Push-based status notifications

**Chosen Approach**: RESTful polling-based status endpoint

**Rationale**:
- **Simplicity**: Standard HTTP polling pattern
- **Reliability**: No connection management or reconnection logic
- **Scalability**: Stateless requests work across multiple API instances
- **Frontend Compatibility**: Easy to implement in existing frontend frameworks
- **Rate Limiting**: Natural rate limiting via polling frequency controls

**Implementation**:
- `GET /api/v2/jobs/{job_id}` endpoint
- Progress calculation based on stage progression
- Error details and retry information
- User authorization and isolation

### D2.7: Job Management Patterns
**Decision**: Comprehensive job management with retry and listing capabilities

**Alternatives Considered**:
1. **Basic status only**: Simple job status without management features
2. **Full management**: Job listing, filtering, and retry capabilities (chosen)
3. **Admin-only management**: Limited management for regular users
4. **External management**: Job management through separate admin interface

**Chosen Approach**: Full job management for authenticated users

**Rationale**:
- **User Control**: Users can manage their own jobs and retry failures
- **Transparency**: Complete visibility into job processing status
- **Self-service**: Users can resolve issues without admin intervention
- **Monitoring**: Better user experience and reduced support burden
- **Debugging**: Users can investigate and retry failed jobs

**Implementation**:
- `GET /api/v2/jobs` for job listing with pagination
- `POST /api/v2/jobs/{job_id}/retry` for job retry
- State-based filtering and sorting
- Comprehensive job metadata and status information

## Security and Access Control Decisions

### D2.8: Row-Level Security Implementation
**Decision**: Enable RLS on all tables with user-scoped access policies

**Alternatives Considered**:
1. **Application-level only**: Security enforced only in API layer
2. **Database-level only**: RLS policies without API validation
3. **Hybrid approach**: RLS + API validation (chosen)
4. **No RLS**: Application-level security only

**Chosen Approach**: Hybrid RLS + API validation

**Rationale**:
- **Defense in Depth**: Multiple layers of security protection
- **Data Integrity**: Database-level enforcement prevents data leaks
- **API Security**: Application-level validation for business logic
- **User Isolation**: Complete separation of user data
- **HIPAA Compliance**: Supports future compliance requirements

**Implementation**:
- RLS enabled on all upload_pipeline tables
- User-scoped policies for documents, jobs, and events
- API-level user validation and authorization
- Service role access for backend processing

### D2.9: CORS and Trusted Host Configuration
**Decision**: Restrictive CORS and trusted host policies for security

**Alternatives Considered**:
1. **Open CORS**: Allow all origins for development flexibility
2. **Restrictive CORS**: Specific allowed origins (chosen)
3. **Environment-based**: Different CORS policies per environment
4. **Dynamic CORS**: CORS policies based on user authentication

**Chosen Approach**: Restrictive CORS with environment-based configuration

**Rationale**:
- **Security**: Prevents unauthorized cross-origin access
- **Production Ready**: Secure by default configuration
- **Flexibility**: Environment-specific CORS policies
- **Compliance**: Supports security audit requirements
- **User Experience**: Allows legitimate frontend integration

**Implementation**:
- CORS configured for localhost:3000 and accessa.ai
- Trusted hosts for localhost, accessa.ai, and Render domains
- Environment-based CORS policy configuration
- Secure headers and middleware stack

## Error Handling and Observability Decisions

### D2.10: Error Response Structure
**Decision**: Structured error responses with consistent format and HTTP status codes

**Alternatives Considered**:
1. **Simple errors**: Basic error messages without structure
2. **Structured errors**: Consistent error format with codes (chosen)
3. **Detailed errors**: Comprehensive error information for debugging
4. **Minimal errors**: Minimal error information for security

**Chosen Approach**: Structured error responses with appropriate detail level

**Rationale**:
- **Consistency**: Uniform error format across all endpoints
- **Frontend Integration**: Structured errors easier to handle in UI
- **Debugging**: Error codes and structured information aid troubleshooting
- **Security**: Appropriate error detail level for production use
- **User Experience**: Clear, actionable error messages

**Implementation**:
- Consistent error response format with codes
- HTTP status codes aligned with REST standards
- Error details appropriate for user consumption
- Comprehensive error logging for debugging

### D2.11: Logging and Monitoring Strategy
**Decision**: Comprehensive structured logging with correlation IDs and event taxonomy

**Alternatives Considered**:
1. **Basic logging**: Simple text-based logging
2. **Structured logging**: JSON-based structured logging (chosen)
3. **External monitoring**: Third-party monitoring service integration
4. **Minimal logging**: Basic logging for essential information only

**Chosen Approach**: Comprehensive structured logging with event taxonomy

**Rationale**:
- **Observability**: Complete visibility into system behavior
- **Debugging**: Structured logs enable efficient troubleshooting
- **Monitoring**: Log-derived metrics for system health
- **Compliance**: Audit trail for security and compliance requirements
- **Performance**: Correlation IDs for request tracing

**Implementation**:
- Structured logging with predefined event taxonomy
- Correlation IDs for request tracing
- Event codes from CONTEXT.md specifications
- Comprehensive request/response logging
- Performance timing and monitoring

## Performance and Scalability Decisions

### D2.12: Async Processing Architecture
**Decision**: Fully asynchronous FastAPI application with async database operations

**Alternatives Considered**:
1. **Synchronous**: Traditional synchronous request handling
2. **Async FastAPI**: Fully asynchronous application (chosen)
3. **Mixed approach**: Async API with sync database operations
4. **Event-driven**: Event-driven architecture with message queues

**Chosen Approach**: Fully asynchronous FastAPI with async database

**Rationale**:
- **Performance**: Non-blocking request handling for better throughput
- **Scalability**: Efficient resource utilization under load
- **Database Efficiency**: Async database operations prevent blocking
- **Modern Python**: Leverages Python's async/await capabilities
- **FastAPI Design**: Aligns with FastAPI's async-first design

**Implementation**:
- All endpoints implemented as async functions
- Async database operations with connection pooling
- Async middleware and exception handlers
- Non-blocking request processing

### D2.13: Connection Pooling Strategy
**Decision**: Fixed-size connection pool with health monitoring and automatic cleanup

**Alternatives Considered**:
1. **Dynamic pool**: Variable pool size based on load
2. **Fixed pool**: Static pool size with monitoring (chosen)
3. **Per-request connections**: No connection pooling
4. **External pool**: Connection management through external service

**Chosen Approach**: Fixed-size pool with health monitoring

**Rationale**:
- **Predictability**: Known resource usage and limits
- **Stability**: Consistent performance characteristics
- **Monitoring**: Easy to monitor pool health and utilization
- **Resource Control**: Prevents connection exhaustion
- **Production Ready**: Proven pattern for production deployments

**Implementation**:
- 5-20 connection pool size
- Health check and monitoring capabilities
- Automatic connection cleanup and timeout handling
- Schema-aware connection configuration

## Configuration and Environment Decisions

### D2.14: Configuration Management Approach
**Decision**: Pydantic-based configuration with environment variable integration

**Alternatives Considered**:
1. **Environment variables only**: Direct os.getenv() usage
2. **Configuration files**: YAML/JSON configuration files
3. **Pydantic settings**: Type-safe configuration with validation (chosen)
4. **External config service**: Configuration from external service

**Chosen Approach**: Pydantic settings with environment variable integration

**Rationale**:
- **Type Safety**: Compile-time validation of configuration values
- **Environment Support**: Native environment variable integration
- **Validation**: Built-in validation and constraint checking
- **Documentation**: Self-documenting configuration schema
- **Error Handling**: Clear error messages for misconfiguration

**Implementation**:
- `UploadPipelineConfig` class with Pydantic validation
- Environment variable prefix: `UPLOAD_PIPELINE_`
- Validation rules for critical parameters
- Sensible defaults with environment overrides

### D2.15: Environment-Specific Configuration
**Decision**: Environment-based configuration with development/production profiles

**Alternatives Considered**:
1. **Single configuration**: Same config for all environments
2. **Environment profiles**: Different configs per environment (chosen)
3. **Runtime configuration**: Configuration loaded at runtime
4. **External configuration**: Configuration from external service

**Chosen Approach**: Environment-based configuration profiles

**Rationale**:
- **Environment Isolation**: Different settings for dev/staging/production
- **Security**: Production-appropriate security settings
- **Development**: Developer-friendly configuration for local development
- **Deployment**: Environment-specific deployment configuration
- **Compliance**: Production security and compliance settings

**Implementation**:
- Environment variable: `UPLOAD_PIPELINE_ENVIRONMENT`
- Environment-specific CORS and security settings
- Development vs. production configuration profiles
- Environment validation and constraints

## Integration and Compatibility Decisions

### D2.16: Frontend Integration Strategy
**Decision**: RESTful API design with standard HTTP patterns for easy frontend integration

**Alternatives Considered**:
1. **GraphQL**: Flexible query language for frontend data needs
2. **REST API**: Standard RESTful design (chosen)
3. **gRPC**: High-performance RPC framework
4. **Custom protocol**: Proprietary API design

**Chosen Approach**: RESTful API with standard HTTP patterns

**Rationale**:
- **Frontend Compatibility**: Easy integration with existing frontend frameworks
- **Standards**: Follows established REST API patterns
- **Tooling**: Rich ecosystem of REST API tools and libraries
- **Documentation**: Self-documenting API design
- **Testing**: Standard HTTP testing tools and frameworks

**Implementation**:
- RESTful endpoint design with proper HTTP methods
- Standard HTTP status codes and error handling
- JSON request/response formats
- Comprehensive API documentation

### D2.17: Database Schema Integration
**Decision**: Direct integration with Phase 1 database schema without abstraction layers

**Alternatives Considered**:
1. **ORM abstraction**: SQLAlchemy or similar ORM layer
2. **Repository pattern**: Abstracted data access layer
3. **Direct SQL**: Direct database queries (chosen)
4. **Query builder**: SQL query builder library

**Chosen Approach**: Direct SQL queries with connection management

**Rationale**:
- **Performance**: Direct database access without ORM overhead
- **Schema Alignment**: Direct use of Phase 1 schema design
- **Flexibility**: Full control over SQL queries and optimization
- **Simplicity**: No additional abstraction layers to maintain
- **Debugging**: Direct SQL visibility for troubleshooting

**Implementation**:
- Raw SQL queries with parameter binding
- Direct schema table access
- Connection pool management
- Schema-aware connection configuration

## Future Considerations and Migration Paths

### D2.18: Microservices Migration Path
**Decision**: Design for future microservices migration while maintaining monolithic structure

**Rationale**:
- **Current Needs**: Monolithic structure sufficient for MVP scale
- **Future Growth**: Design supports microservices migration
- **Modularity**: Endpoint modules can become separate services
- **Shared Components**: Authentication and rate limiting can be extracted
- **Gradual Migration**: Can migrate components incrementally

**Implementation**:
- Modular endpoint organization
- Shared service interfaces
- Configuration-based service boundaries
- Stateless design for horizontal scaling

### D2.19: Distributed Rate Limiting
**Decision**: In-memory rate limiting with future Redis migration path

**Rationale**:
- **Current Scale**: In-memory sufficient for single-instance deployment
- **Future Growth**: Redis migration path for distributed deployment
- **Performance**: In-memory provides best performance for single instance
- **Simplicity**: No external dependencies for initial deployment
- **Migration Path**: Clear path to Redis-based distributed rate limiting

**Implementation**:
- Abstract rate limiter interface
- In-memory implementation for current deployment
- Redis adapter prepared for future migration
- Configuration-based rate limiter selection

## Conclusion

Phase 2 architectural decisions establish a robust, scalable API layer that balances current MVP requirements with future growth considerations. The key decisions focus on:

**Security & Reliability**:
- Comprehensive authentication and authorization
- Row-level security with user isolation
- Structured error handling and logging
- Rate limiting and abuse prevention

**Performance & Scalability**:
- Async-first architecture for high throughput
- Connection pooling and database optimization
- Stateless design for horizontal scaling
- Performance monitoring and health checks

**Integration & Compatibility**:
- RESTful API design for frontend integration
- Standard HTTP patterns and status codes
- Comprehensive API documentation
- Environment-specific configuration

**Future Flexibility**:
- Modular design for microservices migration
- Configuration-based service boundaries
- Migration paths for distributed deployment
- Extensible architecture for new features

These decisions provide a solid foundation for Phase 3 worker implementation and future system evolution while maintaining the simplicity and reliability required for MVP deployment.
