# FRACAS FM-012: Resolution Checklist

**Date:** 2025-09-25T02:12:05  
**Status:** Ready for Resolution  
**Estimated Time:** 7 minutes

## ✅ **Investigation Phase (COMPLETED)**

- [x] Root cause identified: Missing storage policy
- [x] Environment variables verified and corrected
- [x] Worker service confirmed online but failing
- [x] API service confirmed healthy
- [x] Comprehensive testing scripts created
- [x] All investigation files organized
- [x] MCP logs analyzed and confirmed findings

## 🔧 **Resolution Phase (READY TO EXECUTE)**

### **Step 1: Apply Storage Policy (5 minutes)**
- [ ] Navigate to Supabase SQL Editor
  - URL: https://supabase.com/dashboard/project/your-staging-project/sql
- [ ] Execute storage policy SQL:
  ```sql
  CREATE POLICY "Allow service role to download files"
  ON storage.objects
  FOR SELECT
  TO service_role
  USING (bucket_id = 'files');
  ```
- [ ] Verify policy creation:
  ```sql
  SELECT policyname, permissive, roles, cmd, qual 
  FROM pg_policies 
  WHERE tablename = 'objects' 
  AND schemaname = 'storage'
  AND policyname = 'Allow service role to download files';
  ```

### **Step 2: Verify Fix (2 minutes)**
- [ ] Run comprehensive test suite:
  ```bash
  cd /Users/aq_home/1Projects/accessa/insurance_navigator
  export $(cat .env.staging | grep -v '^#' | xargs)
  python docs/incidents/FRACAS_FM_012_investigation_files/staging_manual_test_suite.py
  ```
- [ ] Confirm all 8 tests pass
- [ ] Verify storage access returns 200 OK

### **Step 3: End-to-End Testing (Optional)**
- [ ] Test document upload workflow
- [ ] Verify worker processes documents successfully
- [ ] Check worker logs for successful processing
- [ ] Confirm no more 400 Bad Request errors

## 📊 **Success Metrics**

### **Before Fix:**
- Storage Access: ❌ FAIL (400 Bad Request)
- Storage Policies: ❌ FAIL (Policy missing)
- Test Success Rate: 25% (2/8 tests)
- Worker Status: Online but failing

### **After Fix (Expected):**
- Storage Access: ✅ PASS (200 OK)
- Storage Policies: ✅ PASS (Policy exists)
- Test Success Rate: 100% (8/8 tests)
- Worker Status: Online and processing successfully

## 🚨 **Rollback Plan**

If issues arise after applying the policy:
1. **Remove the policy:**
   ```sql
   DROP POLICY "Allow service role to download files" ON storage.objects;
   ```
2. **Investigate further** using existing test scripts
3. **Contact support** if needed

## 📋 **Documentation**

### **Files Created:**
- `FRACAS_FM_012_STATUS_UPDATE.md` - Current status
- `FRACAS_FM_012_ACTION_REQUIRED.md` - Action needed
- `FRACAS_FM_012_RESOLUTION_CHECKLIST.md` - This checklist
- `staging_manual_test_suite.py` - Validation script
- `FINAL_STAGING_TEST_REPORT.md` - Complete analysis

### **Files Organized:**
- All investigation files moved to `docs/incidents/FRACAS_FM_012_investigation_files/`

## 🎯 **Next Steps After Resolution**

1. **Monitor worker logs** for 24 hours
2. **Test production-like scenarios** in staging
3. **Document lessons learned** for future incidents
4. **Update monitoring** to catch similar issues
5. **Verify all environments** have consistent policies

---

**Ready for execution:** ✅  
**Estimated resolution time:** 7 minutes  
**Confidence level:** High (root cause confirmed)
