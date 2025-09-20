# Staging Service Communication Validation

**Date**: January 21, 2025  
**Purpose**: Validate inter-service communication between staging API and worker services  
**Environment**: Staging  

## Validation Overview

This document outlines the comprehensive validation procedures for staging service communication, including database connectivity, job queuing, and end-to-end workflow testing.

## Pre-Validation Checklist

### Service Status
- [ ] API service deployment completed successfully
- [ ] Worker service deployment completed successfully
- [ ] Both services are running and accessible
- [ ] Environment variables configured correctly

### Database Status
- [ ] Database connectivity established
- [ ] `upload_pipeline` schema accessible
- [ ] Required tables exist and are accessible
- [ ] Service role permissions configured

## Validation Procedures

### 1. Service Health Validation

#### API Service Health Check
```bash
# Test API service health endpoint
curl -f ***REMOVED***/health

# Expected Response: 200 OK
# {
#   "status": "healthy",
#   "environment": "staging",
#   "timestamp": "2025-01-21T18:00:00Z"
# }
```

#### Worker Service Health Check
```bash
# Test worker service database connectivity
# This is validated through job processing capability
```

### 2. Database Connectivity Validation

#### Connection Test
```sql
-- Test basic database connectivity
SELECT 1 as connection_test;

-- Test schema access
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name = 'upload_pipeline';

-- Test table access
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'upload_pipeline' 
ORDER BY table_name;
```

#### Expected Tables
- `documents` - Document metadata storage
- `upload_jobs` - Job queue for processing
- `document_chunks` - Processed text chunks with embeddings
- `events` - Event logging
- `webhook_log` - Webhook processing logs
- `architecture_notes` - Technical debt documentation

### 3. Job Queue Functionality Validation

#### Create Test Job
```sql
-- Insert a test document
INSERT INTO upload_pipeline.documents (
    document_id, user_id, filename, mime, bytes_len, 
    file_sha256, raw_path, processing_status, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    gen_random_uuid(),
    'test-document.pdf',
    'application/pdf',
    1024,
    'test-sha256-hash',
    'test/path/document.pdf',
    'uploaded',
    NOW(),
    NOW()
);

-- Insert a test job
INSERT INTO upload_pipeline.upload_jobs (
    job_id, document_id, status, state, progress, 
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    (SELECT document_id FROM upload_pipeline.documents 
     WHERE filename = 'test-document.pdf' LIMIT 1),
    'uploaded',
    'queued',
    '{"test": true}',
    NOW(),
    NOW()
);
```

#### Verify Job Processing
```sql
-- Check job status
SELECT job_id, status, state, created_at, updated_at 
FROM upload_pipeline.upload_jobs 
WHERE status = 'uploaded' 
ORDER BY created_at DESC 
LIMIT 5;

-- Monitor job processing
SELECT status, COUNT(*) as count 
FROM upload_pipeline.upload_jobs 
GROUP BY status 
ORDER BY count DESC;
```

### 4. Inter-Service Communication Test

#### End-to-End Workflow Test
1. **Upload Document**: Create a test document via API
2. **Job Creation**: Verify job is created in database
3. **Job Processing**: Monitor worker picking up and processing job
4. **Status Updates**: Verify job status progression
5. **Completion**: Confirm job reaches terminal state

#### API Endpoint Testing
```bash
# Test document upload endpoint
curl -X POST ***REMOVED***/api/upload-pipeline/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <test-token>" \
  -d '{
    "filename": "test-document.pdf",
    "mime": "application/pdf",
    "bytes_len": 1024,
    "sha256": "test-sha256-hash"
  }'

# Expected Response: Upload response with job ID and signed URL
```

### 5. Error Handling Validation

#### Database Connection Errors
- [ ] Test with invalid database credentials
- [ ] Verify error logging and handling
- [ ] Confirm graceful degradation

#### Job Processing Errors
- [ ] Test with malformed job data
- [ ] Verify retry logic and error handling
- [ ] Confirm job status updates on failure

