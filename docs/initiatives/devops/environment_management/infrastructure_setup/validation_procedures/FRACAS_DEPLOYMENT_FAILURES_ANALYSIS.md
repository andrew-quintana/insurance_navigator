# FRACAS: Production and Staging Deployment Failures

**Date**: September 21, 2025  
**Status**: 🔴 **CRITICAL - DEPLOYMENT FAILURES**  
**Priority**: **P0 - IMMEDIATE ATTENTION REQUIRED**  

## 🚨 **Failure Summary**

### **Production Environment Failure**
- **Issue**: Wrong port configuration (running on port 10000 instead of 8000)
- **Error**: `Uvicorn running on http://0.0.0.0:10000` → `==> Timed Out`
- **Root Cause**: Environment variable `PORT=10000` in production configuration
- **Impact**: Service timeout, deployment failure

### **Staging Environment Failure**
- **Issue**: Database authentication failure with Supabase pooler
- **Error**: `asyncpg.exceptions._base.InternalClientError: unexpected error while performing authentication: 'NoneType' object has no attribute 'group'`
- **Root Cause**: Supabase pooler URL authentication incompatibility
- **Impact**: Complete service startup failure, database connection impossible

## 🔍 **Detailed Analysis**

### **Production Port Issue**
```
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
==> Timed Out
```
- **Problem**: Production service configured to run on port 10000
- **Expected**: Should run on port 8000 for Render deployment
- **Configuration**: Environment variable `PORT=10000` is incorrect

### **Staging Database Authentication Issue**
```
2025-09-21T01:59:16,967 - api.upload_pipeline.database - ERROR - Failed to initialize database connection pool
asyncpg.exceptions._base.InternalClientError: unexpected error while performing authentication: 'NoneType' object has no attribute 'group'
```
- **Problem**: Supabase pooler URL authentication failing
- **URL**: `postgresql://postgres.your-staging-project:tukwof-...@aws-0-us-west-1.pooler.supabase.com:6543/postgres`
- **Error**: SCRAM authentication protocol failure
- **Impact**: Complete system initialization failure

## 🎯 **Root Cause Analysis**

### **1. Production Port Misconfiguration**
- **Source**: Environment variable `PORT=10000` in production environment
- **Expected**: `PORT=8000` for Render deployment
- **Fix**: Update production environment variables

### **2. Staging Database Connection Issue**
- **Source**: Supabase pooler URL authentication incompatibility
- **Alternative**: Use direct database URL instead of pooler
- **Fix**: Switch to direct database connection for staging

## 📋 **Immediate Actions Required**

### **Phase 1: Investigation and Local Testing**
1. **Environment Variable Audit**
   - Check all environment files for port configurations
   - Verify production vs staging environment differences
   - Document current configuration state

2. **Database Connection Testing**
   - Test direct database connection vs pooler connection
   - Verify Supabase credentials and URLs
   - Test connection locally with both methods

3. **Configuration Isolation**
   - Ensure production and staging configs are properly isolated
   - Verify environment-specific settings are correct
   - Test configuration loading mechanisms

### **Phase 2: Local Validation**
1. **Port Configuration Testing**
   - Test production configuration locally with correct port
   - Verify Render deployment requirements
   - Test staging configuration locally

2. **Database Connection Validation**
   - Test both direct and pooler connections locally
   - Verify Supabase credentials work correctly
   - Test connection pooling and authentication

### **Phase 3: Deployment Preparation**
1. **Code Changes** (apply to both environments)
   - Fix any code issues identified during testing
   - Ensure consistent behavior across environments

2. **Environment Configuration** (isolate per environment)
   - Update production port configuration
   - Update staging database connection method
   - Verify all environment-specific settings

## 🚀 **FRACAS Resolution Prompt**

```
## FRACAS: Production and Staging Deployment Failures

### **CRITICAL DEPLOYMENT FAILURES IDENTIFIED**

**Production Issue**: Wrong port (10000 vs 8000) causing timeout
**Staging Issue**: Database authentication failure with Supabase pooler

### **INVESTIGATION REQUIREMENTS**

1. **Environment Configuration Audit**
   - Read and analyze all environment files (.env.production, .env.staging, .env.development)
   - Document current port configurations
   - Document current database connection configurations
   - Identify differences between environments

2. **Database Connection Testing**
   - Test direct Supabase database connection locally
   - Test Supabase pooler connection locally
   - Verify authentication credentials work
   - Test both connection methods with staging Supabase instance
   - Test both connection methods with production Supabase instance

3. **Port Configuration Testing**
   - Test production configuration locally with PORT=8000
   - Test staging configuration locally with correct port
   - Verify Render deployment port requirements
   - Test service startup with different port configurations

4. **Code Analysis**
   - Review database connection code in core/database.py
   - Review upload pipeline database code in api/upload_pipeline/database.py
   - Check for hardcoded port references
   - Verify environment variable loading mechanisms

5. **Local Validation**
   - Run production configuration locally and test all endpoints
   - Run staging configuration locally and test all endpoints
   - Verify database connectivity in both configurations
   - Test complete application startup and shutdown

### **RESOLUTION STRATEGY**

1. **Code Changes** (apply to both environments)
   - Fix any identified code issues
   - Ensure consistent behavior across environments
   - Update database connection handling if needed

2. **Environment Configuration** (isolate per environment)
   - Fix production port configuration (PORT=8000)
   - Fix staging database connection (use direct URL instead of pooler)
   - Verify all environment-specific settings are correct

3. **Deployment Process**
   - Test changes locally first
   - Deploy to staging and verify functionality
   - Deploy to production and verify functionality
   - Monitor both environments for stability

### **SUCCESS CRITERIA**

- Production service runs on port 8000 and responds to health checks
- Staging service connects to database successfully and responds to health checks
- Both environments pass complete end-to-end testing
- No timeout or authentication errors in deployment logs
- All API endpoints functional in both environments

### **TESTING REQUIREMENTS**

- Local testing with both configurations
- Complete endpoint testing (health, auth, upload, chat)
- Database connectivity verification
- Service startup and shutdown testing
- Environment variable validation

**PRIORITY**: P0 - IMMEDIATE ATTENTION REQUIRED
**ESTIMATED TIME**: 2-4 hours for investigation and resolution
**RISK LEVEL**: HIGH - Both production and staging are down
```

## 📊 **Failure Impact Assessment**

| Environment | Status | Impact | Priority |
|-------------|--------|--------|----------|
| **Production** | 🔴 **DOWN** | Service timeout, no API access | **P0** |
| **Staging** | 🔴 **DOWN** | Database auth failure, no service | **P0** |
| **Development** | ✅ **UP** | Local testing possible | **P1** |

## 🎯 **Next Steps**

1. **Immediate**: Execute FRACAS investigation prompt
2. **Short-term**: Fix identified configuration issues
3. **Medium-term**: Implement better environment isolation
4. **Long-term**: Add deployment validation checks

**Status**: 🔴 **CRITICAL - REQUIRES IMMEDIATE ATTENTION**
