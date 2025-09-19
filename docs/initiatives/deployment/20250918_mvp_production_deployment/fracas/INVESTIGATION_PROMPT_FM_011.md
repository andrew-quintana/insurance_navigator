# Investigation Prompt: FM-011 Worker Storage and Fallback Failure

## 🎯 **Mission Brief**

You are tasked with investigating and resolving the remaining issues from **FM-011: Worker Storage Download and Fallback File Failure**. This is a critical production issue affecting the entire document processing pipeline.

## 📋 **Current Status**

**FM-011 Status**: Partially Resolved  
**Priority**: High  
**Component**: Worker Storage and File Handling  

### **Issues Resolved** ✅
- Hardcoded fallback path removed
- Better error handling implemented
- Error classification added

### **Issues Still Pending** ❌
- **Storage Access**: Supabase storage returning 400 Bad Request
- **Webhook URL**: Environment variable still not deployed
- **Root Cause**: Need to investigate storage permissions

## 🔍 **Investigation Tasks**

### **Task 1: Investigate Supabase Storage Access Issue**

**Problem**: Storage downloads are failing with 400 Bad Request
```
Storage download failed, using local fallback: Client error '400 Bad Request' for url 'https://znvwzkdblknkkztqyfnu.supabase.co/storage/v1/object/files/user/899b78b1-3c14-400b-aa8e-91457759be1e/raw/3fe7d00c_6b144eee.pdf'
```

**Investigation Steps**:
1. **Check file existence in database**:
   ```sql
   SELECT document_id, filename, raw_path, created_at 
   FROM upload_pipeline.documents 
   WHERE document_id = '1319d58d-0f37-5231-a4d6-1e575b5f2742';
   ```

2. **Test storage access manually**:
   ```bash
   # Get the service role key from environment
   curl -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
     "https://znvwzkdblknkkztqyfnu.supabase.co/storage/v1/object/files/user/899b78b1-3c14-400b-aa8e-91457759be1e/raw/3fe7d00c_6b144eee.pdf"
   ```

3. **Check storage permissions**:
   - Verify RLS policies on storage bucket
   - Check if service role has proper access
   - Verify file path format and permissions

4. **Check recent uploads**:
   ```sql
   SELECT document_id, raw_path, created_at, processing_status
   FROM upload_pipeline.documents 
   ORDER BY created_at DESC LIMIT 10;
   ```

**Expected Outcomes**:
- Identify why storage is returning 400 Bad Request
- Determine if it's a permissions, path, or file existence issue
- Provide specific fix recommendations

### **Task 2: Deploy Webhook URL Configuration**

**Problem**: Worker still using localhost URL instead of production URL
```
webhook_url: "http://localhost:8000/api/upload-pipeline/webhook/llamaparse/dc63b04f-7eac-4504-a4d1-c0de1a2cf683"
```

**Investigation Steps**:
1. **Check Render configuration**:
   - Verify `WEBHOOK_BASE_URL` is set in `config/render/render.yaml`
   - Check if environment variable is deployed to production
   - Verify worker service has the environment variable

2. **Check worker environment**:
   ```bash
   # In production worker container
   echo $WEBHOOK_BASE_URL
   echo $ENVIRONMENT
   ```

3. **Force deployment if needed**:
   - Redeploy worker service
   - Restart worker to pick up new environment variables
   - Verify environment variables are loaded

4. **Test webhook URL generation**:
   - Check worker logs for webhook URL generation
   - Verify it uses production URL instead of localhost

**Expected Outcomes**:
- Deploy `WEBHOOK_BASE_URL` environment variable
- Verify worker uses correct production URL
- Test webhook URL generation

### **Task 3: End-to-End Testing**

**Objective**: Verify complete pipeline functionality after fixes

**Test Steps**:
1. **Upload a test document**:
   - Use the API upload endpoint
   - Monitor job status in database
   - Check worker logs for processing

2. **Verify storage access**:
   - Confirm file is stored in Supabase storage
   - Verify worker can download file successfully
   - Check no 400 Bad Request errors

3. **Verify LlamaParse integration**:
   - Check webhook URL uses production URL
   - Verify LlamaParse accepts the webhook URL
   - Monitor job completion

4. **Check final results**:
   - Verify job status updates to `completed`
   - Check parsed content is stored
   - Verify no errors in logs

**Expected Outcomes**:
- Complete end-to-end document processing
- No storage access errors
- Proper webhook URL usage
- Successful job completion

## 📊 **FRACAS Documentation Requirements**

### **Update FM-011 Document**:
1. **Add investigation findings** to the "Investigation Steps" section
2. **Update resolution status** based on findings
3. **Document any new issues** discovered during investigation
4. **Add test results** and verification steps
5. **Update status** to "Resolved" if all issues are fixed

### **Create New FRACAS Documents** (if needed):
- **FM-012**: If storage access issue requires separate tracking
- **FM-013**: If webhook URL deployment requires separate tracking
- **FM-014**: If new issues are discovered during investigation

## 🚨 **Critical Success Criteria**

- [ ] **Storage Access**: Supabase storage downloads work without 400 errors
- [ ] **Webhook URL**: Worker uses production URL instead of localhost
- [ ] **End-to-End**: Complete document processing pipeline works
- [ ] **Documentation**: All findings and fixes properly documented in FRACAS
- [ ] **Testing**: Comprehensive testing completed and documented

## 📁 **Key Files to Review**

- `docs/initiatives/deployment/20250918_mvp_production_deployment/fracas/FM_011_worker_storage_and_fallback_failure.md`
- `config/render/render.yaml` (webhook URL configuration)
- `backend/workers/enhanced_base_worker.py` (storage download logic)
- `api/upload_pipeline/main.py` (API upload handling)
- Supabase storage configuration and RLS policies

## 🔧 **Tools Available**

- **Database Access**: Supabase production database queries
- **Log Analysis**: Worker and API service logs
- **Configuration Management**: Render deployment configuration
- **Testing**: End-to-end upload and processing tests

## ⚠️ **Important Notes**

1. **This is a production system** - be careful with any changes
2. **Document everything** - all findings must be recorded in FRACAS
3. **Test thoroughly** - verify fixes work before marking as resolved
4. **Coordinate with team** - this affects the entire document processing pipeline
5. **Priority is high** - this is blocking all document uploads

## 🎯 **Success Definition**

The investigation is complete when:
- All storage access issues are identified and resolved
- Webhook URL configuration is properly deployed
- End-to-end document processing works without errors
- All findings are documented in appropriate FRACAS documents
- System is ready for normal operation

---

**Created**: 2025-09-18  
**Priority**: High  
**Assigned**: Investigation Team  
**Dependencies**: FM-011, FM-008, FM-009, FM-010
