# FRACAS FM-024 Investigation Prompt

## Failure Mode Analysis and Corrective Action System (FRACAS)

**FRACAS ID**: FM-024  
**Date**: September 30, 2025, 21:35 UTC  
**Environment**: Staging  
**Service**: Upload Pipeline API - Storage Layer  
**Severity**: High (Storage authentication prevents file uploads)  
**Related**: FM-023 (RESOLVED - Database constraint violation)

---

## Executive Summary

The upload pipeline is experiencing a Supabase storage authentication failure when attempting to generate signed URLs for file uploads. While the database constraint violation (FM-023) has been successfully resolved, a new critical issue has emerged that prevents the completion of the upload process.

**Current Status**: 
- ✅ Authentication working (user successfully validated)
- ✅ Database operations working (upload jobs created successfully)
- ❌ Storage authentication failing (signature verification failed)
- ❌ Upload functionality partially broken (files cannot be uploaded)

---

## Failure Description

### Primary Symptom
```
storage3.exceptions.StorageApiError: {'statusCode': 403, 'error': Unauthorized, 'message': signature verification failed}
```

### Error Context
- **Location**: `api/upload_pipeline/endpoints/upload.py:519` in `_generate_signed_url` function
- **Trigger**: User attempts to upload a document after successful authentication and database job creation
- **Result**: 500 Internal Server Error returned to frontend
- **Impact**: File uploads cannot be completed, though database operations succeed

### User Experience Impact
- Users can authenticate successfully
- Upload requests progress past database insertion
- Signed URL generation fails with 500 error
- No files can be uploaded to storage
- Error message: "Failed to process upload request"

---

## Root Cause Analysis Required

### 1. Supabase Storage Configuration Investigation
**Task**: Analyze the Supabase storage configuration and permissions

**Investigation Steps**:
1. Verify Supabase project storage configuration:
   ```bash
   # Check if storage is enabled
   curl -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
        -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
        "$SUPABASE_URL/storage/v1/bucket"
   ```

2. Check if the "raw" bucket exists and is accessible:
   ```bash
   # List storage buckets
   curl -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
        -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
        "$SUPABASE_URL/storage/v1/bucket/raw"
   ```

3. Verify service role key has storage permissions
4. Check storage policies and RLS settings

**Expected Output**: Clear documentation of storage configuration status

### 2. Service Role Key Analysis
**Task**: Examine the service role key configuration and permissions

**Investigation Steps**:
1. Verify the service role key is valid and not expired
2. Check if the key has proper storage permissions
3. Compare with working local development configuration
4. Validate the key format and claims

**Files to Check**:
- `.env.staging` - Staging environment variables
- `.env.development` - Working local configuration
- Supabase project settings

**Expected Output**: Understanding of key validity and permissions

### 3. Environment Configuration Comparison
**Task**: Compare staging vs development environment configurations

**Investigation Steps**:
1. Compare Supabase URLs between environments
2. Compare service role keys between environments
3. Check for any environment-specific storage settings
4. Verify bucket names and paths are consistent

**Expected Output**: Identification of configuration differences

---

## Corrective Action Requirements

### Immediate Actions Required
1. **Fix the storage authentication** - Either:
   - Update service role key with proper storage permissions, OR
   - Fix Supabase project storage configuration, OR
   - Update storage bucket policies

2. **Validate the fix** - Ensure:
   - Signed URL generation works end-to-end
   - File uploads complete successfully
   - No other storage-related errors exist

### Long-term Actions Required
1. **Storage configuration audit** - Ensure storage is properly configured
2. **Permission validation testing** - Add tests to catch storage permission issues
3. **Environment consistency** - Ensure all environments have consistent storage config

---

## Investigation Deliverables

### 1. Root Cause Report
- **What**: Detailed analysis of the storage authentication failure
- **When**: When the issue was introduced
- **Why**: Why the authentication is failing (key issue, config issue, etc.)
- **Impact**: Full impact assessment

### 2. Solution Design
(consider options if still relevant after investigation)
- **Option A**: Update service role key permissions
- **Option B**: Fix Supabase project storage configuration
- **Option C**: Update storage bucket policies
- **Recommendation**: Which option is preferred and why
- **Risk Assessment**: Risks associated with each option

