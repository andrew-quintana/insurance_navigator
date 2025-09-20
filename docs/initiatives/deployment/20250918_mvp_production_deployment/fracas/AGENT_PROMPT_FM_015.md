# Agent Prompt: FM-015 Webhook Processing Failure Investigation

## 🎯 **Mission**
You are tasked with investigating and resolving FM-015: Webhook Processing Failure. The webhook is being received by the API service but is not performing the required processing steps.

## 📋 **Context**
- **Issue**: Webhook received but processing stops after reception
- **Priority**: Critical - blocking document processing pipeline
- **Component**: API service webhook processing (`api/upload_pipeline/webhooks.py`)
- **Environment**: Production (Render)

## 🔍 **Investigation Phases**

### **Phase 1: Enhanced Logging and Observation**
1. **Add Comprehensive Logging** to `api/upload_pipeline/webhooks.py`:
   - Log each step of the webhook processing workflow
   - Add try-catch blocks around each major operation
   - Log database query results and errors
   - Log storage operation results and errors
   - Log webhook payload details
   - Log processing step completion status

2. **Monitor Processing Steps**:
   - Track webhook reception and parsing
   - Monitor database operations (job lookup, status updates)
   - Track storage operations (parsed content storage)
   - Monitor any external API calls
   - Track error conditions and exceptions

3. **Deploy and Test**:
   - Deploy enhanced logging to production
   - Trigger a test webhook to observe processing
   - Collect detailed logs from the processing attempt

### **Phase 2: Root Cause Analysis**
1. **Analyze Logs**:
   - Identify the exact point where processing stops
   - Look for error messages, exceptions, or unexpected behavior
   - Check database operation results
   - Verify storage operation results
   - Analyze webhook payload structure

2. **Investigate Specific Areas**:
   - **Database Operations**: Are database queries succeeding?
   - **Storage Operations**: Are storage operations working?
   - **Webhook Payload**: Is the webhook payload structure correct?
   - **Environment Variables**: Are all required environment variables set?
   - **Dependencies**: Are all required dependencies available?

3. **Identify Root Cause**:
   - Determine the specific failing component
   - Identify configuration issues
   - Find missing dependencies or permissions
   - Locate logic errors in processing workflow

### **Phase 3: Corrective Action**
1. **Implement Fixes**:
   - Fix identified issues based on root cause analysis
   - Add proper error handling
   - Ensure all required operations are performed
   - Add validation and verification steps

2. **Test and Verify**:
   - Deploy fixes to production
   - Test complete webhook processing workflow
   - Verify all processing steps complete successfully
   - Confirm end-to-end document processing works

## 🛠 **Tools and Resources**

### **Available Tools**
- Render service management (check logs, deployments)
- Database access (Supabase production)
- Code modification and deployment
- Log analysis and monitoring

### **Key Files to Investigate**
- `api/upload_pipeline/webhooks.py` - Main webhook processing logic
- `core/database.py` - Database operations
- `backend/shared/storage.py` - Storage operations
- Environment variables and configuration
- Database schema and RLS policies

### **Log Sources**
- API service logs (Render)
- Worker logs (Render)
- Database logs (Supabase)
- Storage logs (Supabase)

## 📊 **Expected Deliverables**

### **Phase 1 Deliverables**
- Enhanced logging code deployed to production
- Detailed logs from webhook processing attempt
- Identification of processing step failures

### **Phase 2 Deliverables**
- Root cause analysis report
- Specific failing component identification
- Error analysis and findings

### **Phase 3 Deliverables**
- Implemented fixes for identified issues
- Verified working webhook processing
- Complete end-to-end pipeline functionality

## 🎯 **Success Criteria**

- ✅ Webhook processing completes all required steps
- ✅ Database operations succeed
- ✅ Storage operations succeed
- ✅ Document processing pipeline works end-to-end
- ✅ No errors in webhook processing logs
- ✅ Complete FRACAS resolution

## 🚨 **Critical Notes**

1. **Production Environment**: All changes will be deployed to production
2. **Data Safety**: Ensure database and storage operations are safe
3. **Rollback Plan**: Have a rollback plan if changes cause issues
4. **Monitoring**: Monitor system health after each change
5. **Documentation**: Document all findings and fixes

## 🔄 **Investigation Workflow**

1. **Start with Enhanced Logging**: Add comprehensive logging to webhook processing
2. **Deploy and Test**: Deploy changes and trigger test webhook
3. **Analyze Results**: Review logs to identify failure points
4. **Investigate Root Cause**: Deep dive into specific failing components
5. **Implement Fixes**: Apply corrective actions based on findings
6. **Verify Resolution**: Test complete pipeline functionality
7. **Document Results**: Update FRACAS with findings and resolution

## 📝 **Reporting Requirements**

- Update FRACAS document with findings
- Document root cause analysis
- Record corrective actions taken
- Verify and document resolution
- Update status to RESOLVED when complete

---

**Remember**: This is a critical production issue. Take a systematic approach, document everything, and ensure all changes are safe and reversible.
