# FM-030 Production Investigation - Quick Reference

## **🚨 CRITICAL PRODUCTION WORKER FAILURE**

### **Service Details**
- **Worker ID**: `srv-d2h5mr8dl3ps73fvvlog`
- **Worker Name**: `upload-worker-production`
- **Status**: ❌ **FAILED**
- **Error**: `[Errno 101] Network is unreachable`
- **Alert**: `CONFIGURATION_ERROR_FATAL`

### **API Service Status**
- **API ID**: `srv-d0v2nqvdiees73cejf0g`
- **API Name**: `api-service-production`
- **Status**: ✅ **HEALTHY**
- **URL**: `https://insurance-navigator-api.onrender.com`

## **🔧 IMMEDIATE FIXES REQUIRED**

### **1. Environment Variables (P0)**
Apply these environment variables to production worker:

```bash
# Core Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd6a2RibGtua2t6dHF5Zm51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0NTYsImV4cCI6MjA2NzI1NjQ1Nn0.k0QHYOgm4EilyyTml57kCGDpbikpEtJCzq-qzGYQZqY
SUPABASE_SERVICE_ROLE_KEY=<PRODUCTION_SERVICE_ROLE_KEY>

# Database Configuration
DATABASE_URL=postgresql://postgres.your-project:<PASSWORD>@aws-0-us-west-1.pooler.supabase.com:6543/postgres
DATABASE_SCHEMA=upload_pipeline
ASYNCPG_DISABLE_PREPARED_STATEMENTS=1

# External API Keys
OPENAI_API_KEY=<PRODUCTION_OPENAI_KEY>
LLAMAPARSE_API_KEY=<PRODUCTION_LLAMAPARSE_KEY>
ANTHROPIC_API_KEY=<PRODUCTION_ANTHROPIC_KEY>
DOCUMENT_ENCRYPTION_KEY=<PRODUCTION_ENCRYPTION_KEY>

# Worker Configuration
USE_MOCK_STORAGE=false
SERVICE_MODE=real
WORKER_POLL_INTERVAL=5
WORKER_MAX_RETRIES=3
WORKER_MAX_JOBS=10
LLAMAPARSE_BASE_URL=https://api.cloud.llamaindex.ai
OPENAI_API_URL=https://api.openai.com
OPENAI_MODEL=text-embedding-3-small
```

### **2. Database URL Format (P0)**
Use pooler URL format:
```
postgresql://postgres.your-project:<PASSWORD>@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

## **📋 INVESTIGATION CHECKLIST**

### **Phase 1: Assessment (15 min)**
- [ ] Check production worker environment variables
- [ ] Compare with staging configuration
- [ ] Identify missing variables
- [ ] Review error logs

### **Phase 2: Environment Variables (30 min)**
- [ ] Apply staging environment variable fixes
- [ ] Update production worker variables
- [ ] Deploy and monitor changes
- [ ] Validate variable loading

### **Phase 3: Database Connectivity (30 min)**
- [ ] Test database connection
- [ ] Apply database URL fixes
- [ ] Deploy and monitor changes
- [ ] Validate connectivity

### **Phase 4: Worker Initialization (30 min)**
- [ ] Apply worker initialization fixes
- [ ] Deploy and monitor changes
- [ ] Validate worker startup
- [ ] Test job processing

### **Phase 5: Validation (15 min)**
- [ ] Test end-to-end functionality
- [ ] Validate worker health
- [ ] Monitor system performance
- [ ] Confirm full restoration

## **🛠️ TOOLS AND COMMANDS**

### **Render MCP Tools**
```bash
# Get service details
mcp_render_get_service --serviceId srv-d2h5mr8dl3ps73fvvlog

# Check logs
mcp_render_list_logs --resource srv-d2h5mr8dl3ps73fvvlog

# Update environment variables
mcp_render_update_environment_variables --serviceId srv-d2h5mr8dl3ps73fvvlog --envVars [...]
```

### **Local Commands**
```bash
# Check production environment
cat .env.production

# Compare with staging
diff .env.staging .env.production
```

## **📊 SUCCESS CRITERIA**

### **Immediate (P0)**
- [ ] Worker is accessible and responding
- [ ] All environment variables are set
- [ ] Database connectivity restored
- [ ] Worker can process jobs
- [ ] Worker starts without errors

### **Short-term (P1)**
- [ ] All services initializing properly
- [ ] Health checks passing
- [ ] End-to-end job processing working
- [ ] Worker stable and reliable

## **⚠️ RISK MITIGATION**

### **Current Risks**
- **High**: Background job processing unavailable
- **Medium**: Data processing delays
- **Low**: API service remains operational

### **Mitigation**
- Apply proven fixes from staging
- Monitor worker stability
- Maintain API service health

## **📞 ESCALATION**

### **If Issues Persist**
1. Check environment variable format
2. Verify database URL format
3. Test individual service initialization
4. Review worker configuration
5. Escalate to senior team members

### **Emergency Contacts**
- **Primary**: Senior DevOps Engineer
- **Secondary**: Backend Team Lead
- **Management**: Engineering Manager

## **📈 MONITORING**

### **Key Metrics**
- Worker startup success rate
- Database connection health
- Job processing throughput
- Error rate and patterns

### **Alerts**
- Worker startup failures
- Database connection errors
- Job processing failures
- Service health degradation

## **🔍 TROUBLESHOOTING**

### **Common Issues**
1. **Database Connection**: Check DATABASE_URL format
2. **Environment Variables**: Verify all required variables
3. **API Keys**: Validate key format and permissions
4. **Service Init**: Check service dependencies

### **Debug Steps**
1. Check worker logs for specific errors
2. Verify environment variable values
3. Test database connectivity
4. Validate service configuration
5. Test individual service initialization

## **📚 REFERENCE DOCUMENTS**

- `FRACAS_FM_030_PRODUCTION_DEPLOYMENT_INVESTIGATION.md` - Full investigation
- `investigation_checklist.md` - Detailed checklist
- `production_environment_reference.md` - Environment reference
- `INVESTIGATION_SUMMARY.md` - Investigation summary

---

**Priority**: P0 - Critical  
**Estimated Time**: 2 hours  
**Status**: 🔴 **IN PROGRESS**  
**Last Updated**: 2025-10-02
