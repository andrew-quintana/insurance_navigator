# PHASE 2: Upload Execution Prompt

## Objective
Execute the actual document uploads for both test files and capture all upload metadata, responses, and timing information for verification.

## Context
Environment is prepared and services are running. You will now perform the core testing by uploading both insurance documents through the upload refactor 003 API and capturing detailed information about the upload process.

## Prerequisites
- Phase 1 completed successfully
- Services are running and healthy
- Upload endpoint identified and accessible
- Authentication configured (if required)

## Tasks

### 1. Upload simulated_insurance_document.pdf
- Calculate file hash (SHA256) before upload
- Prepare upload request with proper metadata:
  - filename: "simulated_insurance_document.pdf"
  - bytes_len: 1740 (actual file size)
  - mime: "application/pdf"
  - sha256: [calculated hash]
  - ocr: false
- Execute POST request to upload endpoint
- Capture complete response including:
  - job_id
  - document_id
  - signed_url
  - upload_expires_at
  - HTTP status code
  - Response headers
  - Timing information

### 2. Upload scan_classic_hmo_parsed.pdf
- Calculate file hash (SHA256) before upload
- Prepare upload request with proper metadata:
  - filename: "scan_classic_hmo_parsed.pdf"
  - bytes_len: 2516582 (actual file size)
  - mime: "application/pdf"
  - sha256: [calculated hash]
  - ocr: false
- Execute POST request to upload endpoint
- Capture complete response (same fields as above)

### 3. Error Handling and Edge Cases
- Document any errors or unexpected responses
- Test error scenarios if upload fails
- Capture retry attempts if needed
- Record any authentication issues

### 4. Response Analysis
- Validate response schema matches expected UploadResponse model
- Verify job_id and document_id are valid UUIDs
- Check signed_url format and accessibility
- Validate upload_expires_at timestamp

### 5. Performance Metrics
- Record upload request duration for each file
- Compare performance between small (1.7KB) and large (2.4MB) files
- Document any timeout or performance issues

## Success Criteria
- [ ] Both documents upload successfully (HTTP 200)
- [ ] Valid job_id and document_id returned for each upload
- [ ] Signed URLs generated and accessible
- [ ] No errors or exceptions during upload process
- [ ] Complete metadata captured for verification

## Upload Request Format
Based on the backend/api/routes/upload.py, use this request format:
```json
{
  "filename": "document.pdf",
  "bytes_len": 1234,
  "mime": "application/pdf",
  "sha256": "abc123...",
  "ocr": false
}
```

## Expected Response Format
```json
{
  "job_id": "uuid",
  "document_id": "uuid", 
  "signed_url": "https://...",
  "upload_expires_at": "2025-08-22T..."
}
```

## Output Required
- Upload execution report with all captured data
- Response payloads for both uploads
- Performance metrics and timing
- Any errors or issues encountered
- File hash calculations and verification

## Authentication Note
Check if JWT authentication is required. If so, use the test JWT generation from scripts/testing/test_production_endpoints_final.py:32-50.

## Next Phase
Once uploads are executed successfully, proceed to Phase 3: Database and Storage Verification to confirm the data was properly stored.