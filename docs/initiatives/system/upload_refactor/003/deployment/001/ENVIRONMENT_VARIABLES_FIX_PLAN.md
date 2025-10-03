# Environment Variables Fix Plan - Cloud Deployment

## 🚨 **Critical Issues Identified**

### **Root Cause**: Missing Environment Variables
Both the API and Worker services are failing due to missing critical environment variables.

### **Specific Issues**:
1. **Worker Service**: Crashing with exit code 3 due to missing `SUPABASE_URL` and `SUPABASE_KEY`
2. **API Service**: Build failed and health check errors due to missing environment variables
3. **Both Services**: Missing `DATABASE_URL` and other critical configuration

## 📋 **Required Environment Variables**

### **For API Service (insurance-navigator-api)**
```bash
# Core Database & Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=[your_supabase_anon_key]
SERVICE_ROLE_KEY=[your_supabase_service_role_key]
DATABASE_URL=[your_postgresql_connection_string]

# API Configuration
API_BASE_URL=https://insurance-navigator-api.onrender.com
JWT_SECRET_KEY=[your_jwt_secret]
ENVIRONMENT=production
LOG_LEVEL=INFO
SECURITY_BYPASS_ENABLED=false

# External Services
LLAMAPARSE_API_KEY=[your_llamaparse_key]
OPENAI_API_KEY=[your_openai_key]
ANTHROPIC_API_KEY=[your_anthropic_key]
```

### **For Worker Service (insurance_navigator)**
```bash
# Core Database & Supabase (SAME AS API)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=[your_supabase_anon_key]
SERVICE_ROLE_KEY=[your_supabase_service_role_key]
DATABASE_URL=[your_postgresql_connection_string]

# API Configuration
API_BASE_URL=https://insurance-navigator-api.onrender.com
JWT_SECRET_KEY=[your_jwt_secret]
ENVIRONMENT=production
LOG_LEVEL=INFO

# Worker-Specific Configuration
WORKER_POLL_INTERVAL=5
WORKER_MAX_JOBS=10
WORKER_MAX_RETRIES=3

# External Services (SAME AS API)
LLAMAPARSE_API_KEY=[your_llamaparse_key]
OPENAI_API_KEY=[your_openai_key]
ANTHROPIC_API_KEY=[your_anthropic_key]
```

## 🛠️ **Step-by-Step Fix Process**

### **Step 1: Access Render Dashboard**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Navigate to your services:
   - `insurance-navigator-api`
   - `insurance_navigator` (worker)

### **Step 2: Configure API Service Environment Variables**
1. Click on `insurance-navigator-api` service
2. Go to "Environment" tab
3. Add the following environment variables:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=[get_from_your_env_production_file]
SERVICE_ROLE_KEY=[get_from_your_env_production_file]
DATABASE_URL=[get_from_your_env_production_file]
API_BASE_URL=https://insurance-navigator-api.onrender.com
JWT_SECRET_KEY=[get_from_your_env_production_file]
ENVIRONMENT=production
LOG_LEVEL=INFO
SECURITY_BYPASS_ENABLED=false
LLAMAPARSE_API_KEY=[get_from_your_env_production_file]
OPENAI_API_KEY=[get_from_your_env_production_file]
ANTHROPIC_API_KEY=[get_from_your_env_production_file]
```

### **Step 3: Configure Worker Service Environment Variables**
1. Click on `insurance_navigator` (worker) service
2. Go to "Environment" tab
3. Add the following environment variables:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=[get_from_your_env_production_file]
SERVICE_ROLE_KEY=[get_from_your_env_production_file]
DATABASE_URL=[get_from_your_env_production_file]
API_BASE_URL=https://insurance-navigator-api.onrender.com
JWT_SECRET_KEY=[get_from_your_env_production_file]
ENVIRONMENT=production
LOG_LEVEL=INFO
WORKER_POLL_INTERVAL=5
WORKER_MAX_JOBS=10
WORKER_MAX_RETRIES=3
LLAMAPARSE_API_KEY=[get_from_your_env_production_file]
OPENAI_API_KEY=[get_from_your_env_production_file]
ANTHROPIC_API_KEY=[get_from_your_env_production_file]
```

### **Step 4: Get Values from .env.production**
Run this command to get the actual values:

```bash
cat .env.production | grep -E "(SUPABASE_URL|SUPABASE_KEY|SERVICE_ROLE_KEY|DATABASE_URL|JWT_SECRET_KEY|LLAMAPARSE_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY)"
```

### **Step 5: Restart Services**
After adding environment variables:
1. **API Service**: Trigger a manual deployment or restart
2. **Worker Service**: Trigger a manual deployment or restart

### **Step 6: Verify Fix**
Run the validation script to verify:

```bash
python scripts/cloud_deployment/validate_environment_variables.py
```

## 🔍 **Verification Steps**

### **1. Check Worker Logs**
```bash
render logs --resources srv-d2h5mr8dl3ps73fvvlog --limit 20
```

### **2. Check API Health**
```bash
curl https://insurance-navigator-api.onrender.com/health
```

### **3. Run Integration Tests**
After fixing environment variables, run the cloud integration tests:

```bash
python scripts/cloud_deployment/phase1_test.py
```

## 🚨 **Critical Notes**

1. **Worker Service**: The worker is currently in a crash loop due to missing `SUPABASE_URL` and `SUPABASE_KEY`
2. **API Service**: Build failed due to missing environment variables
3. **Both Services**: Need the same core environment variables (Supabase, Database, API keys)
4. **Restart Required**: Services need to be restarted after adding environment variables

## 📊 **Expected Results After Fix**

- **Worker Service**: Should start successfully and stop crashing
- **API Service**: Should build and deploy successfully
- **Health Checks**: Both services should show healthy status
- **Integration Tests**: Should pass with 100% success rate

## 🎯 **Next Steps After Fix**

1. **Run Cloud Integration Tests**: Test the full upload pipeline in cloud
2. **Monitor Service Stability**: Ensure no more crash loops
3. **Performance Validation**: Verify response times and reliability
4. **Documentation Update**: Update deployment documentation

---

**Priority**: 🔴 **CRITICAL** - Fix environment variables immediately to resolve service failures
