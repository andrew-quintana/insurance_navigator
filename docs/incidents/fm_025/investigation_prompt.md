# FRACAS FM-025 Investigation Prompt

## Failure Mode Analysis and Corrective Action System (FRACAS)

**FRACAS ID**: FM-025  
**Date**: September 30, 2025, 22:07 UTC  
**Environment**: Staging  
**Service**: Upload Pipeline - Document Processing & Webhook System  
**Severity**: High (Document processing failing, user-facing errors)  
**Related**: FM-024 (RESOLVED - Storage authentication), FM-023 (RESOLVED - Database constraint violation)

---

## Executive Summary

The upload pipeline is experiencing document processing failures after successful file uploads. While storage authentication (FM-024) has been resolved, a new critical issue has emerged where documents are being queued for processing but failing with "Document file is not accessible for processing" errors.

**Current Status**: 
- ✅ Storage authentication working (FM-024 resolved)
- ✅ File uploads completing successfully
- ✅ Database operations working (upload jobs created)
- ❌ Document processing failing (webhook/worker issues)
- ❌ User-facing errors: "Document file is not accessible for processing"

---

## Failure Description

### Primary Symptom
```
"error": "Non-retryable error: user_facing_error: Document file is not accessible for processing. Please try uploading again. (Reference: 76421768-7eb0-45e7-8fb6-27001206b1df)"
```

### Error Context
- **Location**: Upload worker staging service
- **Trigger**: Document processing after successful file upload
- **Result**: Job status "failed_parse" with non-retryable error
- **Impact**: Documents cannot be processed, users receive error messages
- **Reference ID**: 76421768-7eb0-45e7-8fb6-27001206b1df

### User Experience Impact
- Users can upload files successfully
- Files are stored in Supabase storage
- Processing fails with user-facing error message
- No document analysis or RAG functionality available
- Users must retry uploads (which will likely fail again)

---

## Root Cause Analysis Required

### 1. Upload Worker Staging Investigation
**Task**: Analyze the upload worker staging service configuration and logs

**Investigation Steps**:
1. Check upload worker staging service status and logs:
   ```bash
   # Use Render MCP to inspect upload worker
   mcp_render_get_service srv-d37dlmvfte5s73b6uq0g
   mcp_render_list_logs resource=srv-d37dlmvfte5s73b6uq0g
   ```

2. Examine webhook configuration and delivery:
   - Check webhook URL configuration
   - Verify webhook secret handling
   - Analyze webhook delivery attempts and failures

3. Review worker environment variables:
   - Supabase configuration
   - API endpoints and URLs
   - Processing pipeline settings

**Expected Output**: Understanding of worker configuration and webhook setup

### 2. Document Processing Pipeline Analysis
**Task**: Examine the document processing workflow and identify failure points

**Investigation Steps**:
1. Trace the document processing flow:
   - File upload → Storage → Job creation → Worker processing
   - Identify where the "file not accessible" error occurs

2. Check file accessibility from worker perspective:
   - Verify storage bucket permissions
   - Test file access from worker service
   - Check file path resolution

3. Analyze processing dependencies:
   - External API calls (LLaParse, OpenAI)
   - Database connectivity
   - Storage access patterns

**Expected Output**: Clear understanding of processing pipeline failure points

### 3. Webhook System Investigation
**Task**: Examine webhook creation, delivery, and processing

**Investigation Steps**:
1. Check webhook creation in upload pipeline:
   - Verify webhook URL generation
   - Check webhook secret handling
   - Analyze webhook payload structure

2. Examine webhook delivery and processing:
   - Check webhook endpoint accessibility
   - Verify webhook authentication
   - Analyze webhook processing logic

3. Review webhook error handling:
   - Retry mechanisms
   - Error logging and reporting
   - User notification systems

**Expected Output**: Understanding of webhook system functionality and failures

### 4. Related Incident Analysis
**Task**: Review previous incidents with similar failure patterns

**Related Incidents to Investigate**:
- **FM-024**: Storage authentication issues (RESOLVED)
- **FM-023**: Database constraint violations (RESOLVED)
- **FM-012**: Document processing failures (if exists)
- **FM-008**: Webhook delivery issues (if exists)

**Investigation Steps**:
1. Review incident reports for similar error patterns
2. Check if previous fixes introduced new issues
3. Analyze common failure modes across incidents
4. Identify systemic issues in the upload pipeline

**Expected Output**: Understanding of recurring patterns and systemic issues

---

## Corrective Action Requirements

### Immediate Actions Required
1. **Fix document processing** - Either:
   - Resolve file accessibility issues from worker
   - Fix webhook delivery and processing
   - Update worker configuration

2. **Validate the fix** - Ensure:
   - Documents can be processed end-to-end
   - Webhook system functions correctly
   - No user-facing errors occur

### Long-term Actions Required
1. **Pipeline robustness** - Improve error handling and recovery
2. **Monitoring enhancement** - Add better visibility into processing pipeline
3. **Testing improvement** - Add comprehensive integration tests

---

## Investigation Deliverables

### 1. Root Cause Report
- **What**: Detailed analysis of document processing failure
- **When**: When the issue was introduced
- **Why**: Why documents are not accessible for processing
- **Impact**: Full impact assessment

