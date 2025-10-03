# FM-027 Local Replication Investigation Prompt

## Status: PARTIALLY RESOLVED - Local Replication Required

**Date**: October 1, 2025, 00:20 UTC  
**Investigation Phase**: Local Development Replication  
**Previous Work**: Staging environment fixes deployed but storage access still failing

---

## Investigation Summary

### ✅ **Issues Identified and Fixed in Staging**

1. **Supabase Storage Authentication** - FIXED
   - **Problem**: Incorrect header order causing 400 Bad Request
   - **Solution**: Updated headers to match StorageManager pattern
   - **Status**: Deployed to staging (commit: `cc04c4f`)

2. **Webhook URL Configuration** - FIXED  
   - **Problem**: Hardcoded production URL for staging environment
   - **Solution**: Environment-specific URL logic + flexible env vars
   - **Status**: Deployed to staging (commit: `ea783fd`)

3. **Service Role Key** - FIXED
   - **Problem**: Invalid service role key with `.example` suffix
   - **Solution**: Updated with correct service role key
   - **Status**: Deployed to staging (deploy: `dep-d3e76pbipnbc73bi7vi0`)

### ❌ **Ongoing Issue: Storage Access Still Failing**

**Current Failure Pattern:**
```json
{
  "error": "Bucket not found",
  "statusCode": "404",
  "url": "https://your-staging-project.supabase.co/storage/v1/object/files/user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/a61afcc6_36d295c4.pdf"
}
```

**Key Observations:**
- File exists in staging database (`upload_pipeline.documents` table)
- File exists in staging storage (`storage.objects` table)
- Bucket configuration appears correct (`storage.buckets` table)
- Service role key is correct
- Still getting "Bucket not found" error

---

## Local Replication Investigation

### **Objective**
Replicate the FM-027 failure locally in the development environment to:
1. Isolate the root cause without affecting staging/production
2. Test different storage configurations
3. Debug the storage access issue step-by-step
4. Verify fixes before deploying to staging

### **Environment Setup**

#### **1. Start Local Development Environment**
```bash
# Navigate to project root
cd /Users/aq_home/1Projects/accessa/insurance_navigator

# Start local Supabase (if not already running)
supabase start

# Start local development services
docker-compose up -d

# Or start individual services
python -m uvicorn main:app --reload --port 8000
```

#### **2. Configure Environment Variables**
```bash
# Copy staging environment configuration
cp config/env.development.example .env.development

# Set up local Supabase configuration
export SUPABASE_URL="http://127.0.0.1:54321"
export SUPABASE_ANON_KEY="your_local_anon_key"
export SUPABASE_SERVICE_ROLE_KEY="your_local_service_role_key"
export ENVIRONMENT="development"
```

#### **3. Verify Local Supabase Storage**
```bash
# Check if local Supabase is running
curl http://127.0.0.1:54321/health

# Check storage buckets
curl -H "apikey: $SUPABASE_ANON_KEY" \
     "http://127.0.0.1:54321/storage/v1/bucket"

# Check if files bucket exists
curl -H "apikey: $SUPABASE_ANON_KEY" \
     "http://127.0.0.1:54321/storage/v1/bucket/files"
```

---

## Investigation Steps

### **Step 1: Replicate the Exact Failure**

#### **1.1 Upload a Test Document**
```bash
# Use the test document from the failing case
curl -X POST "http://localhost:8000/api/upload-pipeline/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@examples/scan_classic_hmo.pdf" \
     -F "user_id=test-user-123"
```

#### **1.2 Monitor Worker Processing**
```bash
# Check worker logs
tail -f logs/worker.log

# Or check Docker logs
docker-compose logs -f worker
```

#### **1.3 Check Database State**
```sql
-- Connect to local database
psql postgresql://postgres:postgres@localhost:54322/postgres

-- Check upload jobs
SELECT * FROM upload_pipeline.upload_jobs ORDER BY created_at DESC LIMIT 5;

-- Check documents
SELECT * FROM upload_pipeline.documents ORDER BY created_at DESC LIMIT 5;

-- Check storage objects
SELECT * FROM storage.objects WHERE bucket_id = 'files' ORDER BY created_at DESC LIMIT 5;
```

### **Step 2: Debug Storage Access**

#### **2.1 Test Storage Access Directly**
```bash
# Test with local Supabase
curl -H "apikey: $SUPABASE_ANON_KEY" \
     -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
     "http://127.0.0.1:54321/storage/v1/object/files/user/test-user-123/raw/test-file.pdf" \
     -v
```

#### **2.2 Test Different Storage URLs**
```bash
# Test different URL formats
curl "http://127.0.0.1:54321/storage/v1/object/files/user/test-user-123/raw/test-file.pdf"
curl "http://127.0.0.1:54321/storage/v1/object/files/user/test-user-123/raw/test-file.pdf"
curl "http://127.0.0.1:54321/storage/v1/object/files/user/test-user-123/raw/test-file.pdf"
```

