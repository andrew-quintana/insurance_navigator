# FM-036 Supabase Instance Mismatch Analysis

**Date**: January 3, 2025  
**Incident**: Supabase authentication 400 errors in production  
**Status**: 🔍 **ROOT CAUSE IDENTIFIED**  
**Priority**: HIGH  
**Environment**: Vercel Production Deployment  

---

## Executive Summary

**Issue**: Supabase authentication failing with 400 Bad Request errors  
**Root Cause**: Hardcoded Supabase credentials in vercel.json pointing to wrong instance  
**Impact**: Authentication completely broken in production  
**Status**: 🔍 **INVESTIGATION COMPLETE** - Fix required  

---

## Problem Analysis

### **Symptoms Observed**
- ✅ Vercel deployment successful (FM-035 resolved)
- ✅ Application accessible and loading
- ❌ Supabase authentication failing with 400 errors
- ❌ Auth state changes to "INITIAL_SESSION" then fails
- ❌ Token endpoint returning 400 status

### **Error Details**
```
[Log] Auth state changed: – "INITIAL_SESSION" – undefined
[Error] Failed to load resource: the server responded with a status of 400 () (token, line 0)
```

### **Root Cause Identified**
**File**: `ui/vercel.json`  
**Issue**: Hardcoded Supabase credentials pointing to wrong instance  
**Problem**: Vercel.json overrides environment variables with incorrect Supabase URL  

---

## Supabase Instance Analysis

### **Current Configuration (WRONG)**
**File**: `ui/vercel.json` (lines 20-21)
```json
"NEXT_PUBLIC_SUPABASE_URL": "https://your-staging-project.supabase.co",
"NEXT_PUBLIC_SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM"
```

### **Correct Configuration (SHOULD BE)**
**File**: `ui/.env.production`
```bash
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd6a2RibGtua2t6dHF5Zm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0NTYsImV4cCI6MjA2NzI1NjQ1Nn0.k0QHYOgm4EilyyTml57kCGDpbikpEtJCzq-qzGYQZqY
```

### **Instance Comparison**
| Configuration | Supabase URL | Instance ID | Status |
|---------------|--------------|-------------|---------|
| **Vercel.json (WRONG)** | `your-staging-project.supabase.co` | `your-staging-project` | ❌ Wrong instance |
| **Production Env (CORRECT)** | `your-project.supabase.co` | `your-project` | ✅ Correct instance |

---

## Technical Analysis

### **Why This Causes 400 Errors**
1. **Wrong Supabase Instance**: Vercel is trying to authenticate against `your-staging-project` instead of `your-project`
2. **Invalid API Key**: The API key in vercel.json is for the wrong instance
3. **Authentication Failure**: Supabase rejects authentication requests with 400 Bad Request
4. **Token Exchange Failure**: Token endpoint returns 400 status

### **Configuration Override Issue**
- **Vercel.json**: Hardcoded values override environment variables
- **Environment Variables**: Correct values in .env.production are ignored
- **Build Process**: Vercel uses vercel.json values during build
- **Runtime**: Application tries to authenticate against wrong instance

---

## Resolution Strategy

### **Immediate Fix Required**

**Option 1: Remove Hardcoded Values (RECOMMENDED)**
- Remove hardcoded Supabase credentials from vercel.json
- Let Vercel use environment variables from Vercel dashboard
- Ensure Vercel environment variables are set correctly

**Option 2: Update Hardcoded Values**
- Update vercel.json with correct Supabase credentials
- Less flexible but immediate fix

### **Recommended Fix**

**File**: `ui/vercel.json`  
**Action**: Remove hardcoded Supabase credentials from build.env section

**Before (Broken)**:
```json
"build": {
  "env": {
    "NEXT_PUBLIC_SUPABASE_URL": "https://your-staging-project.supabase.co",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "NEXT_PUBLIC_API_BASE_URL": "https://insurance-navigator-staging-api.onrender.com",
    "NEXT_PUBLIC_API_URL": "https://insurance-navigator-staging-api.onrender.com",
    "NODE_ENV": "staging"
  }
}
```

