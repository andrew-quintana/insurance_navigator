# FRACAS FM-020: Persistent SCRAM Authentication Failure in Cloud Deployments

## Incident Summary
**Date:** 2025-09-26  
**Severity:** CRITICAL  
**Status:** INVESTIGATION IN PROGRESS  
**Component:** API Service (Render)  
**Issue:** Persistent SCRAM authentication failure preventing API service startup  
**Last Working Commit:** 0982fb1 (2025-09-24)

## Problem Description
The API service deployed on Render continues to fail during startup with a persistent SCRAM authentication error:

```
asyncpg.exceptions._base.InternalClientError: unexpected error while performing authentication: 'NoneType' object has no attribute 'group'
```

This error occurs during database connection pool initialization when attempting to connect to Supabase's pooler service.

## Root Cause Analysis

### Primary Issue
**SCRAM Authentication Protocol Failure**: The asyncpg library is experiencing a failure in the SCRAM authentication process when connecting to Supabase's pooler service. The error `'NoneType' object has no attribute 'group'` indicates a null pointer exception in the SCRAM authentication verification process.

### Contributing Factors
1. **IPv6 Connectivity Issues**: Related to FRACAS FM-011, Render's network environment has IPv6 connectivity problems with Supabase's direct database endpoints
2. **Pooler URL Configuration**: Recent changes to use Supabase pooler URLs may have introduced authentication compatibility issues
3. **SSL/TLS Configuration**: Changes in SSL configuration for cloud deployments may be affecting authentication handshake
4. **Environment Variable Changes**: Multiple changes to environment variable loading and database configuration

## Investigation History

### Phase 1: Initial IPv6 Fix Attempt (Commit 7851f73)
- **Approach**: Force IPv4 resolution for Supabase pooler connections
- **Implementation**: Resolve hostname to IPv4 address to avoid IPv6 connectivity issues
- **Result**: IPv4 resolution successful but SCRAM authentication still failed
- **Log Evidence**: `Resolved aws-0-us-west-1.pooler.supabase.com to IPv4: 52.8.172.168`

### Phase 2: Session Pooler Attempt (Commit df35463)
- **Approach**: Use SUPABASE_SESSION_POOLER_URL (port 6543) instead of regular pooler (port 5432)
- **Implementation**: Try session pooler first, fallback to regular pooler with connection parameters
- **Result**: Still experiencing SCRAM authentication failure
- **Log Evidence**: `Using Supabase pooler with SCRAM authentication workaround`

### Phase 3: Connection Parameter Approach
- **Approach**: Use individual connection parameters instead of connection strings
- **Implementation**: Separate host, port, database, user, password parameters
- **Result**: No improvement in SCRAM authentication failure

## Code Analysis: Working vs. Broken

### Last Working Commit (0982fb1)
```python
# Simple, direct approach
self.pool = await create_pool(
    self.config.connection_string,
    min_size=self.config.min_connections,
    max_size=self.config.max_connections,
    command_timeout=self.config.command_timeout,
    statement_cache_size=0,
    ssl=ssl_config,
    setup=self._setup_connection
)
```

### Current Broken State
```python
# Complex conditional logic with multiple fallbacks
if self._is_cloud_deployment() and "pooler.supabase.com" in self.config.host:
    # Try session pooler URL first
    # Fallback to regular pooler with connection parameters
    # Multiple exception handling layers
else:
    # Standard connection string approach
```

## Key Differences Analysis

### 1. Database Configuration Changes
- **Working**: Used `DATABASE_URL` directly
- **Broken**: Complex pooler URL selection logic with cloud deployment detection
- **Impact**: May be selecting incompatible connection URLs

### 2. Connection Method Changes
- **Working**: Simple `create_pool()` with connection string
- **Broken**: Conditional logic with individual parameters vs connection strings
- **Impact**: Different connection establishment methods may affect authentication

### 3. SSL Configuration Changes
- **Working**: Dynamic SSL config based on connection type
- **Broken**: Hardcoded `ssl="require"` for pooler connections
- **Impact**: SSL configuration may be incompatible with pooler authentication

