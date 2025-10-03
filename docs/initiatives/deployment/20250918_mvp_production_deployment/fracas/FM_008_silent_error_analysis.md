# FRACAS: FM-008 - Silent Error Analysis in Production

**Date**: 2025-09-18  
**Priority**: High  
**Status**: Active  
**Component**: Production Upload Pipeline  
**Failure Mode**: Silent Error in Job Processing  

## 🚨 **Failure Summary**

Production analysis reveals a silent error pattern where jobs are failing during processing but the failure details are not being properly logged or surfaced. Only 1 job exists in the last 24 hours, and it failed with a generic user-facing error.

## 📋 **Failure Details**

### **Database Analysis Results:**

**Job Status Summary (Last 24 Hours):**
- **Total Jobs**: 1
- **Failed Jobs**: 1 (100% failure rate)
- **Successful Jobs**: 0
- **Jobs with Errors**: 1

**Failed Job Details:**
- **Job ID**: `3ee03299-596e-427e-9a1d-d4bca7c63c1b`
- **Document ID**: `5c7d10ae-6d3e-5d2d-a77f-83129c9bd011`
- **Filename**: `scan_classic_hmo.pdf`
- **Status**: `failed_parse`
- **State**: `queued` (inconsistent - should be `done` if failed)
- **Retry Count**: 0
- **Processing Status**: `failed`

**Error Details:**
```json
{
  "error": "Non-retryable error: user_facing_error: Document processing failed due to an invalid request. Please check your document and try again. (Reference: 489741f9-a780-48cd-8598-e6169dc3c2fc)",
  "timestamp": "2025-09-19T01:34:35.031567"
}
```

### **Silent Error Indicators:**

1. **Low Job Volume**: Only 1 job in 24 hours suggests either:
   - Very low usage (unlikely for production)
   - Jobs are failing before being recorded
   - Worker is not processing jobs from queue

2. **Inconsistent State**: Job shows `status: failed_parse` but `state: queued`
   - Indicates worker processed the job but didn't update state properly
   - Suggests error occurred during state transition

3. **Generic Error Message**: Error message is too generic
   - "Document processing failed due to an invalid request"
   - No specific details about what went wrong
   - Reference ID suggests error handling is working but not informative

4. **No Retry Attempts**: `retry_count: 0` suggests:
   - Error was classified as non-retryable immediately
   - No retry logic was triggered
   - Possible issue with error classification

## 🔍 **Root Cause Analysis**

### **✅ CORRECTED: Worker IS Running and Processing Jobs**

**Updated Evidence from Production Logs:**
- ✅ **Worker IS Running**: Production logs show worker processing jobs
- ✅ **Events ARE Being Logged**: Detailed error logs captured
- ✅ **LlamaParse API Calls Made**: Worker successfully called LlamaParse API
- ✅ **Error Handling Working**: Comprehensive error logging implemented

### **🎯 ACTUAL Root Cause: Webhook URL Security Validation**

**LlamaParse API Error:**
```
LlamaParse API error: 400 - {"detail":"Failed to validate URLs: webhook_url contains a non-public URL which could pose a security risk"}
```

**Problematic Webhook URL:**
```
webhook_url: "http://localhost:8000/api/upload-pipeline/webhook/llamaparse/3ee03299-596e-427e-9a1d-d4bca7c63c1b"
```

### **Confirmed Root Causes:**

1. **Missing Environment Variable**: ✅ **CONFIRMED**
   - `WEBHOOK_BASE_URL` not set in Render configuration
   - Worker falling back to `localhost:8000` instead of production URL
   - LlamaParse correctly rejecting non-public URLs

2. **Environment Detection Issue**: ✅ **CONFIRMED**
   - Worker using development fallback URL in production
   - Environment variable not properly configured
   - Security validation preventing API calls

3. **Configuration Gap**: ✅ **CONFIRMED**
   - Render.yaml missing `WEBHOOK_BASE_URL` environment variable
   - Worker defaulting to localhost instead of production URL
   - API security preventing localhost webhook URLs

### **Secondary Issues:**

4. **Error Classification**: ✅ **WORKING CORRECTLY**
   - 400 errors correctly classified as non-retryable
   - User-facing error messages appropriate
   - Error handling and logging working as designed

5. **Worker Processing**: ✅ **WORKING CORRECTLY**
   - Worker successfully processing jobs
   - Database connections working
   - File processing and API calls functional

6. **Logging and Monitoring**: ✅ **WORKING CORRECTLY**
   - Comprehensive error logging implemented
   - Detailed API response capture
   - Error context properly recorded

