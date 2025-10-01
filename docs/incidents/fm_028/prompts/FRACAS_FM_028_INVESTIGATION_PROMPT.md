# FRACAS FM-028: Intermittent Webhook Failures Investigation Prompt

## 🎯 **Investigation Mission**

**Objective**: Investigate and resolve intermittent webhook processing failures in the staging environment that are causing document processing pipeline interruptions.

**Reference Document**: `docs/incidents/fm_028/README.md`

---

## 📋 **Current Situation**

### Critical Issue Details
- **Environment**: Staging (Render API Service)
- **Service**: Webhook handler for LlamaParse document processing
- **Symptom**: Intermittent failures causing document processing to get stuck or fail
- **Impact**: Users experience incomplete document processing, missing parsed content

### Evidence Available
- Webhook handler code in `api/upload_pipeline/webhooks.py`
- Enhanced logging from FM-027 investigation
- Render staging environment logs
- Database transaction logs
- LlamaParse service integration code

---

## 🔍 **Investigation Tasks**

### **Task 1: Log Analysis and Pattern Identification** ⏱️ 1-2 hours

**Objective**: Analyze staging logs to identify failure patterns and root causes

**Investigation Steps**:
1. **Retrieve Recent Logs**
   ```bash
   # Use Render MCP to get recent webhook-related logs
   # Focus on error patterns and timing
   ```

2. **Identify Failure Patterns**
   - Look for webhook processing errors
   - Identify timing patterns (specific times, intervals)
   - Check for correlation with system load
   - Analyze error message patterns

3. **Analyze Webhook Delivery**
   - Check webhook URL generation and delivery
   - Verify webhook secret handling
   - Look for network connectivity issues

**Expected Output**: 
- Log analysis report with identified patterns
- Timeline of failures
- Error categorization

### **Task 2: Database Transaction Analysis** ⏱️ 1-2 hours

**Objective**: Investigate database transaction failures during webhook processing

**Investigation Steps**:
1. **Check Database Connection Issues**
   ```sql
   -- Use Supabase MCP to query database
   -- Look for connection failures, timeouts
   -- Check transaction rollback patterns
   ```

2. **Analyze Job Status Updates**
   - Check for incomplete job status updates
   - Look for stuck jobs in processing states
   - Identify database constraint violations

3. **Review Transaction Logs**
   - Check for deadlocks or lock timeouts
   - Analyze transaction duration patterns
   - Look for connection pool exhaustion

**Files to Investigate**:
- `api/upload_pipeline/webhooks.py` (lines 40-310)
- `api/upload_pipeline/database.py`
- Database schema and constraints

**Expected Output**:
- Database transaction analysis report
- Identified database-related failure patterns
- Connection pool and transaction health assessment

### **Task 3: Webhook Handler Code Review** ⏱️ 1-2 hours

**Objective**: Review webhook handler code for error handling and reliability issues

**Investigation Steps**:
1. **Analyze Error Handling**
   - Check exception handling completeness
   - Review error recovery mechanisms
   - Identify potential race conditions

2. **Review Database Operations**
   - Check transaction boundaries
   - Verify rollback mechanisms
   - Look for resource cleanup issues

3. **Test Webhook Processing**
   - Create test webhook payloads
   - Test error scenarios
   - Verify retry mechanisms

**Files to Check**:
- `api/upload_pipeline/webhooks.py` - Main webhook handler
- `backend/workers/enhanced_base_worker.py` - Webhook URL generation
- `backend/workers/base_worker.py` - Job processing logic

**Expected Output**:
- Code review report with identified issues
- Test results for webhook processing
- Recommended code improvements

### **Task 4: Environment Configuration Analysis** ⏱️ 1 hour

**Objective**: Compare staging environment configuration with production to identify differences

**Investigation Steps**:
1. **Check Environment Variables**
   - Compare staging vs production webhook configuration
   - Verify database connection settings
   - Check timeout and retry configurations

2. **Review Resource Allocation**
   - Check memory and CPU limits
   - Analyze resource usage patterns
   - Look for resource contention issues

3. **Test Configuration Changes**
   - Test different timeout values
   - Verify retry mechanisms
   - Check error handling improvements

**Files to Check**:
- `config/environment/staging.yaml`
- `config/environment/production.yaml`
- Environment-specific configuration files

**Expected Output**:
- Configuration comparison report
- Identified configuration issues
- Recommended configuration changes

---

## 🧪 **Test Commands**

### **1. Log Analysis Commands**
```bash
# Get recent webhook logs from staging
# Use Render MCP tools to retrieve logs
# Focus on error patterns and timing
```

### **2. Database Investigation Commands**
```sql
-- Check for stuck jobs
SELECT job_id, status, state, created_at, updated_at 
FROM upload_pipeline.upload_jobs 
WHERE state IN ('queued', 'working') 
AND updated_at < NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;

-- Check webhook processing errors
SELECT job_id, last_error, updated_at
FROM upload_pipeline.upload_jobs 
WHERE last_error IS NOT NULL
AND updated_at > NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC;
```

### **3. Webhook Testing Commands**
```python
# Test webhook processing locally
# Create test webhook payloads
# Verify error handling mechanisms
```

---

## 📊 **Expected Output**

### **Investigation Complete When:**
1. ✅ Root cause of intermittent failures identified
2. ✅ Failure patterns documented with evidence
3. ✅ Database transaction issues analyzed
4. ✅ Webhook handler code reviewed for issues
5. ✅ Environment configuration differences identified

### **Resolution Complete When:**
1. ✅ Fix implemented and tested
2. ✅ Monitoring and alerting improved
3. ✅ Documentation updated
4. ✅ Staging environment verified working
5. ✅ Production deployment plan ready

---

## 🚨 **Critical Notes**

- **Intermittent Nature**: This is not a consistent failure, making it harder to reproduce
- **User Impact**: Affects document processing pipeline, impacting user experience
- **Environment Specific**: Issue appears to be staging-specific
- **Recent Changes**: May be related to FM-027 fixes or other recent deployments

---

## 📋 **Deliverables**

### **1. Root Cause Report**
- **What**: Specific cause of intermittent webhook failures
- **When**: When failures occur (timing patterns)
- **Why**: Why failures happen (technical root cause)
- **Impact**: Full impact assessment on user experience

### **2. Solution Design**
- **Option A**: Code fixes for error handling
- **Option B**: Configuration changes for reliability
- **Option C**: Infrastructure improvements
- **Recommendation**: Preferred solution with justification

### **3. Implementation Plan**
- **Steps**: Detailed implementation steps
- **Testing**: How to validate the fix
- **Rollback**: Rollback plan if issues arise
- **Monitoring**: Enhanced monitoring for early detection

### **4. Prevention Measures**
- **Process**: How to prevent similar issues
- **Tooling**: Enhanced monitoring and alerting
- **Documentation**: Updated documentation and runbooks

---

## ⚠️ **Escalation Criteria**

**Escalate if:**
- Root cause cannot be identified within 4 hours
- Fix requires significant infrastructure changes
- Issue affects production environment
- User impact becomes critical

---

**Investigation Priority**: P1 - High  
**Estimated Time**: 4-6 hours  
**Assigned To**: TBD  
**Due Date**: TBD
