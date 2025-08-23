# TEST_METHOD001 — Upload Refactor 003 File Testing Methodology

## Purpose
Validate the end-to-end functionality of the upload refactor 003 system by testing document upload, processing, storage, and database record creation using representative insurance documents. Focus on complete processing pipeline validation and end-to-end workflow testing.

## Scope

### Inclusions
- PDF document upload functionality
- File storage verification in Supabase buckets
- Database record creation and integrity
- File path accuracy and accessibility
- Upload service endpoint validation
- Authentication and authorization flows
- Error handling and edge cases
- **Complete processing pipeline validation (9 stages)**
- **End-to-end workflow testing and integration**
- **Performance and scalability testing**
- **Real API integration testing (cost-controlled)**

### Exclusions
- Performance benchmarking (separate test suite)
- Security penetration testing (separate security audit)
- Mobile client testing (web interface only)
- Bulk upload scenarios (single file focus)

## Verification Goals
1. **Functional Verification**: Confirm upload pipeline processes documents correctly
2. **Data Integrity**: Verify database records match uploaded file metadata
3. **Storage Validation**: Ensure files are stored in correct buckets with proper paths
4. **Accessibility**: Confirm uploaded files can be retrieved and accessed
5. **Traceability**: Validate complete audit trail from upload to storage
6. **Processing Pipeline**: Validate all 9 processing stages work automatically
7. **End-to-End Workflow**: Test complete document lifecycle from upload to completion
8. **Performance**: Establish performance baselines and scalability characteristics

## Acceptance Criteria
- [ ] Documents upload without errors
- [ ] Database records created with correct metadata
- [ ] Files stored in designated Supabase buckets
- [ ] File paths are accessible and valid
- [ ] Upload timestamps are accurate
- [ ] File size and type validation works correctly
- [ ] Visual inspection links are functional
- [ ] **All 9 processing stages transition automatically**
- [ ] **Complete end-to-end pipeline processing validated**
- [ ] **Performance metrics within acceptable limits**
- [ ] **Error handling and recovery working correctly**

## Environment
- **System**: Upload Refactor 003 implementation
- **Database**: **postgres database** (not accessa_dev)
- **Storage**: Supabase bucket storage
- **Client**: Web interface
- **Authentication**: Standard user authentication flow
- **Processing**: Local worker processes with mock services

## Setup Requirements
1. Supabase connection verified
2. Upload service endpoints accessible
3. Test documents available:
   - `examples/simulated_insurance_document.pdf` (1.7KB)
   - `examples/scan_classic_hmo_parsed.pdf` (2.4MB)
4. **Database access for verification queries (postgres database)**
5. Bucket access for storage verification
6. **Local worker processes running and operational**
7. **Mock services (LlamaParse, OpenAI) operational**

## Test Protocol

### Phase 1: Pre-Test Validation
1. Verify upload service is running
2. **Confirm database connectivity (postgres database)**
3. Validate bucket permissions
4. **Verify worker processes are operational**
5. **Verify mock services are responding**
6. Document baseline state

### Phase 2: Upload Execution
1. Upload `simulated_insurance_document.pdf`
2. Capture upload response and metadata
3. Upload `scan_classic_hmo_parsed.pdf`
4. Capture upload response and metadata

### Phase 3: Processing Pipeline Validation (Sub-phases 3.1-3.9)
1. **Phase 3.1**: Validate queued → job_validated transition
2. **Phase 3.2**: Validate job_validated → parsing transition
3. **Phase 3.3**: Validate parsing → parsed transition
4. **Phase 3.4**: Validate parsed → parse_validated transition
5. **Phase 3.5**: Validate parse_validated → chunking transition
6. **Phase 3.6**: Validate chunking → chunks_buffered transition
7. **Phase 3.7**: Validate chunks_buffered → embedding transition
8. **Phase 3.8**: Validate embedding → embedded transition
9. **Phase 3.9**: Validate complete end-to-end pipeline

### Phase 4: End-to-End Workflow Validation
1. **Phase 4.1**: Complete pipeline integration testing
2. **Phase 4.2**: Failure scenario testing and recovery
3. **Phase 4.3**: Performance and scalability testing
4. **Phase 4.4**: Real API integration testing (cost-controlled)
5. **Phase 4.5**: Production readiness validation

