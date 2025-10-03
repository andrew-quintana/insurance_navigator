# FM-033 Local Replication Prompt

## Purpose
This prompt guides the investigation agent through replicating the Supabase authentication 400 errors locally to identify the root cause.

## Prerequisites
- Python 3.8+ installed
- Access to Supabase MCP
- Access to Vercel MCP
- Local development environment set up

---

## Step 1: Environment Setup

### **1.1 Clone and Setup Repository**
```bash
git clone https://github.com/andrew-quintana/insurance_navigator.git
cd insurance_navigator
git checkout fix-vercel-deployment-fm032
```

### **1.2 Install Dependencies**
```bash
cd ui
npm install --legacy-peer-deps
```

### **1.3 Set Environment Variables**
Create `.env.local` file in `ui/` directory:
```bash
NEXT_PUBLIC_SUPABASE_URL=https://dfgzeastcxnoqshgyotp.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM
NEXT_PUBLIC_API_BASE_URL=https://insurance-navigator-staging-api.onrender.com
NEXT_PUBLIC_API_URL=https://insurance-navigator-staging-api.onrender.com
NODE_ENV=staging
```

---

## Step 2: Run Authentication Tests

### **2.1 Run Supabase Authentication Tests**
```bash
cd docs/fm_033
python test_supabase_auth.py
```

**Expected Output**: Test results showing which authentication components are failing

### **2.2 Run Vercel Environment Variable Tests**
```bash
python test_vercel_env_vars.py
```

**Expected Output**: Test results showing environment variable configuration status

---

## Step 3: Local Development Server

### **3.1 Start Development Server**
```bash
cd ui
npm run dev
```

### **3.2 Access Application**
Open browser to `http://localhost:3000`

### **3.3 Test Authentication Flow**
1. Navigate to login page
2. Open browser developer tools (F12)
3. Go to Console tab
4. Attempt to log in
5. Observe console errors

**Expected Behavior**: Should see the same 400 error:
```
[Log] Auth state changed: – "INITIAL_SESSION" – undefined
[Error] Failed to load resource: the server responded with a status of 400 () (token, line 0)
```

---

## Step 4: Supabase Configuration Verification

### **4.1 Check Supabase Dashboard**
```bash
# Use Supabase MCP to check configuration
mcp_supabase_production_get_project_url
mcp_supabase_production_get_anon_key
```

### **4.2 Verify API Key Permissions**
1. Go to Supabase dashboard
2. Navigate to Settings > API
3. Check API key permissions
4. Verify JWT secret configuration

### **4.3 Check Authentication Settings**
1. Go to Authentication > Settings
2. Verify authentication providers
3. Check JWT settings
4. Review CORS configuration

---

## Step 5: Direct API Testing

### **5.1 Test Supabase Auth Endpoint**
```bash
curl -X POST "https://dfgzeastcxnoqshgyotp.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}' \
  -v
```

**Expected**: Should return 400 for invalid credentials, but endpoint should respond

### **5.2 Test Supabase REST API**
```bash
curl -H "apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM" \
  "https://dfgzeastcxnoqshgyotp.supabase.co/rest/v1/" \
  -v
```

**Expected**: Should return 200 OK

---

## Step 6: Code Analysis

### **6.1 Review Supabase Client Configuration**
```bash
cat ui/lib/supabase-client.ts
```

**Check for**:
- Correct environment variable usage
- Proper client initialization
- JWT configuration

### **6.2 Review Authentication Components**
```bash
find ui/components -name "*auth*" -o -name "*Auth*" | head -5
```

**Check for**:
- Authentication request format
- Token handling
- Session management

### **6.3 Review Environment Variable Usage**
```bash
grep -r "NEXT_PUBLIC_SUPABASE" ui/
```

**Check for**:
- Correct variable names
- Proper usage patterns
- Missing variables

---

## Step 7: Network Analysis

### **7.1 Monitor Network Requests**
1. Open browser developer tools
2. Go to Network tab
3. Attempt authentication
4. Look for failed requests

**Look for**:
- 400 status codes
- Request payloads
- Response headers
- CORS errors

### **7.2 Check Request Headers**
**Verify**:
- `apikey` header present
- `Content-Type` header correct
- `Authorization` header format
- CORS headers

---

## Step 8: Hypothesis Testing

### **8.1 Test H1: API Key Permissions**
- Check Supabase dashboard for API key roles
- Verify policies allow authentication
- Test with different API keys

### **8.2 Test H2: JWT Configuration**
- Compare JWT secret between environments
- Test token generation and validation
- Check JWT settings in Supabase

### **8.3 Test H3: Environment Variables**
- Verify variables are set correctly
- Test variable availability at runtime
- Check for typos or incorrect names

### **8.4 Test H4: Request Format**
- Review authentication request payloads
- Check for missing required parameters
- Validate request structure

### **8.5 Test H5: Environment Conflicts**
- Check for rate limiting
- Test with different environments
- Verify shared resource access

---

## Step 9: Documentation

### **9.1 Record Test Results**
```bash
# Save test results
cp fm033_supabase_auth_test_*.json docs/fm_033/
cp fm033_vercel_env_vars_test_*.json docs/fm_033/
```

### **9.2 Update Investigation Status**
Update `hypotheses_ledger.md` with test results

### **9.3 Document Findings**
Update `ROOT_CAUSE_ANALYSIS.md` with findings

---

## Expected Outcomes

### **If H1 is Correct (API Key Issues)**
- API key permissions will be insufficient
- Supabase dashboard will show authorization errors
- Fix: Update API key roles and policies

### **If H2 is Correct (JWT Mismatch)**
- JWT secret will be misaligned
- Token validation will fail
- Fix: Align JWT configuration between environments

### **If H3 is Correct (Environment Variables)**
- Variables will be missing or incorrect
- Runtime access will fail
- Fix: Correct environment variable configuration

### **If H4 is Correct (Request Format)**
- Authentication requests will be malformed
- Required parameters will be missing
- Fix: Correct request format and parameters

### **If H5 is Correct (Environment Conflicts)**
- Rate limiting or conflicts will be detected
- Shared resources will cause issues
- Fix: Separate environments or resolve conflicts

---

## Troubleshooting

### **Common Issues**
1. **Environment Variables Not Set**: Check `.env.local` file
2. **Supabase Connection Failed**: Verify URL and API key
3. **CORS Errors**: Check Supabase CORS configuration
4. **JWT Errors**: Verify JWT secret configuration

### **Debug Commands**
```bash
# Check environment variables
env | grep NEXT_PUBLIC

# Test Supabase connectivity
curl -I https://dfgzeastcxnoqshgyotp.supabase.co

# Check local server
curl -I http://localhost:3000
```

---

## Success Criteria

### **Replication Successful When**
1. ✅ Same 400 error reproduced locally
2. ✅ Root cause identified through testing
3. ✅ Fix implemented and validated
4. ✅ Authentication working end-to-end

### **Investigation Complete When**
1. ✅ All hypotheses tested
2. ✅ Root cause documented
3. ✅ Solution implemented
4. ✅ Tests passing

---

**Last Updated**: January 2025  
**Next Review**: After replication attempt  
**Investigation Lead**: TBD
