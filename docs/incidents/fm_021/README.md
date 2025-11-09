# FRACAS FM-021: Frontend Authentication Token Storage Mismatch

## Incident Summary
**Date:** 2025-09-26  
**Severity:** HIGH  
**Status:** ✅ **RESOLVED**  
**Component:** Frontend (Next.js)  
**Issue:** Token storage key mismatch causing upload authentication failures  
**Root Cause:** Inconsistent token storage keys between auth helpers and API client

## Problem Description
Users experienced repeated "Authentication required. Please log in again." errors during file uploads, despite being successfully authenticated. The issue was caused by a token storage key mismatch between different frontend components.

## Root Cause Analysis
**Token Storage Key Mismatch**:
- `auth-helpers.ts`: Stores tokens as `'token'` or `'supabase.auth.token'`
- `api-client.ts`: Was looking for tokens as `'auth-token'`
- Result: API client couldn't find authentication tokens, causing upload failures

## Resolution
**Fix Applied**: Updated `api-client.ts` to check correct token storage keys:
- `localStorage.getItem('token')`
- `localStorage.getItem('supabase.auth.token')`
- `sessionStorage.getItem('token')`
- `sessionStorage.getItem('supabase.auth.token')`

## Prevention Measures
1. **Centralized Token Management**: Use consistent token storage keys across all components
2. **Code Review**: Ensure token handling consistency in frontend components
3. **Testing**: Test authentication flow end-to-end including upload operations

## Files Modified
- `ui/lib/api-client.ts`: Fixed token storage key lookup
- `ui/test-token-fix.js`: Added test script for verification

## Status
✅ **RESOLVED** - Token storage mismatch fixed, upload authentication working



