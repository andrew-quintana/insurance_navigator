# Staging Environment Configuration Plan

**Date**: January 21, 2025  
**Purpose**: Comprehensive staging environment configuration based on production service audit findings  
**Status**: Phase 2 - Staging Environment Planning  

## Executive Summary

This document defines the complete staging environment configuration for the insurance_navigator project, based on production service audit findings and existing staging database setup. The configuration ensures staging services replicate production functionality while maintaining appropriate staging-specific adaptations.

## 1. Staging Database Configuration Review

### Existing Staging Database Setup
Based on the existing `config/environment/staging.yaml` configuration:

```yaml
# Database Configuration
database:
  url: ${DATABASE_URL}
  schema: upload_pipeline
  pool_size: 10
  max_overflow: 15
  pool_timeout: 30
  pool_recycle: 3600
```

### Staging Database Characteristics
- **Schema**: `upload_pipeline` (same as production)
- **Connection Pool**: 10 connections with 15 max overflow
- **Timeout**: 30 seconds with 3600s recycle
- **Environment**: Staging-specific database instance
- **Isolation**: Separate from production database

### Database Environment Variables
```bash
# Staging Database Configuration
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/staging_db
DATABASE_SCHEMA=upload_pipeline
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=staging_service_role_key
```

## 2. Staging-Specific Environment Variable Adaptations

### Core Environment Configuration
```bash
# Core Environment
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
NODE_ENV=staging
```

### Database Configuration (Staging)
```bash
# Database (Staging)
DATABASE_URL=postgresql://staging_user:staging_pass@staging-db:5432/staging_db
DATABASE_SCHEMA=upload_pipeline
SUPABASE_DB_HOST=staging-db.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_USER=staging_user
SUPABASE_DB_PASSWORD=staging_pass
SUPABASE_DB_NAME=staging_db
```

### Supabase Configuration (Staging)
```bash
# Supabase (Staging)
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=staging_service_role_key
SERVICE_ROLE_KEY=staging_service_role_key
SUPABASE_ANON_KEY=staging_anon_key
SUPABASE_STORAGE_URL=https://staging-project.supabase.co/storage/v1
```

### External API Configuration (Staging/Test)
```bash
# External APIs (Staging/Test)
OPENAI_API_KEY=staging_openai_key
LLAMAPARSE_API_KEY=staging_llamaparse_key
ANTHROPIC_API_KEY=staging_anthropic_key
```

### Service Configuration (Staging)
```bash
# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
API_BASE_URL=***REMOVED***
CORS_ORIGINS=https://staging.accessa.ai,https://staging-app.accessa.ai,https://staging-admin.accessa.ai
```

### RAG Configuration (Staging)
```bash
# RAG Configuration (Staging)
RAG_SIMILARITY_THRESHOLD=0.3
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_VECTOR_DIMENSION=1536
```

### Worker Configuration (Staging)
```bash
# Worker Configuration
WORKER_POLL_INTERVAL=30
WORKER_MAX_RETRIES=3
WORKER_RETRY_BASE_DELAY=5
WORKER_LOG_LEVEL=INFO
```

### Application Configuration (Staging)
```bash
# Application Configuration
APP_VERSION=1.0.0-staging
KEEP_ALIVE=75
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
WORKERS=1
```

## 3. Staging External Service Configurations

### Supabase Staging Project
- **URL**: `https://staging-project.supabase.co`
- **Database**: Separate staging database instance
- **Storage**: Staging-specific storage buckets
- **Auth**: Staging-specific authentication service
- **Realtime**: Staging-specific realtime channels

### OpenAI Staging Configuration
- **API Key**: Staging-specific OpenAI API key
- **Rate Limits**: Staging-appropriate rate limits
- **Models**: Same models as production (text-embedding-3-small)
- **Usage**: Limited to staging/testing purposes

### LlamaParse Staging Configuration
- **API Key**: Staging-specific LlamaParse API key
- **Webhook URL**: Staging-specific webhook endpoints
- **Rate Limits**: Staging-appropriate rate limits
- **Usage**: Limited to staging/testing purposes

### Anthropic Staging Configuration (Optional)
- **API Key**: Staging-specific Anthropic API key
- **Rate Limits**: Staging-appropriate rate limits
- **Usage**: Limited to staging/testing purposes

## 4. Staging Domain and Networking Requirements

### API Service Networking
- **Domain**: `insurance-navigator-staging-api.onrender.com`
- **Port**: 8000 (internal)
- **Health Check**: `/health` endpoint
- **CORS Origins**: 
  - `https://staging.accessa.ai`
  - `https://staging-app.accessa.ai`
  - `https://staging-admin.accessa.ai`

### Worker Service Networking
- **Service**: Background worker (no external access)
- **Internal Communication**: Database-based job queue
- **Health Check**: Import validation check

### Frontend Integration
- **Staging Frontend**: `https://staging.accessa.ai`
- **Staging App**: `https://staging-app.accessa.ai`
- **Staging Admin**: `https://staging-admin.accessa.ai`

### SSL and Security
- **SSL**: Automatic SSL via Render
- **CORS**: Staging-specific CORS configuration
- **Authentication**: JWT-based authentication
- **API Keys**: Staging-specific API keys

## 5. Staging Resource Allocations

