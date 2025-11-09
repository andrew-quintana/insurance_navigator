# FM-031 Production Storage Access Failure Investigation Prompt

## 🚨 **CRITICAL PRODUCTION STORAGE ACCESS FAILURE INVESTIGATION**

### **Investigation Assignment**
You are tasked with investigating a critical storage access failure in the production environment that is preventing document processing. This is a **P0 Critical** incident requiring immediate attention.

**IMPORTANT**: This investigation should focus on **environment-specific differences** between staging and production, as the code has been validated in staging and should behave identically.

### **Error Details**
```json
{
  "error": "Non-retryable error: user_facing_error: Document file is not accessible for processing. Please try uploading again. (Reference: 6c0a696e-e954-49cf-ae26-fb266ab0df76)",
  "timestamp": "2025-10-02T05:11:06.777674"
}
```

### **Key Evidence**
1. **File Exists in Storage**: ✅ Confirmed via Supabase Storage interface
2. **Direct Access Works**: ✅ `curl` requests to same URL return 200 OK
3. **Worker Access Fails**: ❌ Worker gets 400 Bad Request consistently
4. **Code Validated in Staging**: ✅ Same code works in staging environment
5. **Environment Differences**: Only Render env vars, Vercel env vars, and Supabase database differ

### **Investigation Steps**

#### **Step 1: Environment Variable Comparison**
Use the Render MCP to compare production worker environment variables with staging:

1. **Get Production Worker Environment Variables**
   - Service ID: `srv-d2h5mr8dl3ps73fvvlog`
   - Compare with staging worker environment variables

2. **Key Variables to Check**
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_STORAGE_URL`
   - `DATABASE_URL`
   - `OPENAI_API_KEY`
   - `LLAMAPARSE_API_KEY`
   - `DOCUMENT_ENCRYPTION_KEY`

#### **Step 2: Supabase Database State Analysis**
Use the Supabase MCP to check database state differences:

1. **Check RLS Policies**
   ```sql
   SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
   FROM pg_policies 
   WHERE schemaname = 'storage' AND tablename = 'objects';
   ```

2. **Check Storage Bucket Configuration**
   ```sql
   SELECT * FROM storage.buckets WHERE name = 'files';
   ```

3. **Check Service Role Permissions**
   - Verify service role key has correct permissions
   - Check if there are any permission differences from staging

#### **Step 3: Network/Infrastructure Analysis**
Test direct storage access from production worker:

1. **Test Storage Access**
   - Use the same URL and headers that the worker is using
   - Compare with working curl requests
   - Check for any network-level differences

2. **Check HTTP Client Configuration**
   - Verify httpx client configuration
   - Check for any header differences
   - Verify timeout and retry settings

#### **Step 4: Vercel Configuration Verification**
Use the Vercel MCP to check frontend configuration:

1. **Check Environment Variables**
   - Verify `NEXT_PUBLIC_API_BASE_URL` is set correctly
   - Check other critical frontend environment variables

2. **Check Deployment Configuration**
   - Verify environment-specific configuration is deployed
   - Check if there are any routing issues

### **Expected Findings**
Based on the evidence, the issue is likely one of:

1. **Environment Variable Mismatch**: Production worker using different environment variables than staging
2. **Supabase Database State Difference**: Production database has different migration state or RLS policies
3. **Network/Infrastructure Issue**: Production worker has different network access than staging
4. **Vercel Configuration Issue**: Frontend environment variables not properly configured

### **Resolution Strategy**
Once the root cause is identified:

1. **Fix Environment Variables**: Update production worker environment variables to match staging
2. **Fix Database State**: Apply missing migrations or fix RLS policies
3. **Fix Network Issues**: Resolve any network-level problems
4. **Fix Vercel Configuration**: Update frontend environment variables

### **Success Criteria**
- [ ] Worker can successfully access files in Supabase Storage
- [ ] Document processing pipeline works end-to-end
- [ ] No more "Document file is not accessible" errors
- [ ] Production behavior matches staging behavior

### **Investigation Tools**
- **Render MCP**: For environment variable comparison
- **Supabase MCP**: For database state analysis
- **Vercel MCP**: For frontend configuration verification
- **Terminal**: For direct testing and validation

### **Priority**
**P0 Critical** - This is blocking all document processing in production and requires immediate attention.

---

**Begin Investigation**: Start with Step 1 (Environment Variable Comparison) and work through each step systematically.