### 3. Implementation Plan
- **Steps**: Detailed steps to implement the fix
- **Testing**: How to validate the fix works locally first
- **Deployment**: How to deploy to staging safely
- **Rollback**: Plan to rollback if issues arise
- **Monitoring**: How to detect similar issues in the future

### 4. Prevention Measures
- **Process**: How to prevent similar issues
- **Tooling**: Tools or processes to catch storage configuration issues
- **Documentation**: Update documentation to reflect changes

---

## Technical Context

### Error Details
```
httpx.HTTPStatusError: Client error '400 Bad Request' for url 'https://your-staging-project.supabase.co/storage/v1/object/upload/sign/files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/6160e62b_5e4390c2.pdf'

storage3.exceptions.StorageApiError: {'statusCode': 403, 'error': Unauthorized, 'message': signature verification failed}
```

### Staging Configuration
- **Supabase URL**: `https://your-staging-project.supabase.co`
- **Service Role Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTY4MDQ4MywiZXhwIjoyMDY3MjU2NDgzfQ.placeholder`
- **Storage Path**: `files/{user_id}/raw/{filename}`

### Local Development Configuration (Working)
- **Supabase URL**: `http://127.0.0.1:54321`
- **Service Role Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU`
- **Storage Path**: `files/{user_id}/raw/{filename}`

---

## Success Criteria

### Investigation Complete When:
1. ✅ Root cause identified and documented
2. ✅ Storage configuration status understood
3. ✅ Service role key permissions verified
4. ✅ Environment differences identified
5. ✅ Recommended solution identified
6. ✅ Implementation plan created
7. ✅ Prevention measures defined

### Resolution Complete When:
1. ✅ Storage authentication works end-to-end
2. ✅ File uploads complete successfully
3. ✅ All tests pass locally
4. ✅ Staging deployment successful
5. ✅ No storage-related errors occur
6. ✅ Documentation updated
7. ✅ Monitoring in place

---

## Related Incidents

- **FM-023**: Upload 500 Database Constraint Error (RESOLVED)
  - Database constraint violation (status mismatch)
  - Fixed by updating code to use correct status values
  - Upload pipeline now progresses to storage layer

---

## Investigation Notes

### Key Questions to Answer
1. Is the Supabase storage service properly configured?
2. Does the service role key have storage permissions?
3. Are there differences between staging and development configs?
4. Is the "raw" bucket properly configured and accessible?
5. Are there any storage policies blocking the operation?

### Tools Available
- Supabase MCP for database and project queries
- Render MCP for service logs
- Local development environment for testing
- Test scripts for replication

### Test Scripts Available
- `test_staging_storage_error.py` - Replicates the error locally
- `test_storage_auth_error.py` - Tests local storage (working)
- `test_upload_with_auth.py` - Full upload flow test

---

## Development Environment Testing Requirements

### **CRITICAL**: All fixes must be tested locally before deployment

1. **Local Testing Steps**:
   ```bash
   # 1. Start local development environment
   cd /Users/aq_home/1Projects/accessa/insurance_navigator
   source .venv/bin/activate
   supabase start
   python main.py
   
   # 2. Run storage authentication test
   python test_staging_storage_error.py
   
   # 3. Run full upload flow test
   python test_upload_with_auth.py
   ```

2. **Validation Requirements**:
   - ✅ Local storage authentication works
   - ✅ Signed URL generation succeeds
   - ✅ File upload simulation works
   - ✅ No errors in local logs
   - ✅ All test scripts pass

3. **Deployment Process**:
   - ✅ Local testing completed successfully
   - ✅ Code changes committed to feature branch
   - ✅ Pull request created for staging branch
   - ✅ Staging deployment triggered
   - ✅ Staging validation completed

---

**Investigation Priority**: HIGH  
**Estimated Time**: 2-4 hours  
**Assigned To**: [To be assigned]  
**Due Date**: [To be set]  
**Testing Requirement**: MANDATORY local testing before staging deployment