### Phase 5: Documentation and Reporting
1. Record all test results
2. Generate visual inspection links
3. Document any anomalies or issues
4. Create comprehensive verification report

## Traceability Matrix

| Test ID | Requirement | Test Case | Expected Result | Actual Result | Status |
|---------|-------------|-----------|-----------------|---------------|---------|
| TC001 | File Upload | Upload PDF document | HTTP 200, upload ID returned | TBD | Pending |
| TC002 | Database Record | Verify DB entry creation | Record exists with correct metadata | TBD | Pending |
| TC003 | Bucket Storage | Confirm file in bucket | File accessible in designated bucket | TBD | Pending |
| TC004 | File Path | Validate storage path | Path follows expected naming convention | TBD | Pending |
| TC005 | File Integrity | Verify file contents | Uploaded file matches original | TBD | Pending |
| TC006 | Access Links | Test download links | Links provide valid file access | TBD | Pending |
| **TC007** | **Processing Pipeline** | **Validate all 9 stages** | **Automatic transitions working** | **TBD** | **Pending** |
| **TC008** | **End-to-End Workflow** | **Complete document processing** | **Upload to completion working** | **TBD** | **Pending** |
| **TC009** | **Performance Testing** | **Concurrent processing** | **System handles load correctly** | **TBD** | **Pending** |
| **TC010** | **Error Recovery** | **Failure scenario handling** | **System recovers gracefully** | **TBD** | **Pending** |

## Processing Pipeline Test Matrix

| Stage | From | To | Test Focus | Success Criteria |
|-------|------|----|------------|------------------|
| 3.1 | queued | job_validated | Manual validation | ✅ COMPLETED |
| 3.2 | job_validated | parsing | Worker automation | Automatic processing |
| 3.3 | parsing | parsed | LlamaParse integration | Webhook handling |
| 3.4 | parsed | parse_validated | Content validation | Format and completeness |
| 3.5 | parse_validated | chunking | Chunking logic | Chunk generation |
| 3.6 | chunking | chunks_buffered | Buffer management | Chunk storage |
| 3.7 | chunks_buffered | embedding | OpenAI integration | Vector generation |
| 3.8 | embedding | embedded | Finalization | Complete processing |
| 3.9 | Complete Pipeline | End-to-end | Integration | All stages working |

## Risk Assessment & Mitigation

### High Risk
- **Data Loss**: Files uploaded but not properly stored
  - *Mitigation*: Immediate verification after each upload
- **Database Corruption**: Invalid records created
  - *Mitigation*: Transaction rollback capabilities verified
- **Processing Pipeline Failure**: Jobs stuck in intermediate stages
  - *Mitigation*: Comprehensive stage transition validation

### Medium Risk
- **Permission Issues**: Access denied to buckets/database
  - *Mitigation*: Pre-test permission validation
- **Network Failures**: Upload interruption
  - *Mitigation*: Retry mechanisms and error logging
- **Worker Process Issues**: Jobs not processed automatically
  - *Mitigation*: Worker health monitoring and restart procedures

### Low Risk
- **File Format Issues**: Unsupported PDF variants
  - *Mitigation*: Use known-good test documents
- **API Rate Limiting**: External service throttling
  - *Mitigation*: Rate limit handling and retry logic

## Reporting
- **Success Metrics**: Upload completion rate, data integrity score, processing pipeline success rate
- **Failure Tracking**: Error codes, failure points, recovery actions, stage transition failures
- **Performance Notes**: Upload duration, processing time, stage transition timing
- **Visual Evidence**: Screenshots of database records, bucket contents, processing stages
- **Inspection Links**: Direct URLs for manual verification
- **Pipeline Metrics**: Stage transition success rates, processing times, error rates

## Test Execution Date
TBD - To be populated during test execution

## Test Engineer
Claude Code Assistant

## Review and Approval
- [ ] Test methodology reviewed
- [ ] Test cases approved
- [ ] Environment validated
- [ ] **Worker processes operational**
- [ ] **Mock services responding**
- [ ] Ready for execution

## Database Configuration Note
**IMPORTANT**: All testing uses the **postgres database** (not accessa_dev). Ensure all database connections and queries reference the correct database name.