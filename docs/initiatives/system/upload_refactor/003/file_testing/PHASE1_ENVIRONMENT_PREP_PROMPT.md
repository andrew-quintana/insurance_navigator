# PHASE 1: Environment Preparation Prompt

## Objective
Prepare and validate the testing environment for upload refactor 003 file testing, ensuring all services are running and accessible for document upload testing.

## Context
You are testing the upload refactor 003 implementation by uploading two specific insurance documents and verifying they are correctly stored in Supabase buckets and database tables. This phase focuses on getting the environment ready.

## Tasks

### 1. Service Health Verification
- Start the upload refactor 003 services using docker-compose or alternative method
- Verify API server is running on http://localhost:8000
- Check health endpoint: `GET http://localhost:8000/health`
- Verify mock services (llamaparse, openai) are responsive
- Confirm database connectivity

### 2. Upload Service Endpoint Discovery
- Identify the correct upload endpoint (likely `/api/v2/upload` based on main.py:208)
- Test authentication requirements and token generation
- Verify CORS configuration for file uploads
- Document the complete API endpoint structure

### 3. Database Access Setup
- Verify Supabase connection parameters
- Test database query access for verification
- Identify relevant tables: `upload_pipeline.documents`, `upload_pipeline.upload_jobs`, `upload_pipeline.events`
- Confirm bucket access for storage verification

### 4. Test Document Inventory
- Verify test documents are available:
  - `/examples/simulated_insurance_document.pdf` (1.7KB)
  - `/examples/scan_classic_hmo_parsed.pdf` (2.4MB)
- Calculate file hashes for integrity verification
- Document file metadata (size, type, checksum)

### 5. Baseline State Documentation
- Record current database state (document count, job count)
- Document current bucket contents
- Establish baseline metrics for comparison

## Success Criteria
- [ ] All services are running and healthy
- [ ] Upload endpoint is accessible and documented
- [ ] Database connectivity confirmed
- [ ] Test documents are ready and characterized
- [ ] Baseline state is documented

## Environment Variables Required
Verify these are properly configured:
- `UPLOAD_PIPELINE_SUPABASE_URL`
- `UPLOAD_PIPELINE_SUPABASE_SERVICE_ROLE_KEY`
- `UPLOAD_PIPELINE_LLAMAPARSE_API_URL`
- `UPLOAD_PIPELINE_OPENAI_API_URL`

## Output Required
- Environment status report
- Service health check results
- API endpoint documentation
- Test document specifications
- Baseline state snapshot

## Next Phase
Once environment is prepared, proceed to Phase 2: Upload Execution with the validated setup and documented endpoints.