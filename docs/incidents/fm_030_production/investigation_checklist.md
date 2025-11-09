# FM-030 Production Investigation Checklist

## **Investigation Overview**
- **Incident ID**: FM-030-PRODUCTION
- **Priority**: P0 - Critical
- **Environment**: Production
- **Affected Services**: Production Worker (`srv-d2h5mr8dl3ps73fvvlog`)
- **API Service Status**: ✅ Healthy
- **Worker Service Status**: ❌ Failed

## **Phase 1: Immediate Assessment (15 minutes)**

### **1.1 Service Status Check**
- [ ] Verify production API service is healthy
- [ ] Confirm production worker is failing
- [ ] Check recent deployment status
- [ ] Review error patterns in logs

### **1.2 Environment Variable Audit**
- [ ] Access Render Dashboard for production worker
- [ ] List current environment variables
- [ ] Compare with staging environment variables
- [ ] Identify missing variables

### **1.3 Log Analysis**
- [ ] Review recent worker logs
- [ ] Identify error patterns
- [ ] Check for database connectivity issues
- [ ] Look for configuration errors

## **Phase 2: Environment Variable Fix (30 minutes)**

### **2.1 Environment Variable Comparison**
- [ ] Compare production vs staging environment variables
- [ ] Identify missing critical variables
- [ ] Check variable values and formats
- [ ] Verify Supabase project configuration

### **2.2 Required Environment Variables**
- [ ] `ENVIRONMENT=production`
- [ ] `SUPABASE_URL` (production URL)
- [ ] `SUPABASE_ANON_KEY` (production anon key)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` (production service role key)
- [ ] `DATABASE_URL` (production database URL)
- [ ] `OPENAI_API_KEY` (production OpenAI key)
- [ ] `LLAMAPARSE_API_KEY` (production LlamaParse key)
- [ ] `ANTHROPIC_API_KEY` (production Anthropic key)
- [ ] `DOCUMENT_ENCRYPTION_KEY` (production encryption key)
- [ ] `LOG_LEVEL=INFO`
- [ ] `ASYNCPG_DISABLE_PREPARED_STATEMENTS=1`
- [ ] `PYTHONUNBUFFERED=1`
- [ ] `PYTHONDONTWRITEBYTECODE=1`

### **2.3 Worker-Specific Variables**
- [ ] `DATABASE_SCHEMA=upload_pipeline`
- [ ] `USE_MOCK_STORAGE=false`
- [ ] `WORKER_POLL_INTERVAL=5`
- [ ] `WORKER_MAX_RETRIES=3`
- [ ] `WORKER_MAX_JOBS=10`
- [ ] `SERVICE_MODE=real`
- [ ] `LLAMAPARSE_BASE_URL=https://api.cloud.llamaindex.ai`
- [ ] `OPENAI_API_URL=https://api.openai.com`
- [ ] `OPENAI_MODEL=text-embedding-3-small`

### **2.4 Environment Variable Update**
- [ ] Update environment variables in Render Dashboard
- [ ] Trigger new deployment
- [ ] Monitor deployment progress
- [ ] Check for immediate errors

## **Phase 3: Database Connectivity Fix (30 minutes)**

### **3.1 Database URL Verification**
- [ ] Verify production database URL format
- [ ] Check if using pooler URL vs direct URL
- [ ] Test database URL format
- [ ] Compare with staging database URL

### **3.2 Database Connection Test**
- [ ] Test database connectivity from Render
- [ ] Check SSL configuration
- [ ] Verify host accessibility
- [ ] Test connection parameters

### **3.3 Alternative Connection Methods**
- [ ] Try pooler URL if using direct URL
- [ ] Try direct URL if using pooler URL
- [ ] Test different SSL modes
- [ ] Verify connection parameters

### **3.4 Database Fix Deployment**
- [ ] Apply database URL fixes
- [ ] Deploy changes
- [ ] Monitor database connection
- [ ] Verify connectivity success

## **Phase 4: Worker Initialization Fix (30 minutes)**

### **4.1 Worker Configuration Analysis**
- [ ] Check worker configuration loading
- [ ] Verify environment variable parsing
- [ ] Test configuration validation
- [ ] Check for missing dependencies

