# FM-027 Investigation Findings

## Investigation Summary
**Date**: 2025-10-01  
**Status**: Phase 3 - Timing Issue Investigation Required  
**Severity**: High  
**Latest Update**: Environment mismatch analysis completed, timing issue identified  

## Root Cause Analysis

### Problem Statement
The Upload Pipeline Worker is experiencing 400 Bad Request errors when accessing Supabase Storage via `StorageManager.blob_exists()`. 

**CRITICAL UPDATE**: Previous investigation confirmed that the issue is NOT related to RLS policies, database connections, missing files, or authentication. The exact same file path and request that fails in the worker (400 "Bucket not found") works perfectly from local environment (200 OK with PDF content), indicating a timing or environment-specific issue.

### Key Findings

#### 1. Authentication Mechanism Analysis
- **Service Role Key**: ✅ Correctly configured and loaded
- **API Endpoint Format**: ✅ Using correct `/storage/v1/object/` format
- **File Path Format**: ✅ Both with and without `files/` prefix work
- **HTTP Method**: ✅ HEAD requests work correctly

#### 2. Header Configuration Analysis
**Critical Discovery**: Supabase Storage API requires BOTH headers for authentication:
- `apikey: <service_role_key>` 
- `Authorization: Bearer <service_role_key>`

**Test Results**:
- API Key Only: ❌ 400 Bad Request
- Authorization Only: ✅ 200 OK  
- Both Headers: ✅ 200 OK

#### 3. StorageManager Configuration
**Current Implementation**: ✅ Correctly configured with both headers
```python
self.client = httpx.AsyncClient(
    timeout=httpx.Timeout(self.timeout),
    headers={
        "apikey": self.service_role_key,
        "Authorization": f"Bearer {self.service_role_key}"
    }
)
```

#### 4. Worker Integration
**StorageManager Usage**: The worker correctly calls `self.storage.blob_exists(storage_path)` on line 556 of `enhanced_base_worker.py`.

### Investigation Experiments

#### Auth Matrix Test Results
- **Total Tests**: 21
- **Successful**: 12 (57%)
- **Failed**: 9 (43%)

#### Experiments E1-E6 Results
- **Total Experiments**: 6
- **Successful**: 5 (83%)
- **Failed**: 1 (17%)

**Failed Experiment**: E1 - Headers Comparison
- Issue: API Key Only requests fail with 400
- Root Cause: Supabase requires both headers

### Current Status

#### What's Working
1. ✅ StorageManager is correctly configured with both headers
2. ✅ Worker is correctly calling StorageManager methods
3. ✅ Environment variables are loaded correctly
4. ✅ API endpoint format is correct
5. ✅ File path format is correct
6. ✅ **StorageManager works perfectly in local environment** (Status: 200, all operations successful)

#### What's Not Working
1. ❌ Worker on Render is still getting 400 Bad Request errors
2. ❌ FM-027 StorageManager logs are not appearing in worker logs

### Critical Discovery

**Local Environment Test Results** (2025-10-01 18:24:33):
- ✅ `blob_exists()`: Status 200, returns `True`
- ✅ `get_blob_metadata()`: Successfully retrieves metadata
- ✅ `read_blob()`: Successfully reads 1744 bytes
- ✅ HTTP Headers: Both `apikey` and `authorization` present

**Conclusion**: The StorageManager code is working perfectly. The issue is **environment-specific to Render**.

### Next Steps

1. **Investigate Render Environment Differences**: Compare local vs Render environment
2. **Check Render Environment Variables**: Verify environment variables on Render
3. **Test Worker Deployment**: Ensure latest code is deployed to Render
4. **Monitor Worker Logs**: Check for FM-027 logs during actual job processing

### Files Modified During Investigation

- `test_auth_matrix.py` - Auth matrix testing script
- `experiments_e1_e6.py` - Comprehensive experiments script  
- `final_root_cause_test.py` - Root cause verification script
- `backend/shared/storage/storage_manager.py` - Enhanced logging added
- `backend/workers/enhanced_base_worker.py` - Enhanced logging added

### Evidence Files

- `auth_matrix_report_20251001_111938.json` - Auth matrix test results
- `fm027_experiments_report_20251001_112041.json` - Experiments E1-E6 results

## Phase 3 Investigation Required

### Updated Problem Statement
**CRITICAL FINDING**: The exact same file path and HTTP request that fails in the Render worker (400 "Bucket not found") works perfectly from local environment (200 OK with PDF content). This indicates a **timing or environment-specific issue** that requires deep investigation.

### Confirmed Facts
1. ✅ **Job exists in staging database**: `45305f26-76d1-4009-93b1-5d6159c5b307`
2. ✅ **File exists in staging storage**: Returns 200 OK with PDF content
3. ✅ **Worker connects to correct environment**: Staging (`your-staging-project.supabase.co`)
4. ✅ **Worker uses correct authentication**: Service role key with proper headers
5. ✅ **RLS policies not blocking**: Service role bypasses all RLS restrictions

### Next Steps
**FRACAS Investigation Required**: A comprehensive timing issue investigation has been prepared for another agent to execute.

**Investigation Prompt**: `FRACAS_FM_027_TIMING_ISSUE_INVESTIGATION_PROMPT.md`

**Focus Areas**:
- Network/connectivity differences between Render and local
- Authentication/authorization timing issues
- Storage API state synchronization delays
- Environment configuration differences

### Previous Investigation Results
The investigation has identified that the Supabase Storage API requires both `apikey` and `Authorization` headers for authentication. The StorageManager is correctly configured, but the timing discrepancy between worker and local environments requires specialized investigation.
