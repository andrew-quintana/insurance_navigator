# Vercel WebSocket & API Configuration Fix Guide

This guide addresses the WebSocket disconnection issues and API URL mismatches seen in the Safari browser logs.

## Issues Identified

1. **WebSocket URL Misconfiguration**: WebSocket connections were pointing to frontend domain instead of backend API
2. **API URL Inconsistency**: Multiple different API URLs being used across components  
3. **Environment Variable Conflicts**: Vercel environment variables may be overriding local settings

## Required Fixes

### 1. Update Vercel Environment Variables

In your Vercel dashboard, ensure these environment variables are set correctly:

**Production Environment:**
```bash
NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-api.onrender.com
NEXT_PUBLIC_API_VERSION=v1
NODE_ENV=production
```

**Preview/Development Environment:**
```bash
NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-api.onrender.com
NEXT_PUBLIC_API_VERSION=v1
NODE_ENV=development
```

### 2. Remove Conflicting URLs

Make sure you don't have these environment variables set in Vercel (they can cause conflicts):
- `NEXT_PUBLIC_API_URL` (use `NEXT_PUBLIC_API_BASE_URL` instead)
- Any hardcoded URLs to `insurpi.onrender.com`

### 3. Update Vercel Configuration

Update your `vercel.json` to use the correct environment variable:

```json
{
  "version": 2,
  "framework": "nextjs",
  "regions": ["iad1"],
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://insurance-navigator-api.onrender.com/api/$1"
    }
  ]
}
```

### 4. Code Changes Applied

The following code changes have been made to fix the issues:

1. **Created centralized API configuration** (`ui/lib/api-config.ts`)
   - Single source of truth for all API URLs
   - Proper WebSocket URL construction
   - Environment-aware configuration

2. **Updated WebSocket connection** (`ui/lib/useWorkflowStatus.ts`)
   - Now correctly points to backend API domain
   - Uses centralized configuration
   - Proper protocol handling (ws/wss)

3. **Fixed hardcoded URLs** 
   - Removed hardcoded fallback URLs in components
   - All components now use centralized configuration

### 5. Verification Steps

After deploying these changes:

1. **Check browser console** for these debug logs:
   ```
   🔧 API Configuration Debug Info:
   API Base URL: https://insurance-navigator-api.onrender.com
   WebSocket Base URL: wss://insurance-navigator-api.onrender.com
   ```

2. **Verify WebSocket connections** point to the correct backend:
   ```
   WebSocket URL should be: wss://insurance-navigator-api.onrender.com/ws/workflow/...
   NOT: wss://your-frontend-app.vercel.app/ws/workflow/...
   ```

3. **Test API calls** ensure they go to the correct endpoint:
   ```
   API calls should go to: https://insurance-navigator-api.onrender.com/api/...
   ```

### 6. Common Issues & Solutions

**Issue: Still seeing WebSocket disconnections**
- Check that your backend API actually supports WebSocket connections at `/ws/workflow/`
- Verify the backend is running and accessible
- Check Render logs for connection errors

**Issue: API URL still inconsistent**
- Clear browser cache
- Redeploy the Vercel application
- Check Vercel build logs for environment variable values

**Issue: Environment variables not taking effect**
- Environment variables in Vercel override local `.env` files
- Make sure to set them in the correct environment (Production/Preview/Development)
- Redeploy after changing environment variables

### 7. Backend Requirements

Ensure your backend API supports:
- WebSocket endpoint: `/ws/workflow/{workflow_id}?user_id={user_id}`
- CORS headers for your frontend domain
- Proper WebSocket upgrade handling

### 8. Testing the Fix

To test locally before deploying:

1. Set `NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-api.onrender.com` in your local `.env.local`
2. Run `npm run dev`
3. Check browser console for correct API configuration
4. Test WebSocket connections in the chat interface

## Summary

These changes ensure:
- ✅ WebSocket connections point to the correct backend API
- ✅ All API calls use consistent URLs 
- ✅ Environment-specific configuration works properly
- ✅ No more hardcoded URL mismatches
- ✅ Centralized configuration prevents future inconsistencies