### **4.2 Service Initialization Order**
- [ ] Map worker initialization sequence
- [ ] Check service dependencies
- [ ] Verify initialization order
- [ ] Test individual service initialization

### **4.3 Error Handling Implementation**
- [ ] Add proper error handling
- [ ] Implement graceful degradation
- [ ] Add retry mechanisms
- [ ] Improve error messages

### **4.4 Worker Fix Deployment**
- [ ] Apply worker initialization fixes
- [ ] Deploy changes
- [ ] Monitor worker startup
- [ ] Verify successful initialization

## **Phase 5: Validation and Testing (15 minutes)**

### **5.1 Worker Health Check**
- [ ] Verify worker is running
- [ ] Check worker logs for errors
- [ ] Confirm database connectivity
- [ ] Verify service initialization

### **5.2 Job Processing Test**
- [ ] Test job processing capability
- [ ] Verify database operations
- [ ] Test storage operations
- [ ] Confirm end-to-end functionality

### **5.3 System Integration Test**
- [ ] Test API to worker communication
- [ ] Verify job queuing and processing
- [ ] Test error handling
- [ ] Confirm system stability

### **5.4 Performance Validation**
- [ ] Check worker performance
- [ ] Monitor resource usage
- [ ] Verify job processing speed
- [ ] Confirm system reliability

## **Phase 6: Documentation and Prevention (30 minutes)**

### **6.1 Root Cause Analysis**
- [ ] Document root cause
- [ ] Identify contributing factors
- [ ] Analyze failure patterns
- [ ] Document lessons learned

### **6.2 Prevention Measures**
- [ ] Identify prevention strategies
- [ ] Document process improvements
- [ ] Create monitoring recommendations
- [ ] Update deployment procedures

### **6.3 Documentation Updates**
- [ ] Update investigation report
- [ ] Document fixes applied
- [ ] Create prevention checklist
- [ ] Update team procedures

### **6.4 Team Communication**
- [ ] Notify team of resolution
- [ ] Share lessons learned
- [ ] Update incident status
- [ ] Close investigation

## **Success Criteria Checklist**

### **Immediate Success (P0)**
- [ ] Production worker is accessible and responding
- [ ] All critical environment variables are set
- [ ] Database connectivity is restored
- [ ] Worker can process jobs
- [ ] Worker starts without errors

### **Short-term Success (P1)**
- [ ] All worker services are initializing properly
- [ ] Health checks are passing
- [ ] End-to-end job processing is working
- [ ] Worker is stable and reliable

### **Long-term Success (P2)**
- [ ] Prevention measures are implemented
- [ ] Monitoring and alerting are improved
- [ ] Documentation is updated
- [ ] Team processes are enhanced

## **Investigation Timeline**

| Phase | Duration | Status | Notes |
|-------|----------|--------|-------|
| Phase 1: Assessment | 15 min | ⏳ Pending | |
| Phase 2: Env Vars | 30 min | ⏳ Pending | |
| Phase 3: Database | 30 min | ⏳ Pending | |
| Phase 4: Worker Init | 30 min | ⏳ Pending | |
| Phase 5: Validation | 15 min | ⏳ Pending | |
| Phase 6: Documentation | 30 min | ⏳ Pending | |
| **Total** | **2.5 hours** | **⏳ Pending** | |

## **Investigation Notes**

### **Key Findings**
- Production API service is healthy
- Production worker has database connectivity issues
- Environment variables likely missing or incorrect
- Similar issues resolved in staging environment

### **Immediate Actions Required**
1. Audit production worker environment variables
2. Apply staging environment variable fixes
3. Test database connectivity
4. Deploy and monitor changes

### **Risk Mitigation**
- API service is healthy, so no immediate user impact
- Background processing is down, affecting job processing
- Must maintain API service stability during fixes
- Follow established deployment procedures

## **Investigation Status**

- **Status**: 🔴 **IN PROGRESS**
- **Current Phase**: Phase 1 - Assessment
- **Next Action**: Environment variable audit
- **Estimated Completion**: 2 hours
- **Priority**: P0 - Critical
