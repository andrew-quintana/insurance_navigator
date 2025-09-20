# Environment Variables Inventory

**Date**: January 21, 2025  
**Purpose**: Complete inventory of environment variables used by Render services  
**Scope**: Both API and Worker services  

## Overview

This document provides a comprehensive inventory of all environment variables used by the insurance_navigator Render services, categorized by function and service type. This inventory will be used to configure staging services with appropriate environment-specific values.

## Environment Variable Categories

### 1. Core Environment Configuration

| Variable | Description | Default | Required | Used By |
|----------|-------------|---------|----------|---------|
| `ENVIRONMENT` | Deployment environment (development/testing/production) | development | Yes | Both |
| `NODE_ENV` | Node.js environment (legacy) | development | No | Both |
| `DEBUG` | Debug mode flag | false | No | Both |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO | No | Both |

### 2. Database Configuration

| Variable | Description | Default | Required | Used By |
|----------|-------------|---------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes | Both |
| `SUPABASE_DB_HOST` | Supabase database host | localhost | No | Both |
| `SUPABASE_DB_PORT` | Supabase database port | 5432 | No | Both |
| `SUPABASE_DB_USER` | Supabase database user | postgres | No | Both |
| `SUPABASE_DB_PASSWORD` | Supabase database password | - | No | Both |
| `SUPABASE_DB_NAME` | Supabase database name | postgres | No | Both |
| `DATABASE_SCHEMA` | Database schema name | upload_pipeline | No | Both |
| `TEST_DATABASE_SCHEMA` | Test database schema | upload_pipeline_test | No | Both |

### 3. Supabase Configuration

| Variable | Description | Default | Required | Used By |
|----------|-------------|---------|----------|---------|
| `SUPABASE_URL` | Supabase project URL | - | Yes | Both |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key | - | Yes | Both |
| `SERVICE_ROLE_KEY` | Alternative service role key | - | No | Both |

### 4. External API Configuration

| Variable | Description | Default | Required | Used By |
|----------|-------------|---------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - | Yes | Both |
| `ANTHROPIC_API_KEY` | Anthropic API key | - | No | Both |
| `LLAMAPARSE_API_KEY` | LlamaParse API key | - | Yes | Both |

### 5. Service Configuration

| Variable | Description | Default | Required | Used By |
|----------|-------------|---------|----------|---------|
| `SERVICE_HOST` | Service host binding | 0.0.0.0 | No | API |
| `SERVICE_PORT` | Service port | 8000 | No | API |
| `API_BASE_URL` | API base URL for internal calls | http://localhost:8000 | No | Both |
| `CORS_ORIGINS` | CORS allowed origins (comma-separated) | - | No | API |

### 6. RAG System Configuration

| Variable | Description | Default | Required | Used By |
|----------|-------------|---------|----------|---------|
| `RAG_SIMILARITY_THRESHOLD` | Similarity threshold for document retrieval | 0.3 | No | Both |
| `RAG_MAX_CHUNKS` | Maximum chunks to retrieve | 10 | No | Both |
| `RAG_TOKEN_BUDGET` | Token budget for responses | 4000 | No | Both |
| `RAG_EMBEDDING_MODEL` | OpenAI embedding model | text-embedding-3-small | No | Both |
| `RAG_VECTOR_DIMENSION` | Vector dimension for embeddings | 1536 | No | Both |

### 7. Worker-Specific Configuration

| Variable | Description | Default | Required | Used By |
|----------|-------------|---------|----------|---------|
| `WORKER_POLL_INTERVAL` | Polling interval for job processing | - | No | Worker |
| `WORKER_MAX_RETRIES` | Maximum retry attempts | - | No | Worker |
| `WORKER_RETRY_BASE_DELAY` | Base delay for retries | - | No | Worker |
| `WORKER_LOG_LEVEL` | Worker-specific logging level | - | No | Worker |

### 8. Application Configuration

| Variable | Description | Default | Required | Used By |
|----------|-------------|---------|----------|---------|
| `APP_VERSION` | Application version | 1.0.0 | No | Both |
| `KEEP_ALIVE` | Keep-alive timeout | 75 | No | API |
| `MAX_REQUESTS` | Maximum requests per worker | 1000 | No | API |
| `MAX_REQUESTS_JITTER` | Jitter for max requests | 100 | No | API |
| `WORKERS` | Number of worker processes | 1 | No | API |

