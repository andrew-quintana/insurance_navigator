# FM-033 Supabase Authentication 400 Errors

## Incident Overview

**FRACAS ID**: FM-033  
**Date**: January 3, 2025  
**Status**: ✅ **RESOLVED**  
**Priority**: HIGH  
**Environment**: Vercel Production Deployment  

## Problem Summary

Supabase authentication was failing with 400 Bad Request errors in the Vercel deployment. While the Vercel deployment itself was successful, users could not authenticate due to incorrect Supabase configuration.

## Root Cause

Incorrect Supabase URL and API key configuration in Vercel deployment:
- **Wrong URL**: `https://your-staging-project.supabase.co`
- **Correct URL**: `https://your-project.supabase.co`
- **Configuration Issue**: Vercel configuration pointed to wrong Supabase instance

## Resolution

Updated `ui/vercel.json` with correct Supabase configuration:
```json
{
  "build": {
    "env": {
      "NEXT_PUBLIC_SUPABASE_URL": "https://your-project.supabase.co",
      "NEXT_PUBLIC_SUPABASE_ANON_KEY": "[correct production key]"
    }
  }
}
```

## Files in this Directory

- `api-connectivity-400-auth-errors-fm033.md` - Initial investigation report
- `vercel-deployment-success-fm032.md` - Related Vercel deployment success (FM-032)
- `fm033-resolution-summary.md` - Resolution summary
- `fm033-supabase-auth-resolution.md` - Comprehensive resolution report

## Impact

- **Before**: Authentication completely broken with 400 errors
- **After**: Authentication working correctly, users can sign in successfully

## Related Incidents

- **FM-032**: Vercel deployment failure (RESOLVED)
- **FM-033**: Supabase authentication 400 errors (THIS INCIDENT)

## Lessons Learned

1. **Configuration Management**: Ensure environment-specific values are correctly configured
2. **Instance Verification**: Verify Supabase instance URLs match between environments
3. **Testing**: Test authentication in staging before production deployment
4. **Documentation**: Maintain clear documentation of correct configuration values
