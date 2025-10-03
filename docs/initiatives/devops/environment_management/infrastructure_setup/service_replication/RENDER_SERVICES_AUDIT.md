# Render Services Comprehensive Audit Report

**Date**: January 21, 2025  
**Auditor**: AI Assistant  
**Purpose**: Complete documentation of current Render services for staging infrastructure replication  
**Environment**: Production  

## Executive Summary

This audit provides comprehensive documentation of the current Render services for the insurance_navigator project, including detailed configurations, environment variables, dependencies, and performance metrics. The findings will be used to create identical staging services with appropriate environment-specific adaptations.

## Service Overview

### 1. insurance-navigator-api (Web Service)
- **Service ID**: `srv-d0v2nqvdiees73cejf0g`
- **Type**: Web Service
- **Status**: Active (Live)
- **URL**: https://insurance-navigator-api.onrender.com
- **Created**: June 2, 2025
- **Last Updated**: September 20, 2025

### 2. insurance-navigator-worker (Background Worker)
- **Service ID**: `srv-d2h5mr8dl3ps73fvvlog`
- **Type**: Background Worker
- **Status**: Active (Live)
- **Created**: August 17, 2025
- **Last Updated**: September 20, 2025

## Detailed Service Configurations

### API Service Configuration

#### Basic Settings
- **Runtime**: Docker
- **Region**: Oregon
- **Plan**: Starter
- **Auto Deploy**: Yes (on commit to `deployment/cloud-infrastructure` branch)
- **Build Plan**: Starter
- **Instances**: 1
- **Health Check Path**: `/health`
- **Open Ports**: 8000 (TCP)

#### Build Configuration
- **Dockerfile Path**: `./Dockerfile`
- **Docker Context**: `.` (root directory)
- **Build Filter**:
  - **Ignored Paths**: `ui/**`, `docs/**`, `tests/**`, `examples/**`, `*.md`, `.gitignore`, `README.md`
  - **Included Paths**: `api/**`, `backend/shared/**`, `config/render/**`, `supabase/migrations/**`, `requirements-prod.txt`, `Dockerfile`, `main.py`