### 4. Environment Variable Loading
- **Working**: Direct environment variable access
- **Broken**: Complex environment loader with cloud detection
- **Impact**: May be loading incorrect or incompatible environment variables

## Suspected Root Causes

### 1. Pooler URL Incompatibility
The switch from direct `DATABASE_URL` to pooler URLs may have introduced authentication incompatibilities:
- Pooler URLs may require different authentication methods
- SCRAM authentication may not be fully supported by pooler service
- Connection string parsing may be incorrect for pooler URLs

### 2. SSL/TLS Handshake Issues
The hardcoded `ssl="require"` configuration may be causing authentication handshake problems:
- Pooler service may require different SSL configuration
- SCRAM authentication over SSL may have compatibility issues
- Certificate validation may be failing

### 3. Environment Variable Corruption
Complex environment loading may be causing variable corruption:
- Pooler URLs may be malformed or incomplete
- Authentication credentials may be incorrect
- Cloud deployment detection may be selecting wrong configuration

## Recommended Investigation Steps

### 1. Revert to Working Configuration
- Temporarily revert to commit 0982fb1 configuration
- Verify that API service starts successfully
- Confirm that the issue is introduced by recent changes

### 2. Gradual Reintroduction of Changes
- Reintroduce changes one at a time to identify the specific cause
- Test each change individually to isolate the problematic modification
- Document which specific change causes the failure

### 3. Pooler URL Validation
- Verify that pooler URLs are correctly formatted and accessible
- Test pooler URLs independently of the application
- Confirm that pooler URLs support the required authentication methods

### 4. SSL Configuration Testing
- Test different SSL configurations with pooler URLs
- Verify SSL certificate compatibility
- Test authentication without SSL to isolate SSL-related issues

## Immediate Actions Required

### 1. Emergency Rollback
- Revert to commit 0982fb1 to restore service functionality
- Deploy working configuration to staging environment
- Verify that API service starts successfully

### 2. Root Cause Identification
- Perform detailed analysis of each change since 0982fb1
- Identify the specific modification that introduced the failure
- Document the exact cause of the SCRAM authentication failure

### 3. Fix Implementation
- Implement targeted fix for the identified root cause
- Test fix in isolated environment before deployment
- Ensure fix doesn't introduce other compatibility issues

## Prevention Measures

### 1. Incremental Deployment Strategy
- Implement gradual rollout of database configuration changes
- Test each change in isolation before combining
- Maintain rollback capability for each change

### 2. Authentication Testing
- Add comprehensive authentication testing to deployment pipeline
- Test with different database connection methods
- Validate SSL/TLS configuration compatibility

### 3. Environment Validation
- Implement environment variable validation before service startup
- Verify database connectivity before application initialization
- Add health checks for database authentication

## Related Incidents
- **FRACAS FM-011**: IPv6 Connectivity Issue (resolved)
- **FRACAS FM-017**: JWT Authentication Failure (resolved)
- **FRACAS FM-018**: User Table Synchronization Failure (resolved)

## Files Modified Since Last Working State
- `core/database.py` - Major database configuration changes
- `config/database.py` - Database configuration updates
- `config/environment_loader.py` - New environment loading system
- `main.py` - Environment loading integration
- Multiple authentication and database service files

## Environment
- **Platform**: Render
- **Service**: insurance-navigator-staging-api
- **Database**: Supabase (staging)
- **Issue Type**: SCRAM Authentication Protocol Failure
- **Last Working**: 2025-09-24 (commit 0982fb1)

## Next Steps
1. **Emergency Rollback**: Revert to commit 0982fb1 to restore service
2. **Root Cause Analysis**: Identify specific change causing failure
3. **Targeted Fix**: Implement fix for identified root cause
4. **Testing**: Comprehensive testing before re-deployment
5. **Documentation**: Update deployment procedures to prevent recurrence

---

**Status**: CRITICAL - Service Down  
**Priority**: P0 - Immediate Action Required  
**Assigned**: Development Team  
**Due Date**: 2025-09-26 EOD
