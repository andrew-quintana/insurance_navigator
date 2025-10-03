# FRACAS FM-033 Investigation Handoff

## Status: INVESTIGATION REQUIRED - Supabase Authentication 400 Errors

**Date**: January 2025  
**Handoff Reason**: Vercel deployment working but Supabase authentication failing  
**Previous Agent**: Claude (Sonnet)  
**Next Agent**: [To be assigned]  

---

## Investigation Summary

### ✅ **Issues Identified and Fixed**

1. **Vercel Deployment Configuration** - FIXED
   - **Problem**: Build context mismatch causing module resolution errors
   - **Solution**: Moved `vercel.json` from root to `ui/` directory
   - **Status**: Preview deployment working (commit: `bbfcbdc`)

2. **Module Resolution Errors** - FIXED
   - **Problem**: `@/components/ui/button`, `@/components/auth/SessionManager` not found
   - **Solution**: Correct build context from `ui/` directory
   - **Status**: All imports resolving correctly

### ❌ **Ongoing Issue: Supabase Authentication 400 Errors**

**Current Failure Observed:**
```
[Log] Auth state changed: – "INITIAL_SESSION" – undefined (layout-4915cedf6d6693c6.js, line 1)
[Error] Failed to load resource: the server responded with a status of 400 () (token, line 0)
```

**Key Observations:**
- Auth state transitions to "INITIAL_SESSION" then fails
- Token endpoint returning 400 Bad Request
- All environment variables set to production values
- Preview environment accessible but authentication failing

---

## Immediate Investigation Required

### 1. **Verify Environment Variables**
```bash
# Check Vercel environment variables
# Ensure these are set correctly:
NEXT_PUBLIC_SUPABASE_URL=https://dfgzeastcxnoqshgyotp.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-staging-api.onrender.com
NEXT_PUBLIC_API_URL=https://insurance-navigator-staging-api.onrender.com
NODE_ENV=staging
```

### 2. **Test Supabase Authentication Directly**
```bash
# Test Supabase auth endpoint
curl -X POST "https://dfgzeastcxnoqshgyotp.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}' \
  -v
```

### 3. **Check Supabase Dashboard**
- Verify API key permissions and roles
- Check JWT secret configuration
- Review authentication settings
- Check Supabase Log Explorer for errors

### 4. **Review Authentication Code**
- Check `ui/lib/supabase-client.ts` configuration
- Verify authentication request payloads
- Review token exchange process
- Check for hard-coded values

---

## Potential Root Causes

### **A. Supabase Configuration Issues**
- API key lacks appropriate roles/permissions
- JWT secret mismatch between Vercel and Supabase
- Authentication settings changed in Supabase dashboard
- CORS configuration blocking requests

### **B. Environment Variable Issues**
- Variables not properly set in Vercel
- Wrong variable names or values
- Environment variables not available at runtime
- Build vs runtime environment mismatch

### **C. Authentication Request Issues**
- Malformed authentication request payloads
- Missing required parameters
- Invalid token format or expired tokens
- Authentication flow configuration mismatch

### **D. Preview/Production Environment Conflicts**
- Both environments accessing same Supabase instance
- Rate limiting or shared resource conflicts
- Authentication token conflicts
- Session management issues

---

## Files Modified (Previous Work)

### `ui/vercel.json` (Moved from root)
```json
{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install --legacy-peer-deps",
  "framework": "nextjs",
  "regions": ["iad1"],
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://insurance-navigator-staging-api.onrender.com/api/$1"
    }
  ],
  "build": {
    "env": {
      "NEXT_PUBLIC_SUPABASE_URL": "https://dfgzeastcxnoqshgyotp.supabase.co",
      "NEXT_PUBLIC_SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "NEXT_PUBLIC_API_BASE_URL": "https://insurance-navigator-staging-api.onrender.com",
      "NEXT_PUBLIC_API_URL": "https://insurance-navigator-staging-api.onrender.com",
      "NODE_ENV": "staging"
    }
  }
}
```

### `ui/.vercelignore` (Created)
```
# UI-specific .vercelignore
coverage/
playwright-report/
__tests__/
e2e/
docs/
.next/
tsconfig.tsbuildinfo
*.local.*
.env.local
```

---

## Test Scripts Available

### `test_supabase_auth.py` (To be created)
- Tests Supabase authentication endpoints
- Validates API key permissions
- Checks JWT configuration

### `test_vercel_env_vars.py` (To be created)
- Tests environment variable configuration
- Validates variable availability at runtime
- Checks variable values and formats

---

## Next Steps for Investigation

### **Immediate (High Priority)**
1. ✅ Verify Supabase API key permissions and JWT configuration
2. ✅ Test authentication endpoints directly
3. ✅ Check Vercel environment variables
4. ✅ Review authentication request payloads

### **Secondary (Medium Priority)**
1. Implement detailed logging around authentication process
2. Use Supabase Log Explorer to investigate errors
3. Test with different authentication methods
4. Check for preview/production environment conflicts

### **Tertiary (Low Priority)**
1. Review related incidents (FM-027, FM-032)
2. Analyze authentication pipeline end-to-end
3. Add additional monitoring/logging
4. Document authentication flow

---

## Environment Details

### **Vercel Configuration**
- **Framework**: Next.js 15.3.2
- **Build Command**: `npm run build` (from `ui/` directory)
- **Output Directory**: `.next`
- **Regions**: `["iad1"]`

### **Supabase Configuration**
- **URL**: `https://dfgzeastcxnoqshgyotp.supabase.co`
- **Environment**: Production instance
- **Authentication**: JWT-based

### **Recent Commits**
- `bbfcbdc`: Fix: Move Vercel configuration to ui/ directory for correct build context
- `512239b`: Add comprehensive documentation for Vercel deployment failure investigation
- `19f319a`: Correct incident report - 400 Bad Request authentication errors

---

## Success Criteria

### **Investigation Complete When:**
1. ✅ Root cause of authentication 400 errors identified
2. ✅ Supabase configuration verified
3. ✅ Authentication flow working end-to-end
4. ✅ No user-facing authentication errors

### **Resolution Complete When:**
1. ✅ All authentication tests passing
2. ✅ Preview deployment successful with working auth
3. ✅ Monitoring in place
4. ✅ Documentation updated

---

## Key Questions to Answer

1. **Are the Supabase API key permissions correct?** (Check roles and JWT settings)
2. **Why is the token endpoint returning 400?** (Request format vs server expectations)
3. **Are there environment variable issues?** (Vercel configuration vs runtime)
4. **Is there a preview/production conflict?** (Shared resources or rate limiting)

---

## Investigation Priority

**Priority**: HIGH  
**Estimated Time**: 2-4 hours  
**Dependencies**: Vercel MCP, Supabase MCP access  
**Testing Requirement**: MANDATORY local testing before production deployment

---

*This handoff provides complete context for continuing the FM-033 investigation. The previous work resolved Vercel deployment issues, but Supabase authentication 400 errors require further investigation.*
