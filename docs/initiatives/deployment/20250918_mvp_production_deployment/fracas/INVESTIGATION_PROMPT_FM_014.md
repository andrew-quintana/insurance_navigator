# Investigation Prompt: FM-014 Mock Service Fallback Masking Production Issues

## 📋 **Current Status**

**FM-014 Status**: IDENTIFIED ❌  
**Priority**: Critical  
**Component**: ServiceRouter Mock Fallback Configuration  

### **Issues Identified** ❌
- **Mock Service Fallback**: ServiceRouter falling back to mock services in production
- **Masked Real Issues**: Real API failures being hidden by mock fallbacks
- **Database Schema Missing**: `upload_pipeline.upload_jobs` table does not exist
- **Storage Access Failures**: 400 Bad Request errors when accessing Supabase storage
- **Configuration Mismatch**: SERVICE_MODE environment variable not being read by ServiceRouter

### **Issues Resolved** ✅
- **ServiceRouter Configuration**: Fixed to read SERVICE_MODE environment variable
- **Production Fallback**: Disabled mock service fallback in production environment
- **Configuration Logic**: Added proper environment-based fallback configuration

### **Issues Still Pending** ❌
- **Database Schema**: Missing `upload_pipeline.upload_jobs` table needs to be created
- **Storage Access**: 400 Bad Request errors need to be investigated and fixed
- **End-to-End Testing**: Verify complete pipeline works after fixes

## 🚨 **Critical Success Criteria**

- [ ] **Mock Fallback Disabled**: No mock service fallbacks in production
- [ ] **Database Schema**: `upload_pipeline.upload_jobs` table exists and accessible
- [ ] **Storage Access**: Document files can be downloaded from Supabase storage
- [ ] **Real Error Visibility**: Production errors are visible and not masked
- [ ] **End-to-End Pipeline**: Complete document processing works

## 🔍 **Root Cause Analysis**

### **Primary Issue**
The ServiceRouter was not reading the `SERVICE_MODE` environment variable and was defaulting to `hybrid` mode with fallback enabled, causing it to fall back to mock services when real services failed health checks.

### **Secondary Issues**
1. **Database Schema Missing**: The `upload_pipeline.upload_jobs` table doesn't exist in the production database
2. **Storage Access Failures**: Supabase storage returning 400 Bad Request errors
3. **Configuration Mismatch**: Worker setting `SERVICE_MODE=real` but ServiceRouter not reading it

### **Evidence**
- **Warning**: `"Fallback to mock services is enabled in production. This may mask real API failures and should be disabled."`
- **Database Error**: `"relation \"upload_pipeline.upload_jobs\" does not exist"`
- **Storage Error**: `"Client error '400 Bad Request' for url '***REMOVED***/storage/v1/object/files/...'"`
- **Configuration**: `SERVICE_MODE=real` in render.yaml but ServiceRouter not reading it

## 🔧 **Implemented Fixes**

### **1. ServiceRouter Configuration Fix**
- **Action**: Modified ServiceRouter initialization to read `SERVICE_MODE` environment variable
- **Code**: Added `"mode": os.getenv("SERVICE_MODE", "hybrid").lower()` to config
- **Status**: ✅ Fixed

### **2. Production Fallback Disable**
- **Action**: Disabled mock service fallback in production environment
- **Code**: Added `"fallback_enabled": os.getenv("ENVIRONMENT", "development") != "production"`
- **Status**: ✅ Fixed

### **3. Enhanced Logging**
- **Action**: Added logging when fallback is disabled in production
- **Code**: Added info log when fallback is disabled
- **Status**: ✅ Fixed

## 🧪 **Testing Plan**

### **Immediate Verification**
1. **Check Worker Logs**: Verify no mock service fallback warnings
2. **Check Service Mode**: Verify ServiceRouter is in "real" mode
3. **Check Database**: Verify `upload_pipeline.upload_jobs` table exists
4. **Check Storage**: Verify document files can be downloaded

### **End-to-End Testing**
1. **Upload Test Document**: Use existing test file
2. **Monitor Processing**: Check worker logs for real service usage
3. **Verify No Fallbacks**: Confirm no mock service fallbacks occur
4. **Complete Pipeline**: Ensure document processing completes successfully

## 📊 **Expected Results**

### **Worker Logs Should Show**
```
Fallback to mock services disabled in production
ServiceRouter initialized in real mode
No mock service fallback warnings
```

### **Database Should Have**
- `upload_pipeline.upload_jobs` table exists
- Worker can query jobs successfully
- No "relation does not exist" errors

### **Storage Should Work**
- Document files downloadable from Supabase storage
- No 400 Bad Request errors
- Successful file processing

## 🔄 **Next Steps**

1. **Deploy Fixes**: Deploy ServiceRouter configuration fixes
2. **Check Database Schema**: Verify `upload_pipeline.upload_jobs` table exists
3. **Investigate Storage**: Fix 400 Bad Request errors for storage access
4. **Test Pipeline**: Verify complete document processing works
5. **Update Status**: Mark FM-014 as resolved if successful

## 📁 **Files Modified**

- `backend/workers/enhanced_base_worker.py` - Fixed ServiceRouter configuration
- `backend/shared/external/service_router.py` - Enhanced production mode handling

## 🎯 **Success Metrics**

- ✅ No mock service fallback warnings in production logs
- ✅ ServiceRouter operates in "real" mode in production
- ✅ Database schema includes required tables
- ✅ Storage access works without 400 errors
- ✅ Document processing pipeline completes successfully
- ✅ Real production errors are visible and actionable

## 📝 **Notes**

This issue was critical because it was masking real production problems. The mock service fallback was preventing us from seeing the actual root causes of failures, making debugging much more difficult. By disabling fallbacks in production, we can now see and fix the real issues.

The two main remaining issues are:
1. **Database Schema**: Missing `upload_pipeline.upload_jobs` table
2. **Storage Access**: 400 Bad Request errors when accessing Supabase storage

These need to be investigated and fixed to complete the resolution.
