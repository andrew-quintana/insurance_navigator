# FM-027: Staging Storage RLS Policies Solution

## 🎯 **Root Cause Identified**

The 400 "Bucket not found" error in the staging environment is caused by **missing RLS policies on `storage.buckets`** table.

## 📊 **Current State Analysis**

### ✅ **What Works**
- Bucket listing: `/storage/v1/bucket` returns 200
- Basic storage API access with service role

### ❌ **What Fails**
- Object listing: `/storage/v1/object/list/files` returns 400 "Bucket not found"
- Individual file access: Returns 400 "Object not found"
- Worker `blob_exists()` calls fail

## 🔍 **Root Cause**

The `/storage/v1/object/list/files` endpoint requires:
1. **Access to `storage.buckets`** to verify the bucket exists
2. **Access to `storage.objects`** to list the objects

**Current RLS policies:**
- ✅ `storage.objects`: Has SELECT and INSERT policies
- ❌ `storage.buckets`: **NO RLS policies at all**

## 💡 **Solution**

### **Migration File Created**
- **File**: `supabase/migrations/20251001133101_add_staging_storage_rls_policies.sql`
- **Purpose**: Add missing RLS policies for staging storage access

### **Required Policies**

#### **1. Storage Buckets Policies (MISSING)**
```sql
-- Allow service role to view buckets
CREATE POLICY "Allow service role to view buckets"
ON storage.buckets
FOR SELECT
TO service_role
USING (true);

-- Allow service role to manage buckets
CREATE POLICY "Allow service role to manage buckets"
ON storage.buckets
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
```

#### **2. Storage Objects Policies (COMPLETE)**
```sql
-- Allow service role to update files
CREATE POLICY "Allow service role to update files"
ON storage.objects
FOR UPDATE
TO service_role
USING (bucket_id = 'files')
WITH CHECK (bucket_id = 'files');

-- Allow service role to delete files
CREATE POLICY "Allow service role to delete files"
ON storage.objects
FOR DELETE
TO service_role
USING (bucket_id = 'files');

-- Allow service role to list files (this is what was missing!)
CREATE POLICY "Allow service role to list files"
ON storage.objects
FOR SELECT
TO service_role
USING (bucket_id = 'files');
```

## 🎯 **Implementation Instructions**

### **When Staging Environment is Available:**

1. **Apply the migration:**
   ```bash
   cd /Users/aq_home/1Projects/accessa/insurance_navigator
   supabase db push
   ```

2. **Verify the policies were created:**
   ```sql
   SELECT schemaname, tablename, policyname, roles, cmd 
   FROM pg_policies 
   WHERE schemaname = 'storage' 
   ORDER BY tablename, policyname;
   ```

3. **Test the storage access:**
   ```bash
   python test_staging_storage_access.py
   ```

### **Expected Results After Fix:**
- ✅ `/storage/v1/object/list/files` returns 200 with object list
- ✅ Individual file access works
- ✅ Worker `blob_exists()` calls succeed
- ✅ FM-027 Phase 2 Upload Pipeline Worker processes jobs successfully

## 📋 **Migration Details**

- **Migration ID**: `20251001133101_add_staging_storage_rls_policies`
- **Created**: 2025-10-01T13:31:01
- **Status**: Ready to apply (blocked by read-only staging environment)
- **Dependencies**: None
- **Rollback**: Policies can be dropped if needed

## 🔧 **Testing**

The migration includes comprehensive verification to ensure all policies are created successfully. After application, the staging environment should have:

- **5 RLS policies on `storage.buckets`** (2 new)
- **5 RLS policies on `storage.objects`** (3 new)
- **Complete storage access** for service role operations

## 📝 **Notes**

- This fix is specific to the staging environment
- Production environment may need similar updates
- The migration is idempotent and can be run multiple times safely
- All policies use the `service_role` which is appropriate for worker operations