**After (Fixed)**:
```json
"build": {
  "env": {
    "NEXT_PUBLIC_API_BASE_URL": "https://insurance-navigator-staging-api.onrender.com",
    "NEXT_PUBLIC_API_URL": "https://insurance-navigator-staging-api.onrender.com",
    "NODE_ENV": "staging"
  }
}
```

### **Vercel Environment Variables**
Ensure these are set in Vercel dashboard:
- `NEXT_PUBLIC_SUPABASE_URL` = `https://your-project.supabase.co`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd6a2RibGtua2t6dHF5Zm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0NTYsImV4cCI6MjA2NzI1NjQ1Nn0.k0QHYOgm4EilyyTml57kCGDpbikpEtJCzq-qzGYQZqY`

---

## Impact Assessment

### **Current Impact**
- **User Experience**: Authentication completely broken
- **Business Impact**: Users cannot sign in or use application
- **Error Rate**: 100% of authentication requests failing
- **Service Status**: Application accessible but non-functional

### **Post-Fix Impact**
- **User Experience**: Authentication fully restored
- **Business Impact**: Users can sign in and use application
- **Error Rate**: Expected 0% authentication failures
- **Service Status**: Fully functional application

---

## Testing Plan

### **Pre-Fix Testing**
1. ✅ Confirm authentication failing with 400 errors
2. ✅ Confirm wrong Supabase instance being used
3. ✅ Confirm hardcoded values in vercel.json

### **Post-Fix Testing**
1. **Configuration Test**: Verify correct Supabase instance being used
2. **Authentication Test**: Test user sign-in functionality
3. **Token Test**: Verify token exchange working
4. **End-to-End Test**: Test complete authentication flow

---

## Prevention Measures

### **Configuration Management**
1. **Remove Hardcoded Values**: Never hardcode environment-specific values in vercel.json
2. **Use Environment Variables**: Always use Vercel environment variables for sensitive data
3. **Configuration Validation**: Validate environment variables before deployment
4. **Documentation**: Document correct environment variable values

### **Deployment Process**
1. **Environment Check**: Verify environment variables in Vercel dashboard
2. **Configuration Review**: Review vercel.json for hardcoded values
3. **Testing**: Test authentication in staging before production
4. **Monitoring**: Monitor authentication success rates post-deployment

---

## Related Incidents

### **Pattern Analysis**
This follows a pattern of configuration management issues:

- **FM-033**: Supabase configuration mismatches (RESOLVED)
- **FM-035**: Dependency conflicts (RESOLVED)
- **FM-036**: Supabase instance mismatch (THIS INCIDENT)

### **Common Root Causes**
1. **Hardcoded Values**: Environment-specific values hardcoded in configuration files
2. **Configuration Override**: Build configuration overriding environment variables
3. **Environment Mismatch**: Different values across environments
4. **Lack of Validation**: No validation of configuration consistency

---

## Next Steps

### **Immediate Actions**
1. **Fix Configuration**: Remove hardcoded Supabase credentials from vercel.json
2. **Verify Environment**: Ensure Vercel environment variables are set correctly
3. **Deploy Fix**: Deploy corrected configuration
4. **Test Authentication**: Verify authentication working

### **Follow-up Actions**
1. **Monitor**: Watch authentication success rates
2. **Document**: Update configuration management procedures
3. **Prevent**: Implement configuration validation checks
4. **Train**: Ensure team understands configuration management

---

## Success Criteria

### **Investigation Complete** ✅
1. ✅ Root cause of authentication 400 errors identified
2. ✅ Supabase instance mismatch confirmed
3. ✅ Configuration override issue identified
4. ✅ Resolution strategy developed

### **Resolution Required** 🔄
1. 🔄 Remove hardcoded Supabase credentials from vercel.json
2. 🔄 Verify Vercel environment variables are correct
3. 🔄 Deploy fix and test authentication
4. 🔄 Monitor authentication success rates

---

**Status**: 🔍 **ROOT CAUSE IDENTIFIED**  
**Confidence**: **HIGH** - Clear configuration issue  
**Fix Complexity**: **LOW** - Simple configuration change  
**Business Impact**: **HIGH** - Authentication completely broken  

---

*This investigation successfully identifies the FM-036 Supabase instance mismatch issue. The fix requires removing hardcoded Supabase credentials from vercel.json and ensuring Vercel environment variables are set correctly.*
