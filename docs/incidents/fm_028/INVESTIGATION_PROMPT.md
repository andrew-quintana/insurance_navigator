# FM-028 Investigation Prompt for Next Agent

## 🎯 **Mission**
Continue investigation of intermittent webhook processing failures in staging environment. Previous agent identified and fixed two root causes, but jobs are still getting stuck at `parse_queued` status.

## 📋 **Previous Work Completed**
- ✅ Fixed database constraint violation (`duplicate_detection` → `duplicate`)
- ✅ Fixed webhook URL mismatch (staging URL correction)
- ✅ Committed fixes to staging branch
- ❌ **Jobs still stuck at `parse_queued`**

## 🔍 **Investigation Focus**

### **Primary Question**: Why are jobs still getting stuck at `parse_queued` despite fixes?

### **Key Areas to Investigate**

#### 1. **Staging Deployment Verification**
```bash
# Check if fixes are actually deployed
git log --oneline -5  # Verify latest commits
# Check Render deployment status
# Verify staging environment has latest code
```

#### 2. **Webhook URL Verification**
```bash
# Check staging worker logs for webhook URL generation
# Verify STAGING_WEBHOOK_BASE_URL environment variable
# Confirm webhook URLs are being generated correctly
```

#### 3. **LlamaParse Integration**
```bash
# Check if LlamaParse is actually sending webhooks
# Verify webhook delivery to staging API
# Check webhook secret handling and signature verification
```

#### 4. **Database Connection Issues**
```bash
# Check staging database logs
# Verify database connection pool status
# Check for transaction failures in webhook processing
```

#### 5. **Environment Configuration**
```bash
# Compare staging vs production configuration
# Verify all environment variables are set correctly
# Check for missing or incorrect staging-specific settings
```

## 🚨 **Critical Questions**

1. **Are the fixes actually deployed to staging?**
2. **Is the staging environment using the correct webhook URL?**
3. **Are webhooks being sent by LlamaParse to the staging API?**
4. **Are there database connection issues in staging?**
5. **Are there other environment-specific configuration issues?**

## 📊 **Evidence to Collect**

### **Staging Logs**
- Worker logs showing webhook URL generation
- API logs showing webhook processing attempts
- Database logs showing transaction failures
- LlamaParse service logs (if accessible)

### **Database Queries**
```sql
-- Check for stuck jobs
SELECT job_id, status, state, created_at, updated_at, last_error
FROM upload_pipeline.upload_jobs 
WHERE status = 'parse_queued'
ORDER BY updated_at DESC
LIMIT 10;

-- Check for recent webhook processing errors
SELECT job_id, last_error, updated_at, status, state
FROM upload_pipeline.upload_jobs 
WHERE last_error IS NOT NULL
AND updated_at > NOW() - INTERVAL '24 hours'
ORDER BY updated_at DESC
LIMIT 10;
```

### **Environment Verification**
- Check staging deployment configuration
- Verify environment variables
- Compare with working production environment

## 🎯 **Success Criteria**

- **Jobs progress past `parse_queued` status**
- **Webhooks successfully reach staging API**
- **Document processing completes normally**
- **Users see parsed content as expected**

## 📝 **Investigation Approach**

1. **Start with staging deployment verification** - ensure fixes are deployed
2. **Check webhook URL generation** - verify correct URLs are being used
3. **Monitor real webhook processing** - test with actual document uploads
4. **Analyze staging logs** - look for webhook processing errors
5. **Test end-to-end** - verify complete document processing flow

## ⚠️ **Important Notes**

- **Focus on staging environment**, not local testing
- **Use Render MCP tools** for staging environment access
- **Check actual webhook processing**, not just code
- **Verify environment configuration** matches production
- **Test with real document uploads** to see actual behavior

## 🔧 **Recommended Tools**

- `mcp_render_list_logs` - Get staging logs
- `mcp_supabase_staging_execute_sql` - Query staging database
- `mcp_render_get_service` - Check staging service status
- `mcp_render_list_deploys` - Verify deployment status

## 📋 **Deliverables**

1. **Root cause analysis** of remaining issues
2. **Fix implementation** for identified problems
3. **Verification** that jobs no longer get stuck
4. **Documentation** of final solution
5. **Testing** of complete document processing flow

## 🎯 **Expected Outcome**

Jobs should progress from `parse_queued` → `parsed` → `parse_validated` → `chunking` → `chunks_stored` → `embedding_queued` → `embedding_in_progress` → `embeddings_stored` → `complete` without getting stuck.

---

**Previous Agent**: Fixed database constraint violation and webhook URL mismatch
**Current Status**: Jobs still stuck at `parse_queued` despite fixes
**Next Step**: Verify staging deployment and investigate remaining issues
