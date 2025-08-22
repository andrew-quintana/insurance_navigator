# PHASE 4: Visual Inspection Link Generation Prompt

## Objective
Generate accessible links and create visual documentation for stakeholder verification of the upload refactor 003 testing results.

## Context
Database and storage verification has been completed successfully. You now need to create user-friendly links and documentation that allows stakeholders to visually inspect the test results and confirm the upload system is working correctly.

## Prerequisites
- Phase 3 completed successfully
- Database records verified
- File storage confirmed
- All metadata validated

## Tasks

### 1. Generate Signed URLs for Manual Access
Create long-lived signed URLs for both test documents:

#### For simulated_insurance_document.pdf:
- Generate signed URL with extended expiration (24-48 hours)
- Test URL accessibility in browser
- Document URL format and parameters
- Verify PDF opens and displays correctly

#### For scan_classic_hmo_parsed.pdf:
- Generate signed URL with extended expiration (24-48 hours) 
- Test URL accessibility in browser
- Document URL format and parameters
- Verify PDF opens and displays correctly

### 2. Database Inspection Links
If Supabase provides database UI access, create links to:
- Documents table filtered for test documents
- Upload jobs table filtered for test jobs
- Events table showing test upload events
- Any relevant indexes or views

### 3. Create Visual Documentation
Prepare stakeholder-friendly documentation:

#### Upload Summary Report
Create a summary showing:
- Test execution timestamp
- Both uploaded documents with metadata
- Success indicators and status
- File sizes, types, and hashes
- Database record confirmations

#### Visual Evidence Package
Compile screenshots/evidence of:
- Successful upload API responses
- Database records for both documents
- File accessibility via signed URLs
- Bucket storage confirmation
- Any monitoring dashboards showing activity

### 4. Testing Evidence Compilation
Create a comprehensive evidence package:

#### Test Results Dashboard
Format results in an easy-to-read table:
```
| Document | Size | Status | Document ID | Job ID | Signed URL | Database ✓ | Storage ✓ |
|----------|------|---------|-------------|---------|------------|------------|-----------|
| simulated_insurance_document.pdf | 1.7KB | Success | abc-123 | def-456 | [Link] | ✅ | ✅ |
| scan_classic_hmo_parsed.pdf | 2.4MB | Success | ghi-789 | jkl-012 | [Link] | ✅ | ✅ |
```

#### Verification Checklist
Present completed verification items:
- [x] Documents uploaded successfully
- [x] Database records created
- [x] Files stored in correct buckets
- [x] Metadata accuracy verified
- [x] File integrity confirmed
- [x] Access URLs functional

### 5. Create Inspection Instructions
Provide clear instructions for stakeholders:

#### Manual Verification Steps:
1. Click signed URL for each document
2. Verify PDF opens correctly in browser
3. Check document content matches expected files
4. Confirm file properties (size, page count, etc.)
5. Verify timestamps are recent and accurate

#### Database Verification Steps:
1. Access Supabase dashboard
2. Navigate to upload_pipeline schema
3. Check documents table for new records
4. Verify upload_jobs table shows processing status
5. Review events table for audit trail

### 6. Generate Shareable Report
Create a final testing report document containing:
- Executive summary of testing results
- Detailed verification findings
- All access links with instructions
- Evidence screenshots/data
- Success metrics and criteria met
- Recommendations for production deployment

## Success Criteria
- [ ] Signed URLs generated and tested for both documents
- [ ] Visual documentation package complete
- [ ] Stakeholder-friendly report created
- [ ] All access links functional and documented
- [ ] Instructions clear and actionable

## Link Requirements
- URLs must be accessible without special authentication
- Links should remain valid for 24-48 hours minimum
- Include fallback access methods if links expire
- Document any access restrictions or requirements

## Output Required
- Complete set of signed URLs for document access
- Visual inspection report with all evidence
- Stakeholder instructions for verification
- Testing summary dashboard
- Recommendations for next steps

## Quality Assurance
Before finalizing:
- [ ] Test all generated links in fresh browser session
- [ ] Verify documents display correctly
- [ ] Confirm all database links work
- [ ] Review report for clarity and completeness
- [ ] Check that non-technical stakeholders can follow instructions

## Stakeholder Communication
Include in the final report:
- Clear statement of testing success
- Confidence level in system readiness
- Any limitations or notes for production use
- Contact information for questions
- Timeline for production deployment readiness

## Next Phase
Upon completion, deliver the comprehensive testing package to stakeholders and prepare for production deployment validation.