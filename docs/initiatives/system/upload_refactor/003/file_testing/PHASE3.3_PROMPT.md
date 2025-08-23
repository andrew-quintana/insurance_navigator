# Phase 3.3 Execution Prompt: parsing → parsed Transition Validation

## Context
You are implementing Phase 3.3 of the upload refactor 003 file testing initiative. This phase focuses on validating the transition from `parsing` to `parsed` stage, which involves LlamaParse service integration, webhook callback handling, and parsed content storage.

## Documentation References
Please review these documents before starting implementation:
- `docs/initiatives/system/upload_refactor/003/file_testing/TODO001.md` - Phase 3.3 requirements and tasks
- `docs/initiatives/system/upload_refactor/003/file_testing/TEST_METHOD001.md` - Testing methodology and procedures
- `docs/initiatives/system/upload_refactor/003/file_testing/PHASE3.2_PROMPT.md` - Phase 3.2 completion status and handoff
- `docs/initiatives/system/upload_refactor/003/file_testing/PHASE3_SCOPE_UPDATE.md` - Phase 3 scope and objectives

## Primary Objective
**VALIDATE** the transition from `parsing` to `parsed` stage by testing LlamaParse service integration, webhook callback handling, and parsed content storage and metadata capture.

## Expected Outputs
Document your work in these files:
- `TODO001_phase3.3_notes.md` - Phase 3.3 implementation details and validation results
- `TODO001_phase3.3_decisions.md` - Technical decisions and integration approaches
- `TODO001_phase3.3_handoff.md` - Requirements for Phase 3.4 (parsed → parse_validated)
- `TODO001_phase3.3_testing_summary.md` - Phase 3.3 testing results and status

## Implementation Approach
1. **Verify LlamaParse Service**: Ensure mock LlamaParse service is operational
2. **Test Job Submission**: Submit jobs to LlamaParse service for parsing
3. **Validate Webhook Handling**: Test webhook callback processing from LlamaParse
4. **Verify Content Storage**: Confirm parsed content is stored correctly
5. **Validate Stage Transition**: Confirm jobs advance from `parsing` to `parsed` stage

## Phase 3.3 Requirements

### Core Tasks
- [ ] Verify mock LlamaParse service is operational and responding
- [ ] Test job submission to LlamaParse service from parsing stage
- [ ] Validate webhook callback handling from LlamaParse service
- [ ] Test parsed content storage and metadata capture
- [ ] Verify job status updates correctly to `parsed` stage
- [ ] Document parsing stage completion and content storage

### Success Criteria
- ✅ Mock LlamaParse service operational and responding
- ✅ Jobs successfully submitted to LlamaParse service
- ✅ Webhook callbacks processed correctly
- ✅ Parsed content stored with proper metadata
- ✅ Jobs transition from `parsing` to `parsed` stage
- ✅ All parsing metadata captured accurately

### Current Status from Phase 3.2
- **Worker Automation**: Phase 3.2 completion required ✅
- **Database State**: Jobs advancing to parsing stage ✅
- **LlamaParse Integration**: Ready for testing ⏳
- **Webhook Handling**: Ready for validation ⏳

## Technical Focus Areas

### 1. LlamaParse Service Integration
- Verify mock LlamaParse service is running and healthy
- Test job submission API endpoints
- Validate request/response formats
- Test service error handling and recovery

### 2. Webhook Callback Processing
- Test webhook endpoint availability and security
- Validate webhook payload processing
- Test webhook signature verification (if implemented)
- Verify webhook error handling and retry logic

### 3. Parsed Content Storage
- Test parsed content storage in designated locations
- Validate metadata capture and storage
- Test content format validation
- Verify storage access and retrieval

### 4. Stage Transition Management
- Validate job status updates from `parsing` to `parsed`
- Test database transaction management
- Verify correlation ID tracking
- Check for any constraint violations

## Testing Procedures

