# API Connectivity 404 Errors - FM033

**Date**: January 2025  
**Incident**: 404 errors when accessing production Supabase and Render API services  
**Status**: 🔍 INVESTIGATION REQUIRED  
**Priority**: HIGH  
**Environment**: Preview deployment (working) but API calls failing  

## Summary

While the Vercel deployment is now working correctly, the application is experiencing 404 errors when attempting to access the production Supabase and Render API services. All environment variables are set to production values, but API connectivity is failing.

## Current Status

### ✅ **Working Components**
- Vercel deployment: ✅ Successful
- Build process: ✅ No module resolution errors
- Preview environment: ✅ Accessible
- Environment variables: ✅ Set to production values

### ❌ **Failing Components**
- Supabase API calls: ❌ 404 errors
- Render API service calls: ❌ 404 errors
- Production API connectivity: ❌ Not accessible

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

### 1. **Hard-coded Values in Code**
- **Investigation Needed**: Search for hard-coded API URLs in the codebase
- **Risk**: Development/staging URLs might be hard-coded instead of using environment variables
- **Files to Check**: All API client files, configuration files, and service files

### 2. **Environment Conflicts**
- **Issue**: Both preview and production environments accessing the same API services
- **Risk**: Rate limiting, shared resources, or authentication conflicts
- **Consideration**: Preview and production might be competing for the same API endpoints

### 3. **API Service Configuration**
- **Supabase**: Check if production Supabase instance is accessible
- **Render API**: Verify Render API service is running and accessible
- **CORS**: Check if CORS is configured for Vercel domains

### 4. **Environment Variable Issues**
- **Build vs Runtime**: Environment variables might not be available at runtime
- **Variable Names**: Check for typos or incorrect variable names
- **Scope**: Ensure variables are set for the correct environment (preview/production)

## Investigation Checklist

### Phase 1: Code Analysis
- [ ] Search for hard-coded API URLs in codebase
- [ ] Verify all API calls use environment variables
- [ ] Check for development/staging URLs in production code
- [ ] Review API client configuration

### Phase 2: Environment Verification
- [ ] Confirm Vercel environment variables are set correctly
- [ ] Test API endpoints directly (curl/Postman)
- [ ] Verify Supabase instance accessibility
- [ ] Check Render API service status

### Phase 3: Configuration Review
- [ ] Review Vercel rewrites configuration
- [ ] Check CORS settings on API services
- [ ] Verify domain allowlists
- [ ] Review authentication/authorization settings

### Phase 4: Conflict Analysis
- [ ] Check if preview/production environments conflict
- [ ] Review rate limiting on API services
- [ ] Verify shared resource access
- [ ] Check for authentication token conflicts

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

### Common Hard-coded Values
```typescript
// ❌ BAD - Hard-coded URLs
const API_URL = 'https://insurance-navigator-staging-api.onrender.com'
const SUPABASE_URL = 'https://dfgzeastcxnoqshgyotp.supabase.co'

// ✅ GOOD - Environment variables
const API_URL = process.env.NEXT_PUBLIC_API_URL
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
```

### Environment Variable Issues
```typescript
// ❌ BAD - Wrong variable name
const API_URL = process.env.API_URL

// ✅ GOOD - Correct variable name
const API_URL = process.env.NEXT_PUBLIC_API_URL
```

## Next Steps for Investigation Agent

1. **Search Codebase**: Look for hard-coded API URLs
2. **Test API Endpoints**: Verify direct API accessibility
3. **Check Environment Variables**: Confirm Vercel configuration
4. **Review Logs**: Check Vercel deployment logs for API errors
5. **Test Connectivity**: Use curl/Postman to test API endpoints

## Handoff Information

### Current Branch
- `fix-vercel-deployment-fm032` (contains working Vercel configuration)

### Key Files Modified
- `ui/vercel.json` (moved from root, updated build commands)
- `ui/.vercelignore` (created with minimal exclusions)

### Environment Status
- Vercel deployment: ✅ Working
- Preview environment: ✅ Accessible
- API connectivity: ❌ 404 errors

### Investigation Priority
1. **HIGH**: Search for hard-coded API URLs
2. **HIGH**: Test direct API endpoint accessibility
3. **MEDIUM**: Check environment variable configuration
4. **MEDIUM**: Review preview/production environment conflicts

---

**Handoff**: Investigation agent should focus on API connectivity issues while maintaining the working Vercel deployment configuration.
