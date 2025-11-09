# FRACAS FM-012 Investigation Prompt: Staging Worker Storage Access Failure

## 🎯 **INVESTIGATION MISSION**

**Objective**: Investigate and resolve the staging worker storage access failure causing 400 Bad Request errors when accessing files from Supabase Storage.

**Reference Document**: `docs/incidents/failure_modes/storage_access/FRACAS_FM_012_STAGING_WORKER_STORAGE_ACCESS_FAILURE.md`

## 🚨 **CURRENT SITUATION**

### **Critical Issue**
- **Status**: P0 - Critical
- **Impact**: Document processing pipeline completely blocked
- **Error**: `HTTP/1.1 400 Bad Request` when accessing storage URLs
- **Environment**: Staging (your-staging-project.supabase.co)
- **Root Cause**: Missing RLS policies and incorrect API headers

### **Evidence Summary**
```
Error: HTTP/1.1 400 Bad Request
Failed URL: https://your-staging-project.supabase.co/storage/v1/object/files/user/468add2d-e124-4771-8895-958ad38430fb/raw/0bb233ff_f076c0c1.pdf
Error Code: STORAGE_ACCESS_ERROR
Support UUID: 715b82a0-f4d1-49b6-930b-28de13e464bc
```

## 🔍 **INVESTIGATION TASKS**

### **Task 1: Storage Policy Verification (P0 - Critical)**
**Time Estimate**: 15 minutes

**Objective**: Verify if storage policies exist and are correctly configured.

**Investigation Steps**:
1. Check if storage policy exists in Supabase database
2. Verify policy configuration for service role access
3. Test storage access with service role key
4. Compare with working production environment

**Expected Output**:
- Storage policy status confirmation
- Policy configuration analysis
- Service role access verification

### **Task 2: Environment Variable Validation (P0 - Critical)**
**Time Estimate**: 10 minutes

**Objective**: Verify environment variables are correctly configured.

**Investigation Steps**:
1. Check `SUPABASE_SERVICE_ROLE_KEY` in `.env.staging`
2. Verify service role key format and permissions
3. Compare with production environment variables
4. Test environment variable loading

**Expected Output**:
- Environment variable configuration analysis
- Service role key validation
- Configuration comparison results

### **Task 3: Storage Access Testing (P0 - Critical)**
**Time Estimate**: 20 minutes

**Objective**: Test storage access directly to identify the root cause.

**Investigation Steps**:
1. Test storage access with direct API calls
2. Verify file existence in storage bucket
3. Test different authentication methods
4. Check storage URL format and endpoint

**Expected Output**:
- Direct storage access test results
- File existence verification
- Authentication method analysis

### **Task 4: Code Analysis (P1 - High)**
**Time Estimate**: 15 minutes

**Objective**: Analyze storage access implementation in worker code.

**Investigation Steps**:
1. Review `backend/workers/enhanced_base_worker.py` storage access code
2. Check `backend/shared/storage/storage_manager.py` implementation
3. Verify authentication headers being sent
4. Compare with working production code

**Expected Output**:
- Code implementation analysis
- Authentication header verification
- Implementation comparison

### **Task 5: Fix Implementation (P1 - High)**
**Time Estimate**: 30 minutes

**Objective**: Implement the necessary fixes for storage access.

**Implementation Requirements**:
1. Apply missing storage policies via Supabase SQL Editor
2. Fix environment variable configuration if needed
3. Update code to include proper authentication headers
4. Test the complete fix

**Success Criteria**:
- Storage access returns 200 OK
- Worker can download files from storage
- Document processing pipeline functional
- No more 400 Bad Request errors

## 🧪 **TEST COMMANDS**

```bash
# Test 1: Check storage policy
# Run in Supabase SQL Editor
SELECT policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'objects' 
AND schemaname = 'storage'
AND policyname = 'Allow service role to download files';

# Test 2: Test storage access directly
python -c "
import httpx
import asyncio
import os

async def test_storage_access():
    url = 'https://your-staging-project.supabase.co/storage/v1/object/files/user/468add2d-e124-4771-8895-958ad38430fb/raw/0bb233ff_f076c0c1.pdf'
    headers = {
        'Authorization': f'Bearer {os.getenv(\"SUPABASE_SERVICE_ROLE_KEY\")}',
        'apikey': os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text}')

asyncio.run(test_storage_access())
"

# Test 3: Check environment variables
echo "SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY:0:20}..."
echo "SUPABASE_URL: $SUPABASE_URL"

# Test 4: Run comprehensive test suite
python docs/incidents/failure_modes/storage_access/FRACAS_FM_012_investigation_files/staging_manual_test_suite.py
```

## 📋 **EXPECTED OUTPUT**

### **Immediate Fix (P0)**
1. **Storage Policy**: Apply missing RLS policy for service role file downloads
2. **Environment Variables**: Fix service role key configuration
3. **Storage Access**: Verify 200 OK responses for storage operations

### **Short-term Improvements (P1)**
1. **Code Updates**: Add missing `apikey` headers to storage requests
2. **Error Handling**: Improve error messages for storage failures
3. **Testing**: Comprehensive test suite for storage operations

### **Success Metrics**
- ✅ Storage access works for existing files
- ✅ Worker can download files from storage
- ✅ Document processing pipeline functional
- ✅ No 400 Bad Request errors in storage access

## 📄 **DELIVERABLES**

1. **FRACAS Update**: Update `docs/incidents/failure_modes/storage_access/FRACAS_FM_012_STAGING_WORKER_STORAGE_ACCESS_FAILURE.md` with findings
2. **Storage Policy**: Apply missing RLS policies via Supabase SQL Editor
3. **Code Fixes**: Update storage access code with proper headers
4. **Testing Results**: Verify complete resolution
5. **Documentation**: Document storage access requirements

## ⚠️ **CRITICAL NOTES**

- **This is blocking the entire document processing pipeline**
- **The worker is running but cannot process documents**
- **This affects staging environment functionality**
- **Immediate resolution is required**

## 🚨 **ESCALATION CRITERIA**

- If storage policies cannot be applied due to permissions
- If service role key is incorrect or expired
- If storage bucket configuration is incorrect
- If code changes break other functionality

## ⏱️ **ESTIMATED DURATION**
- **Total Time**: 90 minutes
- **Investigation**: 60 minutes
- **Fix Implementation**: 30 minutes

---

**Reference**: See `docs/incidents/failure_modes/storage_access/FRACAS_FM_012_STAGING_WORKER_STORAGE_ACCESS_FAILURE.md` for complete failure details
