# Phase 3.2 Execution Prompt: job_validated → parsing Transition Validation

## Context
You are implementing Phase 3.2 of the upload refactor 003 file testing initiative. This phase focuses on validating the automatic transition from `job_validated` to `parsing` stage, which requires worker automation to be fully operational.

## Documentation References
Please review these documents before starting implementation:
- `docs/initiatives/system/upload_refactor/003/file_testing/TODO001.md` - Phase 3.2 requirements and tasks
- `docs/initiatives/system/upload_refactor/003/file_testing/TEST_METHOD001.md` - Testing methodology and procedures
- `docs/initiatives/system/upload_refactor/003/PHASE3_DATABASE_VERIFICATION_REPORT.md` - Current Phase 3 status and findings
- `docs/initiatives/system/upload_refactor/003/file_testing/PHASE3_SCOPE_UPDATE.md` - Phase 3 scope and objectives

## Primary Objective
**VALIDATE** the automatic transition from `job_validated` to `parsing` stage by ensuring the worker process automatically picks up and processes jobs in the `job_validated` stage.

## Expected Outputs
Document your work in these files:
- `TODO001_phase3.2_notes.md` - Phase 3.2 implementation details and validation results
- `TODO001_phase3.2_decisions.md` - Technical decisions and troubleshooting approaches
- `TODO001_phase3.2_handoff.md` - Requirements for Phase 3.3 (parsing → parsed)
- `TODO001_phase3.2_testing_summary.md` - Phase 3.2 testing results and status

## Implementation Approach
1. **Verify Worker Status**: Ensure base-worker service is running and operational
2. **Check Current Database State**: Verify jobs are in `job_validated` stage
3. **Test Worker Automation**: Verify worker automatically processes `job_validated` jobs
4. **Validate Stage Transition**: Confirm jobs advance from `job_validated` to `parsing`
5. **Document Results**: Record all findings and prepare for Phase 3.3

## Phase 3.2 Requirements

### Core Tasks
- [ ] Verify base-worker service is running and healthy
- [ ] Check current database state for jobs in `job_validated` stage
- [ ] Test automatic job processing for `job_validated` stage
- [ ] Validate worker picks up `job_validated` jobs automatically
- [ ] Test parsing preparation logic and state transition
- [ ] Verify job status updates correctly to `parsing` stage
- [ ] Document parsing stage initialization and preparation

### Success Criteria
- ✅ Worker service operational and healthy
- ✅ Jobs in `job_validated` stage are automatically processed
- ✅ Jobs transition from `job_validated` to `parsing` stage
- ✅ Parsing preparation logic executes correctly
- ✅ Database updates reflect stage transitions accurately

### Current Status from Phase 3.1
- **Database**: postgres database (not accessa_dev) ✅
- **Worker Environment**: Fixed environment variables ✅
- **Worker Implementation**: Added support for queued and job_validated stages ✅
- **Database Query**: Worker can find and process jobs correctly ✅
- **Manual Testing**: Stage advancement works manually ✅
- **Remaining Issue**: Worker not processing jobs automatically in main loop ❌

## Technical Focus Areas

### 1. Worker Process Automation
- Verify worker main loop is calling `_get_next_job()` method
- Check for silent errors preventing job processing
- Validate worker health and operational status
- Test worker restart and recovery procedures

### 2. Job Processing Logic
- Validate `_process_job_validated()` method implementation
- Test parsing preparation logic execution
- Verify stage transition database updates
- Check for any missing dependencies or imports

### 3. Database State Management
- Monitor job stage transitions in real-time
- Validate database update operations
- Check for any constraint violations
- Verify transaction management

## Testing Procedures

### Step 1: Environment Verification
```bash
# Check worker service status
docker-compose ps base-worker

# Check worker logs for any errors
docker-compose logs base-worker --tail=50

# Verify worker health
docker-compose exec base-worker python -c "from backend.workers.base_worker import BaseWorker; print('Worker import successful')"
```

### Step 2: Database State Check
```sql
-- Check current job distribution
SELECT stage, COUNT(*) as job_count 
FROM upload_pipeline.upload_jobs 
GROUP BY stage 
ORDER BY stage;

-- Check specific job_validated jobs
SELECT job_id, document_id, stage, state, created_at, updated_at
FROM upload_pipeline.upload_jobs 
WHERE stage = 'job_validated'
ORDER BY updated_at DESC;
```

### Step 3: Worker Automation Test
```bash
# Monitor worker processing in real-time
docker-compose logs base-worker -f

# Check database for stage transitions
# Monitor for automatic job processing activity
```

### Step 4: Stage Transition Validation
```sql
-- Monitor job stage changes
SELECT job_id, stage, updated_at
FROM upload_pipeline.upload_jobs 
WHERE stage IN ('job_validated', 'parsing')
ORDER BY updated_at DESC;
```

## Expected Outcomes

### Success Scenario
- Worker automatically processes `job_validated` jobs
- Jobs transition from `job_validated` to `parsing` stage
- Parsing preparation logic executes successfully
- Database reflects all stage transitions accurately
- Ready to proceed to Phase 3.3 (parsing → parsed)

### Failure Scenarios
- Worker not processing jobs automatically
- Jobs stuck in `job_validated` stage
- Parsing preparation logic failing
- Database update errors or constraint violations

## Risk Assessment

### High Risk
- **Worker Automation Failure**: Jobs not processed automatically
  - *Mitigation*: Debug worker main loop and job processing logic
- **Database Update Failures**: Stage transitions not recorded
  - *Mitigation*: Check database constraints and transaction management

### Medium Risk
- **Parsing Preparation Logic Errors**: Invalid parsing stage setup
  - *Mitigation*: Validate parsing preparation implementation
- **Worker Health Issues**: Service not responding or unstable
  - *Mitigation*: Check worker logs and restart if necessary

## Next Phase Readiness

### Phase 3.3 Dependencies
- ✅ `job_validated → parsing` transition working automatically
- ✅ Parsing preparation logic operational
- ✅ Worker automation confirmed functional
- ✅ Database state management working correctly

### Handoff Requirements
- Complete Phase 3.2 testing results
- Worker automation status and configuration
- Any issues or workarounds identified
- Recommendations for Phase 3.3 implementation

## Success Metrics

### Phase 3.2 Completion Criteria
- [ ] Worker automatically processes `job_validated` jobs
- [ ] Jobs transition from `job_validated` to `parsing` stage
- [ ] Parsing preparation logic executes successfully
- [ ] Database updates reflect stage transitions accurately
- [ ] No manual intervention required for job processing
- [ ] Ready to proceed to Phase 3.3

---

**Phase 3.2 Status**: 🔄 IN PROGRESS  
**Focus**: job_validated → parsing Transition Validation  
**Environment**: postgres database, local worker processes  
**Success Criteria**: Automatic job processing and stage transitions working  
**Next Phase**: Phase 3.3 (parsing → parsed)
