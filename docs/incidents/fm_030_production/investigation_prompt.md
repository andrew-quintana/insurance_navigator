# FM-030 Production Investigation Prompt

## 🚨 **CRITICAL PRODUCTION WORKER FAILURE INVESTIGATION**

### **Investigation Scope**
You are tasked with investigating a critical deployment failure in the production worker environment that has rendered the background processing service unavailable. This is a **P0 Critical** incident requiring immediate attention.

**IMPORTANT**: This investigation should follow the same successful approach used in FM-030 staging investigation, which was **successfully resolved** using proven fixes.

### **Service Details**
- **API Service ID**: `srv-d0v2nqvdiees73cejf0g`
- **API Service Name**: `api-service-production`
- **Worker Service ID**: `srv-d2h5mr8dl3ps73fvvlog`
- **Worker Service Name**: `upload-worker-production`
- **Environment**: Production
- **API URL**: `https://insurance-navigator-api.onrender.com`
- **Status**: **API HEALTHY** ✅ | **WORKER FAILED** ❌

### **Primary Symptoms**
1. **API Service**: ✅ **HEALTHY** - Health checks passing (200 OK)
2. **Worker Service**: ❌ **FAILED** - `OSError: [Errno 101] Network is unreachable`
3. **Background Processing**: **UNAVAILABLE** - Worker cannot process jobs
4. **Critical Alert**: `CONFIGURATION_ERROR_FATAL` threshold exceeded

### **🎯 PROVEN SOLUTION FROM FM-030 STAGING**

**FM-030 Staging was successfully resolved** using the following approach:

#### **Root Cause Identified in Staging**
1. **Missing Environment Variables**: Critical environment variables were not set in Render services
2. **Database URL Format**: Direct database URL was causing network connectivity issues
3. **Service Configuration**: Both API and worker services had identical environment variable issues

#### **Successful Resolution Applied in Staging**
1. **Environment Variables Fixed**: Applied complete environment variable configuration from `.env.staging`
2. **Database Connectivity Resolved**: Switched to Supabase pooler URL format
3. **Worker Service Fixed**: Applied same environment variable fixes to staging worker

#### **Key Fixes That Worked in Staging**
```bash
# Critical Environment Variables That Fixed Staging
SUPABASE_URL=https://your-staging-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres.your-staging-project:your_database_password_here@aws-0-us-west-1.pooler.supabase.com:6543/postgres
OPENAI_API_KEY=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
LLAMAPARSE_API_KEY=llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS
DOCUMENT_ENCRYPTION_KEY=iSUAmk2NHMNW5bsn8F0UnPSCk9L+IxZhu/v/UyDwFcc=
```

### **Investigation Objectives**

#### **1. Environment Variable Audit (Priority: P0)**
**Objective**: Apply proven environment variable fixes from staging to production

**Tasks**:
- Access Render Dashboard for production worker service
- Compare production environment variables with successful staging configuration
- Apply the same environment variable fixes that resolved staging
- Test environment variable loading mechanism
- Deploy and monitor changes

**Expected Output**: Production worker environment variables match successful staging configuration

#### **2. Database Connectivity Analysis (Priority: P0)**
**Objective**: Apply proven database connectivity fixes from staging

**Tasks**:
- Apply the same database URL format that fixed staging (pooler URL)
- Test database connectivity from Render production worker
- Verify Supabase database host accessibility
- Deploy and monitor database connectivity changes

**Expected Output**: Database connectivity restored using proven staging fixes

#### **3. Worker Service Initialization Analysis (Priority: P1)**
**Objective**: Apply proven worker initialization fixes from staging

**Tasks**:
- Apply the same worker configuration that resolved staging
- Test worker service initialization
- Deploy and monitor worker changes
- Validate job processing capability

**Expected Output**: Worker service initialization successful using proven staging fixes

### **Investigation Approach**

#### **Phase 1: Immediate Assessment (15 minutes)**
1. Access Render Dashboard for production worker service
2. Check current environment variables
3. Compare with successful staging configuration
4. Identify missing variables that were fixed in staging

#### **Phase 2: Environment Variable Fix (30 minutes)**
1. Apply staging environment variable fixes to production worker
2. Deploy and monitor changes
3. Test environment variable loading
4. Validate worker startup

#### **Phase 3: Database Connectivity Fix (30 minutes)**
1. Apply staging database URL format to production
2. Deploy and monitor database changes
3. Test database connectivity
4. Validate worker database operations

#### **Phase 4: Worker Initialization Fix (30 minutes)**
1. Apply staging worker configuration to production
2. Deploy and monitor worker changes
3. Test worker startup sequence
4. Validate job processing capability

#### **Phase 5: Validation and Testing (15 minutes)**
1. Test end-to-end job processing
2. Verify worker health and stability
3. Monitor system performance
4. Confirm full functionality

### **Critical Success Criteria**

#### **Immediate (P0)**
- [ ] Production worker is accessible and responding
- [ ] All critical environment variables are set (same as staging)
- [ ] Database connectivity is restored (using staging fixes)
- [ ] Worker can process jobs
- [ ] Worker starts without errors

#### **Short-term (P1)**
- [ ] All worker services are initializing properly
- [ ] Health checks are passing
- [ ] End-to-end job processing is working
- [ ] Worker is stable and reliable

### **Tools and Resources Available**

#### **Render MCP Tools**
- `mcp_render_get_service` - Get service details
- `mcp_render_list_logs` - Access service logs
- `mcp_render_update_environment_variables` - Update environment variables

#### **Local Files for Reference**
- `.env.production` - Local production environment configuration
- `.env.staging` - **SUCCESSFUL** staging environment configuration (use as reference)
- `config/environment_loader.py` - Environment loading logic
- `backend/workers/enhanced_runner.py` - Worker startup sequence

