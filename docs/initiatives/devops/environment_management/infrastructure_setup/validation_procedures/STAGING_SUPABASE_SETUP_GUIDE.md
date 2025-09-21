# Staging Supabase Setup Guide

**Date**: September 21, 2025  
**Status**: ⚠️ **REQUIRES MANUAL SETUP**  
**Environment**: Staging Supabase Instance  

## 🎯 **Current Status**

The staging Supabase instance is **accessible but empty**. It needs to be manually configured with the database schema.

### **Staging Supabase Details**
- **URL**: `***REMOVED***`
- **Status**: ✅ Accessible
- **Database Schema**: ❌ Empty (no tables)
- **API Endpoints**: ❌ No tables available

## 🔧 **Manual Setup Required**

Since the staging Supabase instance doesn't have the `exec_sql` function and direct database connection is failing, you'll need to set up the database schema manually through the Supabase Dashboard.

### **Step 1: Access Supabase Dashboard**

1. **Go to**: [Supabase Dashboard](https://supabase.com/dashboard)
2. **Select Project**: `dfgzeastcxnoqshgyotp` (staging instance)
3. **Navigate to**: SQL Editor

### **Step 2: Apply Database Migrations**

Run the following SQL scripts in order in the Supabase SQL Editor:

#### **Migration 1: Enable Vector Extension**
```sql
-- 20250707000000_enable_vector_extension.sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### **Migration 2: Initialize Database Tables**
```sql
-- 20250708000000_init_db_tables.sql
-- (Run the content from supabase/migrations/20250708000000_init_db_tables.sql)
```

#### **Migration 3: Upload Pipeline Schema**
```sql
-- 20250814000000_init_upload_pipeline.sql
-- (Run the content from supabase/migrations/20250814000000_init_upload_pipeline.sql)
```

#### **Migration 4: Users Table**
```sql
-- 20250904000000_create_users_table.sql
-- (Run the content from supabase/migrations/20250904000000_create_users_table.sql)
```

#### **Migration 5: Storage Policies**
```sql
-- 20250918201725_add_storage_select_policy.sql
-- (Run the content from supabase/migrations/20250918201725_add_storage_select_policy.sql)
```

### **Step 3: Verify Setup**

After applying all migrations, test the setup:

```bash
# Test users table
curl -s "***REMOVED***/rest/v1/users" \
  -H "apikey: ***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM"

# Test documents table
curl -s "***REMOVED***/rest/v1/upload_pipeline.documents" \
  -H "apikey: ***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM"
```

## 🔄 **Alternative: Use Supabase CLI**

If you have the Supabase CLI installed, you can apply migrations directly:

```bash
# Set up Supabase CLI
supabase login

# Link to staging project
supabase link --project-ref dfgzeastcxnoqshgyotp

# Apply migrations
supabase db push
```

## 📊 **Expected Schema After Setup**

### **Public Schema**
- `users` - User profiles and authentication data

### **Upload Pipeline Schema**
- `documents` - Document metadata and processing status
- `upload_jobs` - Job queue for document processing
- `document_chunks` - Processed document chunks with embeddings
- `events` - Processing events and logging
- `document_vector_buffer` - Write-ahead buffer for embeddings

### **Storage Buckets**
- `raw` - Raw uploaded documents (private)
- `parsed` - Parsed document content (private)

## 🎯 **Next Steps After Setup**

1. **Test API Endpoints**: Verify all tables are accessible via REST API
2. **Test Authentication**: Ensure user registration and login work
3. **Test File Upload**: Verify document upload pipeline works
4. **Update Environment Variables**: Ensure staging service uses correct Supabase instance

## 🚨 **Important Notes**

- **Database Connection**: Direct database connection is currently failing due to authentication issues
- **API Access**: REST API is accessible but no tables are available
- **Manual Setup Required**: Database schema must be applied manually through Supabase Dashboard
- **Migration Order**: Apply migrations in the correct order to avoid dependency issues

---

**Setup Status**: ⚠️ **PENDING MANUAL SETUP**  
**Estimated Time**: 15-30 minutes  
**Priority**: **HIGH** (Required for staging environment functionality)
