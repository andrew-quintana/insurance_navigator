# FRACAS FM-022 Agent Investigation Prompt

## 🎯 **INVESTIGATION MISSION**

You are tasked with continuing the investigation of **FM-022: Upload 500 Authentication Error** using the comprehensive MCP tools now available. This is a persistent issue that has survived multiple fix attempts and requires a full-stack investigation approach.

## 📋 **INCIDENT SUMMARY**

**Incident ID**: FM-022  
**Title**: Upload 500 Authentication Error  
**Status**: 🔄 **PERSISTENT - MCP INVESTIGATION REQUIRED**  
**Priority**: P1 - High  
**Environment**: Staging (Vercel Frontend + Render API)  
**Date**: 2025-09-27 (Initial), 2025-09-30 (Latest Recurrence)  

## 🚨 **CURRENT ERROR PATTERN**

```
[Log] Auth state changed: – "SIGNED_IN" – "sendaqmail@gmail.com"
[Error] Failed to load resource: the server responded with a status of 500 () (upload, line 0)
[Error] Upload error: – Error: Upload failed (Status: 500) - {"detail":"Failed to process upload request"}
```

## 🔍 **INVESTIGATION FRAMEWORK**

### **Phase 1: Service Status & Deployment Analysis**
**Objective**: Verify all services are running latest code and properly configured

**Tasks**:
1. **Render Services Check**:
   - List all services and identify staging services
   - Check deployment status and latest commits
   - Verify environment variables are set correctly
   - Check service logs for errors

2. **Vercel Frontend Check**:
   - Verify frontend deployment status
   - Check environment variables in Vercel
   - Verify API endpoint configuration
   - Check frontend logs for errors

3. **Supabase Database Check**:
   - Verify database connectivity
   - Check RLS policies for upload_pipeline schema
   - Verify JWT secret configuration
   - Check database logs for errors

### **Phase 2: Authentication Flow Deep Dive**
**Objective**: Analyze the complete authentication flow from frontend to database

**Tasks**:
1. **JWT Token Analysis**:
   - Compare JWT secrets between main API and upload pipeline
   - Verify token validation logic in upload pipeline
   - Check token expiration and format
   - Test token validation with different scenarios

2. **Environment Variable Verification**:
   - Verify all required environment variables are set in Render
   - Check environment variable loading in upload pipeline
   - Verify staging environment configuration
   - Test environment variable access

3. **Database Access Analysis**:
   - Check if upload pipeline can access Supabase
   - Verify RLS policies allow upload operations
   - Check database connection configuration
   - Test database queries

### **Phase 3: End-to-End Testing & Validation**
**Objective**: Test the complete flow and identify specific failure points

**Tasks**:
1. **API Health Testing**:
   - Test API health endpoint
   - Test upload-test endpoint
   - Test full upload flow with valid JWT
   - Test error handling scenarios

2. **Authentication Integration Testing**:
   - Verify JWT token generation in frontend
   - Test token validation in upload pipeline
   - Check error handling and logging
   - Test with different user scenarios

## 🛠️ **MCP TOOLS AVAILABLE**

### **Render MCP Tools**
- `mcp_render_list_services` - List all services
- `mcp_render_get_service` - Get specific service details
- `mcp_render_list_deploys` - Check deployment history
- `mcp_render_get_logs` - Get service logs
- `mcp_render_update_environment_variables` - Update environment variables

### **Supabase MCP Tools**
- `mcp_supabase_staging_list_tables` - Check database schema
- `mcp_supabase_staging_execute_sql` - Run database queries
- `mcp_supabase_staging_get_logs` - Check Supabase logs
- `mcp_supabase_staging_get_advisors` - Check for security/performance issues

### **Vercel MCP Tools**
- `mcp_vercel_list_deployments` - Check frontend deployments
- `mcp_vercel_get_deployment` - Get deployment details
- `mcp_vercel_get_environment_variables` - Check environment variables

## 📊 **INVESTIGATION CHECKLIST**

### **Service Status Verification**
- [ ] **Render Services**: All staging services identified and checked
- [ ] **Vercel Frontend**: Frontend deployment status verified
- [ ] **Supabase Database**: Database connectivity confirmed
- [ ] **Environment Variables**: All required variables verified
- [ ] **Service Logs**: Error logs analyzed

