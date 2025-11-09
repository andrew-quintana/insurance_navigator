# FRACAS FM-012: ACTION REQUIRED - Storage Policy Application

**Date:** 2025-09-25T02:12:05  
**Status:** 🚨 **IMMEDIATE ACTION REQUIRED**  
**Priority:** P0 - Critical Production Issue

## 🎯 **SINGLE ACTION REQUIRED**

The investigation is complete. The root cause is identified. **Only one action remains:**

### **Apply Storage Policy via Supabase SQL Editor**

1. **Navigate to Supabase SQL Editor:**
   - URL: https://supabase.com/dashboard/project/your-staging-project/sql
   - Project: `your-staging-project` (staging)

2. **Execute this SQL:**
   ```sql
   CREATE POLICY "Allow service role to download files"
   ON storage.objects
   FOR SELECT
   TO service_role
   USING (bucket_id = 'files');
   ```

3. **Verify the policy was created:**
   ```sql
   SELECT policyname, permissive, roles, cmd, qual 
   FROM pg_policies 
   WHERE tablename = 'objects' 
   AND schemaname = 'storage'
   AND policyname = 'Allow service role to download files';
   ```

## 📊 **Current System Status**

### ✅ **Working Components**
- **API Service**: All services initialized successfully
- **Database**: Pool initialized with 5-20 connections
- **Worker Service**: Online and running
- **Environment**: All variables configured correctly

### ❌ **Blocking Issue**
- **Storage Access**: Service role cannot download files (400 Bad Request)
- **Root Cause**: Missing RLS policy for service role file downloads
- **Impact**: Document processing pipeline completely blocked

## 🔍 **Evidence**

### **Worker Logs Confirmation:**
```
Storage download failed, cannot process document: Client error '400 Bad Request' 
for url 'https://your-staging-project.supabase.co/storage/v1/object/files/user/...'
```

### **Test Results Confirmation:**
- Storage Access: ❌ FAIL (400 Bad Request)
- Storage Policies: ❌ FAIL (Policy does not exist)
- Overall Success Rate: 25% (2/8 tests passed)

## ⏱️ **Timeline**

- **Investigation Time**: 2+ hours (completed)
- **Fix Time**: 5 minutes (SQL execution)
- **Verification Time**: 2 minutes (re-run tests)
- **Total Resolution Time**: 7 minutes

## 🎯 **Success Criteria**

After applying the storage policy:
- [ ] Storage access returns 200 OK
- [ ] Worker can download files from storage
- [ ] Document processing jobs complete successfully
- [ ] No more 400 Bad Request errors in worker logs
- [ ] Test suite shows 8/8 tests passed

## 📋 **Verification Steps**

1. **Apply the SQL policy** (above)
2. **Run validation test:**
   ```bash
   cd /Users/aq_home/1Projects/accessa/insurance_navigator
   export $(cat .env.staging | grep -v '^#' | xargs)
   python docs/incidents/FRACAS_FM_012_investigation_files/staging_manual_test_suite.py
   ```
3. **Check worker logs** for successful processing
4. **Test end-to-end** document upload and processing

---

**Status:** Ready for immediate action  
**Blocking:** Production functionality  
**Resolution:** Single SQL command execution
