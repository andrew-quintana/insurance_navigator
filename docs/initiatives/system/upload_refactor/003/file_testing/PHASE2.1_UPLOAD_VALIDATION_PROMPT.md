# Phase 2.1 Execution Prompt: Upload Endpoint Validation and File Storage Testing

## Context
You are implementing Phase 2.1 of the 003 Worker Refactor iteration. This phase focuses on comprehensive upload endpoint validation and file storage testing to ensure the complete upload flow works correctly. This phase addresses the critical issue identified in Phase 2 where files were not actually being uploaded to storage - only the API contract was being tested.

## Documentation References
Please review these documents before starting implementation:
- `docs/initiatives/system/upload_refactor/003/file_testing/TODO001.md` - **PRIMARY REFERENCE**: Complete Phase 2.1 implementation checklist and requirements
- `docs/initiatives/system/upload_refactor/003/file_testing/PHASE2_UPLOAD_EXECUTION_PROMPT.md` - Previous upload testing approach and lessons learned
- `docs/initiatives/system/upload_refactor/003/file_testing/TEST_METHOD001.md` - Testing methodology and procedures
- `TODO003_phase2_notes.md` - Phase 2 infrastructure validation framework implementation
- `TODO003_phase2_decisions.md` - Previous infrastructure validation decisions
- `docs/initiatives/system/upload_refactor/003/RFC003.md` - Technical design for upload and storage systems

## Primary Objective
**IMPLEMENT** comprehensive upload endpoint validation and file storage testing to ensure the complete upload flow works correctly. All implementation requirements, testing specifications, and detailed checklists are defined in the **TODO003.md** document.

## Critical Issue to Resolve
The previous testing only completed Step 1 (getting signed URL) but never Step 2 (uploading actual file content to storage). This is why no files appeared in the storage system. You must implement and test the complete two-step upload process.

## Implementation Approach
1. **Read TODO003.md thoroughly** - Use the Phase 2.1 section as your primary implementation guide
2. **Follow the detailed checklist** - Complete all Phase 2.1 tasks and validation requirements
3. **Test complete upload flow** - Implement both Step 1 (signed URL) and Step 2 (file upload)
4. **Verify file storage** - Confirm files actually appear in storage system
5. **Validate database integration** - Check that records are created correctly

## Expected Outputs
Document your work in these files:
- `TODO003_phase2.1_notes.md` - Upload validation implementation details and testing results
- `TODO003_phase2.1_decisions.md` - Upload validation strategies and technical decisions
- `TODO003_phase2.1_handoff.md` - BaseWorker implementation requirements for Phase 3
- `TODO003_phase2.1_testing_summary.md` - Complete upload testing results and verification

## Key Focus Areas

### 1. Complete Upload Flow Testing
- **Step 1**: POST to `/api/v2/upload` to get signed URL
- **Step 2**: PUT actual file content to the signed URL
- **Validation**: Confirm files appear in storage system
- **Testing**: Both small (1.7KB) and large (2.4MB) files

### 2. File Storage Verification
- **File Presence**: Check if uploaded files are visible in storage UI
- **Content Integrity**: Validate file metadata and content
- **Access Controls**: Test authentication and authorization
- **Storage Paths**: Verify correct storage structure

### 3. Database Integration Validation
- **Upload Jobs**: Confirm job records are created correctly
- **Documents**: Validate document records in upload_pipeline.documents table
- **Relationships**: Check user_id and document_id relationships
- **Progress Tracking**: Verify job status and correlation IDs

### 4. Error Handling and Resilience
- **Failure Scenarios**: Test various error conditions
- **Recovery Mechanisms**: Validate retry logic and error handling
- **Edge Cases**: Test concurrent uploads and rate limiting
- **Monitoring**: Verify error logging and alerting

## Success Criteria
- [ ] Both test files upload successfully through complete flow
- [ ] Files are visible and accessible in storage system
- [ ] Database records are created correctly for both uploads
- [ ] Upload response schema matches expected format
- [ ] No errors or exceptions during upload process
- [ ] Complete metadata captured for verification
- [ ] File content integrity verified after upload

## Technical Requirements
- **API Endpoint**: `/api/v2/upload` with JWT authentication
- **File Types**: PDF documents (application/pdf)
- **File Sizes**: 1.7KB and 2.4MB test files
- **Storage System**: Local Supabase storage simulation
- **Database**: PostgreSQL with upload_pipeline schema
- **Authentication**: JWT tokens with proper claims

## Next Phase
Once Phase 2.1 is completed successfully, proceed to Phase 3: BaseWorker Implementation with Local Testing to implement the enhanced worker system that will process the uploaded documents.

## Implementation Notes
- **Use TODO003.md as primary reference** - All detailed requirements are defined there
- **Focus on complete upload flow** - Don't just test API contracts, test actual file storage
- **Verify database integration** - Ensure records are created and relationships are correct
- **Document everything** - Create comprehensive testing documentation for future reference

Start by reading the Phase 2.1 section in TODO003.md thoroughly, then implement comprehensive upload endpoint validation and file storage testing following the detailed checklist and requirements.