### 2. Solution Design
- **Option A**: Fix file accessibility from worker
- **Option B**: Resolve webhook delivery issues
- **Option C**: Update worker configuration
- **Recommendation**: Which option is preferred and why
- **Risk Assessment**: Risks associated with each option

### 3. Implementation Plan
- **Steps**: Detailed steps to implement the fix
- **Testing**: How to validate the fix works
- **Deployment**: How to deploy safely
- **Rollback**: Plan to rollback if issues arise
- **Monitoring**: How to detect similar issues

### 4. Prevention Measures
- **Process**: How to prevent similar issues
- **Tooling**: Tools to catch processing pipeline issues
- **Documentation**: Update documentation

---

## Technical Context

### Error Details
```json
{
  "idx": 0,
  "job_id": "f3d824bd-7be8-4686-a437-7bdb5f7ab595",
  "document_id": "2f064818-4568-5ca2-ad05-e26484d8f1c4",
  "state": "queued",
  "retry_count": 0,
  "last_error": "{\"error\": \"Non-retryable error: user_facing_error: Document file is not accessible for processing. Please try uploading again. (Reference: 76421768-7eb0-45e7-8fb6-27001206b1df)\", \"timestamp\": \"2025-09-30T22:07:36.599165\"}",
  "created_at": "2025-09-30 22:07:35.034727+00",
  "updated_at": "2025-09-30 22:07:36.607914+00",
  "status": "failed_parse",
  "progress": "{}",
  "webhook_secret": null,
  "chunks_version": "markdown-simple@1",
  "embed_model": "text-embedding-3-small",
  "embed_version": "1"
}
```

### Staging Configuration
- **Upload Worker Service ID**: `srv-d37dlmvfte5s73b6uq0g`
- **API Service ID**: `srv-d3740ijuibrs738mus1g`
- **Supabase URL**: `https://your-staging-project.supabase.co`
- **Storage Buckets**: `files`, `examples`

### Key Investigation Points
1. **Render MCP Usage**:
   - `mcp_render_get_service` - Check worker service status
   - `mcp_render_list_logs` - Analyze worker logs
   - `mcp_render_get_metrics` - Check worker performance

2. **Webhook Analysis**:
   - Check webhook URL configuration
   - Verify webhook secret handling
   - Analyze webhook delivery attempts

3. **File Accessibility**:
   - Test file access from worker service
   - Check storage permissions
   - Verify file path resolution

---

## Success Criteria

### Investigation Complete When:
1. ✅ Root cause identified and documented
2. ✅ Worker service configuration understood
3. ✅ Webhook system status verified
4. ✅ File accessibility issues identified
5. ✅ Related incidents analyzed
6. ✅ Recommended solution identified
7. ✅ Implementation plan created
8. ✅ Prevention measures defined

### Resolution Complete When:
1. ✅ Document processing works end-to-end
2. ✅ Webhook system functions correctly
3. ✅ No user-facing errors occur
4. ✅ All tests pass
5. ✅ Staging deployment successful
6. ✅ Monitoring in place
7. ✅ Documentation updated

---

## Related Incidents

- **FM-024**: Upload 500 Storage Authentication Error (RESOLVED)
  - Storage authentication failure (signature verification failed)
  - Fixed by configuring storage buckets and updating service role keys
  - May have introduced new issues in processing pipeline

- **FM-023**: Upload 500 Database Constraint Error (RESOLVED)
  - Database constraint violation (status mismatch)
  - Fixed by updating code to use correct status values
  - May have affected job processing logic

---

## Investigation Notes

### Key Questions to Answer
1. Is the upload worker service running and healthy?
2. Are webhooks being created and delivered correctly?
3. Can the worker access files from Supabase storage?
4. Are there configuration mismatches between services?
5. Is the processing pipeline properly configured?
6. Are there dependency failures (external APIs, database)?

### Tools Available
- Render MCP for service inspection and logs
- Supabase MCP for database and storage queries
- Local development environment for testing
- Test scripts for replication

### Test Scripts to Create
- `test_worker_connectivity.py` - Test worker service health
- `test_webhook_delivery.py` - Test webhook creation and delivery
- `test_file_accessibility.py` - Test file access from worker
- `test_processing_pipeline.py` - Test complete processing flow

---

## Development Environment Testing Requirements

### **CRITICAL**: All fixes must be tested locally before deployment

1. **Local Testing Steps**:
   ```bash
   # 1. Start local development environment
   cd /Users/aq_home/1Projects/accessa/insurance_navigator
   source .venv/bin/activate
   supabase start
   python main.py
   
   # 2. Start upload worker locally
   python -m backend.workers.upload_worker
   
   # 3. Test complete upload and processing flow
   python test_processing_pipeline.py
   ```

2. **Validation Requirements**:
   - ✅ Local worker service starts successfully
   - ✅ Webhook creation and delivery works
   - ✅ File processing completes successfully
   - ✅ No errors in local logs
   - ✅ All test scripts pass

3. **Deployment Process**:
   - ✅ Local testing completed successfully
   - ✅ Code changes committed to feature branch
   - ✅ Pull request created for staging branch
   - ✅ Staging deployment triggered
   - ✅ Staging validation completed

---

**Investigation Priority**: HIGH  
**Estimated Time**: 3-6 hours  
**Assigned To**: [To be assigned]  
**Due Date**: [To be set]  
**Testing Requirement**: MANDATORY local testing before staging deployment
