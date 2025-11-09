# FM-030 Investigation Prompt

## 🚨 **CRITICAL STAGING DEPLOYMENT FAILURE INVESTIGATION**

### **Investigation Scope**
You are tasked with investigating a critical deployment failure in the staging environment that has rendered the entire service unavailable. This is a **P0 Critical** incident requiring immediate attention.

### **Service Details**
- **Service ID**: `srv-d3740ijuibrs738mus1g`
- **Service Name**: `api-service-staging`
- **Environment**: Staging
- **URL**: `https://insurance-navigator-staging-api.onrender.com`
- **Status**: **FAILED** - Application startup failure

### **Primary Symptoms**
1. **Database Connection Failure**: `OSError: [Errno 101] Network is unreachable`
2. **Storage Service Failure**: `Document encryption key not configured`
3. **Application Startup Failure**: `RuntimeError: Failed to initialize core services`
4. **Service Unavailability**: Complete service failure with exit code 3

### **Investigation Objectives**

#### **1. Environment Variable Audit (Priority: P0)**
**Objective**: Identify and fix missing environment variables

**Tasks**:
- Access Render Dashboard for staging service
- Compare staging environment variables with local `.env.staging`
- Identify missing critical variables:
  - `DOCUMENT_ENCRYPTION_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DATABASE_URL`
  - `OPENAI_API_KEY`
  - `LLAMAPARSE_API_KEY`
- Test environment variable loading mechanism
- Fix missing variables in Render Dashboard

**Expected Output**: Complete environment variable audit with fixes applied

#### **2. Database Connectivity Analysis (Priority: P0)**
**Objective**: Resolve database connection failures

**Tasks**:
- Test database connectivity from Render staging
- Verify Supabase database host accessibility
- Check database URL format and credentials
- Test alternative connection methods (pooler vs direct)
- Investigate network connectivity issues

**Expected Output**: Database connectivity root cause analysis with resolution

#### **3. Service Initialization Analysis (Priority: P1)**
**Objective**: Fix service initialization failures

**Tasks**:
- Map service initialization sequence in `main.py`
- Identify service dependencies and initialization order
- Test individual service initialization
- Fix service initialization issues
- Implement proper error handling

**Expected Output**: Service initialization fix with proper error handling

### **Investigation Approach**

#### **Phase 1: Immediate Assessment (30 minutes)**
1. Access Render Dashboard for staging service
2. Check current environment variables
3. Review recent logs for error patterns
4. Identify immediate fixes needed

#### **Phase 2: Environment Variable Fix (1 hour)**
1. Compare staging vs local environment variables
2. Add missing variables to Render Dashboard
3. Test environment variable loading
4. Deploy and monitor changes

#### **Phase 3: Database Connectivity Fix (1-2 hours)**
1. Test database connection from Render
2. Fix database URL if needed
3. Test alternative connection methods
4. Deploy and monitor changes

#### **Phase 4: Service Initialization Fix (1-2 hours)**
1. Fix service initialization order
2. Add proper error handling
3. Test service startup sequence
4. Deploy and monitor changes

#### **Phase 5: Validation and Testing (1 hour)**
1. Test all service endpoints
2. Verify database operations
3. Test storage operations
4. Confirm service health

### **Critical Success Criteria**

#### **Immediate (P0)**
- [ ] Staging environment is accessible and responding
- [ ] All critical environment variables are set
- [ ] Database connectivity is restored
- [ ] Storage service is functional
- [ ] Application starts without errors

#### **Short-term (P1)**
- [ ] All services are initializing properly
- [ ] Health checks are passing
- [ ] End-to-end functionality is working
- [ ] Service is stable and reliable

### **Tools and Resources Available**

#### **Render MCP Tools**
- `mcp_render_get_service` - Get service details
- `mcp_render_list_logs` - Access service logs
- `mcp_render_update_environment_variables` - Update environment variables

#### **Local Files for Reference**
- `.env.staging` - Local staging environment configuration
- `config/environment_loader.py` - Environment loading logic
- `config/configuration_manager.py` - Configuration management
- `main.py` - Application startup sequence

