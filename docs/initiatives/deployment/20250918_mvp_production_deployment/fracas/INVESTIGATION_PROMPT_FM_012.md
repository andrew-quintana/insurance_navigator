# Investigation Prompt: FM-012 Webhook URL Security Validation

## 📋 **Current Status**

**FM-012 Status**: IN PROGRESS 🔄  
**Priority**: High  
**Component**: Worker Webhook URL Generation  

### **Issues Identified** ❌
- **Webhook URL Security**: LlamaParse rejecting localhost URLs for security reasons
- **Environment Detection**: Worker detecting `ENVIRONMENT=development` in production
- **Webhook Logic Flaw**: Development branch using localhost instead of respecting `WEBHOOK_BASE_URL`

### **Issues Resolved** ✅
- **Environment Variable**: Added `ENVIRONMENT=production` to worker service
- **Webhook Logic**: Fixed to always respect `WEBHOOK_BASE_URL` when set
- **Deployment**: Triggered worker redeployment with fixes

### **Issues Still Pending** ❌
- **Verification**: Test that worker now generates production webhook URLs
- **End-to-End Testing**: Verify complete pipeline works with fixed webhook URLs

## 🚨 **Critical Success Criteria**

- [x] **Environment Variable**: `ENVIRONMENT=production` set in worker service
- [x] **Webhook Logic**: Fixed to respect `WEBHOOK_BASE_URL` in all cases
- [x] **Deployment**: Worker redeployed with fixes
- [ ] **Verification**: Worker generates production webhook URLs (not localhost)
- [ ] **End-to-End**: Complete document processing pipeline works
- [ ] **Documentation**: All findings and fixes properly documented

## 🔍 **Root Cause Analysis**

### **Primary Issue**
LlamaParse API rejects webhook URLs containing localhost for security reasons:
```
"Failed to validate URLs: webhook_url contains a non-public URL which could pose a security risk"
```

### **Secondary Issues**
1. **Environment Detection**: Worker was detecting `ENVIRONMENT=development` in production
2. **Webhook Logic Flaw**: Development branch was using localhost fallback instead of respecting `WEBHOOK_BASE_URL`
3. **Missing Environment Variable**: `ENVIRONMENT` was not explicitly set in worker service

### **Evidence**
- **Generated Webhook URL**: `http://localhost:8000/api/upload-pipeline/webhook/llamaparse/21ec4e2b-4498-402a-848a-53779ed10088`
- **Environment Detection**: `ENVIRONMENT=development, WEBHOOK_BASE_URL=***REMOVED***`
- **LlamaParse Error**: 400 Bad Request with security validation failure

## 🔧 **Implemented Fixes**

### **1. Environment Variable Enforcement**
- **Action**: Added `ENVIRONMENT=production` to worker service environment variables
- **Method**: Used Render API to update worker service configuration
- **Status**: ✅ Deployed (Deployment ID: dep-d36d408dl3ps7387nmp0)

### **2. Webhook URL Logic Fix**
- **Action**: Modified webhook URL generation to always respect `WEBHOOK_BASE_URL` when set
- **Logic**: 
  ```python
  # Always respect WEBHOOK_BASE_URL when explicitly set (production override)
  if webhook_base_url:
      base_url = webhook_base_url
  elif environment == "development":
      # Development logic with ngrok discovery
  else:
      # Production default
  ```
- **Status**: ✅ Code updated

### **3. Deployment Triggered**
- **Action**: Worker service redeployed with environment variable fix
- **Status**: ✅ In progress

## 🧪 **Testing Plan**

### **Immediate Verification**
1. **Check Worker Logs**: Verify `ENVIRONMENT=production` is detected
2. **Check Webhook URLs**: Verify production URLs are generated (not localhost)
3. **Test Document Upload**: Upload test document and monitor processing

### **End-to-End Testing**
1. **Upload Test Document**: Use existing test file
2. **Monitor Job Processing**: Check worker logs for correct webhook URL generation
3. **Verify LlamaParse Success**: Confirm no 400 errors from LlamaParse API
4. **Complete Pipeline**: Ensure document processing completes successfully

## 📊 **Expected Results**

### **Worker Logs Should Show**
```
Environment detection: ENVIRONMENT=production, WEBHOOK_BASE_URL=***REMOVED***
Using explicit WEBHOOK_BASE_URL: ***REMOVED***
Generated webhook URL: ***REMOVED***/api/upload-pipeline/webhook/llamaparse/{job_id}
```

### **LlamaParse Should Accept**
- Webhook URL: `***REMOVED***/api/upload-pipeline/webhook/llamaparse/{job_id}`
- No 400 Bad Request errors
- Successful document processing

## 🔄 **Next Steps**

1. **Wait for Deployment**: Monitor deployment completion
2. **Verify Environment**: Check worker logs for correct environment detection
3. **Test Webhook URLs**: Confirm production URLs are generated
4. **End-to-End Test**: Upload document and verify complete processing
5. **Update Status**: Mark FM-012 as resolved if successful

## 📁 **Files Modified**

- `config/render/render.yaml` - Environment variable configuration (already had ENVIRONMENT=production)
- `backend/workers/enhanced_base_worker.py` - Fixed webhook URL generation logic
- Worker service environment variables - Updated via Render API

## 🎯 **Success Metrics**

- ✅ Worker detects `ENVIRONMENT=production`
- ✅ Worker generates production webhook URLs
- ✅ LlamaParse accepts webhook URLs (no 400 errors)
- ✅ Document processing completes successfully
- ✅ No localhost references in production logs

## 📝 **Notes**

This issue was caused by a combination of:
1. Missing environment variable enforcement in worker service
2. Flawed webhook URL generation logic that didn't respect `WEBHOOK_BASE_URL` in development mode
3. LlamaParse's security validation rejecting localhost URLs

The fix ensures that:
- Environment variables are properly enforced
- Webhook URLs always use production URLs when `WEBHOOK_BASE_URL` is set
- The system is more robust against environment detection issues
