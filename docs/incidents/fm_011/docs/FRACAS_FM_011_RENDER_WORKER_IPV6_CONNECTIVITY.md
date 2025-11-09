# FRACAS FM-011: Render Worker IPv6 Connectivity Issue

## Incident Summary
**Date:** 2025-09-25  
**Severity:** CRITICAL  
**Status:** INVESTIGATION IN PROGRESS  
**Component:** Staging Worker Service (Render)  
**Issue:** Worker service fails to connect to Supabase database with "Network is unreachable" error

## Problem Description
The staging worker service deployed on Render is experiencing persistent connection failures to the Supabase database. The error manifests as:

```
OSError: [Errno 101] Network is unreachable
```

This occurs during worker initialization when attempting to create a database connection pool.

## Root Cause Analysis

### Primary Issue
**IPv6 Connectivity Problem**: Render's network environment has IPv6 connectivity issues when connecting to Supabase's direct database endpoints. Supabase provides IPv6 addresses for direct connections, but Render's infrastructure cannot reach these addresses.

### Contributing Factors
1. **Build Filter Limitation**: The worker service has a build filter that only includes specific paths (`backend/workers/**`, `backend/shared/**`, `config/render/**`, `requirements.txt`, `pyproject.toml`). The `core/` directory is excluded, preventing database configuration changes from being deployed.

2. **Missing Pooler URL Usage**: The worker was not configured to use Supabase's pooler URLs, which provide IPv4 connectivity and bypass IPv6 issues.

3. **Environment Variable Detection**: The cloud deployment detection logic was not properly identifying the Render environment.

## Investigation Steps Taken

### 1. Initial Diagnosis
- Identified that worker service was using direct `DATABASE_URL` instead of pooler URLs
- Confirmed that `SUPABASE_SESSION_POOLER_URL` and `SUPABASE_POOLER_URL` are available in environment variables
- Verified that the issue is specific to Render's network environment

### 2. Database Configuration Fix
- Modified `core/database.py` to prioritize pooler URLs for cloud deployments
- Added comprehensive debugging logs to track URL selection
- Implemented cloud deployment detection logic

### 3. Build Filter Workaround
- Discovered that `core/` directory changes don't trigger worker deployments
- Created `backend/workers/database_config.py` with pooler URL logic
- Updated `enhanced_base_worker.py` to use local database configuration

### 4. Deployment Verification
- Committed and pushed changes to staging branch
- Triggered worker service redeployment
- Added debugging logs to verify pooler URL usage

## Technical Details

### Environment Variables Available
```
SUPABASE_SESSION_POOLER_URL: postgresql://postgres:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
SUPABASE_POOLER_URL: postgresql://postgres:[password]@aws-0-us-west-1.pooler.supabase.com:5432/postgres
DATABASE_URL: postgresql://postgres:[password]@db.your-staging-project.supabase.co:5432/postgres
```

### Error Pattern
```
File "/app/backend/workers/../../core/database.py", line 80, in initialize
    self.pool = await create_pool(
OSError: [Errno 101] Network is unreachable
```

### Solution Implemented
1. **Pooler URL Priority**: Modified database configuration to use pooler URLs for cloud deployments
2. **Worker-Specific Config**: Created local database configuration in worker directory
3. **Debugging Logs**: Added comprehensive logging to track URL selection process

## Current Status
- **Deployment**: New worker deployment in progress (started 2025-09-25T02:27:11Z)
- **Expected Resolution**: Worker should now use pooler URL and avoid IPv6 connectivity issues
- **Verification Needed**: Check logs for debugging information confirming pooler URL usage

## Next Steps
1. **Verify Deployment**: Check latest worker logs for debugging information
2. **Confirm Pooler Usage**: Ensure worker is using `SUPABASE_SESSION_POOLER_URL` or `SUPABASE_POOLER_URL`
3. **Test Connectivity**: Verify worker can successfully connect to database
4. **Update Build Filter**: Consider updating worker service build filter to include `core/` directory
5. **Documentation**: Update deployment documentation with pooler URL requirements

## Prevention Measures
1. **Build Filter Review**: Audit all service build filters to ensure critical directories are included
2. **Pooler URL Standard**: Make pooler URL usage standard for all cloud deployments
3. **Connectivity Testing**: Add IPv6 connectivity tests to deployment pipeline
4. **Environment Validation**: Enhance environment variable validation for cloud deployments

## Related Issues
- **FRACAS FM-010**: LlamaParse Invalid Token Format (resolved)
- **FRACAS FM-009**: LlamaParse Invalid Token Format (resolved)

## Files Modified
- `core/database.py` - Added pooler URL support and debugging
- `backend/workers/database_config.py` - Created worker-specific database configuration
- `backend/workers/enhanced_base_worker.py` - Updated to use local database config

## Environment
- **Platform**: Render
- **Service**: upload-worker-staging
- **Database**: Supabase (staging)
- **Issue Type**: Network connectivity (IPv6)