#### **Investigation Files**
- `docs/incidents/fm_030/FRACAS_FM_030_STAGING_DEPLOYMENT_FAILURE.md` - Incident details
- `docs/incidents/fm_030/investigation_checklist.md` - Detailed checklist
- Previous incidents: FM-012, FM-027 (similar issues)

### **Investigation Constraints**

#### **Time Constraints**
- **Total Investigation Time**: 4-6 hours maximum
- **Immediate Fixes**: Must be completed within 2 hours
- **Service Restoration**: Must be completed within 4 hours

#### **Resource Constraints**
- Limited to Render MCP tools and local file access
- Cannot modify production environment
- Must maintain staging environment stability

#### **Risk Constraints**
- Must not break production environment
- Must maintain data integrity
- Must follow established deployment procedures

### **Investigation Deliverables**

#### **1. Root Cause Analysis Report**
- Complete analysis of environment variable issues
- Database connectivity problem diagnosis
- Service initialization failure analysis
- Recommended fixes and implementation plan

#### **2. Implementation Report**
- Environment variable fixes applied
- Database connectivity fixes implemented
- Service initialization fixes deployed
- Testing results and validation

#### **3. Prevention Measures**
- Recommendations for preventing similar issues
- Process improvements for environment management
- Monitoring and alerting recommendations
- Documentation updates needed

### **Investigation Questions to Answer**

1. **Environment Variables**: Why are critical environment variables missing from staging?
2. **Database Connectivity**: What is causing the "Network is unreachable" error?
3. **Service Initialization**: Why are services failing to initialize properly?
4. **Configuration Management**: How can we prevent similar configuration issues?
5. **Deployment Process**: What improvements are needed in the deployment process?

### **Investigation Success Metrics**

#### **Primary Metrics**
- Service availability: 100%
- Environment variable completeness: 100%
- Database connectivity: 100%
- Service initialization success: 100%

#### **Secondary Metrics**
- Investigation completion time: < 6 hours
- Number of issues identified: All critical issues
- Number of fixes implemented: All critical fixes
- Service stability: 100% for 24 hours

### **Investigation Notes**

#### **Key Focus Areas**
1. **Environment Variable Management**: Critical for service functionality
2. **Database Connectivity**: Essential for data operations
3. **Service Initialization**: Required for application startup
4. **Error Handling**: Important for service reliability

#### **Investigation Tips**
1. Start with environment variables - they're often the root cause
2. Test database connectivity early - it's critical for service operation
3. Check service initialization order - dependencies matter
4. Monitor logs continuously - they provide valuable insights
5. Test fixes incrementally - don't change everything at once

### **Investigation Timeline**

#### **Hour 1: Assessment and Environment Variables**
- Access Render Dashboard
- Audit environment variables
- Add missing variables
- Test basic connectivity

#### **Hour 2: Database Connectivity**
- Test database connection
- Fix connectivity issues
- Deploy database fixes
- Monitor database operations

#### **Hour 3: Service Initialization**
- Fix service initialization
- Add error handling
- Deploy service fixes
- Test service startup

#### **Hour 4: Validation and Testing**
- Test all endpoints
- Verify functionality
- Monitor service health
- Document results

#### **Hours 5-6: Documentation and Prevention**
- Complete investigation report
- Document prevention measures
- Update procedures
- Close investigation

---

## 🎯 **INVESTIGATION SUCCESS CRITERIA**

### **Must Complete**
- [ ] Staging environment is fully operational
- [ ] All critical environment variables are set
- [ ] Database connectivity is restored
- [ ] Storage service is functional
- [ ] Application starts without errors
- [ ] All services are healthy and responding

### **Should Complete**
- [ ] Root cause analysis is documented
- [ ] Prevention measures are identified
- [ ] Process improvements are recommended
- [ ] Investigation report is complete
- [ ] Team is informed of findings

---

**Investigation Priority**: **P0 - Critical**  
**Estimated Time**: **4-6 hours**  
**Investigation Started**: **2025-10-02**  
**Target Completion**: **2025-10-02 (Same day)**

---

**Remember**: This is a critical incident affecting staging environment availability. Focus on rapid resolution while maintaining thorough investigation standards. The staging environment must be restored to full functionality as quickly as possible.
