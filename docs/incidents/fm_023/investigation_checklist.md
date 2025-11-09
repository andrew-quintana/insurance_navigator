# FM-023 Investigation Checklist

## Pre-Investigation Setup
- [ ] Create investigation branch: `git checkout -b investigation/fm-023-upload-constraint-violation`
- [ ] Set up local environment with staging database access
- [ ] Review the investigation prompt thoroughly
- [ ] Gather all relevant tools and access credentials

## Phase 1: Database Schema Analysis

### Database Constraint Investigation
- [ ] Query the constraint definition:
  ```sql
  SELECT conname, pg_get_constraintdef(oid) as definition
  FROM pg_constraint 
  WHERE conrelid = 'upload_pipeline.upload_jobs'::regclass 
  AND conname = 'ck_upload_jobs_status';
  ```
- [ ] Document all allowed status values from the constraint
- [ ] Check if there are other constraints on the upload_jobs table
- [ ] Verify the constraint is active and enforced

### Database Schema History
- [ ] Check migration history for upload_jobs table changes
- [ ] Look for any recent migrations that modified status constraints
- [ ] Compare staging vs production database schemas
- [ ] Identify when the constraint was last modified

## Phase 2: Code Analysis

### Upload Pipeline Code Review
- [ ] Examine `api/upload_pipeline/endpoints/upload.py` line 479 (`_create_upload_job`)
- [ ] Check `api/upload_pipeline/models.py` for status validation
- [ ] Review `api/upload_pipeline/utils/upload_pipeline_utils.py` for status handling
- [ ] Search for all hardcoded status values in the codebase

### Status Value Mapping
- [ ] Create a complete list of status values used in code
- [ ] Identify where each status value is defined
- [ ] Check for any status value transformations or mappings
- [ ] Document the intended status flow/workflow

### Code vs Database Comparison
- [ ] Compare code status values with database constraint values
- [ ] Identify all mismatches
- [ ] Determine which values are missing from each side
- [ ] Document the complete mismatch analysis

## Phase 3: Root Cause Determination

### Schema Evolution Analysis
- [ ] Determine when the mismatch was introduced
- [ ] Check if it was a migration issue or code change
- [ ] Verify if this affects other environments
- [ ] Identify the original intended design

### Impact Assessment
- [ ] Determine how many status values are affected
- [ ] Check if other parts of the system use these values
- [ ] Assess the impact on existing data
- [ ] Evaluate the risk of different fix approaches

## Phase 4: Solution Design

### Option Analysis
- [ ] **Option A**: Update code to match database constraint
  - [ ] List all code changes required
  - [ ] Assess impact on existing functionality
  - [ ] Identify testing requirements
  - [ ] Evaluate implementation complexity

- [ ] **Option B**: Update database constraint to match code
  - [ ] List all database changes required
  - [ ] Assess impact on existing data
  - [ ] Identify migration requirements
  - [ ] Evaluate implementation complexity

### Recommendation
- [ ] Choose the preferred option
- [ ] Document the reasoning
- [ ] Create detailed implementation plan
- [ ] Identify risks and mitigation strategies

## Phase 5: Implementation Planning

### Implementation Steps
- [ ] Create detailed step-by-step implementation plan
- [ ] Identify all files that need to be modified
- [ ] Plan database changes (if needed)
- [ ] Design testing strategy

### Testing Strategy
- [ ] Unit tests for status validation
- [ ] Integration tests for upload flow
- [ ] End-to-end tests with real uploads
- [ ] Regression tests for existing functionality

### Rollback Planning
- [ ] Design rollback strategy
- [ ] Identify rollback triggers
- [ ] Plan rollback testing
- [ ] Document rollback procedures

## Phase 6: Prevention Measures

### Process Improvements
- [ ] Design schema validation process
- [ ] Create code-database sync checks
- [ ] Plan regular schema audits
- [ ] Design constraint validation tests

### Tooling Recommendations
- [ ] Identify tools for schema validation
- [ ] Plan automated constraint checking
- [ ] Design monitoring for constraint violations
- [ ] Create alerting for schema mismatches

## Phase 7: Documentation

### Investigation Report
- [ ] Write comprehensive root cause analysis
- [ ] Document all findings and evidence
- [ ] Create solution recommendation
- [ ] Include implementation plan

### Process Documentation
- [ ] Update FRACAS procedures
- [ ] Document prevention measures
- [ ] Create investigation templates
- [ ] Update troubleshooting guides

## Phase 8: Implementation

### Code Changes
- [ ] Implement the chosen solution
- [ ] Update all affected files
- [ ] Add/update tests
- [ ] Update documentation

### Database Changes (if needed)
- [ ] Create migration scripts
- [ ] Test migration on staging
- [ ] Plan production migration
- [ ] Update database documentation

### Testing
- [ ] Run all unit tests
- [ ] Run integration tests
- [ ] Test upload functionality end-to-end
- [ ] Verify no regression issues

## Phase 9: Validation

### Functionality Testing
- [ ] Test upload with various file types
- [ ] Test upload with different users
- [ ] Test error scenarios
- [ ] Verify status transitions work correctly

### Performance Testing
- [ ] Test upload performance
- [ ] Check database query performance
- [ ] Monitor resource usage
- [ ] Verify no performance degradation

### Monitoring
- [ ] Set up monitoring for constraint violations
- [ ] Create alerts for similar issues
- [ ] Monitor upload success rates
- [ ] Track error rates

## Phase 10: Closure

### Final Validation
- [ ] Confirm all success criteria met
- [ ] Verify no outstanding issues
- [ ] Complete all documentation
- [ ] Update incident status

### Knowledge Transfer
- [ ] Share findings with team
- [ ] Update runbooks
- [ ] Train team on prevention measures
- [ ] Document lessons learned

### Follow-up
- [ ] Schedule follow-up review
- [ ] Plan monitoring review
- [ ] Schedule prevention measure audit
- [ ] Update FRACAS process based on learnings

---

## Investigation Notes

### Key Findings
- [ ] Finding 1
- [ ] Finding 2
- [ ] Finding 3

### Decisions Made
- [ ] Decision 1: [Rationale]
- [ ] Decision 2: [Rationale]
- [ ] Decision 3: [Rationale]

### Issues Encountered
- [ ] Issue 1: [Resolution]
- [ ] Issue 2: [Resolution]
- [ ] Issue 3: [Resolution]

### Lessons Learned
- [ ] Lesson 1
- [ ] Lesson 2
- [ ] Lesson 3

---

**Investigation Started**: [Date]  
**Investigation Completed**: [Date]  
**Total Time**: [Hours]  
**Investigator**: [Name]