### Step 1: LlamaParse Service Verification
```bash
# Check mock LlamaParse service status
docker-compose ps mock-llamaparse

# Verify service health endpoint
curl http://localhost:8001/health

# Check service logs for any errors
docker-compose logs mock-llamaparse --tail=20
```

### Step 2: Job Submission Testing
```bash
# Test job submission to LlamaParse service
curl -X POST http://localhost:8001/parse \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test-job-123",
    "source_url": "http://localhost:5001/storage/v1/object/upload/test-doc.pdf",
    "webhook_url": "http://localhost:8000/webhooks/llamaparse"
  }'

# Monitor service response and processing
docker-compose logs mock-llamaparse -f
```

### Step 3: Webhook Callback Testing
```bash
# Monitor webhook endpoint for callbacks
docker-compose logs api-server -f

# Check webhook processing in real-time
# Verify callback payload processing
# Test webhook error scenarios
```

### Step 4: Content Storage Validation
```bash
# Check parsed content storage
ls -la local-storage/parsed/

# Verify content metadata
# Test content retrieval and access
# Validate content format and completeness
```

### Step 5: Database State Validation
```sql
-- Check job stage transitions
SELECT job_id, stage, updated_at, parsed_path
FROM upload_pipeline.upload_jobs 
WHERE stage IN ('parsing', 'parsed')
ORDER BY updated_at DESC;

-- Verify parsed content metadata
SELECT * FROM upload_pipeline.documents 
WHERE parsed_path IS NOT NULL;
```

## Expected Outcomes

### Success Scenario
- Mock LlamaParse service operational and responding
- Jobs successfully submitted and processed by LlamaParse
- Webhook callbacks processed correctly
- Parsed content stored with proper metadata
- Jobs transition from `parsing` to `parsed` stage
- Ready to proceed to Phase 3.4 (parsed → parse_validated)

### Failure Scenarios
- LlamaParse service not responding or operational
- Job submission failures or errors
- Webhook callback processing issues
- Parsed content storage problems
- Stage transition failures

## Risk Assessment

### High Risk
- **LlamaParse Service Failures**: Service not operational or responding
  - *Mitigation*: Verify service health and restart if necessary
- **Webhook Processing Failures**: Callbacks not handled correctly
  - *Mitigation*: Test webhook endpoint and error handling

### Medium Risk
- **Content Storage Issues**: Parsed content not stored correctly
  - *Mitigation*: Validate storage configuration and permissions
- **Stage Transition Failures**: Jobs not advancing to parsed stage
  - *Mitigation*: Check database constraints and transaction management

### Low Risk
- **Metadata Capture Issues**: Incomplete parsing metadata
  - *Mitigation*: Validate metadata capture logic and storage
- **Format Validation Problems**: Invalid parsed content format
  - *Mitigation*: Test content format validation and error handling

## Next Phase Readiness

### Phase 3.4 Dependencies
- ✅ `parsing → parsed` transition working correctly
- ✅ LlamaParse service integration operational
- ✅ Webhook callback handling functional
- ✅ Parsed content storage working correctly
- ✅ Parsing metadata captured accurately

### Handoff Requirements
- Complete Phase 3.3 testing results
- LlamaParse service integration status
- Webhook handling configuration and status
- Parsed content storage configuration
- Recommendations for Phase 3.4 implementation

## Success Metrics

### Phase 3.3 Completion Criteria
- [ ] Mock LlamaParse service operational and responding
- [ ] Jobs successfully submitted to LlamaParse service
- [ ] Webhook callbacks processed correctly
- [ ] Parsed content stored with proper metadata
- [ ] Jobs transition from `parsing` to `parsed` stage
- [ ] All parsing metadata captured accurately
- [ ] Ready to proceed to Phase 3.4

---

**Phase 3.3 Status**: 🔄 IN PROGRESS  
**Focus**: parsing → parsed Transition Validation  
**Environment**: postgres database, mock LlamaParse service, webhook handling  
**Success Criteria**: LlamaParse integration and webhook processing working  
**Next Phase**: Phase 3.4 (parsed → parse_validated)
