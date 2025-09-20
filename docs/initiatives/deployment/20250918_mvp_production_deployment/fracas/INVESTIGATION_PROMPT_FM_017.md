# Investigation Prompt: FM-017 Worker Storage Access Issue

## Mission
Investigate and resolve FM-017: Worker storage access issue where signedUrl generation fails, preventing document processing completion in the upload pipeline.

## Context
The webhook processing system successfully extracts and stores parsed content, but the worker fails to access the stored content due to signedUrl generation errors, causing the upload pipeline to fail despite successful content parsing.

## Investigation Phases

### Phase 1: Immediate Analysis
**Objective**: Understand the storage access failure and identify the root cause

**Tasks**:
1. **Analyze Worker Logs**
   - Review worker service logs for storage access errors
   - Identify the exact signedUrl generation failure
   - Check for environment configuration issues

2. **Examine Storage Access Code**
   - Review `backend/shared/storage/storage_manager.py` implementation
   - Identify why signedUrl is being used instead of direct access
   - Check environment configuration logic

3. **Database State Analysis**
   - Check job status in database
   - Verify document processing status
   - Identify any data inconsistencies

**Deliverables**:
- Storage access failure analysis
- Code analysis report
- Database state summary

### Phase 2: Root Cause Identification
**Objective**: Identify why worker needs signedUrl and design proper fix

**Tasks**:
1. **Code Analysis**
   - Review StorageManager implementation
   - Identify environment configuration logic
   - Check for hardcoded assumptions

2. **Integration Analysis**
   - Review webhook vs worker storage access patterns
   - Identify why webhook works but worker fails
   - Check for service role key usage

3. **Configuration Analysis**
   - Review environment variable setup
   - Check for missing or incorrect configuration
   - Identify production vs development differences

**Deliverables**:
- Root cause analysis report
- Contributing factors list
- Fix design document

### Phase 3: Implementation and Testing
**Objective**: Fix storage access and verify end-to-end processing

**Tasks**:
1. **Code Implementation**
   - Fix StorageManager to use direct access in production
   - Remove unnecessary signedUrl generation
   - Ensure proper service role key usage

2. **Testing Implementation**
   - Test worker storage access locally
   - Verify end-to-end document processing
   - Test error scenarios

3. **Deployment and Verification**
   - Deploy fix to production
   - Test with real document processing
   - Verify complete upload pipeline
   - Monitor for any issues

**Deliverables**:
- Fixed storage access code
- Comprehensive test suite
- Deployment verification report
- Monitoring and alerting setup

## Key Files to Investigate

### Primary Files
- `backend/shared/storage/storage_manager.py` - Storage access implementation
- `backend/workers/` - Worker service code
- `backend/shared/config/` - Configuration management

### Configuration Files
- `.env.production` - Production environment variables
- `backend/shared/config/worker_config.py` - Worker configuration

### Test Files
- `tests/` - Existing test suite
- `backend/workers/tests/` - Worker-specific tests

## Log Sources

### Production Logs
- **Render Worker Service**: `srv-d2h5mr8dl3ps73fvvlog`
- **Time Range**: 2025-09-19 19:40:00 - 20:00:00 UTC
- **Key Job ID**: `c9f71569-612a-4599-a7e4-58e37273256e`

### Database Queries
```sql
-- Check job status
SELECT job_id, status, state, last_error, updated_at 
FROM upload_pipeline.upload_jobs 
WHERE job_id = 'c9f71569-612a-4599-a7e4-58e37273256e';

-- Check document status
SELECT document_id, processing_status, parsed_sha256, parsed_path, updated_at 
FROM upload_pipeline.documents 
WHERE document_id = 'cbc0c15a-4056-43e5-a4b8-95be11175719';
```

## Expected Behavior
- Worker should access storage directly using service role key
- No signedUrl generation needed for production
- Direct HTTP requests to Supabase Storage API
- Same pattern as webhook storage access

## Actual Behavior
- Worker attempts to generate signedUrl
- signedUrl generation fails
- Document processing cannot complete
- Job remains in failed state

## Critical Notes

### Production Environment
- **Service**: insurance-navigator-worker.onrender.com
- **Database**: Supabase production
- **Storage**: Supabase Storage
- **Monitoring**: Render logs

### Data Safety
- No data loss risk (content is already stored)
- Database state may be inconsistent
- Worker processing is blocked

### Rollback Plan
- Revert storage access changes if needed
- Database state can be corrected
- No data corruption risk

### Monitoring
- Watch for worker processing success rates
- Monitor storage access metrics
- Alert on signedUrl generation failures

## Success Criteria

### Immediate Success
- [ ] Worker accesses storage without signedUrl generation
- [ ] Document processing completes successfully
- [ ] End-to-end upload pipeline works
- [ ] Database state is consistent

### Verification Steps
1. **Test Worker Storage Access**
   - Verify worker can read stored content
   - Check for any access errors
   - Verify service role key usage

2. **End-to-End Testing**
   - Upload test document
   - Verify parsing completes
   - Check worker processing completes
   - Verify content is accessible

3. **Error Handling**
   - Test with invalid storage paths
   - Verify error messages are helpful
   - Check graceful degradation

## Tools and Resources

### Available Tools
- Render MCP for production logs and monitoring
- Supabase MCP for database operations
- Terminal for code analysis and testing
- File system access for code review

### External Resources
- Supabase Storage API documentation
- Service role key usage patterns
- Storage access best practices

## Workflow

1. **Start with Log Analysis** - Understand what's happening in production
2. **Code Review** - Identify the storage access issue
3. **Root Cause Analysis** - Understand why signedUrl is being used
4. **Fix Design** - Plan proper storage access solution
5. **Implementation** - Code the fix with proper testing
6. **Deployment** - Deploy and verify in production
7. **Monitoring** - Set up ongoing monitoring and alerting

## Expected Timeline

- **Phase 1**: 30 minutes (immediate analysis)
- **Phase 2**: 45 minutes (root cause and design)
- **Phase 3**: 60 minutes (implementation and testing)
- **Total**: ~2.5 hours

## Risk Mitigation

### High Risk Items
- **Data Loss**: Content already stored, no risk
- **System Downtime**: Worker processing already broken
- **User Impact**: Already experiencing failures

### Mitigation Strategies
- Test fixes thoroughly before deployment
- Implement proper error handling
- Add comprehensive monitoring
- Create rollback plan

---

**Document Version**: 1.0  
**Created**: 2025-09-19  
**Priority**: High  
**Status**: Ready for Investigation
