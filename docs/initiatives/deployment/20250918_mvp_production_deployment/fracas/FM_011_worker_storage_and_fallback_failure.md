# FRACAS: FM-011 - Worker Storage Download and Fallback File Failure

**Date**: 2025-09-18  
**Priority**: High  
**Status**: Active  
**Component**: Worker Storage and File Handling  
**Failure Mode**: Multiple Cascading Failures  

## 🚨 **Failure Summary**

The worker experienced a cascading failure involving storage download issues, fallback file handling problems, and webhook URL configuration issues, resulting in complete job processing failure.

## 📋 **Failure Details**

### **Error Sequence (2025-09-19 02:26:13):**

**Job ID**: `dc63b04f-7eac-4504-a4d1-c0de1a2cf683`  
**Document ID**: `1319d58d-0f37-5231-a4d6-1e575b5f2742`  
**Filename**: `scan_classic_hmo.pdf`  
**Status**: `uploaded` → `failed_parse`  

### **Cascading Failure Analysis:**

#### **1. Storage Download Failure (Primary Issue)**
```
Storage download failed, using local fallback: Client error '400 Bad Request' for url 'https://znvwzkdblknkkztqyfnu.supabase.co/storage/v1/object/files/user/899b78b1-3c14-400b-aa8e-91457759be1e/raw/3fe7d00c_6b144eee.pdf'
```

**Root Cause**: Supabase storage returning 400 Bad Request
- **Storage URL**: `https://znvwzkdblknkkztqyfnu.supabase.co/storage/v1/object/files/user/899b78b1-3c14-400b-aa8e-91457759be1e/raw/3fe7d00c_6b144eee.pdf`
- **Error**: 400 Bad Request from Supabase storage
- **Impact**: Worker falls back to local file handling

#### **2. Fallback File Not Found (Secondary Issue)**
```
FileNotFoundError: [Errno 2] No such file or directory: 'examples/simulated_insurance_document.pdf'
```

**Root Cause**: Hardcoded fallback path doesn't exist in production
- **Expected Path**: `examples/simulated_insurance_document.pdf`
- **Actual Issue**: This file doesn't exist in the production worker container
- **Impact**: Worker cannot process the document at all

#### **3. Webhook URL Still Using Localhost (Tertiary Issue)**
```
webhook_url: "http://localhost:8000/api/upload-pipeline/webhook/llamaparse/dc63b04f-7eac-4504-a4d1-c0de1a2cf683"
```

**Root Cause**: Environment variable still not applied
- **Expected**: `https://insurance-navigator-api.onrender.com`
- **Actual**: `http://localhost:8000`
- **Impact**: LlamaParse would reject this URL (but job failed before reaching LlamaParse)

## 🔍 **Root Cause Analysis**

### **Primary Root Cause: Storage Access Issues**
- Supabase storage returning 400 Bad Request
- Possible causes:
  - File doesn't exist in storage
  - Storage permissions issue
  - Storage service configuration problem
  - File path corruption

### **Secondary Root Cause: Hardcoded Fallback Path**
- Worker has hardcoded fallback to `examples/simulated_insurance_document.pdf`
- This file doesn't exist in production environment
- Fallback mechanism is broken

### **Tertiary Root Cause: Environment Variable Not Applied**
- `WEBHOOK_BASE_URL` configuration still not deployed
- Worker still using localhost URL
- Configuration deployment issue

## 🔧 **Resolution Plan**

### **Immediate Actions (Critical):**

#### **1. Fix Storage Access Issue**
- **Investigate Supabase storage**: Check if file exists and permissions
- **Verify storage configuration**: Ensure proper access credentials
- **Test storage download**: Manually verify file accessibility

#### **2. Fix Fallback File Handling**
- **Remove hardcoded path**: Use dynamic fallback or proper error handling
- **Implement proper fallback**: Create appropriate fallback mechanism
- **Add error handling**: Better error messages for missing files

#### **3. Deploy Webhook URL Configuration**
- **Force deployment**: Ensure `WEBHOOK_BASE_URL` is deployed
- **Restart worker**: Force worker restart to pick up new config
- **Verify environment**: Check environment variables in production

### **Code Changes Required:**

#### **Fix 1: Remove Hardcoded Fallback Path**
```python
# Current problematic code (line 1258)
with open(local_path, 'rb') as f:

# Should be:
if os.path.exists(local_path):
    with open(local_path, 'rb') as f:
        # process file
else:
    raise UserFacingError("Document file not available for processing")
```

#### **Fix 2: Improve Storage Error Handling**
```python
# Add better error handling for storage failures
try:
    # storage download logic
except Exception as e:
    self.logger.error(f"Storage download failed: {e}")
    # Don't fall back to non-existent hardcoded file
    raise UserFacingError("Document storage access failed")
```

## 📊 **Impact Assessment**

- **System Status**: Complete failure - no documents can be processed
- **User Impact**: 100% failure rate for all uploads
- **Business Impact**: Critical - entire document processing pipeline down
- **Priority**: EMERGENCY - Multiple critical issues

## 🎯 **Success Criteria**

- [ ] Supabase storage downloads work correctly
- [ ] Fallback mechanism handles missing files gracefully
- [ ] Webhook URL uses correct production URL
- [ ] Worker processes documents successfully
- [ ] No hardcoded file paths in production code

## 🔍 **Investigation Steps**

### **1. Check Storage Status**
```sql
-- Check if file exists in database
SELECT raw_path, filename FROM upload_pipeline.documents 
WHERE document_id = '1319d58d-0f37-5231-a4d6-1e575b5f2742';

-- Check recent uploads
SELECT document_id, raw_path, created_at 
FROM upload_pipeline.documents 
ORDER BY created_at DESC LIMIT 5;
```

### **2. Test Storage Access**
```bash
# Test storage URL manually
curl -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  "https://znvwzkdblknkkztqyfnu.supabase.co/storage/v1/object/files/user/899b78b1-3c14-400b-aa8e-91457759be1e/raw/3fe7d00c_6b144eee.pdf"
```

### **3. Check Worker Environment**
```bash
# Check if environment variables are set
echo $WEBHOOK_BASE_URL
echo $ENVIRONMENT
```

---

**Created**: 2025-09-18  
**Updated**: 2025-09-18  
**Status**: Active  
**Assigned**: Development Team  
**Priority**: High
