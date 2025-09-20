# Staging Service Specifications

**Date**: January 21, 2025  
**Purpose**: Detailed specifications for staging service creation and configuration  
**Status**: Phase 2 - Staging Environment Planning  

## Overview

This document provides detailed specifications for creating and configuring staging services based on production service audit findings. These specifications ensure staging services replicate production functionality while maintaining appropriate staging-specific adaptations.

## 1. Staging API Service Specification

### Service Details
- **Service Name**: `insurance-navigator-staging-api`
- **Service Type**: Web Service
- **Runtime**: Docker
- **Region**: Oregon (us-west-2)
- **Plan**: Starter
- **Auto Deploy**: Disabled (manual control for staging)

### Build Configuration
```yaml
# Build Configuration
dockerfile_path: ./Dockerfile
docker_context: .
build_command: docker build -t staging-api .
build_plan: starter

# Build Filter
ignored_paths:
  - ui/**
  - docs/**
  - tests/**
  - examples/**
  - *.md
  - .gitignore
  - README.md

included_paths:
  - api/**
  - backend/shared/**
  - config/render/**
  - supabase/migrations/**
  - requirements-prod.txt
  - Dockerfile
  - main.py
```

### Runtime Configuration
```yaml
# Runtime Configuration
base_image: python:3.11-slim
port: 8000
start_command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-keep-alive 75 --limit-max-requests 1000
health_check_path: /health
health_check_command: curl -f http://localhost:8000/health
```

### Environment Variables
```bash
# Core Environment
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
NODE_ENV=staging

# Database Configuration
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/staging_db
DATABASE_SCHEMA=upload_pipeline
SUPABASE_DB_HOST=staging-db.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_USER=staging_user
SUPABASE_DB_PASSWORD=staging_pass
SUPABASE_DB_NAME=staging_db

# Supabase Configuration
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=staging_service_role_key
SERVICE_ROLE_KEY=staging_service_role_key
SUPABASE_ANON_KEY=staging_anon_key
SUPABASE_STORAGE_URL=https://staging-project.supabase.co/storage/v1

# External API Configuration
OPENAI_API_KEY=staging_openai_key
LLAMAPARSE_API_KEY=staging_llamaparse_key
ANTHROPIC_API_KEY=staging_anthropic_key

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
API_BASE_URL=***REMOVED***
CORS_ORIGINS=https://staging.accessa.ai,https://staging-app.accessa.ai,https://staging-admin.accessa.ai

# RAG Configuration
RAG_SIMILARITY_THRESHOLD=0.3
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_VECTOR_DIMENSION=1536

# Application Configuration
APP_VERSION=1.0.0-staging
KEEP_ALIVE=75
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
WORKERS=1
```

### Networking Configuration
```yaml
# Networking
open_ports:
  - 8000/tcp

# CORS Configuration
cors_origins:
  - https://staging.accessa.ai
  - https://staging-app.accessa.ai
  - https://staging-admin.accessa.ai

# Trusted Hosts
trusted_hosts:
  - staging.accessa.ai
  - staging-app.accessa.ai
  - staging-admin.accessa.ai
  - *.render.com
```

## 2. Staging Worker Service Specification

### Service Details
- **Service Name**: `insurance-navigator-staging-worker`
- **Service Type**: Background Worker
- **Runtime**: Docker
- **Region**: Oregon (us-west-2)
- **Plan**: Starter
- **Auto Deploy**: Disabled (manual control for staging)

### Build Configuration
```yaml
# Build Configuration
dockerfile_path: ./backend/workers/Dockerfile
docker_context: .
build_command: docker build -f backend/workers/Dockerfile -t staging-worker .
build_plan: starter

# Build Filter
ignored_paths: []

included_paths:
  - backend/workers/**
  - backend/shared/**
  - config/render/**
  - supabase/migrations/**
  - requirements.txt
  - pyproject.toml
```

### Runtime Configuration
```yaml
# Runtime Configuration
base_image: python:3.11-slim
start_command: python backend/workers/enhanced_runner.py
health_check: python -c "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('Enhanced worker import successful')"
```

### Environment Variables
```bash
# Core Environment
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
NODE_ENV=staging

# Database Configuration
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/staging_db
DATABASE_SCHEMA=upload_pipeline
SUPABASE_DB_HOST=staging-db.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_USER=staging_user
SUPABASE_DB_PASSWORD=staging_pass
SUPABASE_DB_NAME=staging_db

# Supabase Configuration
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=staging_service_role_key
SERVICE_ROLE_KEY=staging_service_role_key
SUPABASE_ANON_KEY=staging_anon_key
SUPABASE_STORAGE_URL=https://staging-project.supabase.co/storage/v1

# External API Configuration
OPENAI_API_KEY=staging_openai_key
LLAMAPARSE_API_KEY=staging_llamaparse_key
ANTHROPIC_API_KEY=staging_anthropic_key

# Worker Configuration
WORKER_POLL_INTERVAL=30
WORKER_MAX_RETRIES=3
WORKER_RETRY_BASE_DELAY=5
WORKER_LOG_LEVEL=INFO

# RAG Configuration
RAG_SIMILARITY_THRESHOLD=0.3
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_VECTOR_DIMENSION=1536

# Application Configuration
APP_VERSION=1.0.0-staging
```

## 3. Staging Service Dependencies

