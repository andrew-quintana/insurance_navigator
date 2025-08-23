# Phase 3.4 Execution Prompt: parsed → parse_validated Transition Validation

## Context
You are implementing Phase 3.4 of the upload refactor 003 file testing initiative. This phase focuses on validating the transition from `parsed` to `parse_validated` stage, which involves parsed content validation, format checking, duplicate detection, and canonical path handling.

## Documentation References
Please review these documents before starting implementation:
- `docs/initiatives/system/upload_refactor/003/file_testing/TODO001.md` - Phase 3.4 requirements and tasks
- `docs/initiatives/system/upload_refactor/003/file_testing/TEST_METHOD001.md` - Testing methodology and procedures
- `docs/initiatives/system/upload_refactor/003/file_testing/PHASE3.3_PROMPT.md` - Phase 3.3 completion status and handoff
- `docs/initiatives/system/upload_refactor/003/file_testing/PHASE3_SCOPE_UPDATE.md` - Phase 3 scope and objectives

## Primary Objective
**VALIDATE** the transition from `parsed` to `parse_validated` stage by testing parsed content validation logic, format checking, duplicate content detection, and canonical path handling.

## Expected Outputs
Document your work in these files:
- `TODO001_phase3.4_notes.md` - Phase 3.4 implementation details and validation results
- `TODO001_phase3.4_decisions.md` - Technical decisions and validation approaches
- `TODO001_phase3.4_handoff.md` - Requirements for Phase 3.5 (parse_validated → chunking)
- `TODO001_phase3.4_testing_summary.md` - Phase 3.4 testing results and status

## Implementation Approach
1. **Verify Parsed Content**: Ensure parsed content is available and accessible
2. **Test Content Validation**: Validate content format and completeness checks
3. **Test Duplicate Detection**: Test duplicate content detection and canonical path handling
4. **Validate Stage Transition**: Confirm jobs advance from `parsed` to `parse_validated` stage
5. **Document Validation Results**: Record all validation findings and metadata

## Phase 3.4 Requirements

### Core Tasks
- [ ] Verify parsed content is available and accessible from previous phase
- [ ] Test parsed content validation logic and format checking
- [ ] Validate content completeness and structure validation
- [ ] Test duplicate content detection and canonical path handling
- [ ] Verify job status updates correctly to `parse_validated` stage
- [ ] Document parse validation results and metadata capture

### Success Criteria
- ✅ Parsed content available and accessible for validation
- ✅ Content validation logic executes successfully
- ✅ Format and completeness checks pass
- ✅ Duplicate detection working correctly
- ✅ Jobs transition from `parsed` to `parse_validated` stage
- ✅ All validation metadata captured accurately

### Current Status from Phase 3.3
- **LlamaParse Integration**: Phase 3.3 completion required ✅
- **Parsed Content**: Ready for validation ⏳
- **Content Validation Logic**: Ready for testing ⏳
- **Duplicate Detection**: Ready for validation ⏳

## Technical Focus Areas

### 1. Parsed Content Validation
- Verify parsed content is accessible and readable
- Test content format validation (text, structure, encoding)
- Validate content completeness and integrity
- Test content size and metadata validation

### 2. Duplicate Content Detection
- Test duplicate content detection algorithms
- Validate canonical path generation and handling
- Test content hash comparison and deduplication
- Verify duplicate handling policies and procedures

### 3. Content Structure Validation
- Test content structure parsing and validation
- Validate metadata extraction and storage
- Test content quality assessment and scoring
- Verify content classification and categorization

### 4. Stage Transition Management
- Validate job status updates from `parsed` to `parse_validated`
- Test database transaction management
- Verify correlation ID tracking and audit logging
- Check for any constraint violations or errors

## Testing Procedures

### Step 1: Parsed Content Verification
```bash
# Check parsed content availability
ls -la local-storage/parsed/

# Verify content readability and format
file local-storage/parsed/*.txt
head -20 local-storage/parsed/*.txt

# Check content metadata
python scripts/check-parsed-content.py
```

### Step 2: Content Validation Testing
```bash
# Test content validation logic
python scripts/test-content-validation.py

# Validate content format and structure
python scripts/validate-content-format.py

# Test content completeness checks
python scripts/check-content-completeness.py
```

### Step 3: Duplicate Detection Testing
```bash
# Test duplicate content detection
python scripts/test-duplicate-detection.py

# Validate canonical path handling
python scripts/test-canonical-paths.py

# Test content hash comparison
python scripts/test-content-hashing.py
```

### Step 4: Stage Transition Validation
```bash
# Monitor job stage transitions
docker-compose logs base-worker -f

# Check database for stage changes
python scripts/monitor-stage-transitions.py
```

### Step 5: Database State Validation
```sql
-- Check job stage transitions
SELECT job_id, stage, updated_at, parsed_path, parsed_sha256
FROM upload_pipeline.upload_jobs 
WHERE stage IN ('parsed', 'parse_validated')
ORDER BY updated_at DESC;

-- Verify parsed content metadata
SELECT * FROM upload_pipeline.documents 
WHERE parsed_path IS NOT NULL AND parsed_sha256 IS NOT NULL;
```

## Expected Outcomes

### Success Scenario
- Parsed content available and accessible for validation
- Content validation logic executes successfully
- Format and completeness checks pass
- Duplicate detection working correctly
- Jobs transition from `parsed` to `parse_validated` stage
- All validation metadata captured accurately
- Ready to proceed to Phase 3.5 (parse_validated → chunking)

### Failure Scenarios
- Parsed content not accessible or readable
- Content validation logic failing
- Format or completeness checks failing
- Duplicate detection not working correctly
- Stage transition failures

## Risk Assessment

### High Risk
- **Content Validation Failures**: Validation logic not working correctly
  - *Mitigation*: Test validation logic thoroughly with various content types
- **Duplicate Detection Issues**: Duplicate content not detected properly
  - *Mitigation*: Test with known duplicate content scenarios

### Medium Risk
- **Content Access Issues**: Parsed content not accessible
  - *Mitigation*: Verify file permissions and storage configuration
- **Stage Transition Failures**: Jobs not advancing to parse_validated stage
  - *Mitigation*: Check database constraints and transaction management

### Low Risk
- **Metadata Capture Issues**: Incomplete validation metadata
  - *Mitigation*: Validate metadata capture logic and storage
- **Content Quality Issues**: Poor content quality assessment
  - *Mitigation*: Test content quality scoring and validation

## Next Phase Readiness

### Phase 3.5 Dependencies
- ✅ `parsed → parse_validated` transition working correctly
- ✅ Content validation logic operational
- ✅ Duplicate detection functional
- ✅ Content metadata captured accurately
- ✅ Parse validation results stored correctly

### Handoff Requirements
- Complete Phase 3.4 testing results
- Content validation logic status and configuration
- Duplicate detection configuration and status
- Content metadata storage configuration
- Recommendations for Phase 3.5 implementation

## Success Metrics

### Phase 3.4 Completion Criteria
- [ ] Parsed content available and accessible for validation
- [ ] Content validation logic executes successfully
- [ ] Format and completeness checks pass
- [ ] Duplicate detection working correctly
- [ ] Jobs transition from `parsed` to `parse_validated` stage
- [ ] All validation metadata captured accurately
- [ ] Ready to proceed to Phase 3.5

---

**Phase 3.4 Status**: 🔄 IN PROGRESS  
**Focus**: parsed → parse_validated Transition Validation  
**Environment**: postgres database, parsed content storage, validation logic  
**Success Criteria**: Content validation and duplicate detection working  
**Next Phase**: Phase 3.5 (parse_validated → chunking)
