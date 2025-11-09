# FRACAS FM-023 Investigation Prompt

## Failure Mode Analysis and Corrective Action System (FRACAS)

**FRACAS ID**: FM-023  
**Date**: September 30, 2025, 20:55 UTC  
**Environment**: Staging  
**Service**: Upload Pipeline API  
**Severity**: High (Complete upload functionality failure)

---

## Executive Summary

The upload pipeline is experiencing a database constraint violation when attempting to create upload jobs. While authentication has been successfully resolved (FM-022), a new critical issue has emerged that completely prevents document uploads.

**Current Status**: 
- ✅ Authentication working (user successfully validated)
- ❌ Database constraint violation when creating upload jobs
- ❌ Upload functionality completely broken

---

## Failure Description

### Primary Symptom
```
asyncpg.exceptions.CheckViolationError: new row for relation "upload_jobs" violates check constraint "ck_upload_jobs_status"
DETAIL: Failing row contains (..., job_validated, ...)
```

### Error Context
- **Location**: `api/upload_pipeline/endpoints/upload.py:479` in `_create_upload_job` function
- **Trigger**: User attempts to upload a document after successful authentication
- **Result**: 500 Internal Server Error returned to frontend
- **Impact**: Complete upload functionality failure

### User Experience Impact
- Users can authenticate successfully
- Upload requests fail with 500 error
- No documents can be processed
- Error message: "Failed to process upload request"

---

## Root Cause Analysis Required

### 1. Database Schema Investigation
**Task**: Analyze the database constraint definition and compare with code expectations

**Investigation Steps**:
1. Query the database constraint definition:
   ```sql
   SELECT conname, pg_get_constraintdef(oid) as definition
   FROM pg_constraint 
   WHERE conrelid = 'upload_pipeline.upload_jobs'::regclass 
   AND conname = 'ck_upload_jobs_status';
   ```

2. Document the allowed status values from the constraint
3. Identify which specific values are causing violations

**Expected Output**: Clear documentation of what status values the database allows

### 2. Code Analysis
**Task**: Examine the upload pipeline code to identify status values being used

**Files to Investigate**:
- `api/upload_pipeline/endpoints/upload.py` (line 479 - `_create_upload_job`)
- `api/upload_pipeline/models.py` (status validation)
- `api/upload_pipeline/utils/upload_pipeline_utils.py` (status handling)

**Investigation Steps**:
1. Find all places where status values are hardcoded
2. Identify the status values being inserted into the database
3. Check for any status value mappings or transformations
4. Document the complete list of status values used in code

**Expected Output**: Complete list of status values the code is trying to use

### 3. Schema Evolution Analysis
**Task**: Determine if this is a schema drift issue

**Investigation Steps**:
1. Check migration history for `upload_jobs` table changes
2. Look for any recent migrations that modified the status constraint
3. Compare the original migration definition with current database state
4. Identify when the mismatch was introduced

**Files to Check**:
- `supabase/migrations/20250814000000_init_upload_pipeline.sql`
- Any subsequent migrations affecting `upload_jobs` table
- Database schema in staging vs production

**Expected Output**: Understanding of when and why the schema mismatch occurred

---

## Corrective Action Requirements

### Immediate Actions Required
1. **Fix the constraint violation** - Either:
   - Update code to use valid status values, OR
   - Update database constraint to include code's values

2. **Validate the fix** - Ensure:
   - Upload functionality works end-to-end
   - No other constraint violations exist
   - Status values are consistent across the system

### Long-term Actions Required
1. **Schema consistency audit** - Ensure code and database are always in sync
2. **Constraint validation testing** - Add tests to catch constraint violations
3. **Migration validation** - Ensure migrations don't introduce schema mismatches

---

## Investigation Deliverables

### 1. Root Cause Report
- **What**: Detailed analysis of the schema mismatch
- **When**: When the mismatch was introduced
- **Why**: Why the mismatch occurred (migration issue, code change, etc.)
- **Impact**: Full impact assessment

### 2. Solution Design
- **Option A**: Update code to match database constraint
- **Option B**: Update database constraint to match code
- **Recommendation**: Which option is preferred and why
- **Risk Assessment**: Risks associated with each option

### 3. Implementation Plan
- **Steps**: Detailed steps to implement the fix
- **Testing**: How to validate the fix works
- **Rollback**: Plan to rollback if issues arise
- **Monitoring**: How to detect similar issues in the future

### 4. Prevention Measures
- **Process**: How to prevent similar issues
- **Tooling**: Tools or processes to catch schema mismatches
- **Documentation**: Update documentation to reflect changes

---

## Technical Context

### Database Constraint (Current)
```sql
CHECK ((status = ANY (ARRAY['uploaded'::text, 'parse_queued'::text, 'parsed'::text, 'parse_validated'::text, 'chunking'::text, 'chunks_stored'::text, 'embedding_queued'::text, 'embedding_in_progress'::text, 'embeddings_stored'::text, 'complete'::text, 'failed_parse'::text, 'failed_chunking'::text, 'failed_embedding'::text, 'duplicate'::text])))
```

### Code Status Values (Suspected)
- `"job_validated"` (causing the violation)
- Additional values to be identified during investigation

### Error Details
```
Failing row contains (51ccc660-daf4-4db2-9d5f-9e1226d09cae, 2f064818-4568-5ca2-ad05-e26484d8f1c4, queued, 0, null, 2025-09-30 20:55:04.154692+00, 2025-09-30 20:55:04.154692+00, job_validated, {}, null, markdown-simple@1, text-embedding-3-small, 1)
```

---

## Success Criteria

### Investigation Complete When:
1. ✅ Root cause identified and documented
2. ✅ All status values in code and database catalogued
3. ✅ Schema evolution timeline understood
4. ✅ Recommended solution identified
5. ✅ Implementation plan created
6. ✅ Prevention measures defined

### Resolution Complete When:
1. ✅ Upload functionality works end-to-end
2. ✅ No constraint violations occur
3. ✅ All tests pass
4. ✅ Documentation updated
5. ✅ Monitoring in place

---

## Related Incidents

- **FM-022**: Upload 500 Authentication Error (RESOLVED)
  - Asyncio event loop conflict
  - Database schema mismatch (stage vs status)
  - Supabase project configuration mismatch

---

## Investigation Notes

### Key Questions to Answer
1. What status values does the code expect to use?
2. What status values does the database constraint allow?
3. When did this mismatch occur?
4. Which approach is better: update code or update database?
5. Are there other similar mismatches in the system?

### Tools Available
- Supabase MCP for database queries
- Render MCP for service logs
- Local development environment for testing
- Git history for code analysis

---

**Investigation Priority**: HIGH  
**Estimated Time**: 2-4 hours  
**Assigned To**: [To be assigned]  
**Due Date**: [To be set]