#### **Investigation Files**
- `docs/incidents/fm_030/FRACAS_FM_030_STAGING_DEPLOYMENT_FAILURE.md` - **SUCCESSFUL** staging investigation
- `docs/incidents/fm_030/investigation_checklist.md` - Staging checklist (use as reference)
- `docs/incidents/fm_030_production/investigation_checklist.md` - Production checklist

### **Investigation Constraints**

#### **Time Constraints**
- **Total Investigation Time**: 2 hours maximum
- **Immediate Fixes**: Must be completed within 1 hour
- **Worker Restoration**: Must be completed within 1.5 hours

#### **Resource Constraints**
- Limited to Render MCP tools and local file access
- Cannot modify production API service (it's healthy)
- Must maintain production environment stability

#### **Risk Constraints**
- Must not break production API service
- Must maintain data integrity
- Must follow established deployment procedures

### **Investigation Deliverables**

#### **1. Root Cause Analysis Report**
- Analysis of environment variable issues (based on staging findings)
- Database connectivity problem diagnosis (using staging solutions)
- Worker initialization failure analysis (using staging fixes)
- Implementation plan based on proven staging approach

#### **2. Implementation Report**
- Environment variable fixes applied (same as staging)
- Database connectivity fixes implemented (same as staging)
- Worker initialization fixes deployed (same as staging)
- Testing results and validation

#### **3. Prevention Measures**
- Recommendations based on staging lessons learned
- Process improvements for environment management
- Monitoring and alerting recommendations
- Documentation updates needed

### **Investigation Questions to Answer**

1. **Environment Variables**: Why are production environment variables different from successful staging?
2. **Database Connectivity**: Why is production experiencing the same database issues that staging had?
3. **Worker Initialization**: Why is production worker failing with the same errors that staging had?
4. **Configuration Management**: How can we ensure production matches successful staging configuration?
5. **Deployment Process**: What improvements are needed to prevent similar issues?

### **Investigation Success Metrics**

#### **Primary Metrics**
- Worker availability: 100%
- Environment variable completeness: 100% (matching staging)
- Database connectivity: 100% (using staging fixes)
- Worker initialization success: 100% (using staging configuration)

#### **Secondary Metrics**
- Investigation completion time: < 2 hours
- Number of issues identified: All critical issues (based on staging)
- Number of fixes implemented: All critical fixes (same as staging)
- Worker stability: 100% for 24 hours

### **Investigation Notes**

#### **Key Focus Areas**
1. **Environment Variable Management**: Apply proven staging fixes
2. **Database Connectivity**: Use proven staging database URL format
3. **Worker Initialization**: Apply proven staging worker configuration
4. **Error Handling**: Use proven staging error handling approach

#### **Investigation Tips**
1. Start with environment variables - staging proved this is the root cause
2. Use staging database URL format - this fixed staging connectivity
3. Apply staging worker configuration - this resolved staging worker issues
4. Monitor logs continuously - staging investigation showed this is critical
5. Test fixes incrementally - staging approach was successful

### **Investigation Timeline**

#### **Minutes 1-15: Assessment and Environment Variables**
- Access Render Dashboard
- Compare with successful staging configuration
- Identify missing variables from staging
- Apply staging environment variable fixes

#### **Minutes 16-45: Database Connectivity**
- Apply staging database URL format
- Deploy and monitor database changes
- Test database connectivity
- Validate worker database operations

#### **Minutes 46-75: Worker Initialization**
- Apply staging worker configuration
- Deploy and monitor worker changes
- Test worker startup sequence
- Validate job processing capability

#### **Minutes 76-90: Validation and Testing**
- Test end-to-end job processing
- Verify worker health and stability
- Monitor system performance
- Confirm full functionality

#### **Minutes 91-120: Documentation and Prevention**
- Complete investigation report
- Document prevention measures
- Update procedures
- Close investigation

---

## 🎯 **INVESTIGATION SUCCESS CRITERIA**

### **Must Complete**
- [ ] Production worker is fully operational
- [ ] All critical environment variables are set (matching staging)
- [ ] Database connectivity is restored (using staging fixes)
- [ ] Worker can process jobs
- [ ] Worker starts without errors
- [ ] All worker services are healthy and responding

### **Should Complete**
- [ ] Root cause analysis is documented
- [ ] Prevention measures are identified
- [ ] Process improvements are recommended
- [ ] Investigation report is complete
- [ ] Team is informed of findings

---

**Investigation Priority**: **P0 - Critical**  
**Estimated Time**: **2 hours**  
**Investigation Started**: **2025-10-02**  
**Target Completion**: **2025-10-02 (Same day)**

---

**Remember**: This is a critical incident affecting production background processing. The staging investigation was **successfully resolved** using proven fixes. Apply the same approach to production for rapid resolution.

## **Current Status Summary**

### **Production Services Status**
- **API Service**: ✅ **HEALTHY** - All health checks passing
- **Worker Service**: ❌ **FAILED** - Same errors as staging (resolved)
- **Overall System**: ⚠️ **PARTIALLY OPERATIONAL** - API works, background processing down

### **Next Steps**
1. Begin environment variable audit for production worker
2. Apply proven staging environment variable fixes
3. Apply proven staging database connectivity fixes
4. Apply proven staging worker configuration fixes
5. Monitor and validate worker restoration

### **Reference: Successful Staging Resolution**
- **Staging API Service**: ✅ **RESOLVED** - Fully operational
- **Staging Worker Service**: ✅ **RESOLVED** - Fully operational
- **Staging Database**: ✅ **RESOLVED** - Using pooler URL format
- **Staging Environment Variables**: ✅ **RESOLVED** - Complete configuration applied
