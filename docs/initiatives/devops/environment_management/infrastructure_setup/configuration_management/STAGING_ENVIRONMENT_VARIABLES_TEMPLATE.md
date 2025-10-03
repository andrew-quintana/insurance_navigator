# Staging Environment Variables Template

**Date**: January 21, 2025  
**Purpose**: Complete template for staging environment variables  
**Status**: Phase 2 - Staging Environment Planning  

## Overview

This document provides a complete template for staging environment variables based on production service audit findings and existing staging database configuration. This template ensures staging services have all required environment variables with appropriate staging-specific values.

## Complete Staging Environment Variables Template

### Core Environment Configuration
```bash
# ===========================================
# CORE ENVIRONMENT CONFIGURATION
# ===========================================

# Environment Type
ENVIRONMENT=staging

# Debug and Logging
DEBUG=false
LOG_LEVEL=INFO
NODE_ENV=staging

# Application Version
APP_VERSION=1.0.0-staging
```

### Database Configuration
```bash
# ===========================================
# DATABASE CONFIGURATION
# ===========================================

# Primary Database Connection
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/staging_db

# Database Schema
DATABASE_SCHEMA=upload_pipeline
TEST_DATABASE_SCHEMA=upload_pipeline_test

# Supabase Database Details
SUPABASE_DB_HOST=staging-db.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_USER=staging_user
SUPABASE_DB_PASSWORD=staging_pass
SUPABASE_DB_NAME=staging_db
```

### Supabase Configuration
```bash
# ===========================================
# SUPABASE CONFIGURATION
# ===========================================

# Supabase Project
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_ANON_KEY=staging_anon_key
SUPABASE_SERVICE_ROLE_KEY=staging_service_role_key
SERVICE_ROLE_KEY=staging_service_role_key

# Supabase Storage
SUPABASE_STORAGE_URL=https://staging-project.supabase.co/storage/v1
```

### External API Configuration
```bash
# ===========================================
# EXTERNAL API CONFIGURATION
# ===========================================

# OpenAI API
OPENAI_API_KEY=staging_openai_key
OPENAI_API_URL=https://api.openai.com/v1

# LlamaParse API
LLAMAPARSE_API_KEY=staging_llamaparse_key
LLAMAPARSE_API_URL=https://api.llamaparse.com

# Anthropic API (Optional)
ANTHROPIC_API_KEY=staging_anthropic_key
```

### Service Configuration
```bash
# ===========================================
# SERVICE CONFIGURATION
# ===========================================

# Service Host and Port
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000

# API Base URL
API_BASE_URL=https://insurance-navigator-staging-api.onrender.com

# CORS Configuration
CORS_ORIGINS=https://staging.accessa.ai,https://staging-app.accessa.ai,https://staging-admin.accessa.ai
```

### RAG System Configuration
```bash
# ===========================================
# RAG SYSTEM CONFIGURATION
# ===========================================

# Similarity and Retrieval
RAG_SIMILARITY_THRESHOLD=0.3
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000

# Embedding Model
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_VECTOR_DIMENSION=1536
```

### Worker Configuration
```bash
# ===========================================
# WORKER CONFIGURATION
# ===========================================

# Polling and Retry
WORKER_POLL_INTERVAL=30
WORKER_MAX_RETRIES=3
WORKER_RETRY_BASE_DELAY=5

# Logging
WORKER_LOG_LEVEL=INFO
```

### Application Configuration
```bash
# ===========================================
# APPLICATION CONFIGURATION
# ===========================================

# Server Configuration
KEEP_ALIVE=75
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
WORKERS=1
```

## Environment-Specific Variations

### Development Environment
```bash
# Development-specific overrides
DEBUG=true
LOG_LEVEL=DEBUG
SERVICE_PORT=8000
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000
```

### Testing Environment
```bash
# Testing-specific overrides
DEBUG=false
LOG_LEVEL=WARNING
SERVICE_PORT=8001
RAG_MAX_CHUNKS=8
RAG_TOKEN_BUDGET=3000
DATABASE_SCHEMA=upload_pipeline_test
```

### Production Environment
```bash
# Production-specific overrides
DEBUG=false
LOG_LEVEL=ERROR
SERVICE_PORT=8000
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000
```

## Service-Specific Environment Variables

### API Service Only
```bash
# ===========================================
# API SERVICE SPECIFIC VARIABLES
# ===========================================

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
API_BASE_URL=https://insurance-navigator-staging-api.onrender.com

# CORS Configuration
CORS_ORIGINS=https://staging.accessa.ai,https://staging-app.accessa.ai,https://staging-admin.accessa.ai

# Server Configuration
KEEP_ALIVE=75
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
WORKERS=1
```

### Worker Service Only
```bash
# ===========================================
# WORKER SERVICE SPECIFIC VARIABLES
# ===========================================

# Worker Configuration
WORKER_POLL_INTERVAL=30
WORKER_MAX_RETRIES=3
WORKER_RETRY_BASE_DELAY=5
WORKER_LOG_LEVEL=INFO
```

## Environment Variable Validation

### Required Variables
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

### Optional Variables
The following variables are optional but recommended:

**API Service**:
- `ANTHROPIC_API_KEY`
- `CORS_ORIGINS`
- `RAG_SIMILARITY_THRESHOLD`
- `RAG_MAX_CHUNKS`
- `RAG_TOKEN_BUDGET`

**Worker Service**:
- `ANTHROPIC_API_KEY`
- `WORKER_POLL_INTERVAL`
- `WORKER_MAX_RETRIES`
- `WORKER_RETRY_BASE_DELAY`

## Security Considerations

### Sensitive Variables
The following variables contain sensitive information and should be secured:

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
2. **Environment-Specific**: `.env.staging` file
3. **Production Override**: `.env.production` file (for testing/staging)
4. **Environment Variables**: System environment variables (highest priority)

## Environment Variable Monitoring

### Monitoring Requirements
- Track missing required variables
- Monitor API key validity
- Alert on configuration changes
- Validate environment consistency

### Staging-Specific Monitoring
- Monitor staging service health
- Track staging environment variables
- Alert on staging configuration drift
- Validate staging service connectivity

## Implementation Notes

### Render Service Configuration
When creating Render services, use the following approach:

1. **Create Service**: Use Render MCP to create staging services
2. **Set Environment Variables**: Apply staging environment variables
3. **Validate Configuration**: Run health checks and functionality tests
4. **Monitor Services**: Set up staging monitoring and alerting

### Environment Variable Management
- Store sensitive variables securely
- Use staging-specific values
- Validate all required variables
- Monitor variable changes

## Troubleshooting

### Common Issues
- **Missing Variables**: Check required variable list
- **Invalid Values**: Validate variable formats
- **Connection Issues**: Verify database and API configurations
- **Performance Issues**: Check resource allocations

### Debug Procedures
- **Log Analysis**: Review service logs for errors
- **Variable Validation**: Check environment variable loading
- **Health Checks**: Analyze health check responses
- **Dependency Checks**: Verify external service connectivity

## Conclusion

This template provides a complete reference for staging environment variables. Use this template to configure staging services with appropriate staging-specific values while maintaining the same variable structure and validation logic as production services.

**Next Steps**:
1. Create staging services using this template
2. Configure staging-specific API keys and database connections
3. Validate staging environment variable loading
4. Set up staging environment variable monitoring
5. Test staging service functionality

---

**Document Status**: Complete  
**Last Updated**: January 21, 2025  
**Next Review**: After staging service creation