#### Service Communication Errors
- [ ] Test with database unavailable
- [ ] Verify circuit breaker functionality
- [ ] Confirm error propagation

### 6. Performance Validation

#### Job Processing Performance
- [ ] Measure job processing time
- [ ] Test concurrent job processing
- [ ] Verify database query performance

#### Service Response Times
- [ ] API response time under load
- [ ] Worker polling efficiency
- [ ] Database query optimization

### 7. Security Validation

#### Database Access
- [ ] Verify service role permissions
- [ ] Test schema-level access control
- [ ] Confirm no cross-environment data access

#### API Security
- [ ] Test authentication requirements
- [ ] Verify CORS configuration
- [ ] Confirm input validation

#### Environment Isolation
- [ ] Verify staging-specific configurations
- [ ] Test API key isolation
- [ ] Confirm no production data access

## Monitoring and Alerting

### Key Metrics to Monitor
1. **Job Queue Health**
   - Pending jobs count
   - Processing time per job
   - Failed jobs count
   - Retry attempts

2. **Service Health**
   - API response times
   - Worker polling frequency
   - Database connection pool status
   - Error rates

3. **Resource Utilization**
   - CPU usage
   - Memory usage
   - Database connections
   - Network I/O

### Alerting Thresholds
- Job queue backlog > 100 jobs
- Job processing time > 5 minutes
- API response time > 2 seconds
- Error rate > 5%
- Database connection failures

## Troubleshooting Guide

### Common Issues

#### 1. Service Not Starting
**Symptoms**: 502 errors, service unavailable
**Causes**: 
- Environment variable misconfiguration
- Database connection issues
- Missing dependencies
**Solutions**:
- Check environment variables
- Verify database credentials
- Review deployment logs

#### 2. Job Queue Stalls
**Symptoms**: Jobs not processing, worker idle
**Causes**:
- Database connection issues
- Worker service down
- Job data corruption
**Solutions**:
- Check worker service status
- Verify database connectivity
- Review job data integrity

#### 3. Database Connection Failures
**Symptoms**: Connection timeouts, authentication errors
**Causes**:
- Invalid credentials
- Network issues
- Database unavailable
**Solutions**:
- Verify credentials
- Check network connectivity
- Confirm database status

### Debug Commands
```bash
# Check service logs
curl ***REMOVED***/health

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Check job queue status
psql $DATABASE_URL -c "SELECT status, COUNT(*) FROM upload_pipeline.upload_jobs GROUP BY status;"

# Check recent jobs
psql $DATABASE_URL -c "SELECT job_id, status, created_at FROM upload_pipeline.upload_jobs ORDER BY created_at DESC LIMIT 10;"
```

## Validation Results

### Test Results Template
```
Date: [DATE]
Environment: Staging
Tester: [NAME]

Service Health:
- [ ] API Service: [STATUS]
- [ ] Worker Service: [STATUS]
- [ ] Database: [STATUS]

Job Queue:
- [ ] Job Creation: [STATUS]
- [ ] Job Processing: [STATUS]
- [ ] Status Updates: [STATUS]

Communication:
- [ ] API to Database: [STATUS]
- [ ] Worker to Database: [STATUS]
- [ ] End-to-End Workflow: [STATUS]

Security:
- [ ] Database Access: [STATUS]
- [ ] API Authentication: [STATUS]
- [ ] Environment Isolation: [STATUS]

Performance:
- [ ] Response Times: [STATUS]
- [ ] Job Processing: [STATUS]
- [ ] Resource Usage: [STATUS]

Issues Found:
- [LIST ISSUES]

Recommendations:
- [LIST RECOMMENDATIONS]
```

## Next Steps

1. Execute validation procedures
2. Document test results
3. Address any issues found
4. Implement monitoring and alerting
5. Create operational runbooks

---

**Document Status**: Ready for Execution  
**Last Updated**: January 21, 2025  
**Next Review**: After validation completion
