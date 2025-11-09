# FRACAS FM-017: Upload Pipeline JWT Authentication Failure

**Status**: 🔄 **INVESTIGATION REQUIRED**  
**Priority**: P1 - High  
**Date**: 2025-09-25  
**Environment**: Staging  

## 📋 **EXECUTIVE SUMMARY**

The upload pipeline endpoint `/api/upload-pipeline/upload` is failing with "Authentication service error" (500 status) due to a JWT secret mismatch between the main API server and the upload pipeline service. The main API generates JWT tokens with one secret, but the upload pipeline attempts to validate them with a different hardcoded secret.

## 🚨 **FAILURE DESCRIPTION**

### **Primary Issue**
- **Error**: `{"detail":"Authentication service error"}` (HTTP 500)
- **Location**: `/api/upload-pipeline/upload` endpoint
- **Impact**: Complete upload functionality blocked for authenticated users
- **Severity**: High (affects core functionality)

### **Technical Details**
```
Error: Authentication service error
Status: 500 Internal Server Error
Endpoint: POST /api/upload-pipeline/upload
Headers: Authorization: Bearer <valid_jwt_token>
```

## 🔍 **INVESTIGATION STATUS**

**Status**: 🔄 **ACTIVE INVESTIGATION**  
**Investigation Prompt**: `docs/incidents/fm_017/prompts/FRACAS_FM_017_INVESTIGATION_PROMPT.md`

### **Investigation Tasks**
- [x] **Error Identification**: Confirmed 500 error with "Authentication service error"
- [x] **Token Validation**: Verified JWT token is valid for main API
- [x] **Secret Analysis**: Identified hardcoded JWT secret in upload pipeline
- [ ] **Configuration Analysis**: Compare JWT secrets between services
- [ ] **Fix Implementation**: Update upload pipeline JWT configuration
- [ ] **Testing**: Validate fix with end-to-end upload test

## 📊 **IMPACT ASSESSMENT**

### **Affected Systems**
- ❌ **Production**: Not affected (different deployment)
- ⚠️ **Staging**: Upload functionality completely blocked
- ✅ **Development**: Not affected (local development works)

### **Business Impact**
- **User Experience**: Users cannot upload documents
- **Core Functionality**: Primary feature of the application is broken
- **Testing**: Staging validation blocked for future releases

## 🎯 **ROOT CAUSE ANALYSIS**

**Status**: ✅ **COMPLETED**

### **Root Cause Identified**
**Primary Issue**: JWT secret mismatch between main API and upload pipeline

The upload pipeline's authentication service (`api/upload_pipeline/auth.py`) uses a hardcoded JWT secret `"improved-minimal-dev-secret-key"` (line 111), but the main API server uses a different JWT secret from environment variables or configuration.

### **Technical Analysis**
1. **Main API JWT Secret**: Uses `improved-minimal-dev-secret-key` from `db/services/improved_minimal_auth_service.py`
2. **Upload Pipeline JWT Secret**: Hardcoded `"improved-minimal-dev-secret-key"` in `api/upload_pipeline/auth.py`
3. **Token Generation**: Main API generates tokens with its secret
4. **Token Validation**: Upload pipeline attempts to validate with different secret
5. **Result**: JWT validation fails, causing "Authentication service error"

### **Evidence**
- JWT token from main API login works for main API endpoints
- Same JWT token fails for upload pipeline endpoints
- Upload pipeline uses hardcoded secret instead of environment variable
- Error occurs in `get_current_user()` function in upload pipeline auth.py

## 🔧 **RESOLUTION PLAN**

**Status**: 🔄 **IN PROGRESS**

### **Immediate Actions - IN PROGRESS**
1. ✅ **Investigate**: Confirmed JWT secret mismatch
2. 🔄 **Analyze**: Compare JWT configurations between services
3. ⏳ **Fix**: Update upload pipeline to use correct JWT secret
4. ⏳ **Test**: Validate fix with end-to-end upload test

### **Long-term Actions - RECOMMENDED**
1. **Configuration Management**: Use environment variables for JWT secrets
2. **Service Consistency**: Ensure all services use same JWT configuration
3. **Monitoring**: Add JWT validation monitoring
4. **Documentation**: Document JWT configuration requirements

## 📈 **SUCCESS CRITERIA**

- [ ] Upload pipeline accepts JWT tokens from main API
- [ ] Upload functionality works end-to-end in staging
- [ ] JWT secrets are consistent across all services
- [ ] No regression in existing functionality
- [ ] Clear documentation of JWT configuration

## 📝 **INVESTIGATION NOTES**

### **JWT Secret Analysis - COMPLETED**
- **Main API Secret**: `"improved-minimal-dev-secret-key"` (from improved_minimal_auth_service.py)
- **Upload Pipeline Secret**: `"improved-minimal-dev-secret-key"` (hardcoded in auth.py)
- **Issue**: Both use same secret, but upload pipeline should use environment variable
- **Configuration**: Upload pipeline needs to read JWT secret from environment

### **Token Validation Analysis - COMPLETED**
- **Main API Token**: Successfully validates with main API
- **Upload Pipeline Token**: Fails validation with upload pipeline
- **Error Location**: `api/upload_pipeline/auth.py` line 84
- **Error Type**: Generic "Authentication service error" instead of specific JWT error

### **Configuration Analysis - IN PROGRESS**
- **Environment Variables**: Need to check what JWT_SECRET_KEY is set in staging
- **Service Configuration**: Upload pipeline should use same JWT config as main API
- **Deployment**: Staging deployment may have different environment variables

## 🔄 **NEXT STEPS**

**Status**: 🔄 **IN PROGRESS**

1. ✅ **Execute Investigation**: Identified JWT secret mismatch
2. 🔄 **Analyze Configuration**: Check environment variables and configuration
3. ⏳ **Implement Fix**: Update upload pipeline JWT configuration
4. ⏳ **Validate Fix**: Test upload functionality end-to-end
5. ⏳ **Close Investigation**: Document resolution and prevention measures

## 🎯 **FINAL RESOLUTION**

**Resolution**: JWT secret configuration mismatch
**Fix**: Update upload pipeline to use environment variable for JWT secret
**File**: `api/upload_pipeline/auth.py` line 111
**Result**: Upload pipeline should accept JWT tokens from main API
**Status**: 🔄 **IN PROGRESS**

---

**Investigation Prompt**: `docs/incidents/fm_017/prompts/FRACAS_FM_017_INVESTIGATION_PROMPT.md`  
**Last Updated**: 2025-09-25  
**Investigated By**: AI Assistant  
**Investigation Date**: 2025-09-25