### API Service Resources
- **Plan**: Starter (same as production)
- **CPU**: Limited (starter plan)
- **Memory**: Limited (starter plan)
- **Instances**: 1
- **Region**: Oregon (us-west-2)

### Worker Service Resources
- **Plan**: Starter (same as production)
- **CPU**: Limited (starter plan)
- **Memory**: Limited (starter plan)
- **Instances**: 1
- **Region**: Oregon (us-west-2)

### Resource Justification
- **Staging Workload**: Lower than production
- **Testing Focus**: Development and testing purposes
- **Cost Optimization**: Starter plan sufficient for staging
- **Scalability**: Can upgrade if needed

## 6. Staging Service Naming and Organizational Strategy

### Service Naming Convention
- **API Service**: `insurance-navigator-staging-api`
- **Worker Service**: `insurance-navigator-staging-worker`
- **Database**: `insurance-navigator-staging-db` (if separate)
- **Storage**: `insurance-navigator-staging-storage`

### Service Organization
- **Environment Prefix**: `staging-` for all services
- **Service Type**: Clear service type identification
- **Project Identification**: `insurance-navigator` prefix
- **Consistency**: Matches production naming pattern

### Service Grouping
- **API Services**: Grouped under staging API services
- **Worker Services**: Grouped under staging worker services
- **Database Services**: Grouped under staging database services
- **Storage Services**: Grouped under staging storage services

## 7. Staging Environment Variables Template

### Complete Staging Environment Variables
```bash
# ===========================================
# STAGING ENVIRONMENT CONFIGURATION
# ===========================================

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

# Worker Configuration
WORKER_POLL_INTERVAL=30
WORKER_MAX_RETRIES=3
WORKER_RETRY_BASE_DELAY=5
WORKER_LOG_LEVEL=INFO

# Application Configuration
APP_VERSION=1.0.0-staging
KEEP_ALIVE=75
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
WORKERS=1
```

## 8. Staging Service Configuration Specifications

### API Service Configuration
```yaml
# API Service Configuration
name: insurance-navigator-staging-api
runtime: docker
region: oregon
plan: starter
auto_deploy: false  # Manual control for staging
build_command: docker build -t staging-api .
start_command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-keep-alive 75 --limit-max-requests 1000
health_check_path: /health
port: 8000
```

### Worker Service Configuration
```yaml
# Worker Service Configuration
name: insurance-navigator-staging-worker
runtime: docker
region: oregon
plan: starter
auto_deploy: false  # Manual control for staging
build_command: docker build -f backend/workers/Dockerfile -t staging-worker .
start_command: python backend/workers/enhanced_runner.py
health_check: python -c "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('Enhanced worker import successful')"
```

## 9. Staging Environment Validation

### Required Validations
- [ ] Staging API service responds to health checks
- [ ] Staging worker service processes test jobs
- [ ] All environment variables properly loaded
- [ ] Database connections established
- [ ] External API integrations working
- [ ] CORS configuration correct
- [ ] SSL certificates valid

### Performance Baselines
- **API Response Time**: < 2 seconds for health checks
- **Worker Job Processing**: < 30 seconds for test jobs
- **Database Connection**: < 1 second connection time
- **External API Calls**: < 5 seconds response time

## 10. Security Considerations

### Staging Security
- **API Keys**: Staging-specific keys with limited scope
- **Database**: Isolated staging database
- **CORS**: Staging-specific origins only
- **SSL**: Automatic SSL via Render
- **Monitoring**: Staging-specific monitoring

### Data Isolation
- **Database**: Separate staging database instance
- **Storage**: Staging-specific storage buckets
- **API Keys**: Staging-specific API keys
- **Logs**: Staging-specific log aggregation

## 11. Monitoring and Alerting

### Staging Monitoring
- **Health Checks**: Service health monitoring
- **Performance**: Response time monitoring
- **Errors**: Error rate monitoring
- **Dependencies**: External service monitoring

### Staging Alerting
- **Service Down**: Immediate alerts
- **High Error Rate**: Threshold-based alerts
- **Performance Degradation**: Response time alerts
- **Dependency Failures**: External service alerts

## 12. Implementation Checklist

### Pre-Implementation
- [ ] Verify staging database configuration
- [ ] Obtain staging API keys
- [ ] Configure staging domain settings
- [ ] Prepare staging environment variables

### Implementation
- [ ] Create staging API service
- [ ] Create staging worker service
- [ ] Configure staging environment variables
- [ ] Set up staging networking
- [ ] Validate staging services

### Post-Implementation
- [ ] Run comprehensive health checks
- [ ] Test staging functionality
- [ ] Validate staging performance
- [ ] Set up staging monitoring
- [ ] Document staging configuration

## Conclusion

This staging environment configuration provides a comprehensive plan for creating staging services that replicate production functionality while maintaining appropriate staging-specific adaptations. The configuration ensures staging services are properly isolated, secure, and optimized for development and testing purposes.

**Next Steps**:
1. Create staging services using Render MCP
2. Configure staging environment variables
3. Set up staging networking and security
4. Validate staging service functionality
5. Implement staging monitoring and alerting

---

**Document Status**: Complete  
**Last Updated**: January 21, 2025  
**Next Review**: After staging service creation