### **Authentication Flow Analysis**
- [ ] **JWT Configuration**: JWT secrets compared and verified
- [ ] **Token Validation**: Upload pipeline token validation tested
- [ ] **Database Access**: Upload pipeline database access confirmed
- [ ] **RLS Policies**: Database policies verified
- [ ] **Error Handling**: Error handling logic tested

### **End-to-End Testing**
- [ ] **API Health**: All API endpoints tested
- [ ] **Upload Flow**: Complete upload flow tested
- [ ] **Authentication**: JWT token flow tested
- [ ] **Error Scenarios**: Error handling tested
- [ ] **User Scenarios**: Different user scenarios tested

## 🎯 **EXPECTED OUTCOMES**

### **Root Cause Identification**
The investigation should identify one or more of:
1. **Service Deployment Issue**: Services not running latest code
2. **JWT Secret Mismatch**: Different JWT secrets between services
3. **Environment Variable Issue**: Missing or incorrect environment variables
4. **Database Access Issue**: RLS policies blocking upload operations
5. **Configuration Issue**: Incorrect API endpoint or authentication setup

### **Resolution Plan**
Based on findings, provide:
1. **Specific Root Cause**: Detailed explanation of the issue
2. **Fix Required**: Specific steps to resolve the issue
3. **Testing Plan**: How to validate the fix
4. **Prevention Measures**: How to prevent recurrence

## 📝 **DOCUMENTATION REQUIREMENTS**

### **Investigation Report**
Create a comprehensive report including:
1. **Executive Summary**: High-level findings and recommendations
2. **Service Status**: Current status of all services
3. **Environment Analysis**: Environment variable and configuration analysis
4. **Authentication Flow**: Detailed analysis of authentication flow
5. **Root Cause Analysis**: Specific identification of the root cause
6. **Resolution Plan**: Detailed steps to resolve the issue
7. **Testing Results**: Results of all tests performed

### **FRACAS Document Update**
Update `docs/incidents/fm_022/docs/FRACAS_FM_022_UPLOAD_500_AUTHENTICATION_ERROR.md` with:
- MCP investigation findings
- Updated status and next steps
- New root causes identified
- Resolution plan and timeline

## 🚀 **INVESTIGATION EXECUTION**

### **Step 1: Initial Assessment**
1. Read the current FRACAS document to understand the full context
2. Check service status using Render MCP tools
3. Verify frontend deployment using Vercel MCP tools
4. Check database status using Supabase MCP tools

### **Step 2: Deep Dive Analysis**
1. Analyze authentication flow step by step
2. Test JWT token validation
3. Verify environment variable configuration
4. Check database access and permissions

### **Step 3: Testing & Validation**
1. Perform end-to-end testing
2. Test error scenarios
3. Validate fix implementation
4. Document all findings

### **Step 4: Documentation & Resolution**
1. Update FRACAS document with findings
2. Provide specific resolution plan
3. Document prevention measures
4. Close investigation with resolution

## 🎯 **SUCCESS CRITERIA**

The investigation is complete when:
1. ✅ **Root Cause Identified**: Specific cause of persistent 500 error
2. ✅ **Services Verified**: All services running latest code with correct configuration
3. ✅ **Authentication Working**: JWT token validation working end-to-end
4. ✅ **Upload Functional**: Upload endpoint working with valid authentication
5. ✅ **Documentation Updated**: FRACAS document updated with findings and resolution

## 🚀 **READY TO BEGIN**

You have access to all necessary MCP tools and the investigation framework. Begin with Phase 1 (Service Status & Deployment Analysis) and work through each phase systematically. Document all findings and update the FRACAS document as you progress.

**Investigation Start Time**: 2025-09-30  
**Expected Duration**: 2-4 hours  
**Priority**: P1 - High  
**Environment**: Staging  

---

**Investigation Prompt Status**: ✅ **READY FOR EXECUTION**  
**Last Updated**: 2025-09-30  
**Scope**: FM-022 MCP Full-Stack Investigation  
**Tools Available**: Render, Supabase, Vercel MCPs  
**Investigation Type**: Persistent Issue Resolution