## Environment-Specific Defaults

### Development Environment
- `LOG_LEVEL`: DEBUG
- `DEBUG`: true
- `SERVICE_PORT`: 8000
- `RAG_MAX_CHUNKS`: 10
- `RAG_TOKEN_BUDGET`: 4000

### Testing Environment
- `LOG_LEVEL`: WARNING
- `DEBUG`: false
- `SERVICE_PORT`: 8001
- `RAG_MAX_CHUNKS`: 8
- `RAG_TOKEN_BUDGET`: 3000
- `DATABASE_SCHEMA`: upload_pipeline_test

### Production Environment
- `LOG_LEVEL`: ERROR
- `DEBUG`: false
- `SERVICE_PORT`: 8000
- `RAG_MAX_CHUNKS`: 10
- `RAG_TOKEN_BUDGET`: 4000

## Staging Environment Recommendations

### Required Staging Variables
```bash
# Core Environment
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO

# Database (Staging)
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/staging_db
DATABASE_SCHEMA=upload_pipeline_staging

# Supabase (Staging)
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=staging_service_role_key

# External APIs (Staging/Test)
OPENAI_API_KEY=staging_openai_key
LLAMAPARSE_API_KEY=staging_llamaparse_key
ANTHROPIC_API_KEY=staging_anthropic_key

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
API_BASE_URL=https://staging-api.onrender.com
CORS_ORIGINS=https://staging-frontend.vercel.app,https://staging-admin.vercel.app

# RAG Configuration (Staging)
RAG_SIMILARITY_THRESHOLD=0.3
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_VECTOR_DIMENSION=1536

# Worker Configuration
WORKER_POLL_INTERVAL=30
WORKER_MAX_RETRIES=3
WORKER_RETRY_BASE_DELAY=5
WORKER_LOG_LEVEL=INFO
```

### Optional Staging Variables
```bash
# Application Configuration
APP_VERSION=1.0.0-staging
KEEP_ALIVE=75
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
WORKERS=1
```

## Environment Variable Validation

### Required Variables Check
The following variables must be present for services to function:

**API Service**:
- `ENVIRONMENT`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `LLAMAPARSE_API_KEY`

**Worker Service**:
- `ENVIRONMENT`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `LLAMAPARSE_API_KEY`

### Validation Logic
The configuration manager validates:
1. Required variables are present
2. Database URL is valid
3. API keys are non-empty
4. Port numbers are valid (1-65535)
5. Similarity threshold is in range (0, 1]
6. Chunk limits are positive integers

## Security Considerations

### Sensitive Variables
- `SUPABASE_SERVICE_ROLE_KEY`
- `SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `LLAMAPARSE_API_KEY`
- `DATABASE_URL`
- `SUPABASE_DB_PASSWORD`

### Staging Security
- Use staging-specific API keys with limited scope
- Implement staging database isolation
- Use staging-specific Supabase project
- Configure staging-specific CORS origins
- Implement staging-specific monitoring

## Configuration Loading Order

1. **Base Configuration**: `.env` file
2. **Environment-Specific**: `.env.{environment}` file
3. **Production Override**: `.env.production` file (for testing/staging)
4. **Environment Variables**: System environment variables (highest priority)

## Monitoring and Alerting

### Environment Variable Monitoring
- Track missing required variables
- Monitor API key validity
- Alert on configuration changes
- Validate environment consistency

### Staging-Specific Monitoring
- Monitor staging service health
- Track staging environment variables
- Alert on staging configuration drift
- Validate staging service connectivity

## Conclusion

This inventory provides a complete reference for environment variable configuration across all Render services. The staging environment should use staging-specific values while maintaining the same variable structure and validation logic.

**Next Steps**:
1. Create staging environment variable templates
2. Set up staging-specific API keys and database connections
3. Configure staging service environment variables
4. Validate staging environment variable loading
5. Implement staging environment variable monitoring

---

**Document Status**: Complete  
**Last Updated**: January 21, 2025  
**Next Review**: After staging service creation
