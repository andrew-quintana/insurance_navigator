# FRACAS FM-014 Investigation Prompt: API Upload Authentication Failure

## 🎯 **INVESTIGATION MISSION**

**Objective**: Investigate and resolve the API upload authentication failure causing FastAPI dependency injection issues.

**Reference Document**: `docs/incidents/failure_modes/authentication/FRACAS_FM_014_API_UPLOAD_AUTHENTICATION_FAILURE.md`

## 🚨 **CURRENT SITUATION**

### **Critical Issue**
- **Status**: Medium Priority (Resolved with workaround)
- **Impact**: API upload testing was blocked
- **Error**: `'Depends' object has no attribute 'user_id'`
- **Root Cause**: FastAPI dependency injection issue in no-auth endpoint

### **Evidence Summary**
```
Status Code: 500
Response Body: {"detail":"'Depends' object has no attribute 'user_id'"}
Location: /upload-document-backend-no-auth endpoint
Root Cause: FastAPI dependency injection bypass
```

## 🔍 **INVESTIGATION TASKS**

### **Task 1: FastAPI Dependency Analysis (P1 - High)**
**Time Estimate**: 20 minutes

**Objective**: Understand the FastAPI dependency injection issue and why it occurs.

**Investigation Steps**:
1. Analyze the function signature mismatch between expected and actual parameters
2. Understand how FastAPI dependency injection works
3. Identify why direct function calls bypass dependency resolution
4. Review the no-auth endpoint implementation

**Expected Output**:
- Clear understanding of FastAPI dependency injection
- Analysis of function signature mismatch
- Root cause explanation

### **Task 2: No-Auth Endpoint Review (P1 - High)**
**Time Estimate**: 15 minutes

**Objective**: Review the no-auth endpoint implementation and identify issues.

**Investigation Steps**:
1. Examine `/upload-document-backend-no-auth` endpoint code
2. Check how it calls the `upload_document` function
3. Identify missing dependency parameters
4. Review alternative endpoint options

**Expected Output**:
- No-auth endpoint code analysis
- Missing dependency identification
- Alternative endpoint options

### **Task 3: Proper No-Auth Implementation (P2 - Medium)**
**Time Estimate**: 30 minutes

**Objective**: Implement proper no-auth endpoint that doesn't bypass dependency injection.

**Implementation Requirements**:
1. Create proper mock user for no-auth endpoint
2. Implement separate upload function for no-auth case
3. Add proper error handling and documentation
4. Test both authenticated and non-authenticated endpoints

**Code Changes Needed**:
- Fix `/upload-document-backend-no-auth` endpoint implementation
- Create proper mock user handling
- Add endpoint documentation
- Implement comprehensive testing

**Success Criteria**:
- No-auth endpoint works without dependency injection issues
- Clear documentation of endpoint requirements
- Proper error handling for both cases

### **Task 4: Testing Implementation (P2 - Medium)**
**Time Estimate**: 20 minutes

**Objective**: Create comprehensive tests for both authenticated and non-authenticated endpoints.

**Testing Steps**:
1. Create tests for no-auth upload endpoint
2. Create tests for authenticated upload endpoint
3. Test error handling scenarios
4. Verify dependency injection works correctly

**Expected Output**:
- Comprehensive test suite for upload endpoints
- Test results showing proper functionality
- Error handling validation

### **Task 5: Documentation Updates (P3 - Low)**
**Time Estimate**: 15 minutes

**Objective**: Update documentation to reflect endpoint requirements and usage.

**Documentation Requirements**:
1. Document which endpoints require authentication
2. Provide clear examples of how to call functions with dependencies
3. Create testing guidelines for different endpoint types
4. Update API documentation

**Success Criteria**:
- Clear endpoint documentation
- Usage examples provided
- Testing guidelines documented

## 🧪 **TEST COMMANDS**

```bash
# Test 1: Test no-auth endpoint (should fail with current implementation)
curl -X POST http://localhost:8000/upload-document-backend-no-auth \
  -F "file=@test.pdf" \
  -F "policy_id=test-policy"

# Test 2: Test authenticated endpoint
curl -X POST http://localhost:8000/upload-document-backend \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "file=@test.pdf" \
  -F "policy_id=test-policy"

# Test 3: Test alternative upload-test endpoint
curl -X POST http://localhost:8000/upload-test \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.pdf", "content_type": "application/pdf"}'

# Test 4: Test FastAPI dependency injection
python -c "
from fastapi import Depends
from api.upload_pipeline.endpoints.upload import upload_document
from db.models.user import User

# This should show the dependency issue
print('Function signature:', upload_document.__annotations__)
"
```

## 📋 **EXPECTED OUTPUT**

### **Immediate Fix (P0)**
1. **Workaround**: Use existing `/upload-test` endpoint for testing
2. **Issue Identification**: Clear understanding of FastAPI dependency issue
3. **Alternative Solution**: Identify proper no-auth endpoint implementation

### **Short-term Improvements (P1)**
1. **Proper Implementation**: Fix no-auth endpoint with proper mock user
2. **Testing**: Create comprehensive tests for both endpoint types
3. **Documentation**: Clear documentation of endpoint requirements

### **Long-term Improvements (P2)**
1. **Code Organization**: Separate no-auth and authenticated implementations
2. **Error Handling**: Improved error handling for both cases
3. **Monitoring**: Add monitoring for endpoint usage patterns

### **Success Metrics**
- ✅ No-auth endpoint works without dependency injection issues
- ✅ Authenticated endpoint works correctly
- ✅ Clear error messages for both cases
- ✅ Comprehensive test coverage
- ✅ Clear documentation of endpoint requirements

## 📄 **DELIVERABLES**

1. **FRACAS Update**: Update `docs/incidents/failure_modes/authentication/FRACAS_FM_014_API_UPLOAD_AUTHENTICATION_FAILURE.md` with findings
2. **Code Fix**: Implement proper no-auth endpoint
3. **Testing**: Create comprehensive test suite
4. **Documentation**: Update endpoint documentation
5. **Best Practices**: Document FastAPI dependency injection best practices

## ⚠️ **CRITICAL NOTES**

- **FastAPI Dependencies**: Direct function calls bypass dependency injection
- **Testing Strategy**: Need separate tests for authenticated vs non-authenticated endpoints
- **Code Organization**: No-auth endpoints should have their own implementation logic
- **Documentation**: Clear documentation of endpoint requirements is essential

## 🚨 **ESCALATION CRITERIA**

- If FastAPI dependency injection changes break other functionality
- If no-auth endpoint implementation requires significant architectural changes
- If testing reveals additional authentication issues
- If documentation updates require API contract changes

## ⏱️ **ESTIMATED DURATION**
- **Total Time**: 100 minutes
- **Investigation**: 35 minutes
- **Implementation**: 50 minutes
- **Testing**: 15 minutes

---

**Reference**: See `docs/incidents/failure_modes/authentication/FRACAS_FM_014_API_UPLOAD_AUTHENTICATION_FAILURE.md` for complete failure details