#### **2.3 Check Storage Policies**
```sql
-- Check storage policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'storage' AND tablename = 'objects';
```

### **Step 3: Test Worker Code Changes**

#### **3.1 Modify Worker Storage Access**
```python
# In backend/workers/enhanced_base_worker.py
# Add debug logging around line 1367-1377

async with httpx.AsyncClient() as storage_client:
    # Add debug logging
    self.logger.info(f"Attempting storage access: {storage_url}/storage/v1/object/{bucket}/{key}")
    self.logger.info(f"Headers: {headers}")
    
    response = await storage_client.get(
        f"{storage_url}/storage/v1/object/{bucket}/{key}",
        headers=headers
    )
    
    # Add response debugging
    self.logger.info(f"Storage response status: {response.status_code}")
    self.logger.info(f"Storage response headers: {dict(response.headers)}")
    self.logger.info(f"Storage response body: {response.text}")
    
    response.raise_for_status()
```

#### **3.2 Test Different Storage Configurations**
```python
# Test different storage URL formats
storage_urls = [
    "http://127.0.0.1:54321",
    "http://localhost:54321", 
    "http://127.0.0.1:54321/storage/v1",
]

# Test different authentication methods
auth_methods = [
    {"apikey": service_role_key, "Authorization": f"Bearer {service_role_key}"},
    {"Authorization": f"Bearer {service_role_key}"},
    {"apikey": service_role_key},
]
```

### **Step 4: Compare with Working Production**

#### **4.1 Test Production Storage Access**
```bash
# Test production storage access (if accessible)
curl -H "apikey: $PROD_SUPABASE_ANON_KEY" \
     -H "Authorization: Bearer $PROD_SUPABASE_SERVICE_ROLE_KEY" \
     "https://your-project.supabase.co/storage/v1/object/files/user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/a61afcc6_36d295c4.pdf" \
     -I
```

#### **4.2 Compare Storage Configurations**
```sql
-- Compare bucket configurations
-- Local
SELECT * FROM storage.buckets;

-- Staging  
SELECT * FROM storage.buckets;

-- Production
SELECT * FROM storage.buckets;
```

---

## Expected Outcomes

### **Success Criteria**
1. **Local Replication**: Successfully reproduce the "Bucket not found" error locally
2. **Root Cause Identification**: Identify why storage access is failing
3. **Fix Validation**: Test and validate fixes locally before staging deployment
4. **Documentation**: Document the exact steps to reproduce and fix the issue

### **Potential Root Causes to Investigate**
1. **Storage Service Configuration**: Local Supabase storage not properly configured
2. **Authentication Issues**: Service role key or authentication method problems
3. **URL Format Issues**: Incorrect storage URL construction
4. **Bucket Policy Issues**: Storage policies preventing access
5. **File Path Issues**: Incorrect file path construction
6. **Environment Variable Issues**: Missing or incorrect environment variables

### **Debugging Tools**
1. **Enhanced Logging**: Add detailed logging to worker storage access
2. **Storage API Testing**: Direct API calls to test different configurations
3. **Database Inspection**: Check database state at each step
4. **Network Analysis**: Use curl/wget to test different URL formats
5. **Code Comparison**: Compare with working production code

---

## Next Steps After Local Replication

### **If Local Replication Succeeds**
1. **Identify Root Cause**: Document the exact cause of the storage access failure
2. **Implement Fix**: Apply the fix locally and test
3. **Deploy to Staging**: Deploy the fix to staging environment
4. **Verify Resolution**: Confirm the issue is resolved in staging

### **If Local Replication Fails**
1. **Environment Issues**: Check local development environment setup
2. **Configuration Issues**: Verify local Supabase configuration
3. **Code Issues**: Check if local code differs from staging
4. **Dependencies**: Verify all required services are running

---

## Files to Monitor

### **Worker Code**
- `backend/workers/enhanced_base_worker.py` (lines 1350-1390)
- `backend/workers/database_config.py`
- `backend/shared/storage/storage_manager.py`

### **Configuration Files**
- `.env.development`
- `config/environment/staging.yaml`
- `docker-compose.yml`

### **Log Files**
- `logs/worker.log`
- `logs/api.log`
- Docker container logs

---

## Success Metrics

1. **Reproduction**: Can reproduce the exact failure locally
2. **Isolation**: Can isolate the root cause
3. **Fix**: Can implement and test a fix locally
4. **Validation**: Can validate the fix resolves the issue
5. **Deployment**: Can deploy the fix to staging successfully

---

**Investigation Priority**: HIGH  
**Estimated Time**: 2-4 hours  
**Dependencies**: Local development environment, Supabase CLI, Docker  
**Testing Requirement**: MANDATORY local testing before staging deployment

---

*This prompt provides a comprehensive approach to replicating the FM-027 failure locally and systematically debugging the storage access issue.*
