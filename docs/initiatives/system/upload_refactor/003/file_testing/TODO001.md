# TODO001 — Upload Refactor 003 File Testing

## Phase 0 — Context Harvest
- [x] Review adjacent components in CONTEXT.md
- [x] Update ADJACENT_INDEX.md with current dates
- [x] Collect interface contracts from adjacent systems
- [x] Validate token budget allocation
- [x] Block: Implementation cannot proceed until Phase 0 complete

## Phase 1 — Planning
- [x] Complete TEST_METHOD001.md
- [ ] Review upload refactor 003 implementation details
- [ ] Identify test file specifications and requirements
- [ ] Map database schema for verification
- [ ] Define bucket structure and naming conventions
- [ ] Establish baseline metrics and acceptance criteria

## Phase 2 — Environment Preparation
- [x] Verify Supabase connection and authentication
- [x] Confirm upload service endpoint availability
- [x] Validate bucket permissions and access
- [x] Set up database query tools and access
- [x] Prepare test document inventory
- [x] Document pre-test system state

## Phase 2.1 — Upload Validation and File Storage Testing
- [x] Implement comprehensive upload endpoint validation
- [x] Test complete two-step upload process (signed URL + file upload)
- [x] Verify files appear in storage system
- [x] Validate database integration
- [x] Fix signed URL configuration for environment switching
- [x] Implement mock vs development environment switching
- [x] Test end-to-end upload flow in development mode
- [x] Verify files appear in Supabase dashboard

## Phase 3 — Database Flow Verification and Processing Outcomes

### Expected Processing State Flow
```
queued → job_validated → parsing → parsed → parse_validated → chunking → chunks_buffered → embedding → embedded
```

### Job Status Definitions
- **queued**: Initial state when job is first created. Document has been uploaded and a job has been enqueued for processing.
- **job_validated**: Confirmed via hash not to be a dupe upload, proceeds to this state to confirm it needs processing
- **parsing**: Document is actively being processed by the parser (e.g., LlamaParse) to extract text and structure.
- **parsed**: Parser has completed processing and returned results via webhook, but results haven't been validated yet.
- **parse_validated**: Parsed content has been validated (format, completeness, uniqueness in blob storage) and is ready for chunking.
- **chunking**: System is actively dividing the parsed document into semantic chunks for embedding and deduped via hashing.
- **chunks_buffered**: All chunks have been created and stored in the appropriate table but not yet committed to the main chunks table.
- **embedding**: System is actively generating vector embeddings for the document chunks in the buffer table. (As each row is embedded written to the `document_chunks` table (with hashing deduping) it is removed from the buffer table.
- **embedded**: All embeddings have been successfully written to the appropriate chunks and the chunks have been moved from the buffer to the `document_chunks` table. The table is ready for rag operations.

### Database Verification Tasks
- [ ] Connect to upload_pipeline database schema
- [ ] Query documents table for uploaded file records (master document metadata)
- [ ] Verify upload_jobs table for processing queue entries (job lifecycle management)
- [ ] Check events table for audit trail and processing history (state transitions)
- [ ] Validate document_chunks table for processed chunks (final output)
- [ ] Check chunk buffer table for temporary storage during processing
- [ ] Validate cross-table relationships and foreign key integrity
- [ ] Verify processing state progression follows defined flow (queued → embedded)
- [ ] Test data integrity (file sizes, hashes, metadata accuracy)
- [ ] Measure database processing performance and capacity
- [ ] Document complete data flow through all database tables
- [ ] Verify correlation IDs and traceability end-to-end
- [ ] Check for any processing errors or failed states
- [ ] Validate user authentication and session tracking
- [ ] Verify state transition events logged for each status change
- [ ] Confirm chunking and embedding processes working correctly
- [ ] Validate buffer table management during processing

## Phase 4 — Verification & Validation
- [ ] Query database for created records
- [ ] Verify file metadata accuracy (size, type, timestamps)
- [ ] Confirm bucket storage locations and paths
- [ ] Test file accessibility via generated URLs
- [ ] Validate file integrity (checksums, content verification)
- [ ] Cross-reference upload responses with database entries

## Phase 5 — Documentation & Reporting
- [ ] Generate visual inspection links for manual verification
- [ ] Create verification report with test results
- [ ] Document discovered issues or anomalies
- [ ] Update traceability matrix with actual results
- [ ] Prepare stakeholder summary
- [ ] Archive test artifacts and evidence

## Phase 6 — Post-Test Activities
- [ ] Clean up test data if required
- [ ] Update system documentation based on findings
- [ ] Recommend improvements or fixes
- [ ] Schedule follow-up testing if needed
- [ ] Mark initiative testing phase complete

## Blockers
- Database access credentials or permissions
- Upload service availability or configuration issues
- Network connectivity to Supabase infrastructure
- Test document availability or corruption

## Notes
- Test documents:
  - `test_document.pdf` (63 bytes) - Successfully uploaded and stored in Phase 2.1
  - Additional test documents can be created as needed for database flow testing
- Focus on database processing pipeline validation rather than file storage testing
- Processing state flow: queued → job_validated → parsing → parsed → parse_validated → chunking → chunks_buffered → embedding → embedded
- Visual inspection links critical for stakeholder confidence
- Database record verification must include all expected fields and relationships
- Processing state progression validation essential for downstream processing
- State transitions must be properly logged in events table
- Chunking and embedding processes must be validated through buffer and final tables
- Performance metrics should be captured for each processing stage

## Risk Mitigation
- Backup test environment state before execution
- Document rollback procedures for any test data
- Maintain audit trail of all test activities
- Establish communication channel for real-time issue reporting

## Success Criteria
- Database processing pipeline fully validated
- All tables populated with correct data and relationships
- Processing state progression working correctly
- Performance metrics within acceptable limits
- Complete traceability maintained end-to-end
- Zero data integrity issues identified
- Complete documentation package delivered

## Current Status
- **Phase 2.1**: ✅ COMPLETED - Upload validation and file storage working
- **Phase 3**: 🔄 IN PROGRESS - Database flow verification and processing outcomes
- **Next Focus**: Database schema validation, processing pipeline verification, and performance testing