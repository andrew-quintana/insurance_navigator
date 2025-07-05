# Edge Functions Deployment Checklist

**Project**: `jhrespvvhbnloxrieycf.supabase.co`  
**Required for**: Phase 5 Vector Processing Pipeline  
**Estimated Time**: 5-10 minutes

## 📋 **Pre-Deployment Checklist**

- [ ] **Supabase CLI Installed**: `npm install -g supabase`
- [ ] **Project Linked**: Have project reference ID ready
- [ ] **Environment Variables**: Configured in Supabase Dashboard
- [ ] **Code Ready**: Edge Functions in `db/supabase/functions/`

## 🚀 **Deployment Options**

### **Option A: Supabase CLI (Recommended)**

```bash
# 1. Install Supabase CLI
npm install -g supabase

# 2. Login to Supabase
supabase auth login

# 3. Link to your project
supabase link --project-ref jhrespvvhbnloxrieycf

# 4. Deploy all functions
supabase functions deploy

# 5. Verify deployment
supabase functions list
```

### **Option B: Supabase Dashboard**

1. Go to [Supabase Dashboard](https://supabase.com/dashboard/project/jhrespvvhbnloxrieycf)
2. Navigate to **Edge Functions**
3. Click **Create a new function**
4. Copy-paste code from each function file:
   - `upload-handler` → `db/supabase/functions/upload-handler/index.ts`
   - `processing-webhook` → `db/supabase/functions/processing-webhook/index.ts`
   - `progress-tracker` → `db/supabase/functions/progress-tracker/index.ts`

## 🔧 **Environment Variables Required**

Ensure these are set in **Project Settings** → **Edge Functions**:

```bash
# LlamaParse Integration
LLAMAPARSE_API_KEY=llx-your-key-here
LLAMAPARSE_BASE_URL=https://api.cloud.llamaindex.ai

# Supabase Configuration (Auto-configured)
SUPABASE_URL=https://jhrespvvhbnloxrieycf.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Database Connection (Auto-configured)
DATABASE_URL=your-connection-string

# Webhook Configuration (Optional)
WEBHOOK_SECRET=""
```

## ✅ **Post-Deployment Verification**

After deployment, verify each function:

### **1. Upload Handler**
```bash
curl -X POST https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/upload-handler \
  -H "Content-Type: application/json" \
  -d '{}'
# Expected: 401 Unauthorized (correct - needs auth)
```

### **2. Processing Webhook**
```bash
curl -X POST https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/processing-webhook \
  -H "Content-Type: application/json" \
  -d '{"source": "test", "status": "completed"}'
# Expected: 404 or error (correct - needs valid document)
```

### **3. Progress Tracker**
```bash
curl https://jhrespvvhbnloxrieycf.supabase.co/functions/v1/progress-tracker
# Expected: 401 Unauthorized (correct - needs auth)
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Function Not Found (404)**
   - Check function name spelling
   - Verify deployment completed successfully
   - Check project reference ID

2. **Import Errors**
   - Ensure `_shared/` directory is included
   - Verify Deno import URLs are correct
   - Check TypeScript syntax

3. **Environment Variables Missing**
   - Add missing variables in Dashboard
   - Redeploy functions after adding variables

4. **CORS Issues**
   - Check `corsHeaders` in function code
   - Verify OPTIONS method handling

### **Debug Commands**

```bash
# Check function logs
supabase functions logs upload-handler

# Re-deploy specific function
supabase functions deploy upload-handler

# Test locally (optional)
supabase functions serve
```

## 📊 **Deployment Success Criteria**

- [ ] **All 3 functions deployed**: `upload-handler`, `processing-webhook`, `progress-tracker`
- [ ] **Functions respond to requests**: Even with 401/404 (authentication required)
- [ ] **Environment variables set**: LlamaParse API key configured
- [ ] **CORS working**: OPTIONS requests return 200/204
- [ ] **Logs accessible**: Can view function logs in dashboard

## 🎯 **Phase 5 Readiness**

Once Edge Functions are deployed:

- ✅ **Upload Pipeline**: Ready for document processing
- ✅ **LlamaParse Integration**: Ready for text extraction
- ✅ **Webhook Processing**: Ready for status updates
- ✅ **Progress Tracking**: Ready for real-time updates

**Next Step**: Proceed to Phase 5 - Vector Processing Pipeline

---

**Note**: Edge Functions are the final piece needed for complete Phase 3/4 functionality. Once deployed, the V2 Upload System will be fully operational and ready for Phase 5 vector processing development. 