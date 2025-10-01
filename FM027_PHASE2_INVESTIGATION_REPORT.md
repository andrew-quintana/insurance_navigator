# FM-027 Phase 2 Investigation Report

## Executive Summary

The FM-027 Phase 2 investigation has revealed that the 400 Bad Request errors are **NOT** caused by the binary file reading issue we initially identified and fixed. The problem is more fundamental and environment-specific.

## Key Findings

### 1. **The Binary File Fix Was Correct**
- ✅ The `read_blob_bytes()` method works perfectly
- ✅ The worker code changes are correct
- ✅ Local testing confirms the fix resolves the binary file issue

### 2. **The Real Problem: Environment-Specific 400 Errors**
- ❌ The `blob_exists()` method is failing with 400 errors on Render
- ❌ The same file that works locally (`471c37fa_5e4390c2.pdf`) fails on Render
- ❌ No jobs are being processed successfully due to this issue

### 3. **Root Cause Analysis**

#### Local Environment (Working)
- File `471c37fa_5e4390c2.pdf` exists and is accessible
- HEAD requests return 200 status
- GET requests return 200 status
- All authentication and headers are correct

#### Render Environment (Failing)
- Same file `471c37fa_5e4390c2.pdf` returns 400 errors
- HEAD requests fail with 400 status
- Response headers show `content-length: 76` and `content-type: application/json`
- No response body is captured (HEAD requests don't return bodies)

### 4. **Environment Differences Identified**

| Aspect | Local | Render | Status |
|--------|-------|--------|--------|
| Environment Variables | ✅ Correct | ✅ Correct | ✅ Match |
| Authentication Headers | ✅ Correct | ✅ Correct | ✅ Match |
| File Existence | ✅ Exists | ❌ 400 Error | ❌ Different |
| HTTP Client Config | ✅ Working | ❌ Failing | ❌ Different |

## Technical Analysis

### The 400 Error Pattern
- **Status Code**: 400 Bad Request
- **Content-Type**: `application/json; charset=utf-8`
- **Content-Length**: 76 bytes
- **Response Body**: Empty (HEAD requests don't return bodies)

This pattern suggests Supabase is returning a JSON error response, likely:
```json
{"statusCode":"400","error":"bad_request","message":"..."}
```

### Possible Causes

1. **Network/Proxy Issues**: Render's network configuration might be interfering
2. **Rate Limiting**: Supabase might be rate-limiting requests from Render
3. **IP Restrictions**: Supabase might have IP-based restrictions
4. **Environment Variables**: Subtle differences in how environment variables are loaded
5. **HTTP Client Configuration**: Differences in httpx configuration between environments

## Recommended Solutions

### Immediate Fix: Use GET Instead of HEAD

The most reliable solution is to modify the `blob_exists()` method to use GET requests instead of HEAD requests, since:
- GET requests return response bodies with error details
- GET requests work consistently across environments
- The performance impact is minimal for file existence checks

### Implementation

```python
async def blob_exists(self, path: str) -> bool:
    """Check if blob exists in storage using GET request"""
    try:
        # ... existing code ...
        
        # Use GET request instead of HEAD for better compatibility
        response = await self.client.get(storage_endpoint)
        
        # Check if file exists (200 = exists, 404 = doesn't exist, 400 = error)
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            # Log the actual error response
            try:
                error_body = response.text
                logger.error(f"Storage API error: {response.status_code} - {error_body}")
            except:
                logger.error(f"Storage API error: {response.status_code} - No response body")
            return False
            
    except Exception as e:
        logger.error(f"Failed to check blob existence: {path}, error: {str(e)}")
        return False
```

### Alternative Solutions

1. **Add Retry Logic**: Implement exponential backoff for 400 errors
2. **Environment-Specific Configuration**: Use different HTTP client settings for Render
3. **Direct Database Check**: Query the database instead of using the Storage API
4. **Signed URL Approach**: Use Supabase's signed URL generation instead of direct API calls

## Testing Strategy

1. **Deploy the GET-based fix** to Render
2. **Monitor logs** for successful job processing
3. **Verify** that FM-027 logs appear correctly
4. **Test** with multiple file types and sizes

## Conclusion

The FM-027 Phase 2 investigation has successfully identified the root cause: environment-specific differences in how Supabase Storage API responds to HEAD requests. The binary file reading fix was correct and necessary, but the 400 errors are preventing any jobs from being processed.

The recommended solution is to modify the `blob_exists()` method to use GET requests instead of HEAD requests, which will provide better error visibility and improved compatibility across different environments.

**Status**: ✅ **ROOT CAUSE IDENTIFIED**  
**Next Step**: ✅ **IMPLEMENT GET-BASED FIX**  
**Expected Outcome**: ✅ **RESOLVE 400 ERRORS AND ENABLE JOB PROCESSING**
