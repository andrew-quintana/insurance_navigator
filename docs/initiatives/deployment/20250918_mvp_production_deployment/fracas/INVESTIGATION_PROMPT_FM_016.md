# Investigation Prompt: FM-016 Parsed Content Empty

## Mission
Investigate and resolve FM-016: Parsed Content Empty error in webhook processing system.

## Context
The webhook processing system is receiving valid parsed content from LlamaParse but reporting "Parsed content is empty" errors, causing document processing to fail despite successful parsing.

## Investigation Phases

### Phase 1: Immediate Analysis
**Objective**: Understand the exact payload structure and identify the mismatch

**Tasks**:
1. **Analyze Production Logs**
   - Review webhook processing logs for job `2842e2cc-aff5-489c-a905-e60845d00ab0`
   - Identify the exact payload structure received from LlamaParse
   - Compare with expected payload structure in webhook code

2. **Examine Webhook Code**
   - Review `api/upload_pipeline/webhooks.py` content extraction logic
   - Identify hardcoded payload structure assumptions
   - Document the expected vs actual payload structure

3. **Database State Analysis**
   - Check job status in database
   - Verify document processing status
   - Identify any data inconsistencies

**Deliverables**:
- Payload structure comparison document
- Code analysis report
- Database state summary

### Phase 2: Root Cause Identification
**Objective**: Identify all contributing factors and design comprehensive fix

**Tasks**:
1. **Code Analysis**
   - Identify all payload structure assumptions
   - Review error handling patterns
   - Check for defensive programming practices

2. **Integration Analysis**
   - Review LlamaParse API documentation
   - Identify all possible payload structures
   - Check for version differences or changes

3. **Testing Gap Analysis**
   - Review existing webhook tests
   - Identify missing integration tests
   - Check for payload structure validation

**Deliverables**:
- Root cause analysis report
- Contributing factors list
- Fix design document

### Phase 3: Implementation and Testing
**Objective**: Implement comprehensive fix and verify resolution

**Tasks**:
1. **Code Implementation**
   - Fix payload structure handling
   - Add multiple page support
   - Improve error handling and validation
   - Add backward compatibility

2. **Testing Implementation**
   - Create unit tests for payload handling
   - Add integration tests with real LlamaParse payloads
   - Test multiple page documents
   - Test error scenarios

3. **Deployment and Verification**
   - Deploy fix to production
   - Test with real webhook calls
   - Verify end-to-end document processing
   - Monitor for any issues

**Deliverables**:
- Fixed webhook processing code
- Comprehensive test suite
- Deployment verification report
- Monitoring and alerting setup

## Key Files to Investigate

### Primary Files
- `api/upload_pipeline/webhooks.py` - Main webhook processing logic
- `api/upload_pipeline/database.py` - Database operations
- `core/database.py` - Database connection management

### Configuration Files
- `config/storage.py` - Storage configuration
- `main.py` - Application initialization

### Test Files
- `tests/` - Existing test suite
- `api/upload_pipeline/tests/` - Webhook-specific tests

## Log Sources

### Production Logs
- **Render API Service**: `srv-d0v2nqvdiees73cejf0g`
- **Time Range**: 2025-09-19 18:20:00 - 18:30:00 UTC
- **Key Job ID**: `2842e2cc-aff5-489c-a905-e60845d00ab0`

### Database Queries
```sql
-- Check job status
SELECT job_id, status, state, last_error, updated_at 
FROM upload_pipeline.upload_jobs 
WHERE job_id = '2842e2cc-aff5-489c-a905-e60845d00ab0';

-- Check document status
SELECT document_id, processing_status, parsed_sha256, parsed_path, updated_at 
FROM upload_pipeline.documents 
WHERE document_id = '4ee23c78-51a9-5a6b-a23c-7c95882c510f';
```

## Expected Payload Structure (Current Code)
```json
{
  "status": "completed",
  "md": "# Document content...",
  "txt": "Document content...",
  "parsed_content": "Document content..."
}
```

## Actual Payload Structure (LlamaParse)
```json
{
  "status": "OK",
  "result": [
    {
      "page": 1,
      "md": "# Document content...",
      "txt": "Document content...",
      "parsed_content": "Document content...",
      "json": [...],
      "status": "OK"
    }
  ]
}
```

## Critical Notes

### Production Environment
- **Service**: insurance-navigator-api.onrender.com
- **Database**: Supabase production
- **Storage**: Supabase Storage
- **Monitoring**: Render logs

### Data Safety
- No data loss risk (content is already parsed)
- Database state may be inconsistent
- Storage operations may be incomplete

### Rollback Plan
- Revert webhook code changes if needed
- Database state can be corrected
- No data corruption risk

### Monitoring
- Watch for webhook processing success rates
- Monitor content extraction metrics
- Alert on payload structure validation failures

## Success Criteria

### Immediate Success
- [ ] Webhook processes LlamaParse payloads without "Parsed content is empty" errors
- [ ] Multiple page documents are handled correctly
- [ ] Content is properly extracted and stored
- [ ] Database state is consistent

### Verification Steps
1. **Test with Real Webhook**
   - Send test webhook with actual LlamaParse payload structure
   - Verify content extraction works
   - Check database updates

2. **End-to-End Testing**
   - Upload test document
   - Verify parsing completes
   - Check content is accessible

3. **Error Handling**
   - Test with invalid payloads
   - Verify error messages are helpful
   - Check graceful degradation

## Tools and Resources

### Available Tools
- Render MCP for production logs and monitoring
- Supabase MCP for database operations
- Terminal for code analysis and testing
- File system access for code review

### External Resources
- LlamaParse API documentation
- Webhook testing tools
- Payload structure examples

## Workflow

1. **Start with Log Analysis** - Understand what's happening in production
2. **Code Review** - Identify the exact mismatch
3. **Root Cause Analysis** - Understand why this happened
4. **Fix Design** - Plan comprehensive solution
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
- **Data Loss**: Content already parsed, no risk
- **System Downtime**: Webhook processing already broken
- **User Impact**: Already experiencing failures

### Mitigation Strategies
- Test fixes thoroughly before deployment
- Implement backward compatibility
- Add comprehensive monitoring
- Create rollback plan

---

**Document Version**: 1.0  
**Created**: 2025-09-19  
**Priority**: High  
**Status**: Ready for Investigation
