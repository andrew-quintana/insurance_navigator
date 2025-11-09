# Staging Worker IPv6 Connectivity Fix - Continuation Prompt

## Context
The staging worker service on Render is experiencing persistent database connectivity issues due to IPv6 connectivity problems. A fix has been implemented but needs verification and completion.

## Current Status
- **Issue**: Worker service fails with "Network is unreachable" error when connecting to Supabase database
- **Root Cause**: Render's network environment cannot reach Supabase's IPv6 addresses
- **Solution Implemented**: Modified database configuration to use Supabase pooler URLs (IPv4)
- **Deployment**: New worker deployment in progress (started 2025-09-25T02:27:11Z)

## Files Modified
1. `core/database.py` - Added pooler URL support and debugging logs
2. `backend/workers/database_config.py` - Created worker-specific database configuration
3. `backend/workers/enhanced_base_worker.py` - Updated to use local database config

## Immediate Tasks

### 1. Verify Deployment Status
```bash
# Check if worker deployment completed
# Look for logs showing the debugging information:
# - "Database config creation - Cloud deployment: True"
# - "Using Supabase pooler URL for cloud deployment"
# - "DEBUG: Using worker-specific database config with pooler URL support"
```

### 2. Check Worker Logs
Use Render MCP tools to check latest worker logs:
- Look for debugging logs from the new database configuration
- Verify that pooler URL is being used instead of direct DATABASE_URL
- Confirm worker can successfully connect to database

### 3. Test Worker Functionality
If worker is running successfully:
- Test document upload functionality
- Verify worker can process jobs
- Check that database operations work correctly

## Expected Debugging Logs
The worker should now show these logs:
```
Database config creation - Cloud deployment: True
RENDER env var: true
SUPABASE_SESSION_POOLER_URL available: True
SUPABASE_POOLER_URL available: True
DEBUG: Using worker-specific database config with pooler URL support
Using Supabase pooler URL for cloud deployment: postgresql://postgres:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres...
```

## If Issue Persists

### Check Environment Variables
Verify these environment variables are set in Render:
- `SUPABASE_SESSION_POOLER_URL`
- `SUPABASE_POOLER_URL`
- `RENDER` (should be set automatically)

### Alternative Solutions
1. **Update Build Filter**: Modify worker service build filter to include `core/` directory
2. **Manual Pooler URL**: Hardcode pooler URL in worker configuration
3. **Network Configuration**: Check if Render service needs specific network settings

## Success Criteria
- [ ] Worker service starts successfully without "Network is unreachable" error
- [ ] Debugging logs show pooler URL usage
- [ ] Worker can process jobs and connect to database
- [ ] Document upload pipeline works end-to-end

## Next Steps After Fix
1. **Update Documentation**: Document pooler URL requirements for cloud deployments
2. **Build Filter Review**: Audit all service build filters
3. **Production Deployment**: Apply same fix to production worker service
4. **Monitoring**: Add alerts for database connectivity issues

## Technical Details
- **Service ID**: srv-d37dlmvfte5s73b6uq0g
- **Environment**: staging
- **Database**: Supabase (staging)
- **Issue**: IPv6 connectivity from Render to Supabase
- **Solution**: Use Supabase pooler URLs (IPv4)

## Commands to Run
```bash
# Check latest worker logs
# Use Render MCP tools to get logs from service srv-d37dlmvfte5s73b6uq0g

# If worker is running, test API endpoints
curl -X GET https://insurance-navigator-staging-api.onrender.com/health

# Test document upload (if worker is working)
# Upload a test document and verify processing
```

## Files to Check
- `backend/workers/database_config.py` - Worker-specific database configuration
- `backend/workers/enhanced_base_worker.py` - Updated worker implementation
- `core/database.py` - Main database configuration with pooler support

## Expected Resolution Time
- **Immediate**: 5-10 minutes to verify deployment and logs
- **If successful**: Worker should be fully functional
- **If issues persist**: Additional investigation needed (30-60 minutes)

## Contact Information
- **FRACAS Reference**: FM-011
- **Related Issues**: IPv6 connectivity, Supabase pooler URLs
- **Priority**: CRITICAL (blocking staging environment)
