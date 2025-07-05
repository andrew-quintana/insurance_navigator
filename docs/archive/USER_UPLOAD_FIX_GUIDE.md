# User Upload Vector Processing Fix Guide

**Issue**: User document uploads failing at vectorization stage with 500 error  
**Root Cause**: Invalid OpenAI API key in Supabase Edge Functions secrets  
**Impact**: Regulatory uploads work fine, user uploads fail at vector generation  

## 🔍 Root Cause Analysis

### Why This Happened
1. **Regulatory Processing**: Uses backend server OpenAI API calls (has environment variables)
2. **User Processing**: Uses Supabase Edge Functions (needs secrets, not environment variables)
3. **Invalid API Key**: The OpenAI API key deployed as a secret is invalid/expired

### Evidence from Production Logs
```
2025-06-23T23:06:53.864 - Edge function doc-parser failed: 500
"error":"Vector processing failed"
"details":"Edge Function returned a non-2xx status code"
"stage":"vectorization"
```

### Evidence from Diagnostics
```
OpenAI API failed: 401
"Incorrect API key provided"
```

## 🚀 Immediate Fix (CRITICAL - Do This First)

### Step 1: Get Valid OpenAI API Key
1. **Navigate to OpenAI Dashboard**: https://platform.openai.com/account/api-keys
2. **Create new API key** OR verify existing key is active
3. **Copy the valid API key**

### Step 2: Deploy Secrets Using Supabase CLI
According to [Supabase documentation](https://supabase.com/docs/guides/functions/secrets), Edge Functions use **secrets**, not environment variables.

```bash
# First, set the key in your local environment
export OPENAI_API_KEY=your_valid_openai_key_here

# Then deploy secrets to Supabase
./scripts/deploy_secrets_to_supabase.sh
```

**Alternative: Manual CLI approach**
```bash
# Set secret individually using Supabase CLI
supabase secrets set OPENAI_API_KEY=your_valid_openai_key_here

# Verify it was set
supabase secrets list
```

### Step 3: Verify Secrets Deployment
```bash
# Test that secrets are properly accessible
python scripts/test_supabase_secrets.py
```

## 🛠️ Fix Current Stuck Documents

### Check Production Database for Stuck Documents
```sql
-- Run this in Supabase SQL Editor
SELECT id, original_filename, user_id, status, progress_percentage, 
       created_at, error_message
FROM documents 
WHERE status IN ('vectorizing', 'processing', 'parsing') 
AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

### Option 1: Reset Failed Documents for Retry
```sql
-- Reset stuck documents to allow retry
UPDATE documents 
SET status = 'pending', 
    progress_percentage = 0,
    error_message = 'Reset for retry after API key fix',
    updated_at = NOW()
WHERE status IN ('vectorizing', 'processing', 'parsing') 
AND created_at > NOW() - INTERVAL '24 hours';
```

### Option 2: Use the Emergency Fix SQL
```sql
-- See scripts/fix_specific_stuck_document.sql
-- Creates placeholder vector and marks document as completed
```

## 🔄 Test the Fix

### Test User Upload After Secrets Deployment
1. Upload a small PDF document through the UI
2. Monitor the logs for successful vector processing
3. Verify document shows as "completed" in database
4. Confirm vectors are created in `document_vectors` table

### Verification Queries
```sql
-- Check if new uploads work
SELECT status, progress_percentage, created_at 
FROM documents 
ORDER BY created_at DESC 
LIMIT 5;

-- Verify vectors are being created
SELECT COUNT(*) as vector_count, document_source_type
FROM document_vectors 
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY document_source_type;
```

## 🛡️ Prevention Measures

### 1. Secrets Management Checklist
Ensure these secrets are set in Supabase Edge Functions:
- [x] `OPENAI_API_KEY` - For vector embeddings
- [x] `SUPABASE_URL` - Supabase project URL (default)
- [x] `SUPABASE_SERVICE_ROLE_KEY` - Service role key (default)
- [ ] `LLAMAPARSE_API_KEY` - For advanced PDF parsing (optional)

### 2. Regular Secrets Validation
```bash
# Add to deployment pipeline
python scripts/test_supabase_secrets.py
```

### 3. Monitoring Setup
Add monitoring for Edge Function failures:
```sql
-- Create a view for monitoring document processing
CREATE OR REPLACE VIEW document_processing_health AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    status,
    COUNT(*) as count,
    AVG(progress_percentage) as avg_progress
FROM documents 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), status
ORDER BY hour DESC, status;
```

## 📋 System Architecture Notes

### Why Regulatory Works But User Uploads Don't

**Regulatory Document Processing Flow:**
```
Frontend → Backend API → Unified Processor → Direct OpenAI API calls → Database
```
✅ **Works**: Backend has OPENAI_API_KEY in environment variables

**User Document Processing Flow:**  
```
Frontend → Backend API → Supabase Storage → Edge Functions → OpenAI API → Database
```
❌ **Fails**: Edge Functions need OPENAI_API_KEY as a secret (not environment variable)

### Supabase Secrets vs Environment Variables

| Aspect | Environment Variables | Secrets |
|--------|----------------------|---------|
| **Usage** | Backend applications | Edge Functions |
| **Access Method** | `process.env.VAR_NAME` | `Deno.env.get('SECRET_NAME')` |
| **Deployment** | Set in hosting platform | `supabase secrets set` |
| **Security** | Platform-dependent | Encrypted by Supabase |
| **Visibility** | Often visible in dashboards | Hashed for security |

## 🎯 Success Metrics

After implementing the fix, you should see:
- ✅ User uploads complete with status 'completed'
- ✅ Vector count increases in document_vectors table
- ✅ No 500 errors in Edge Function logs
- ✅ Semantic search works for uploaded documents
- ✅ Regulatory processing continues to work unchanged

## 🔗 Related Documentation

- [Supabase Secrets Management](https://supabase.com/docs/guides/functions/secrets)
- [RCA Report](./RCA_USER_UPLOAD_FAILURE.md)
- [Functionality Validation Report](./FUNCTIONALITY_VALIDATION_REPORT.md)

---

**Priority**: CRITICAL  
**Impact**: User experience severely affected  
**Complexity**: Low (secrets deployment)  
**Time to Fix**: 2 minutes + testing  
**Long-term Solution**: Automated secrets validation in deployment pipeline 