#### Docker Configuration
- **Base Image**: Python 3.11-slim (multi-stage build)
- **Port**: 8000
- **Health Check**: `curl -f http://localhost:8000/health`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-keep-alive 75 --limit-max-requests 1000`

#### Environment Variables (Inferred from Code)
Based on the main.py and configuration files, the API service requires:

**Core Environment Variables**:
- `ENVIRONMENT` - Environment setting (development/testing/production)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key
- `LLAMAPARSE_API_KEY` - LlamaParse API key
- `ANTHROPIC_API_KEY` - Anthropic API key (optional)

**Service Configuration**:
- `SERVICE_HOST` - Host binding (default: 0.0.0.0)
- `SERVICE_PORT` - Port number (default: 8000)
- `LOG_LEVEL` - Logging level (ERROR for production)
- `DEBUG` - Debug mode (false for production)
- `CORS_ORIGINS` - CORS allowed origins

**RAG Configuration**:
- `RAG_SIMILARITY_THRESHOLD` - Similarity threshold (default: 0.3)
- `RAG_MAX_CHUNKS` - Maximum chunks to retrieve (default: 10)
- `RAG_TOKEN_BUDGET` - Token budget for responses (default: 4000)
- `RAG_EMBEDDING_MODEL` - Embedding model (default: text-embedding-3-small)
- `RAG_VECTOR_DIMENSION` - Vector dimension (default: 1536)

**Database Configuration**:
- `SUPABASE_DB_HOST` - Database host
- `SUPABASE_DB_PORT` - Database port (default: 5432)
- `SUPABASE_DB_USER` - Database user
- `SUPABASE_DB_PASSWORD` - Database password
- `SUPABASE_DB_NAME` - Database name
- `DATABASE_SCHEMA` - Database schema (default: upload_pipeline)

### Worker Service Configuration

#### Basic Settings
- **Runtime**: Docker
- **Region**: Oregon
- **Plan**: Starter
- **Auto Deploy**: Yes (on commit to `deployment/cloud-infrastructure` branch)
- **Build Plan**: Starter
- **Instances**: 1

#### Build Configuration
- **Dockerfile Path**: `./backend/workers/Dockerfile`
- **Docker Context**: `.` (root directory)
- **Build Filter**:
  - **Ignored Paths**: None
  - **Included Paths**: `backend/workers/**`, `backend/shared/**`, `config/render/**`, `supabase/migrations/**`, `requirements.txt`, `pyproject.toml`

#### Docker Configuration
- **Base Image**: Python 3.11-slim (multi-stage build)
- **Health Check**: `python -c "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('Enhanced worker import successful')"`
- **Start Command**: `python backend/workers/enhanced_runner.py`

#### Environment Variables (Inferred from Code)
The worker service shares the same environment variables as the API service, with additional worker-specific settings:

**Worker-Specific Variables**:
- `WORKER_POLL_INTERVAL` - Polling interval for job processing
- `WORKER_MAX_RETRIES` - Maximum retry attempts
- `WORKER_RETRY_BASE_DELAY` - Base delay for retries
- `WORKER_LOG_LEVEL` - Worker-specific logging level

## Service Dependencies and External Integrations

### Database Dependencies
- **Primary Database**: Supabase PostgreSQL
- **Connection Pool**: asyncpg-based connection pooling
- **Schema**: `upload_pipeline` (main schema)
- **Tables**: 
  - `documents` - Document metadata and status
  - `document_chunks` - Vector embeddings and text chunks
  - `upload_jobs` - Job processing queue

### External API Integrations
1. **Supabase**:
   - Authentication service
   - Database operations
   - Storage service
   - Real-time subscriptions

2. **OpenAI**:
   - Text embeddings (text-embedding-3-small)
   - Chat completions
   - RAG system integration

3. **LlamaParse**:
   - PDF document parsing
   - Document processing pipeline
   - Webhook-based status updates

4. **Anthropic** (Optional):
   - Alternative AI model for chat completions

### Internal Service Dependencies
- **RAG System**: Document retrieval and similarity search
- **Storage Manager**: File storage and retrieval
- **Service Router**: External service routing and fallbacks
- **Circuit Breakers**: Service failure handling
- **Degradation Managers**: Graceful service degradation

## Resource Allocations and Performance

### Current Resource Allocation
- **Plan**: Starter (both services)
- **CPU**: Limited (starter plan)
- **Memory**: Limited (starter plan)
- **Instances**: 1 per service
- **Region**: Oregon (us-west-2)

### Performance Metrics
**Note**: No recent performance data available in the metrics API for the queried time range. This may indicate:
- Services are not actively processing requests
- Metrics collection is not enabled
- Services are in idle state

### Recent Deployment Activity
**API Service** (Last 5 deployments):
1. **Latest** (Sep 20, 2025): Fix FM-018 - Resolve generic response generation issue
2. **Previous** (Sep 20, 2025): Complete FM-016 and FM-017 resolution
3. **Earlier** (Sep 19, 2025): Fix FM-017 - Worker storage access issue
4. **Earlier** (Sep 19, 2025): Fix FM-016 - Resolve 'Parsed content is empty' error
5. **Earlier** (Sep 19, 2025): Fix FM-015 - Use correct database system

**Worker Service** (Last 5 deployments):
1. **Latest** (Sep 20, 2025): Complete FM-016 and FM-017 resolution
2. **Previous** (Sep 19, 2025): Fix FM-017 - Worker storage access issue
3. **Earlier** (Sep 19, 2025): Fix FM-014 - Mock service fallback masking production issues
4. **Earlier** (Sep 19, 2025): Fix critical hardcoded development values
5. **Earlier** (Sep 19, 2025): Fix FM-013 - Update db_pool.py to use environment variables

## Architecture Analysis

### Service Architecture
- **API Service**: FastAPI-based web service with comprehensive middleware
- **Worker Service**: Background job processor using enhanced base worker
- **Communication**: Database-based job queue system
- **Storage**: Supabase storage with direct HTTP access
- **Monitoring**: Structured logging and health checks

### Key Features
1. **Document Processing Pipeline**: Complete PDF processing with LlamaParse
2. **RAG System**: Vector-based document retrieval and similarity search
3. **Authentication**: Supabase-based user authentication
4. **Resilience**: Circuit breakers and degradation managers
5. **Health Monitoring**: Comprehensive health check endpoints

### Security Considerations
- Service role keys for Supabase access
- JWT-based authentication
- CORS configuration
- Environment-based configuration management
- No hardcoded secrets (recently fixed)

## Staging Replication Requirements

### Configuration Preservation
- **Runtime**: Docker (both services)
- **Region**: Oregon (or staging-specific region)
- **Plan**: Starter (or staging-appropriate plan)
- **Build Commands**: Identical Docker build processes
- **Health Checks**: Same health check endpoints
- **Ports**: Same port configurations

### Environment Variable Adaptations
- **Database URLs**: Point to staging database instances
- **API Keys**: Use staging/test API keys
- **Service URLs**: Update to staging-specific endpoints
- **CORS Origins**: Add staging domain configurations
- **Log Levels**: Adjust for staging debugging needs

### Service Dependencies
- **Staging Database**: Separate Supabase project or staging schema
- **External APIs**: Staging/test API endpoints
- **Storage**: Staging storage buckets
- **Monitoring**: Staging-specific logging and alerting

## Recommendations for Staging Setup

### 1. Service Creation Strategy
- Create services with identical base configurations
- Apply staging-specific environment variables
- Maintain same Docker build processes
- Preserve health check configurations

### 2. Environment Variable Management
- Use staging-specific database connections
- Implement staging API key management
- Configure staging-specific CORS origins
- Set appropriate logging levels for staging

### 3. Monitoring and Observability
- Implement staging-specific monitoring
- Set up staging health check alerts
- Configure staging log aggregation
- Monitor staging service performance

### 4. Testing and Validation
- Validate staging service startup
- Test staging service health checks
- Verify staging database connectivity
- Test staging external API integrations

## Conclusion

The current Render services are well-configured with comprehensive error handling, monitoring, and resilience features. The staging replication should preserve all core functionality while adapting environment-specific configurations. The services demonstrate recent active development with multiple bug fixes and improvements, indicating a mature and stable production system.

**Next Steps**:
1. Create staging services using Render MCP
2. Configure staging-specific environment variables
3. Set up staging database and external service connections
4. Validate staging service functionality
5. Implement staging monitoring and alerting

---

**Document Status**: Complete  
**Last Updated**: January 21, 2025  
**Next Review**: After staging service creation