## 🔧 **Critical Action Plan**

### **Immediate Actions (CRITICAL):**
1. **🚨 Fix Webhook URL Configuration** ✅ **COMPLETED**
   - **URGENT**: Add `WEBHOOK_BASE_URL` environment variable to Render configuration
   - Set value to `https://insurance-navigator-api.onrender.com`
   - **Action**: Updated `config/render/render.yaml` with missing environment variable

2. **🚨 Deploy Configuration Fix**
   - Deploy updated Render configuration
   - Verify environment variable is set in production
   - Test webhook URL generation
   - **Action**: Deploy to production and verify

3. **🚨 Test End-to-End Flow**
   - Create new test job via API
   - Monitor worker processing with correct webhook URL
   - Verify LlamaParse API acceptance
   - **Action**: Test complete upload pipeline

4. **🚨 Clean Up Failed Job**
   - Delete the failed job from database
   - Reset document processing status
   - Prepare for fresh testing
   - **Action**: Clean database state

### **Secondary Actions:**
5. **Test End-to-End Flow**
   - Create new test job via API
   - Monitor worker processing
   - Verify event logging
   - Check webhook processing

6. **Implement Monitoring**
   - Add worker health checks
   - Monitor job queue status
   - Set up alerts for failed jobs
   - Track processing metrics

### **Database Queries to Run:**
```sql
-- Check for jobs in different states
SELECT status, state, COUNT(*) 
FROM upload_pipeline.upload_jobs 
GROUP BY status, state;

-- Check recent job activity
SELECT 
    job_id,
    status,
    state,
    created_at,
    updated_at,
    retry_count,
    last_error
FROM upload_pipeline.upload_jobs 
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Check document processing status
SELECT 
    processing_status,
    COUNT(*) as count
FROM upload_pipeline.documents 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY processing_status;
```

## 📊 **Impact Assessment**

- **User Impact**: 100% failure rate for document processing
- **System Impact**: Upload pipeline completely non-functional
- **Business Impact**: Users cannot process any documents
- **Priority**: CRITICAL - Complete system failure

## 🎯 **Next Steps**

1. **Immediate**: Check production worker status and logs
2. **Investigate**: Analyze the specific failed job in detail
3. **Test**: Verify LlamaParse API connectivity and authentication
4. **Fix**: Address root cause of silent failures
5. **Monitor**: Implement better error visibility and alerting

## 📈 **Success Criteria**

- [ ] Production worker is running and processing jobs
- [ ] Error messages provide specific failure details
- [ ] Retry logic is working correctly
- [ ] Job states are consistent and accurate
- [ ] Webhook processing is functional
- [ ] Document processing success rate > 90%

## ✅ **Resolution**

**Date Resolved**: 2025-09-18  
**Resolution Method**: Environment Variable Configuration Fix

### **Root Cause Identified:**
The production worker was using `localhost:8000` as the webhook URL because the `WEBHOOK_BASE_URL` environment variable was missing from the Render configuration. LlamaParse correctly rejected this non-public URL for security reasons.

### **Fix Applied:**
```yaml
# Added to config/render/render.yaml
- key: WEBHOOK_BASE_URL
  value: https://insurance-navigator-api.onrender.com
```

### **Expected Results:**
- ✅ Worker will use correct production webhook URL
- ✅ LlamaParse API will accept webhook URLs
- ✅ Document processing will complete successfully
- ✅ Upload pipeline will be fully functional

### **Next Steps:**
1. Deploy updated configuration to production
2. Test end-to-end upload flow
3. Verify webhook processing works correctly
4. Monitor for successful job completions

### **⚠️ Ongoing Issue (2025-09-19 02:20:15):**
Despite adding the `WEBHOOK_BASE_URL` environment variable to the Render configuration, the production worker continues to use `localhost:8000` as the webhook URL. This indicates that either:
- The configuration change has not been deployed to production yet
- The environment variable is not being read correctly
- There's a caching issue with the worker

**New Job Failure:**
- Job ID: `016cea63-3771-4ef7-a9dd-e26d36e92dac`
- Same webhook URL security validation error
- Worker still using `http://localhost:8000` instead of production URL

**Debug logging added to track:**
- Environment variable values (`ENVIRONMENT`, `WEBHOOK_BASE_URL`)
- Base URL selection logic
- Final webhook URL generation

See FM-009 for detailed analysis of the persistent failure.

---

**Created**: 2025-09-18  
**Updated**: 2025-09-18  
**Status**: Partially Resolved - Configuration Not Deployed  
**Assigned**: Development Team  
**Priority**: High
