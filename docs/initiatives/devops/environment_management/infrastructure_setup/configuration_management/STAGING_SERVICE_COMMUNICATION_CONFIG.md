# Staging Service Communication Configuration

**Date**: January 21, 2025  
**Purpose**: Configure and validate inter-service communication between staging API and worker services  
**Environment**: Staging  

## Executive Summary

This document outlines the configuration and validation of inter-service communication between the staging API service (`api-service-staging`) and worker service (`upload-worker-staging`). The services communicate through a database-based job queue system using the `upload_pipeline` schema.

## Service Architecture Overview

### Communication Pattern
```
API Service ──┐
              ├─ Database Job Queue (upload_pipeline.upload_jobs)
              └─ Worker Service
```

### Key Components
1. **API Service**: Creates jobs in the database queue
2. **Worker Service**: Polls database for jobs and processes them
3. **Database**: Shared PostgreSQL instance with `upload_pipeline` schema
4. **Job Queue**: `upload_pipeline.upload_jobs` table with status-based processing

## Service Configuration

### Staging API Service Configuration
- **Service ID**: `srv-d3740ijuibrs738mus1g`
- **Name**: `api-service-staging`
- **URL**: `https://insurance-navigator-staging-api.onrender.com`
- **Port**: 10000 (configured for staging)
- **Type**: Web Service

### Staging Worker Service Configuration
- **Service ID**: `srv-d37dlmvfte5s73b6uq0g`
- **Name**: `upload-worker-staging`
- **Type**: Background Worker
- **Auto Deploy**: Yes (on commit to `staging` branch)

## Environment Variables Configuration

### Required Environment Variables for Both Services

#### Database Configuration
```bash
# Supabase Database Connection
SUPABASE_URL=https://znvwzkdblknkkztqyfnu.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd6a2RibGtua2t6dHF5Zm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0NTYsImV4cCI6MjA2NzI1NjQ1Nn0.k0QHYOgm4EilyyTml57kCGDpbikpEtJCzq-qzGYQZqY
SUPABASE_SERVICE_ROLE_KEY=<staging_service_role_key>
DATABASE_URL=postgresql://postgres:<password>@db.znvwzkdblknkkztqyfnu.supabase.co:5432/postgres
SUPABASE_DB_HOST=db.znvwzkdblknkkztqyfnu.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=<staging_db_password>
SUPABASE_DB_NAME=postgres
DATABASE_SCHEMA=upload_pipeline_staging
```

#### Environment Settings
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
```

#### Service Configuration
```bash
SERVICE_HOST=0.0.0.0
SERVICE_PORT=10000
CORS_ORIGINS=https://insurance-navigator-staging-api.onrender.com,http://localhost:3000
```

#### RAG Configuration
```bash
RAG_SIMILARITY_THRESHOLD=0.3
RAG_MAX_CHUNKS=10
RAG_TOKEN_BUDGET=4000
RAG_EMBEDDING_MODEL=text-embedding-3-small
RAG_VECTOR_DIMENSION=1536
```

#### API Keys (Staging/Test Keys)
```bash
OPENAI_API_KEY=sk-staging-...
ANTHROPIC_API_KEY=sk-ant-staging-...
LLAMAPARSE_API_KEY=llx-staging-...
```

#### Worker-Specific Configuration
```bash
WORKER_POLL_INTERVAL=5
WORKER_MAX_RETRIES=3
WORKER_RETRY_BASE_DELAY=1.0
WORKER_LOG_LEVEL=INFO
```

## Inter-Service Communication Flow

### 1. Job Creation (API Service)
```python
# API creates job in database
await conn.execute("""
    INSERT INTO upload_pipeline.upload_jobs (
        job_id, document_id, status, state, progress, 
        created_at, updated_at
    ) VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
""", job_id, document_id, "uploaded", "queued", json.dumps(payload))
```

### 2. Job Processing (Worker Service)
```python
# Worker polls for jobs
job = await conn.fetchrow("""
    SELECT uj.job_id, uj.document_id, d.user_id, uj.status, uj.state,
           uj.progress, uj.retry_count, uj.last_error, uj.created_at,
           d.raw_path as storage_path, d.mime as mime_type
    FROM upload_pipeline.upload_jobs uj
    JOIN upload_pipeline.documents d ON uj.document_id = d.document_id
    WHERE uj.status IN ('uploaded', 'parsed', 'parse_validated', ...)
    ORDER BY priority, uj.created_at
    FOR UPDATE SKIP LOCKED
    LIMIT 1
""")
```

### 3. Job Status Updates
The worker updates job status through the database:
- `uploaded` → `parsing` → `parsed` → `parse_validated` → `chunking` → `chunks_stored` → `embedding_queued` → `embedding_in_progress` → `embeddings_stored` → `complete`

## Database Schema Requirements

### Required Tables
1. **upload_pipeline.documents**: Document metadata
2. **upload_pipeline.upload_jobs**: Job queue with status tracking
3. **upload_pipeline.document_chunks**: Processed text chunks with embeddings

### Schema Isolation
- **Production**: `upload_pipeline` schema
- **Staging**: `upload_pipeline_staging` schema (recommended for isolation)

## Security Configuration

### Database Access
- Both services use the same database credentials
- Service role key provides elevated permissions
- Schema-level isolation prevents cross-environment data access

### Network Security
- Services communicate only through database
- No direct HTTP communication between services
- CORS configured for staging domains only

### API Keys
- Staging-specific API keys for external services
- Separate from production keys
- Test/development rate limits

## Monitoring and Health Checks

### API Service Health Check
- **Endpoint**: `/health`
- **Port**: 10000
- **Expected Response**: 200 OK with service status

### Worker Service Health Check
- **Method**: Database connectivity test
- **Validation**: Successful job polling query
- **Monitoring**: Job processing metrics

## Validation Procedures

### 1. Service Connectivity
- [ ] API service can connect to database
- [ ] Worker service can connect to database
- [ ] Both services can access `upload_pipeline` schema

### 2. Job Queue Functionality
- [ ] API can create jobs in queue
- [ ] Worker can poll and claim jobs
- [ ] Job status updates work correctly
- [ ] Error handling and retry logic functions

### 3. Inter-Service Communication
- [ ] End-to-end job processing workflow
- [ ] Database transaction consistency
- [ ] Error propagation and handling
- [ ] Performance under load

### 4. Security Validation
- [ ] Database access permissions
- [ ] API key validation
- [ ] CORS configuration
- [ ] Schema isolation

## Troubleshooting

### Common Issues
1. **Database Connection Failures**: Check credentials and network access
2. **Job Queue Stalls**: Verify worker polling and job status updates
3. **Schema Access Issues**: Ensure proper permissions on `upload_pipeline` schema
4. **API Key Errors**: Validate staging-specific keys

### Debug Commands
```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check schema access
psql $DATABASE_URL -c "SELECT * FROM upload_pipeline.upload_jobs LIMIT 1;"

# Check job queue status
psql $DATABASE_URL -c "SELECT status, COUNT(*) FROM upload_pipeline.upload_jobs GROUP BY status;"
```

## Next Steps

1. Configure environment variables for both staging services
2. Validate database connectivity and schema access
3. Test job creation and processing workflows
4. Implement monitoring and alerting
5. Document operational procedures

---

**Document Status**: In Progress  
**Last Updated**: January 21, 2025  
**Next Review**: After environment variable configuration