### Database Dependencies
- **Primary Database**: Supabase PostgreSQL (staging instance)
- **Connection Pool**: asyncpg-based connection pooling
- **Schema**: `upload_pipeline` (same as production)
- **Tables**: 
  - `documents` - Document metadata and status
  - `document_chunks` - Vector embeddings and text chunks
  - `upload_jobs` - Job processing queue

### External Service Dependencies
- **Supabase**: Staging project for database, auth, storage, realtime
- **OpenAI**: Staging API key for embeddings and chat completions
- **LlamaParse**: Staging API key for document processing
- **Anthropic**: Staging API key for alternative chat completions (optional)

### Internal Service Dependencies
- **RAG System**: Document retrieval and similarity search
- **Storage Manager**: File storage and retrieval
- **Service Router**: External service routing and fallbacks
- **Circuit Breakers**: Service failure handling
- **Degradation Managers**: Graceful service degradation

## 4. Staging Service Health Checks

### API Service Health Checks
- **Endpoint**: `/health`
- **Method**: GET
- **Expected Response**: 200 OK with service status
- **Timeout**: 30 seconds
- **Interval**: 30 seconds

### Worker Service Health Checks
- **Check**: Import validation for enhanced base worker
- **Command**: `python -c "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('Enhanced worker import successful')"`
- **Timeout**: 30 seconds
- **Interval**: 30 seconds

## 5. Staging Service Monitoring

### Performance Monitoring
- **Response Time**: API response time monitoring
- **Job Processing**: Worker job processing time monitoring
- **Database Connections**: Connection pool monitoring
- **External API Calls**: External service response time monitoring

### Error Monitoring
- **API Errors**: HTTP error rate monitoring
- **Worker Errors**: Job processing error monitoring
- **Database Errors**: Database connection error monitoring
- **External API Errors**: External service error monitoring

### Resource Monitoring
- **CPU Usage**: CPU utilization monitoring
- **Memory Usage**: Memory utilization monitoring
- **Disk Usage**: Disk space monitoring
- **Network Usage**: Network traffic monitoring

## 6. Staging Service Security

### Authentication
- **JWT Tokens**: Supabase JWT token validation
- **Service Role Keys**: Staging-specific service role keys
- **API Keys**: Staging-specific API keys with limited scope

### Network Security
- **SSL/TLS**: Automatic SSL via Render
- **CORS**: Staging-specific CORS configuration
- **Firewall**: Render's built-in firewall protection

### Data Security
- **Database Isolation**: Separate staging database
- **Storage Isolation**: Staging-specific storage buckets
- **Log Security**: Staging-specific log aggregation

## 7. Staging Service Deployment

### Deployment Process
1. **Service Creation**: Create services using Render MCP
2. **Configuration**: Apply staging environment variables
3. **Validation**: Run health checks and functionality tests
4. **Monitoring**: Set up staging monitoring and alerting

### Rollback Procedures
- **Service Rollback**: Revert to previous service configuration
- **Environment Rollback**: Revert environment variable changes
- **Database Rollback**: Restore from staging database backup

### Emergency Procedures
- **Service Restart**: Restart staging services if needed
- **Configuration Reset**: Reset to known good configuration
- **Database Recovery**: Restore staging database from backup

## 8. Staging Service Validation

### Pre-Deployment Validation
- [ ] Verify staging database configuration
- [ ] Validate staging environment variables
- [ ] Test staging service builds
- [ ] Confirm staging API keys

### Post-Deployment Validation
- [ ] Run health checks on all services
- [ ] Test API endpoints functionality
- [ ] Validate worker job processing
- [ ] Verify database connectivity
- [ ] Test external API integrations

### Performance Validation
- [ ] Measure API response times
- [ ] Test worker job processing times
- [ ] Validate database connection performance
- [ ] Test external API response times

## 9. Staging Service Maintenance

### Regular Maintenance
- **Health Checks**: Daily health check monitoring
- **Performance Review**: Weekly performance analysis
- **Security Review**: Monthly security assessment
- **Configuration Audit**: Quarterly configuration review

### Update Procedures
- **Service Updates**: Update staging services as needed
- **Configuration Updates**: Update environment variables
- **Dependency Updates**: Update external service dependencies
- **Security Updates**: Apply security patches and updates

## 10. Staging Service Troubleshooting

### Common Issues
- **Service Startup Failures**: Check environment variables and dependencies
- **Database Connection Issues**: Verify database configuration and connectivity
- **External API Issues**: Check API keys and service availability
- **Performance Issues**: Monitor resource usage and optimize configuration

### Debugging Procedures
- **Log Analysis**: Review service logs for errors
- **Health Check Analysis**: Analyze health check responses
- **Performance Analysis**: Monitor performance metrics
- **Dependency Analysis**: Check external service dependencies

## Conclusion

These specifications provide a comprehensive guide for creating and configuring staging services that replicate production functionality while maintaining appropriate staging-specific adaptations. The specifications ensure staging services are properly configured, secure, and optimized for development and testing purposes.

**Next Steps**:
1. Create staging services using these specifications
2. Configure staging environment variables
3. Validate staging service functionality
4. Set up staging monitoring and alerting
5. Document staging service operations

---

**Document Status**: Complete  
**Last Updated**: January 21, 2025  
**Next Review**: After staging service creation
