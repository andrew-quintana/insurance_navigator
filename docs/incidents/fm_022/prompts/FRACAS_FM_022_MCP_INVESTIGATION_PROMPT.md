# FRACAS FM-022 MCP Investigation Prompt

## 🎯 **INVESTIGATION OBJECTIVE**

Continue the investigation of FM-022 (Upload 500 Authentication Error) using MCP tools across the full stack. The error persists despite multiple fixes, and we now have access to Vercel and Supabase MCPs for comprehensive debugging.

## 📋 **CURRENT STATUS**

**Incident**: FM-022 - Upload 500 Authentication Error  
**Status**: 🔄 **PERSISTENT - MCP INVESTIGATION REQUIRED**  
**Environment**: Staging (Vercel Frontend + Render API)  
**Priority**: P1 - High  

## 🚨 **ERROR PATTERN**

```
[Log] Auth state changed: – "SIGNED_IN" – "sendaqmail@gmail.com"
[Error] Failed to load resource: the server responded with a status of 500 () (upload, line 0)
[Error] Upload error: – Error: Upload failed (Status: 500) - {"detail":"Failed to process upload request"}
```

## 🔍 **INVESTIGATION TASKS**

### **Phase 1: Service Status Verification**
1. **Check Render Services**:
   - Verify staging API service status and latest deployment
   - Check staging worker service status and latest deployment
   - Identify if services need manual redeployment

2. **Check Vercel Deployment**:
   - Verify frontend deployment status
   - Check environment variables in Vercel
   - Verify API endpoint configuration

3. **Check Supabase Configuration**:
   - Verify staging database connection
   - Check RLS policies for upload_pipeline schema
   - Verify JWT secret configuration

### **Phase 2: Authentication Flow Analysis**
1. **JWT Token Analysis**:
   - Compare JWT secrets between main API and upload pipeline
   - Verify token validation logic in upload pipeline
   - Check token expiration and format

2. **Environment Variable Verification**:
   - Verify all required environment variables are set in Render
   - Check environment variable loading in upload pipeline
   - Verify staging environment configuration

3. **Database Access Analysis**:
   - Check if upload pipeline can access Supabase
   - Verify RLS policies allow upload operations
   - Check database connection configuration

### **Phase 3: End-to-End Testing**
1. **Frontend to API Communication**:
   - Test API health endpoint
   - Test upload-test endpoint
   - Test full upload flow with valid JWT

2. **Authentication Integration**:
   - Verify JWT token generation in frontend
   - Test token validation in upload pipeline
   - Check error handling and logging

## 🛠️ **MCP TOOLS AVAILABLE**

### **Render MCP Tools**
- `mcp_render_list_services` - Check service status
- `mcp_render_get_service` - Get service details
- `mcp_render_list_deploys` - Check deployment history
- `mcp_render_get_logs` - Get service logs
- `mcp_render_update_environment_variables` - Update env vars

### **Supabase MCP Tools**
- `mcp_supabase_staging_list_tables` - Check database schema
- `mcp_supabase_staging_execute_sql` - Run database queries
- `mcp_supabase_staging_get_logs` - Check Supabase logs
- `mcp_supabase_staging_get_advisors` - Check for issues

### **Vercel MCP Tools**
- `mcp_vercel_list_deployments` - Check frontend deployments
- `mcp_vercel_get_deployment` - Get deployment details
- `mcp_vercel_get_environment_variables` - Check env vars

## 📊 **EXPECTED FINDINGS**

### **Likely Root Causes**
1. **Service Deployment Issue**: Staging services not running latest code
2. **JWT Secret Mismatch**: Different JWT secrets between services
3. **Environment Variable Issue**: Missing or incorrect environment variables
4. **Database Access Issue**: RLS policies blocking upload operations
5. **Configuration Issue**: Incorrect API endpoint or authentication setup

### **Success Criteria**
- [ ] Identify specific root cause of persistent 500 error
- [ ] Verify all services are running latest code
- [ ] Confirm JWT token validation is working
- [ ] Validate complete authentication flow
- [ ] Document specific fix required

## 🔧 **INVESTIGATION STEPS**

### **Step 1: Service Status Check**
```bash
# Check Render services
mcp_render_list_services
mcp_render_get_service --service-id <staging-api-id>
mcp_render_list_deploys --service-id <staging-api-id>

# Check Vercel deployment
mcp_vercel_list_deployments
mcp_vercel_get_deployment --deployment-id <latest-deployment>
```

### **Step 2: Environment Verification**
```bash
# Check Supabase configuration
mcp_supabase_staging_list_tables
mcp_supabase_staging_execute_sql --query "SELECT * FROM upload_pipeline.upload_jobs LIMIT 1"

# Check Vercel environment variables
mcp_vercel_get_environment_variables
```

### **Step 3: Log Analysis**
```bash
# Get Render logs
mcp_render_get_logs --resource <staging-api-id>

# Get Supabase logs
mcp_supabase_staging_get_logs --service api
```

### **Step 4: Testing**
```bash
# Test API health
curl -f https://insurance-navigator-staging-api.onrender.com/health

# Test upload endpoint
curl -X POST https://insurance-navigator-staging-api.onrender.com/api/upload-pipeline/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <valid-jwt-token>" \
  -d '{"filename":"test.pdf","bytes_len":1000,"mime":"application/pdf","sha256":"test","ocr":false}'
```

## 📝 **DOCUMENTATION REQUIREMENTS**

### **Investigation Report**
1. **Service Status**: Current deployment status of all services
2. **Environment Variables**: Verification of all required environment variables
3. **JWT Configuration**: Analysis of JWT secret configuration
4. **Database Access**: Verification of database connectivity and permissions
5. **Error Analysis**: Detailed analysis of error logs and patterns
6. **Root Cause**: Specific identification of the root cause
7. **Fix Required**: Specific steps needed to resolve the issue

### **Update FRACAS Document**
- Update `docs/incidents/fm_022/docs/FRACAS_FM_022_UPLOAD_500_AUTHENTICATION_ERROR.md`
- Add MCP investigation findings
- Update status and next steps
- Document any new root causes identified

## 🎯 **SUCCESS CRITERIA**

The investigation is complete when:
1. ✅ **Root Cause Identified**: Specific cause of persistent 500 error
2. ✅ **Services Verified**: All services running latest code with correct configuration
3. ✅ **Authentication Working**: JWT token validation working end-to-end
4. ✅ **Upload Functional**: Upload endpoint working with valid authentication
5. ✅ **Documentation Updated**: FRACAS document updated with findings and resolution

## 🚀 **READY TO BEGIN**

You have access to all necessary MCP tools and the investigation framework. Begin with Phase 1 (Service Status Verification) and work through each phase systematically. Document all findings and update the FRACAS document as you progress.

**Investigation Start Time**: 2025-09-30  
**Expected Duration**: 2-4 hours  
**Priority**: P1 - High  
**Environment**: Staging  

---

**Investigation Prompt Status**: ✅ **READY FOR EXECUTION**  
**Last Updated**: 2025-09-30  
**Scope**: FM-022 MCP Full-Stack Investigation  
**Tools Available**: Render, Supabase, Vercel MCPs
