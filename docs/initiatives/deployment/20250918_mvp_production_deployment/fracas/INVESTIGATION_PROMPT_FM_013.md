# Investigation Prompt: FM-013 API Service Database Connection Failure

## 📋 **Current Status**

**FM-013 Status**: IDENTIFIED ❌  
**Priority**: Critical  
**Component**: API Service Database Connection  

### **Issues Identified** ❌
- **Database Connection**: API service trying to connect to localhost:54321 in production
- **Configuration Issue**: `db_pool.py` hardcoded to use local Supabase instance
- **Environment Variables**: Not using production Supabase URL from environment
- **Service Impact**: API service cannot process webhooks due to database connection failure

### **Issues Resolved** ✅
- **Database Pool Configuration**: Fixed `db_pool.py` to use environment variables instead of hardcoded localhost
- **Code Deployment**: Database pool fix committed and pushed to repository
- **Partial Webhook Processing**: API service can receive webhooks and parse content successfully

### **Issues Still Pending** ❌
- **Deployment Status**: Database pool fix not yet deployed to production (deployment stuck in build_in_progress)
- **Database Connection**: Still seeing "All connection attempts failed" errors in webhook processing
- **Complete Pipeline**: Webhook processing fails at database connection step

## 🚨 **Critical Success Criteria**

- [ ] **Database Connection**: API service connects to production Supabase database
- [ ] **Configuration Fix**: `db_pool.py` uses environment variables instead of hardcoded localhost
- [ ] **Webhook Processing**: API service can process LlamaParse webhooks successfully
- [ ] **End-to-End**: Complete document processing pipeline works
- [ ] **Documentation**: All findings and fixes properly documented

## 🔍 **Root Cause Analysis**

### **Primary Issue**
API service is hardcoded to connect to `http://127.0.0.1:54321` (local Supabase instance) instead of using the production Supabase URL from environment variables.

### **Evidence**
- **Error**: `httpx.ConnectError: All connection attempts failed` when trying to connect to `127.0.0.1:54321`
- **Location**: `db/services/db_pool.py` line 61: `url = "http://127.0.0.1:54321"`
- **Impact**: API service cannot process webhooks, blocking document processing pipeline

### **Root Cause**
The `_create_client()` function in `db_pool.py` is hardcoded to use local development settings instead of reading from environment variables like the `SupabaseConfig` class does.

## 🔧 **Proposed Fixes**

### **1. Fix Database Pool Configuration**
- **Action**: Modify `db_pool.py` to use `SupabaseConfig.from_env()` instead of hardcoded values
- **Method**: Replace hardcoded URL and token generation with proper configuration
- **Status**: Pending

### **2. Environment Variable Validation**
- **Action**: Ensure production API service has correct Supabase environment variables
- **Method**: Verify `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_ANON_KEY` are set
- **Status**: Pending

### **3. Test Webhook Processing**
- **Action**: Verify API service can process webhooks after database connection fix
- **Method**: Test complete document processing pipeline
- **Status**: Pending

## 🧪 **Testing Plan**

### **Immediate Verification**
1. **Check Environment Variables**: Verify production API service has correct Supabase credentials
2. **Fix Database Pool**: Update `db_pool.py` to use environment configuration
3. **Test Connection**: Verify API service can connect to production database

### **End-to-End Testing**
1. **Upload Test Document**: Use existing test file
2. **Monitor Webhook Processing**: Check API service logs for successful webhook processing
3. **Verify Complete Pipeline**: Ensure document processing completes successfully

## 📊 **Expected Results**

### **API Service Logs Should Show**
```
Successfully created Supabase client
Database pool initialized successfully
```

### **Webhook Processing Should Work**
- API service receives LlamaParse webhooks
- Database operations succeed
- Document processing completes

## 🔄 **Next Steps**

1. **Fix Database Pool**: Update `db_pool.py` to use proper configuration
2. **Verify Environment**: Check production API service environment variables
3. **Test Connection**: Verify database connection works
4. **End-to-End Test**: Test complete document processing pipeline
5. **Update Status**: Mark FM-013 as resolved if successful

## 📁 **Files to Modify**

- `db/services/db_pool.py` - Fix hardcoded database connection
- Production API service environment variables - Verify correct Supabase credentials

## 🎯 **Success Metrics**

- ✅ API service connects to production Supabase database
- ✅ Webhook processing works without connection errors
- ✅ Document processing pipeline completes successfully
- ✅ No localhost references in production logs

## 📝 **Notes**

This issue is preventing the API service from processing webhooks, which blocks the entire document processing pipeline. The fix should be straightforward - replace hardcoded localhost configuration with proper environment variable usage.
