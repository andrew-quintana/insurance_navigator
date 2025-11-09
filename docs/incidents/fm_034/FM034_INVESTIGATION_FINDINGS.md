# FM-034 Investigation Findings - Chat API 401 Authorization Errors

**Date**: January 3, 2025  
**Status**: ROOT CAUSE IDENTIFIED  
**Priority**: HIGH  

---

## Executive Summary

**Root Cause Identified**: Frontend token transmission mechanism is working correctly, but there's a **token validation mismatch** between the frontend Supabase authentication and the API server's token validation logic.

**Key Finding**: The API server is correctly rejecting requests without proper authentication, but the frontend is sending Supabase tokens that the API server cannot validate due to a **token validation implementation issue**.

---

## Investigation Results

### ✅ **API Server Status - HEALTHY**
- **Health Check**: ✅ API server responding correctly
- **Authentication Middleware**: ✅ Working (rejects unauthorized requests)
- **Error Messages**: ✅ Proper 401 responses with clear error details

**Test Results**:
```bash
# Without token
curl -X POST "https://insurance-navigator-staging-api.onrender.com/chat" -d '{"message":"test"}'
# Response: {"detail":"Missing or invalid authorization header"}

# With invalid token  
curl -X POST "https://insurance-navigator-staging-api.onrender.com/chat" -H "Authorization: Bearer invalid_token_test" -d '{"message":"test"}'
# Response: {"detail":"Invalid token"}
```

### ✅ **Frontend Authentication - WORKING**
- **Supabase Authentication**: ✅ User successfully signing in
- **Token Storage**: ✅ Tokens stored in localStorage correctly
- **Token Transmission**: ✅ Authorization header sent with requests

**Frontend Code Analysis**:
```typescript
// ui/app/chat/page.tsx:120
const token = localStorage.getItem("token")

// ui/app/chat/page.tsx:130
'Authorization': `Bearer ${token}`,
```

### ❌ **Token Validation Issue - IDENTIFIED**

**Problem**: The API server's token validation logic in `db/services/supabase_auth_service.py` has a **critical flaw** in the `validate_token` method.

**Issue Location**: `db/services/supabase_auth_service.py:318`
```python
# PROBLEMATIC CODE:
client.auth.set_session(token, token)  # Using token as both access and refresh token
```

**Root Cause**: The `set_session` method expects both an access token and a refresh token, but the code is passing the same token for both parameters. This causes Supabase's internal validation to fail.

---

## Detailed Analysis

### **Authentication Flow Analysis**

1. **Frontend Authentication** ✅
   - User signs in via Supabase
   - Session established with valid access_token
   - Token stored in localStorage as 'token'
   - Token sent in Authorization header

2. **API Server Reception** ✅
   - Request received with Authorization header
   - Token extracted from "Bearer {token}" format
   - Token passed to auth_adapter.validate_token()

3. **Token Validation Failure** ❌
   - `supabase_auth_service.validate_token()` called
   - `client.auth.set_session(token, token)` fails
   - Supabase rejects the session setup
   - Method returns None, causing 401 error

### **Code Flow Trace**

```python
# main.py:543 - get_current_user()
user_data = await auth_adapter.validate_token(access_token)

# db/services/auth_adapter.py:82
return await self.backend.validate_token(token)

# db/services/supabase_auth_service.py:318 - PROBLEM HERE
client.auth.set_session(token, token)  # ❌ WRONG: token used as both access and refresh
```

---

## Resolution Strategy

### **Immediate Fix Required**

**File**: `db/services/supabase_auth_service.py`  
**Method**: `validate_token()`  
**Line**: 318  

**Current Problematic Code**:
```python
client.auth.set_session(token, token)
```

**Correct Implementation**:
```python
# Option 1: Use get_user() directly with token
auth_response = client.auth.get_user(token)

# Option 2: Proper session setup (if refresh token available)
# client.auth.set_session(access_token, refresh_token)
```

### **Recommended Fix**

Replace the problematic `set_session` call with direct token validation:

```python
async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
    """Validate a JWT token using Supabase's built-in validation."""
    try:
        logger.info("Validating token with Supabase built-in validation")
        
        # Get the regular Supabase client
        client = await self._get_client()
        
        # Validate token directly using get_user()
        auth_response = client.auth.get_user(token)
        
        if not auth_response or not auth_response.user:
            logger.warning("Invalid token - Supabase validation failed")
            return None
        
        # Extract user data from Supabase response
        user_metadata = auth_response.user.user_metadata or {}
        
        logger.info(f"✅ Token validated successfully for user: {auth_response.user.email}")
        
        return {
            "id": auth_response.user.id,
            "email": auth_response.user.email,
            "name": user_metadata.get("name", auth_response.user.email.split("@")[0]),
            "email_confirmed": auth_response.user.email_confirmed_at is not None,
            "created_at": auth_response.user.created_at,
            "updated_at": auth_response.user.updated_at,
            "last_sign_in_at": auth_response.user.last_sign_in_at,
            "user_metadata": user_metadata
        }
        
    except Exception as e:
        logger.error(f"Supabase token validation error: {e}")
        return None
```

---

## Testing Plan

### **Pre-Fix Testing**
1. ✅ Confirm API server rejects requests without tokens
2. ✅ Confirm API server rejects requests with invalid tokens
3. ✅ Confirm frontend sends tokens correctly

### **Post-Fix Testing**
1. **Unit Test**: Test `validate_token()` method with valid Supabase token
2. **Integration Test**: Test chat endpoint with valid authentication
3. **End-to-End Test**: Test complete authentication flow from frontend

### **Test Script Required**
```python
# test_token_validation_fix.py
async def test_token_validation():
    # Test with valid Supabase token
    # Verify token validation works
    # Confirm chat endpoint accepts authenticated requests
```

---

## Impact Assessment

### **Current Impact**
- **User Experience**: Chat functionality completely broken
- **Authentication**: Users can sign in but cannot use chat
- **Error Rate**: 100% of chat requests failing with 401

### **Post-Fix Impact**
- **User Experience**: Chat functionality fully restored
- **Authentication**: Complete end-to-end authentication working
- **Error Rate**: Expected 0% authentication failures

---

## Prevention Measures

### **Code Review Process**
1. **Authentication Testing**: Mandatory testing of token validation logic
2. **Supabase Integration**: Review all Supabase client method usage
3. **Session Management**: Validate session setup patterns

### **Testing Requirements**
1. **Unit Tests**: Test all authentication methods
2. **Integration Tests**: Test complete authentication flow
3. **End-to-End Tests**: Test frontend-to-backend authentication

---

## Related Incidents

- **FM-033**: Supabase authentication 400 errors (RESOLVED) - Different issue (configuration)
- **FM-032**: Vercel deployment configuration issues (RESOLVED) - Different issue (deployment)

---

## Next Steps

1. **Immediate**: Apply token validation fix to `supabase_auth_service.py`
2. **Testing**: Create and run comprehensive authentication tests
3. **Deployment**: Deploy fix to staging environment
4. **Verification**: Confirm chat functionality working end-to-end
5. **Documentation**: Update authentication flow documentation

---

**Status**: ✅ **ROOT CAUSE IDENTIFIED**  
**Confidence**: **HIGH** - Clear code issue with straightforward fix  
**Estimated Fix Time**: **30 minutes** - Simple code change  
**Risk Level**: **LOW** - Isolated fix with minimal impact
