# FRACAS FM-027 Investigation Checklist

## Pre-Investigation Setup
- [ ] Access to Render MCP tools
- [ ] Access to Supabase MCP tools
- [ ] Local development environment ready
- [ ] Test scripts prepared

## Phase 1: Service Analysis (Immediate)

### Upload Worker Service Investigation
- [ ] Check worker service status using `mcp_render_get_service`
- [ ] Analyze worker logs using `mcp_render_list_logs`
- [ ] Check worker metrics using `mcp_render_get_metrics`
- [ ] Verify worker environment variables
- [ ] Check worker service health and connectivity

### API Service Verification
- [ ] Confirm API service is operational
- [ ] Test API health endpoint
- [ ] Verify API service logs for errors
- [ ] Check API service configuration

## Phase 2: Pipeline Analysis (Next 2 hours)

### Document Processing Flow Analysis
- [ ] Trace complete upload flow: Upload → Storage → Job Creation → Processing
- [ ] Identify where "file not accessible" error occurs
- [ ] Check file storage in Supabase
- [ ] Verify file path resolution
- [ ] Test file access from worker perspective

### Webhook System Investigation
- [ ] Check webhook URL configuration
- [ ] Verify webhook secret handling
- [ ] Analyze webhook creation process
- [ ] Test webhook delivery
- [ ] Check webhook processing logic

### Storage Access Analysis
- [ ] Verify storage bucket permissions
- [ ] Test file access from worker service
- [ ] Check service role key configuration
- [ ] Verify file path resolution
- [ ] Test storage authentication

## Phase 3: Root Cause Identification

### Error Analysis
- [ ] Analyze error message: "Document file is not accessible for processing"
- [ ] Check error reference ID: 10996029-d6fd-4118-a55b-089ac140a3b7
- [ ] Review job details and timestamps
- [ ] Identify failure point in processing pipeline

### Configuration Analysis
- [ ] Compare worker configuration with working setup
- [ ] Check environment variable differences
- [ ] Verify Supabase project configuration
- [ ] Check storage bucket settings

### Dependency Analysis
- [ ] Test external API calls (LLaParse, OpenAI)
- [ ] Verify database connectivity
- [ ] Check storage access patterns
- [ ] Test webhook delivery mechanisms

## Phase 4: Solution Development

### Solution Options
- [ ] **Option A**: Fix file accessibility from worker
- [ ] **Option B**: Resolve webhook delivery issues
- [ ] **Option C**: Update worker configuration
- [ ] **Option D**: Fix storage permissions

### Solution Analysis
- [ ] Evaluate each solution option
- [ ] Assess risks and benefits
- [ ] Determine preferred solution
- [ ] Create implementation plan

## Phase 5: Implementation and Testing

### Local Testing
- [ ] Test solution locally
- [ ] Verify file accessibility
- [ ] Test complete processing pipeline
- [ ] Run test scripts
- [ ] Validate no errors in logs

### Staging Deployment
- [ ] Deploy solution to staging
- [ ] Monitor deployment logs
- [ ] Test document upload and processing
- [ ] Verify webhook functionality
- [ ] Confirm no user-facing errors

### Validation
- [ ] Test multiple document uploads
- [ ] Verify RAG functionality works
- [ ] Check job status monitoring
- [ ] Confirm processing completes successfully
- [ ] Validate user experience

## Phase 6: Documentation and Prevention

### Documentation
- [ ] Document root cause
- [ ] Record solution implemented
- [ ] Update configuration documentation
- [ ] Create troubleshooting guide

### Prevention Measures
- [ ] Add monitoring for file accessibility
- [ ] Implement alerts for processing failures
- [ ] Create dashboards for pipeline health
- [ ] Add integration tests

## Investigation Tools

### Render MCP Commands
```bash
# Check worker service
mcp_render_get_service srv-d37dlmvfte5s73b6uq0g

# Get worker logs
mcp_render_list_logs resource=srv-d37dlmvfte5s73b6uq0g

# Get worker metrics
mcp_render_get_metrics resourceId=srv-d37dlmvfte5s73b6uq0g

# Check API service
mcp_render_get_service srv-d3740ijuibrs738mus1g
```

### Supabase MCP Commands
```bash
# Check database tables
mcp_supabase_production_list_tables

# Query upload jobs
mcp_supabase_production_execute_sql "SELECT * FROM upload_pipeline.upload_jobs ORDER BY created_at DESC LIMIT 10"

# Check documents table
mcp_supabase_production_execute_sql "SELECT * FROM upload_pipeline.documents ORDER BY created_at DESC LIMIT 10"
```

### Test Scripts
```bash
# Run test script
python docs/incidents/fm_027/test_document_processing_failure.py

# Test local processing
python -m backend.workers.upload_worker
```

## Success Criteria

### Investigation Complete When:
- [ ] Root cause identified and documented
- [ ] Worker service configuration understood
- [ ] Webhook system status verified
- [ ] File accessibility issues identified
- [ ] Recommended solution identified

### Resolution Complete When:
- [ ] Document processing works end-to-end
- [ ] Webhook system functions correctly
- [ ] No user-facing errors occur
- [ ] All tests pass
- [ ] Staging deployment successful

## Notes and Observations

### Key Questions to Answer
1. Is the upload worker service running and healthy?
2. Are webhooks being created and delivered correctly?
3. Can the worker access files from Supabase storage?
4. Are there configuration mismatches between services?
5. Is the processing pipeline properly configured?
6. Are there dependency failures (external APIs, database)?

### Investigation Log
- [ ] Record all findings
- [ ] Document error patterns
- [ ] Note configuration differences
- [ ] Track solution attempts
- [ ] Record test results

---

**Investigation Priority**: HIGH  
**Estimated Time**: 3-6 hours  
**Testing Requirement**: MANDATORY local testing before staging deployment
