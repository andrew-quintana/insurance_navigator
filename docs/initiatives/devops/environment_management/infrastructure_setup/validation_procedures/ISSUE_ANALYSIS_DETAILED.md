# Issue Analysis: File Upload & Staging Endpoints

**Date**: September 21, 2025  
**Purpose**: Detailed analysis of identified issues from end-to-end testing  
**Status**: ✅ ANALYSIS COMPLETE

## Issue 1: File Upload Authentication Problems

### Problem Description
The file upload endpoints are failing with the error:
```
"Metadata upload failed: 'Depends' object has no attribute 'user_id'"
```

### Root Cause Analysis

#### Code Flow Issue
1. **Main.py upload-metadata endpoint** (line 766-784):
   ```python
   @app.post("/upload-metadata")
   async def upload_metadata(
       request: UploadRequest,
       current_user: Dict[str, Any] = Depends(get_current_user)  # Returns Dict
   ):
   ```

2. **Upload pipeline upload_document function** (line 32-34):
   ```python
   @router.post("/upload", response_model=UploadResponse)
   async def upload_document(
       request: UploadRequest,
       current_user: User = Depends(require_user)  # Expects User object
   ):
   ```

3. **The Problem**: 
   - `main.py` uses `get_current_user()` which returns `Dict[str, Any]`
   - `upload_pipeline/endpoints/upload.py` expects `User` object from `require_user`
   - When `upload_metadata` calls `upload_document(request)`, it passes a `Depends` object instead of the actual user data

#### Authentication Dependency Mismatch
- **Main.py**: Uses `auth_adapter.validate_token()` → Returns `Dict`
- **Upload Pipeline**: Uses `require_user` → Returns `User` object
- **Result**: Type mismatch causing the `'Depends' object has no attribute 'user_id'` error

### Impact
- ❌ **File Upload**: Completely broken
- ❌ **Document Processing**: Cannot process user uploads
- ❌ **User Experience**: Upload functionality unavailable

### Solution Required
1. **Option A**: Modify `upload_metadata` to extract user data and pass it correctly
2. **Option B**: Standardize authentication across all endpoints
3. **Option C**: Fix the dependency injection in the upload pipeline

---

## Issue 2: Staging Endpoint Availability

### Problem Description
Staging environment has limited endpoint availability - many endpoints return 404 errors.

### Root Cause Analysis

#### Staging vs Production Configuration
1. **FastAPI Configuration** (main.py lines 80-86):
   ```python
   app = FastAPI(
       title="Insurance Navigator API",
       description="Backend-orchestrated document processing with LlamaParse",
       version="3.0.0",
       docs_url="/docs",        # Should be available
       redoc_url="/redoc"       # Should be available
   )
   ```

2. **Router Inclusion** (main.py lines 88-94):
   ```python
   # Include webhook router
   from api.upload_pipeline.webhooks import router as webhook_router
   app.include_router(webhook_router, prefix="/api/upload-pipeline")
   
   # Include upload router
   from api.upload_pipeline.endpoints.upload import router as upload_router
   app.include_router(upload_router, prefix="/api/upload-pipeline")
   ```

3. **The Problem**: 
   - Staging service is running but many endpoints are not accessible
   - This suggests either:
     - Different code version deployed to staging
     - Environment-specific configuration disabling endpoints
     - Missing dependencies or initialization issues

#### Testing Results
| Endpoint | Staging | Production | Expected |
|----------|---------|------------|----------|
| `/` | ✅ 200 | ✅ 200 | ✅ Working |
| `/health` | ✅ 200 | ✅ 200 | ✅ Working |
| `/docs` | ❌ 404 | ✅ 200 | ❌ Missing |
| `/redoc` | ❌ 404 | ✅ 200 | ❌ Missing |
| `/openapi.json` | ❌ 404 | ✅ 200 | ❌ Missing |
| `/login` | ❌ 404 | ✅ 200 | ❌ Missing |
| `/register` | ❌ 404 | ✅ 200 | ❌ Missing |
| `/api/upload-pipeline/upload` | ❌ 404 | ❌ 404 | ❌ Missing |

### Impact
- ❌ **API Documentation**: Cannot access docs in staging
- ❌ **Authentication**: Login/register not available in staging
- ❌ **Upload Pipeline**: Upload endpoints not accessible
- ❌ **Testing**: Limited testing capabilities in staging

### Possible Causes
1. **Code Version Mismatch**: Staging running older code version
2. **Environment Configuration**: Staging-specific settings disabling endpoints
3. **Dependency Issues**: Missing dependencies in staging environment
4. **Router Registration**: Upload pipeline routers not properly registered

---

## Issue 3: Upload Pipeline Endpoints Missing

### Problem Description
Even in production, the upload pipeline endpoints are not accessible:
- `/api/upload-pipeline/upload` returns 404
- This suggests the router is not properly registered

### Root Cause Analysis

#### Router Registration Issue
1. **Router Import** (main.py lines 92-94):
   ```python
   from api.upload_pipeline.endpoints.upload import router as upload_router
   app.include_router(upload_router, prefix="/api/upload-pipeline")
   ```

2. **Expected Endpoint**: `/api/upload-pipeline/upload`
3. **Actual Result**: 404 Not Found

#### Possible Causes
1. **Import Error**: `api.upload_pipeline.endpoints.upload` module not found
2. **Router Definition**: Router not properly defined
3. **Path Conflict**: Route path conflicts with other routes
4. **Environment Issue**: Module not available in deployed environment

---

## Detailed Recommendations

### For File Upload Issue (CRITICAL)
1. **Immediate Fix**: Modify `upload_metadata` endpoint to properly handle user data
2. **Long-term Fix**: Standardize authentication across all endpoints
3. **Testing**: Add unit tests for upload functionality

### For Staging Endpoints (HIGH)
1. **Investigate**: Check staging deployment configuration
2. **Compare**: Compare staging vs production code versions
3. **Fix**: Ensure all endpoints are available in staging
4. **Document**: Document staging-specific configurations

### For Upload Pipeline (HIGH)
1. **Debug**: Check if upload pipeline module is properly imported
2. **Test**: Verify router registration in development
3. **Deploy**: Ensure upload pipeline is included in deployment
4. **Monitor**: Add logging to track router registration

---

## Next Steps

### Immediate Actions (Today)
1. Fix the file upload authentication issue
2. Investigate staging endpoint availability
3. Check upload pipeline router registration

### Short-term Actions (This Week)
1. Standardize authentication across all endpoints
2. Ensure staging environment has full endpoint access
3. Add comprehensive testing for upload functionality

### Long-term Actions (Next Sprint)
1. Implement proper error handling for upload endpoints
2. Add monitoring for endpoint availability
3. Create staging environment parity with production

---

**Document Status**: ✅ ANALYSIS COMPLETE  
**Last Updated**: September 21, 2025  
**Priority**: HIGH - Critical functionality affected
