# PHASE 3: Database and Storage Verification Prompt

## Objective
Verify that uploaded documents were correctly stored in the database and Supabase buckets, with accurate metadata and accessible file paths.

## Context
Both test documents have been uploaded successfully via the upload refactor 003 API. You now need to verify that the data was properly persisted in the database and that files are accessible in the correct bucket locations.

## Prerequisites
- Phase 2 completed successfully
- Both uploads returned job_id and document_id values
- Upload responses captured and available

## Tasks

### 1. Database Record Verification
Query the following tables to verify records were created:

#### Documents Table (`upload_pipeline.documents`)
```sql
SELECT document_id, user_id, filename, mime, bytes_len, 
       file_sha256, raw_path, created_at, updated_at
FROM upload_pipeline.documents 
WHERE document_id IN ('doc_id_1', 'doc_id_2')
ORDER BY created_at DESC;
```

Verify for each document:
- [ ] Document ID matches upload response
- [ ] Filename is correct
- [ ] File size (bytes_len) matches actual file size
- [ ] SHA256 hash matches calculated hash
- [ ] Raw path follows expected format
- [ ] Created/updated timestamps are recent

#### Upload Jobs Table (`upload_pipeline.upload_jobs`)
```sql
SELECT job_id, document_id, user_id, status, raw_path,
       chunks_version, embed_model, embed_version, progress,
       retry_count, correlation_id, created_at, updated_at
FROM upload_pipeline.upload_jobs 
WHERE job_id IN ('job_id_1', 'job_id_2')
ORDER BY created_at DESC;
```

Verify for each job:
- [ ] Job ID matches upload response
- [ ] Document ID links correctly
- [ ] Status is "uploaded" (initial state)
- [ ] Raw path matches document record
- [ ] Progress field contains enhanced payload
- [ ] Retry count is 0

#### Events Table (`upload_pipeline.events`)
```sql
SELECT event_id, job_id, document_id, type, severity, code,
       payload, correlation_id, ts
FROM upload_pipeline.events 
WHERE job_id IN ('job_id_1', 'job_id_2')
ORDER BY ts DESC;
```

Verify events were logged:
- [ ] UPLOAD_ACCEPTED events created
- [ ] Correlation IDs match
- [ ] Event payloads contain upload metadata

### 2. Storage Bucket Verification
Check Supabase bucket storage for uploaded files:

#### File Existence Verification
For each document, verify the file exists at the raw_path location:
- Check bucket: [configured raw bucket name]
- Path format: `{user_id}/{document_id}.pdf`
- File accessibility via generated signed URLs

#### File Integrity Verification
- Download files via signed URLs
- Calculate SHA256 hash of downloaded files
- Compare with original file hashes
- Verify file sizes match exactly

### 3. Cross-Reference Validation
Ensure data consistency across all systems:
- [ ] Database document_id matches job document_id
- [ ] Raw paths in documents table match jobs table
- [ ] File paths in database match actual bucket locations
- [ ] File hashes in database match actual file hashes
- [ ] File sizes in database match actual file sizes

### 4. Access Control Verification
Test file accessibility:
- [ ] Files are accessible via signed URLs from upload response
- [ ] Direct bucket access works (if configured)
- [ ] Files are not publicly accessible without authentication

### 5. Metadata Accuracy
Comprehensive metadata verification:

**For simulated_insurance_document.pdf:**
- [ ] Size: ~1,740 bytes
- [ ] Type: application/pdf
- [ ] SHA256: [verify hash]
- [ ] Path: storage://{bucket}/{user_id}/{doc_id}.pdf

**For scan_classic_hmo_parsed.pdf:**
- [ ] Size: ~2,516,582 bytes
- [ ] Type: application/pdf
- [ ] SHA256: [verify hash]
- [ ] Path: storage://{bucket}/{user_id}/{doc_id}.pdf

## Success Criteria
- [ ] All database records created correctly
- [ ] Files stored in correct bucket locations
- [ ] File integrity verified (hashes match)
- [ ] All metadata is accurate
- [ ] Files are accessible via generated URLs
- [ ] Cross-references between tables are consistent

## Database Connection
Use the database configuration from the upload service:
- URL: From UPLOAD_PIPELINE_SUPABASE_URL environment variable
- Service role key for admin access

## Output Required
- Database verification report with query results
- Storage verification report with file details
- Cross-reference validation results
- Any discrepancies or issues discovered
- Complete traceability matrix showing data flow

## Troubleshooting
If verification fails:
- Check service logs for errors
- Verify database permissions
- Confirm bucket permissions and configuration
- Review upload response data for accuracy

## Next Phase
Once verification is complete, proceed to Phase 4: Visual Inspection Link Generation to provide stakeholder-friendly access for manual verification.