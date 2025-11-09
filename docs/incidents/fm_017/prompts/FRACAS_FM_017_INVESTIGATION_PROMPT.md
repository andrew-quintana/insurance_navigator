# FRACAS FM-017 Investigation Prompt: Upload Pipeline JWT Authentication Failure

## 🎯 **INVESTIGATION OBJECTIVE**

Investigate and resolve the JWT authentication failure in the upload pipeline that is preventing users from uploading documents in the staging environment.

## 📋 **INVESTIGATION CHECKLIST**

### **Phase 1: Error Confirmation and Analysis**
- [ ] **Confirm Error**: Verify 500 "Authentication service error" on `/api/upload-pipeline/upload`
- [ ] **Test Token Validity**: Confirm JWT token works for main API but fails for upload pipeline
- [ ] **Check Error Location**: Identify exact location of authentication failure
- [ ] **Analyze Error Message**: Understand why "Authentication service error" is returned

### **Phase 2: JWT Configuration Analysis**
- [ ] **Main API JWT Secret**: Identify JWT secret used by main API server
- [ ] **Upload Pipeline JWT Secret**: Identify JWT secret used by upload pipeline
- [ ] **Environment Variables**: Check JWT_SECRET_KEY environment variable in staging
- [ ] **Configuration Files**: Review JWT configuration in both services

### **Phase 3: Root Cause Identification**
- [ ] **Secret Comparison**: Compare JWT secrets between main API and upload pipeline
- [ ] **Configuration Source**: Identify where each service gets its JWT secret
- [ ] **Environment Analysis**: Check if environment variables are properly set
- [ ] **Code Analysis**: Review JWT validation logic in both services

### **Phase 4: Fix Implementation**
- [ ] **Update Configuration**: Fix JWT secret configuration in upload pipeline
- [ ] **Environment Variables**: Ensure proper environment variable usage
- [ ] **Code Changes**: Update hardcoded secrets to use environment variables
- [ ] **Consistency Check**: Ensure both services use same JWT configuration

### **Phase 5: Testing and Validation**
- [ ] **Unit Testing**: Test JWT validation with correct secret
- [ ] **Integration Testing**: Test upload pipeline with main API tokens
- [ ] **End-to-End Testing**: Test complete upload workflow
- [ ] **Regression Testing**: Ensure no impact on other functionality

## 🔍 **INVESTIGATION QUESTIONS**

### **Error Analysis**
1. **What is the exact error message and status code?**
   - Error: `{"detail":"Authentication service error"}` (HTTP 500)
   - Location: `/api/upload-pipeline/upload` endpoint

2. **Where does the error occur in the code?**
   - File: `api/upload_pipeline/auth.py`
   - Function: `get_current_user()` or `require_user()`
   - Line: Around line 84 (generic exception handler)

3. **Why is a generic error returned instead of specific JWT error?**
   - The code catches all exceptions and returns generic "Authentication service error"
   - Need to identify the specific JWT validation failure

### **JWT Configuration Analysis**
4. **What JWT secret does the main API use?**
   - Check: `db/services/improved_minimal_auth_service.py`
   - Look for: `self.secret_key` value

5. **What JWT secret does the upload pipeline use?**
   - Check: `api/upload_pipeline/auth.py`
   - Look for: JWT decode secret parameter

6. **Are environment variables properly configured?**
   - Check: `JWT_SECRET_KEY` environment variable
   - Check: Staging deployment configuration

### **Root Cause Analysis**
7. **Are the JWT secrets different between services?**
   - Compare secrets used by both services
   - Identify configuration mismatch

8. **Why is the upload pipeline using hardcoded secret?**
   - Check if environment variable is not being read
   - Check if configuration is not properly loaded

9. **What should the correct configuration be?**
   - Both services should use same JWT secret
   - Should come from environment variable, not hardcoded

## 🛠️ **INVESTIGATION TOOLS AND COMMANDS**

### **Error Testing**
```bash
# Test upload endpoint with valid token
curl -X POST "https://insurance-navigator-staging-api.onrender.com/api/upload-pipeline/upload" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.pdf", "mime": "application/pdf", "bytes_len": 1000, "sha256": "test123"}'

# Test main API with same token
curl -X GET "https://insurance-navigator-staging-api.onrender.com/me" \
  -H "Authorization: Bearer <token>"
```

### **JWT Token Analysis**
```python
# Decode JWT token to see payload
import jwt
token = "<jwt_token>"
payload = jwt.decode(token, options={"verify_signature": False})
print(payload)
```

### **Configuration Analysis**
```bash
# Check environment variables in staging
curl -X GET "https://insurance-navigator-staging-api.onrender.com/debug-auth"

# Check JWT configuration files
grep -r "JWT_SECRET" config/
grep -r "secret_key" api/upload_pipeline/
grep -r "secret_key" db/services/
```

## 📊 **EXPECTED OUTCOMES**

### **Phase 1: Error Confirmation**
- Confirmed 500 error with "Authentication service error"
- JWT token works for main API but fails for upload pipeline
- Error occurs in upload pipeline authentication

### **Phase 2: Configuration Analysis**
- Main API uses `"improved-minimal-dev-secret-key"`
- Upload pipeline uses hardcoded `"improved-minimal-dev-secret-key"`
- Environment variable may not be properly configured

### **Phase 3: Root Cause**
- JWT secret mismatch between services
- Upload pipeline should use environment variable
- Configuration inconsistency

### **Phase 4: Fix Implementation**
- Update upload pipeline to use environment variable
- Ensure both services use same JWT secret
- Remove hardcoded secrets

### **Phase 5: Validation**
- Upload pipeline accepts JWT tokens from main API
- Upload functionality works end-to-end
- No regression in other functionality

## 🚨 **CRITICAL SUCCESS FACTORS**

1. **JWT Secret Consistency**: Both services must use identical JWT secrets
2. **Environment Variable Usage**: No hardcoded secrets in production code
3. **Error Handling**: Proper error messages for debugging
4. **Testing**: Complete end-to-end validation
5. **Documentation**: Clear configuration requirements

## 📝 **INVESTIGATION NOTES**

### **Key Files to Review**
- `api/upload_pipeline/auth.py` - Upload pipeline JWT validation
- `db/services/improved_minimal_auth_service.py` - Main API JWT generation
- `config/auth_config.py` - Authentication configuration
- Environment variables in staging deployment

### **Common Issues to Check**
- Hardcoded JWT secrets instead of environment variables
- Different JWT secrets between services
- Missing environment variable configuration
- Incorrect JWT validation logic

### **Resolution Strategy**
1. Identify correct JWT secret to use
2. Update upload pipeline to use environment variable
3. Ensure both services use same configuration source
4. Test with valid JWT tokens
5. Validate end-to-end functionality

---

**Investigation Status**: 🔄 **IN PROGRESS**  
**Priority**: P1 - High  
**Estimated Resolution Time**: 2-4 hours  
**Assigned To**: AI Assistant  
**Created**: 2025-09-25
