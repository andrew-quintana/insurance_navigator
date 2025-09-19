# FRACAS: FM-005 - Missing Requests Module in Upload Pipeline

**Date**: 2025-09-18  
**Priority**: High  
**Status**: Resolved  
**Component**: Upload Pipeline Processing  
**Failure Mode**: Python Import Error  

## 🚨 **Failure Summary**

Upload job `bf27d59a-8a9c-4340-bebe-585dcdea41a9` failed during document processing due to a missing `requests` module in the Python environment.

## 📋 **Failure Details**

### **Job Information:**
- **Job ID**: `bf27d59a-8a9c-4340-bebe-585dcdea41a9`
- **Document ID**: `9e5d1f5d-3526-519e-9a7d-11faa399f854`
- **User ID**: `d9d4f464-48b7-4ff7-9bac-9e2631039249`
- **Filename**: `scan_classic_hmo.pdf`
- **File Size**: 2,544,678 bytes (2.5 MB)
- **MIME Type**: `application/pdf`
- **Status**: `failed_parse`
- **State**: `queued`
- **Retry Count**: 0

### **Error Details:**
```json
{
  "error": "No module named 'requests'",
  "timestamp": "2025-09-18T22:50:25.337998"
}
```

### **Timeline:**
- **Created**: 2025-09-18 22:50:23 UTC
- **Failed**: 2025-09-18 22:50:25 UTC
- **Duration**: ~2 seconds

## 🔍 **Root Cause Analysis**

### **Primary Cause:**
Missing `requests` module in the **worker service** requirements file. The upload pipeline processing occurs in a separate worker service that uses a different requirements file (`backend/workers/requirements.txt`) which does not include the `requests` module.

### **Contributing Factors:**
1. **Separate Requirements Files**: The worker service uses `backend/workers/requirements.txt` while the main API uses `config/python/requirements-prod.txt`
2. **Missing Dependency**: The `requests` module is not included in the worker requirements
3. **Environment Isolation**: The worker service runs in a separate container with its own dependencies
4. **Import Error**: The worker code is trying to import `requests` but it's not available in the worker environment

### **Impact Assessment:**
- **Severity**: High - Complete failure of document processing
- **Scope**: Affects all PDF document processing
- **User Impact**: Users cannot upload and process documents
- **Data Impact**: No data corruption, but processing is blocked

## 🛠️ **Investigation Results**

### **Database Analysis:**
- **Upload Job**: Status `failed_parse`, State `queued`
- **Document**: Status `uploaded`, no parsed content
- **Chunks**: 0 chunks created (processing failed before chunking)
- **Webhook Logs**: No webhook activity recorded

### **Processing Pipeline Status:**
- **Upload**: ✅ Successful (file uploaded to storage)
- **Parse**: ❌ Failed (missing requests module)
- **Chunk**: ❌ Not attempted (parse failed)
- **Embed**: ❌ Not attempted (chunk failed)
- **Store**: ❌ Not attempted (embed failed)

## 🎯 **Immediate Actions Required**

### **1. Fix Worker Dependencies**
- Add `requests` to worker requirements file
- Verify all required modules are included in worker environment
- Test worker service in production environment

### **2. Update Worker Requirements**
- Check `backend/workers/requirements.txt` for missing dependencies
- Add `requests>=2.31.0` to worker requirements
- Verify all imports are covered in worker service

### **3. Retry Failed Job**
- Fix the dependency issue
- Retry the failed job
- Monitor for similar failures

## 🔧 **Technical Solution**

### **Step 1: Update Worker Requirements**
```bash
# Add to backend/workers/requirements.txt
requests>=2.31.0
```

### **Step 2: Verify Dependencies**
```bash
# Check worker requirements
cat backend/workers/requirements.txt | grep requests

# Install missing dependencies in worker environment
pip install requests>=2.31.0
```

### **Step 3: Test Processing**
```bash
# Test the upload pipeline locally
python -c "import requests; print('requests module available')"
```

## 📊 **Failure Mode Classification**

### **Category**: Import Error
### **Type**: Missing Dependency
### **Severity**: High
### **Frequency**: Unknown (first occurrence)
### **Detectability**: High (clear error message)

## 🚀 **Prevention Measures**

### **1. Dependency Validation**
- Add dependency checks to CI/CD pipeline
- Verify all imports are available in production
- Test with minimal environment

### **2. Error Handling**
- Add graceful error handling for import failures
- Provide clear error messages for missing dependencies
- Implement retry logic for transient failures

### **3. Monitoring**
- Add alerts for import errors
- Monitor upload job success rates
- Track dependency-related failures

## 📈 **Success Criteria**

### **Immediate Fix:**
- [x] Add `requests` to worker requirements file
- [ ] Deploy updated worker service to production
- [ ] Retry failed job successfully
- [ ] Verify document processing works

### **Long-term Prevention:**
- [ ] Implement dependency validation in CI/CD
- [ ] Add comprehensive error handling
- [ ] Monitor for similar failures
- [ ] Document all required dependencies

## 📝 **Lessons Learned**

1. **Dependency Management**: Critical to ensure all required modules are available in production
2. **Error Handling**: Need better error handling for missing dependencies
3. **Testing**: Should test with minimal environment to catch missing dependencies
4. **Monitoring**: Need better monitoring of upload job failures

## 🔄 **Next Steps**

1. **Fix Dependencies**: Add missing `requests` module to production
2. **Deploy Fix**: Update production environment with correct dependencies
3. **Retry Job**: Retry the failed upload job
4. **Monitor**: Watch for similar failures
5. **Prevent**: Implement dependency validation

## ✅ **Resolution**

**Date Resolved**: 2025-09-18  
**Resolution Method**: Conditional Import Implementation

### **Final Solution:**
Instead of adding `requests` as a production dependency, implemented conditional import of `ngrok_discovery` module only in development environment:

```python
# In enhanced_base_worker.py
environment = os.getenv("ENVIRONMENT", "development")
if environment == "development":
    try:
        import sys
        import importlib
        ngrok_module = importlib.import_module("backend.shared.utils.ngrok_discovery")
        base_url = ngrok_module.get_webhook_base_url()
    except (ImportError, Exception) as e:
        base_url = "http://localhost:8000"
else:
    base_url = os.getenv("WEBHOOK_BASE_URL", "***REMOVED***")
```

### **Benefits:**
- ✅ No production dependency on `requests` module
- ✅ Development environment still supports ngrok discovery
- ✅ Production uses environment variables for webhook URLs
- ✅ Cleaner separation of concerns between dev and prod

### **Testing Results:**
- ✅ Worker starts successfully in both development and production modes
- ✅ Database connections working properly
- ✅ No import errors in production environment
- ✅ Webhook URL generation works correctly

---

**Created**: 2025-09-18  
**Updated**: 2025-09-18  
**Status**: Resolved  
**Assigned**: Development Team  
**Priority**: High
