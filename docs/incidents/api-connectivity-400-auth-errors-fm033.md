# API Connectivity 400 Authentication Errors - FM033

**Date**: January 2025  
**Incident**: 400 Bad Request errors during Supabase authentication  
**Status**: 🔍 INVESTIGATION REQUIRED  
**Priority**: HIGH  
**Environment**: Preview deployment (working) but authentication failing  

## Summary

While the Vercel deployment is now working correctly, the application is experiencing 400 Bad Request errors during Supabase authentication. The error occurs during the authentication token exchange process, suggesting a configuration mismatch between Vercel and Supabase services.

## Current Status

### ✅ **Working Components**
- Vercel deployment: ✅ Successful
- Build process: ✅ No module resolution errors
- Preview environment: ✅ Accessible
- Environment variables: ✅ Set to production values

### ❌ **Failing Components**
- Supabase authentication: ❌ 400 Bad Request errors
- Authentication token exchange: ❌ Failed resource load
- Production API connectivity: ❌ Authentication failing

## Error Details

### Specific Error Messages
```
[Log] Auth state changed: – "INITIAL_SESSION" – undefined (layout-4915cedf6d6693c6.js, line 1)
[Error] Failed to load resource: the server responded with a status of 400 () (token, line 0)
```

### Error Analysis
- **Error Type**: HTTP 400 Bad Request
- **Location**: Authentication token exchange process
- **Context**: Auth state changes to "INITIAL_SESSION" then fails
- **Resource**: Token endpoint returning 400 status

## Environment Configuration

### Vercel Environment Variables (Set to Production)
```bash
NEXT_PUBLIC_SUPABASE_URL=https://dfgzeastcxnoqshgyotp.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-staging-api.onrender.com
NEXT_PUBLIC_API_URL=https://insurance-navigator-staging-api.onrender.com
NODE_ENV=staging
```

### Vercel Configuration
```json
// ui/vercel.json
{
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

## Potential Root Causes

### 1. **Invalid Request Parameters**
- **Issue**: HTTP 400 errors typically indicate malformed syntax or invalid request parameters
- **Investigation Needed**: Review authentication request payloads for proper format
- **Risk**: Missing required parameters or incorrect parameter values in auth requests

### 2. **Supabase API Key and JWT Configuration**
- **Issue**: API key or JWT settings may be incorrectly configured
- **Investigation Needed**: Verify Supabase API key has appropriate roles and permissions
- **Risk**: JWT secret mismatch between Vercel and production Supabase configuration

### 3. **Supabase Auth Settings**
- **Issue**: Recent changes to Supabase authentication settings
- **Investigation Needed**: Review Supabase Auth settings for production environment
- **Risk**: Auth flow configuration mismatch between environments

### 4. **Environment Variable Configuration**
- **Issue**: Vercel environment variables may not match production settings
- **Investigation Needed**: Double-check environment variable values in Vercel
- **Risk**: Incorrect Supabase URL or API key values

### 5. **Authentication Token Exchange**
- **Issue**: Token endpoint returning 400 during auth state transition
- **Investigation Needed**: Review token exchange process and endpoint configuration
- **Risk**: Invalid token format or expired tokens

## Investigation Checklist

### Phase 1: Authentication Analysis
- [ ] Review authentication request payloads for proper format
- [ ] Check for missing required parameters in auth requests
- [ ] Verify token exchange process and endpoint configuration
- [ ] Analyze authentication flow and state transitions

### Phase 2: Supabase Configuration
- [ ] Verify Supabase API key has appropriate roles and permissions
- [ ] Check JWT secret alignment with production configuration
- [ ] Review Supabase Auth settings for production environment
- [ ] Confirm Supabase instance accessibility and configuration

### Phase 3: Environment Verification
- [ ] Double-check Vercel environment variable values
- [ ] Verify Supabase URL and API key values match production
- [ ] Test authentication endpoints directly (curl/Postman)
- [ ] Check for environment variable typos or incorrect names

### Phase 4: Logging and Debugging
- [ ] Implement additional logging around authentication process
- [ ] Use Supabase Log Explorer to investigate authentication errors
- [ ] Capture request and response details for debugging
- [ ] Review browser network tab for detailed error information

## Files to Investigate

### API Client Files
- `ui/lib/api-client.ts`
- `ui/lib/supabase-client.ts`
- `ui/lib/auth-helpers.ts`

### Configuration Files
- `ui/vercel.json`
- `ui/.env.*` files
- `ui/next.config.*`

### Service Files
- Any files making API calls
- Authentication service files
- Data fetching utilities

## Error Patterns to Look For

### Authentication Request Issues
```typescript
// ❌ BAD - Missing required parameters
const authRequest = {
  email: userEmail
  // Missing password or other required fields
}

// ✅ GOOD - Complete authentication request
const authRequest = {
  email: userEmail,
  password: userPassword,
  // All required parameters included
}
```

### Environment Variable Issues
```typescript
// ❌ BAD - Wrong variable name or missing prefix
const SUPABASE_URL = process.env.SUPABASE_URL

// ✅ GOOD - Correct variable name with NEXT_PUBLIC_ prefix
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
```

### Token Exchange Issues
```typescript
// ❌ BAD - Invalid token format or expired token
const token = localStorage.getItem('invalid-token')

// ✅ GOOD - Proper token validation and refresh
const token = await supabase.auth.getSession()
```

## Next Steps for Investigation Agent

1. **Review Authentication Flow**: Analyze authentication request payloads and token exchange
2. **Check Supabase Configuration**: Verify API key permissions and JWT settings
3. **Test Authentication Endpoints**: Use curl/Postman to test Supabase auth endpoints
4. **Implement Detailed Logging**: Add logging around authentication process
5. **Use Supabase Log Explorer**: Investigate authentication errors in Supabase dashboard

## Handoff Information

### Current Branch
- `fix-vercel-deployment-fm032` (contains working Vercel configuration)

### Key Files Modified
- `ui/vercel.json` (moved from root, updated build commands)
- `ui/.vercelignore` (created with minimal exclusions)

### Environment Status
- Vercel deployment: ✅ Working
- Preview environment: ✅ Accessible
- Authentication: ❌ 400 Bad Request errors

### Investigation Priority
1. **HIGH**: Review authentication request payloads and token exchange
2. **HIGH**: Verify Supabase API key permissions and JWT configuration
3. **MEDIUM**: Check environment variable configuration
4. **MEDIUM**: Implement detailed logging for authentication process

---

**Handoff**: Investigation agent should focus on Supabase authentication 400 errors while maintaining the working Vercel deployment configuration.
