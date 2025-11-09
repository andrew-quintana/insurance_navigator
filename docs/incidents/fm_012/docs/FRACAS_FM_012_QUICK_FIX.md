# FRACAS FM-012: Quick Fix Reference

**🚨 CRITICAL: Storage Policy Missing**

## ⚡ **IMMEDIATE ACTION (5 minutes)**

### **1. Go to Supabase SQL Editor**
https://supabase.com/dashboard/project/your-staging-project/sql

### **2. Run This SQL**
```sql
CREATE POLICY "Allow service role to download files"
ON storage.objects
FOR SELECT
TO service_role
USING (bucket_id = 'files');
```

### **3. Verify It Worked**
```sql
SELECT policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'objects' 
AND schemaname = 'storage'
AND policyname = 'Allow service role to download files';
```

### **4. Test the Fix**
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
export $(cat .env.staging | grep -v '^#' | xargs)
python docs/incidents/FRACAS_FM_012_investigation_files/staging_manual_test_suite.py
```

## ✅ **Expected Result**
- All 8 tests should pass
- Storage access should return 200 OK
- Worker should process documents successfully

## 📊 **Current Status**
- **API Service**: ✅ Healthy (all services initialized)
- **Worker Service**: ✅ Online but failing on storage access
- **Root Cause**: ❌ Missing storage policy (this fix)
- **Investigation**: ✅ Complete

---

**Time to fix:** 5 minutes  
**Confidence:** High (root cause confirmed)
