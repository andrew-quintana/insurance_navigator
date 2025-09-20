# Service Dependencies and External Integrations Mapping

**Date**: January 21, 2025  
**Purpose**: Complete mapping of service dependencies and external integrations  
**Scope**: Both API and Worker services  

## Overview

This document provides a comprehensive mapping of all service dependencies and external integrations for the insurance_navigator Render services. This mapping will be used to configure staging services with appropriate dependency connections and integration endpoints.

## Service Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Service   │    │ Worker Service  │
│   (Vercel)      │◄──►│   (Render)      │◄──►│   (Render)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Supabase      │    │   Supabase      │
                       │   (Database)    │    │   (Storage)     │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   External      │    │   External      │
                       │   APIs          │    │   APIs          │
                       └─────────────────┘    └─────────────────┘
```

## Internal Service Dependencies

### 1. API Service Dependencies

#### Core Dependencies
- **Database Manager**: PostgreSQL connection pooling
- **Service Manager**: Service lifecycle management
- **Configuration Manager**: Environment-aware configuration
- **Resilience Systems**: Circuit breakers and degradation managers

#### Service-Specific Dependencies
- **User Service**: User authentication and management
- **Conversation Service**: Chat conversation management
- **Storage Service**: File storage operations
- **Document Service**: Document metadata management
- **RAG Service**: Document retrieval and similarity search

#### Middleware Dependencies
- **CORS Middleware**: Cross-origin request handling
- **Error Handler Middleware**: Global error handling
- **Request Logging Middleware**: Request/response logging
- **Authentication Middleware**: JWT token validation

### 2. Worker Service Dependencies

#### Core Dependencies
- **Enhanced Base Worker**: Core worker functionality
- **Database Manager**: PostgreSQL connection pooling
- **Storage Manager**: File storage operations
- **Service Router**: External service routing

#### Processing Dependencies
- **Job Queue System**: Background job processing
- **Document Processing Pipeline**: PDF processing workflow
- **RAG System**: Document chunking and embedding
- **Error Handler**: Worker-specific error handling

## External Service Integrations

### 1. Supabase Integration

#### Database Operations
- **Connection**: PostgreSQL via asyncpg
- **Schema**: `upload_pipeline`
- **Tables**:
  - `documents` - Document metadata
  - `document_chunks` - Vector embeddings
  - `upload_jobs` - Job queue
- **Operations**: CRUD operations, vector similarity search

#### Authentication
- **Service**: Supabase Auth
- **Methods**: JWT token validation
- **Endpoints**: `/auth/v1/token`, `/auth/v1/user`
- **Integration**: Auth adapter pattern

#### Storage
- **Service**: Supabase Storage
- **Operations**: File upload/download, signed URLs
- **Integration**: Direct HTTP API calls
- **Buckets**: Document storage buckets

#### Real-time
- **Service**: Supabase Realtime
- **Channels**: Document status updates
- **Integration**: WebSocket connections

### 2. OpenAI Integration

#### Embeddings
- **Model**: `text-embedding-3-small`
- **Dimension**: 1536
- **Usage**: Document vectorization for RAG
- **Integration**: OpenAI Python client

#### Chat Completions
- **Model**: GPT models (various)
- **Usage**: AI chat responses
- **Integration**: LangChain OpenAI integration

### 3. LlamaParse Integration

#### Document Processing
- **Service**: LlamaParse API
- **Usage**: PDF parsing and text extraction
- **Integration**: Webhook-based processing
- **Endpoints**: Parse API, webhook callbacks

### 4. Anthropic Integration (Optional)

#### Chat Completions
- **Model**: Claude models
- **Usage**: Alternative AI chat responses
- **Integration**: LangChain Anthropic integration

## Database Schema Dependencies

### Core Tables
```sql
-- Document metadata and status
CREATE TABLE upload_pipeline.documents (
    document_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    filename VARCHAR(255) NOT NULL,
    mime VARCHAR(100),
    bytes_len INTEGER,
    file_sha256 VARCHAR(64),
    raw_path VARCHAR(500),
    processing_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vector embeddings and text chunks
CREATE TABLE upload_pipeline.document_chunks (
    chunk_id UUID PRIMARY KEY,
    document_id UUID REFERENCES upload_pipeline.documents(document_id),
    chunk_ord INTEGER NOT NULL,
    text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Job processing queue
CREATE TABLE upload_pipeline.upload_jobs (
    job_id UUID PRIMARY KEY,
    document_id UUID REFERENCES upload_pipeline.documents(document_id),
    status VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    progress JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Indexes and Extensions
- **pgvector**: Vector similarity search
- **GIN Index**: Full-text search on document content
- **B-tree Indexes**: Performance optimization

## Network Dependencies

### Inbound Connections
- **HTTPS**: 443 (API service)
- **HTTP**: 80 (API service)
- **Health Checks**: Internal health check endpoints

### Outbound Connections
- **Supabase**: HTTPS (443) - Database, Auth, Storage
- **OpenAI**: HTTPS (443) - API calls
- **LlamaParse**: HTTPS (443) - Document processing
- **Anthropic**: HTTPS (443) - API calls (optional)

### Internal Communication
- **Database**: PostgreSQL connection pooling
- **Job Queue**: Database-based job processing
- **Service Discovery**: Configuration-based service routing

## Configuration Dependencies

### Environment Configuration
- **Environment Variables**: Service configuration
- **Configuration Files**: `.env` files
- **Configuration Manager**: Centralized configuration

### Service Configuration
- **Database URLs**: Connection strings
- **API Keys**: External service authentication
- **Service URLs**: External service endpoints
- **CORS Configuration**: Cross-origin settings

## Staging Dependencies Configuration

### 1. Database Dependencies

#### Staging Database Setup
```bash
# Staging database configuration
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/staging_db
DATABASE_SCHEMA=upload_pipeline_staging
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=staging_service_role_key
```

#### Staging Schema Requirements
- Create staging-specific schema
- Copy production table structure
- Set up staging-specific indexes
- Configure staging-specific permissions

### 2. External API Dependencies

#### Staging API Keys
```bash
# Staging external API configuration
OPENAI_API_KEY=staging_openai_key
LLAMAPARSE_API_KEY=staging_llamaparse_key
ANTHROPIC_API_KEY=staging_anthropic_key
```

#### Staging API Endpoints
- Use staging-specific API endpoints
- Configure staging-specific rate limits
- Set up staging-specific monitoring

### 3. Storage Dependencies

#### Staging Storage Setup
- Create staging-specific storage buckets
- Configure staging-specific permissions
- Set up staging-specific CORS policies

### 4. Network Dependencies

#### Staging Network Configuration
- Configure staging-specific CORS origins
- Set up staging-specific domain configurations
- Implement staging-specific SSL certificates

## Dependency Health Checks

### Database Health Checks
- Connection pool status
- Query performance monitoring
- Schema validation
- Index health monitoring

### External API Health Checks
- API endpoint availability
- Authentication validation
- Rate limit monitoring
- Response time monitoring

### Service Health Checks
- Service startup validation
- Dependency availability checks
- Configuration validation
- Performance monitoring

## Monitoring and Alerting

### Dependency Monitoring
- Database connection monitoring
- External API availability monitoring
- Service dependency health monitoring
- Performance degradation detection

### Staging-Specific Monitoring
- Staging service health monitoring
- Staging dependency monitoring
- Staging performance monitoring
- Staging error rate monitoring

## Error Handling and Resilience

### Circuit Breakers
- Database circuit breaker
- External API circuit breakers
- Service dependency circuit breakers

### Fallback Mechanisms
- Service degradation modes
- Graceful degradation
- Error recovery procedures
- Service restart procedures

### Retry Logic
- Exponential backoff
- Maximum retry limits
- Retry timeout handling
- Dead letter queue processing

## Security Considerations

### Dependency Security
- API key rotation
- Database connection security
- Network security policies
- Service authentication

### Staging Security
- Staging-specific security policies
- Staging data isolation
- Staging access controls
- Staging audit logging

## Conclusion

This mapping provides a comprehensive view of all service dependencies and external integrations. The staging environment should replicate all dependencies with staging-specific configurations while maintaining the same architectural patterns and integration points.

**Next Steps**:
1. Set up staging database and external service connections
2. Configure staging-specific API keys and endpoints
3. Implement staging dependency health checks
4. Set up staging monitoring and alerting
5. Validate staging service dependencies

---

**Document Status**: Complete  
**Last Updated**: January 21, 2025  
**Next Review**: After staging service creation
