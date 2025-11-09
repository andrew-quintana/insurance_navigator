# FRACAS FM-023: Upload Jobs Status Constraint Violation

## Overview

This directory contains all documentation and investigation materials for FRACAS FM-023, a critical failure in the upload pipeline that prevents document uploads due to a database constraint violation.

## Incident Summary

- **FRACAS ID**: FM-023
- **Date**: September 30, 2025, 20:55 UTC
- **Environment**: Staging
- **Service**: Upload Pipeline API
- **Severity**: High (Complete upload functionality failure)
- **Status**: Under Investigation

## Problem Statement

The upload pipeline fails when attempting to create upload jobs due to a database check constraint violation. The code attempts to insert status values that are not allowed by the database constraint.

**Error**: `asyncpg.exceptions.CheckViolationError: new row for relation "upload_jobs" violates check constraint "ck_upload_jobs_status"`

## Files in This Directory

### Investigation Materials
- **`investigation_prompt.md`** - Comprehensive investigation prompt with detailed requirements
- **`investigation_checklist.md`** - Step-by-step checklist for conducting the investigation
- **`fracas_template.md`** - Template for future FRACAS investigations

### Key Documents
- **`investigation_prompt.md`** - Start here for the investigation
- **`investigation_checklist.md`** - Use this to track investigation progress

## Quick Start for Investigators

1. **Read the investigation prompt**: Start with `investigation_prompt.md` for full context
2. **Use the checklist**: Follow `investigation_checklist.md` to ensure thorough investigation
3. **Follow FRACAS process**: Use `fracas_template.md` for consistent documentation

## Investigation Status

- [ ] **Phase 1**: Database Schema Analysis
- [ ] **Phase 2**: Code Analysis  
- [ ] **Phase 3**: Root Cause Determination
- [ ] **Phase 4**: Solution Design
- [ ] **Phase 5**: Implementation Planning
- [ ] **Phase 6**: Prevention Measures
- [ ] **Phase 7**: Documentation
- [ ] **Phase 8**: Implementation
- [ ] **Phase 9**: Validation
- [ ] **Phase 10**: Closure

## Key Technical Details

### Database Constraint (Current)
```sql
CHECK ((status = ANY (ARRAY['uploaded'::text, 'parse_queued'::text, 'parsed'::text, 'parse_validated'::text, 'chunking'::text, 'chunks_stored'::text, 'embedding_queued'::text, 'embedding_in_progress'::text, 'embeddings_stored'::text, 'complete'::text, 'failed_parse'::text, 'failed_chunking'::text, 'failed_embedding'::text, 'duplicate'::text])))
```

### Code Status Values (Causing Violation)
- `"job_validated"` (not in allowed list)
- Additional values to be identified during investigation

### Error Location
- **File**: `api/upload_pipeline/endpoints/upload.py:479`
- **Function**: `_create_upload_job`
- **Operation**: Database INSERT into `upload_pipeline.upload_jobs`

## Related Incidents

- **FM-022**: Upload 500 Authentication Error (RESOLVED)
  - Asyncio event loop conflict
  - Database schema mismatch (stage vs status)
  - Supabase project configuration mismatch

## Investigation Requirements

### Immediate Actions
1. Identify all status values used in code vs database
2. Determine root cause of the mismatch
3. Design and implement a fix
4. Validate the fix works end-to-end

### Long-term Actions
1. Implement schema validation processes
2. Add constraint violation monitoring
3. Create prevention measures
4. Update documentation and procedures

## Success Criteria

### Investigation Complete When:
- ✅ Root cause identified and documented
- ✅ All status values catalogued
- ✅ Schema evolution timeline understood
- ✅ Recommended solution identified
- ✅ Implementation plan created

### Resolution Complete When:
- ✅ Upload functionality works end-to-end
- ✅ No constraint violations occur
- ✅ All tests pass
- ✅ Documentation updated
- ✅ Monitoring in place

## Contact Information

- **Primary Investigator**: [To be assigned]
- **Technical Lead**: [To be assigned]
- **Product Owner**: [To be assigned]

## Last Updated

September 30, 2025 - Initial investigation materials created
