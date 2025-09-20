# Hardcoded Development Values Analysis

## 🚨 **Critical Issue Identified**

After analyzing the codebase for hardcoded development values from `.env.development`, I found **multiple critical issues** that could cause production failures similar to FM-013.

## 📋 **Summary of Findings**

**Total Files with Hardcoded Values**: 149 files  
**Critical Production Files**: 8 files  
**High Risk**: 15+ hardcoded values that could break production

## 🔍 **Critical Hardcoded Values Found**

### **1. Database Connection Issues (HIGH RISK)**

#### **Files with Hardcoded Database URLs:**
- `main.py` (line 871): `storage_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")`
- `api/upload_pipeline/webhooks.py` (line 121): `f"http://127.0.0.1:54321/storage/v1/object/{bucket}/{key}"`
- `backend/shared/external/llamaparse_real.py` (line 204): `storage_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")`
- `backend/shared/external/llamaparse_real.py` (line 636): `f"http://127.0.0.1:54321/storage/v1/object/{bucket}/{key}"`

#### **Database Configuration Defaults:**
- `config/database.py` (line 22): `self.host = os.getenv('DB_HOST', '127.0.0.1')`
- `config/database.py` (line 23): `self.port = int(os.getenv('DB_PORT', '54322'))`

### **2. Webhook URL Issues (HIGH RISK)**

#### **Files with Hardcoded Webhook URLs:**
- `main.py` (line 849): `'signed_url': f"http://localhost:8000/upload-complete"`
- `api/upload_pipeline/endpoints/upload.py` (line 464): `f"http://localhost:8000/api/upload-pipeline/upload-file-proxy/{bucket}/{key}"`
- `api/upload_pipeline/endpoints/upload.py` (line 467): `f"http://localhost:8000/api/upload-pipeline/upload-file-proxy/{storage_path}"`

### **3. Ngrok Discovery Issues (MEDIUM RISK)**

#### **Files with Hardcoded Ngrok URLs:**
- `backend/shared/utils/ngrok_discovery.py` (line 26): `response = requests.get("http://localhost:4040/api/tunnels", timeout=5)`
- `backend/shared/utils/ngrok_discovery.py` (line 64): `return "http://localhost:8000"`
- `backend/shared/utils/ngrok_discovery.py` (line 86): `return "http://localhost:8000"`
- `backend/shared/utils/ngrok_discovery.py` (line 100): `response = requests.get("http://localhost:4040/api/tunnels", timeout=2)`
- `backend/shared/utils/ngrok_discovery.py` (line 111): `return "http://localhost:4040"`

### **4. Development Keys and Secrets (HIGH RISK)**

#### **Files with Hardcoded Development Keys:**
- Multiple test files contain hardcoded Supabase development keys
- JWT secrets and API keys from development environment
- Database credentials: `postgres:postgres@127.0.0.1:54322`

## 🚨 **Immediate Action Required**

### **Critical Files to Fix (Production Impact)**

1. **`main.py`** - API service main file
   - Line 871: Hardcoded Supabase URL fallback
   - Line 849: Hardcoded localhost webhook URL

2. **`api/upload_pipeline/webhooks.py`** - Webhook processing
   - Line 121: Hardcoded Supabase storage URL

3. **`backend/shared/external/llamaparse_real.py`** - LlamaParse integration
   - Line 204: Hardcoded Supabase URL fallback
   - Line 636: Hardcoded Supabase storage URL

4. **`api/upload_pipeline/endpoints/upload.py`** - Upload endpoints
   - Lines 464, 467: Hardcoded localhost URLs

### **Configuration Files to Review**

1. **`config/database.py`** - Database configuration
   - Lines 22-23: Hardcoded localhost defaults

2. **`backend/shared/utils/ngrok_discovery.py`** - Ngrok discovery
   - Multiple hardcoded localhost URLs

## 🔧 **Recommended Fixes**

### **1. Environment Variable Enforcement**

Replace all hardcoded fallbacks with proper environment variable validation:

```python
# BAD (current):
storage_url = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")

# GOOD (recommended):
storage_url = os.getenv("SUPABASE_URL")
if not storage_url:
    raise ValueError("SUPABASE_URL environment variable is required")
```

### **2. Configuration Validation**

Add startup validation to ensure all required environment variables are set:

```python
def validate_production_config():
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY", 
        "SUPABASE_ANON_KEY",
        "API_BASE_URL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {missing_vars}")
```

### **3. Environment-Specific Defaults**

Use environment-aware defaults:

```python
def get_api_base_url():
    environment = os.getenv("ENVIRONMENT", "development")
    if environment == "production":
        return os.getenv("API_BASE_URL")  # Required in production
    else:
        return os.getenv("API_BASE_URL", "http://localhost:8000")  # Dev fallback
```

## 📊 **Risk Assessment**

| File | Risk Level | Impact | Priority |
|------|------------|--------|----------|
| `main.py` | HIGH | API service failures | 1 |
| `api/upload_pipeline/webhooks.py` | HIGH | Webhook processing failures | 1 |
| `backend/shared/external/llamaparse_real.py` | HIGH | Document processing failures | 1 |
| `api/upload_pipeline/endpoints/upload.py` | MEDIUM | Upload endpoint failures | 2 |
| `config/database.py` | MEDIUM | Database connection issues | 2 |
| `backend/shared/utils/ngrok_discovery.py` | LOW | Development workflow issues | 3 |

## 🎯 **Success Criteria**

- [ ] All hardcoded localhost URLs replaced with environment variables
- [ ] All hardcoded development keys removed
- [ ] Environment variable validation added to startup
- [ ] Production deployment tested with proper environment variables
- [ ] No fallback to development values in production

## 📝 **Next Steps**

1. **Immediate**: Fix critical files (main.py, webhooks.py, llamaparse_real.py)
2. **Short-term**: Add environment variable validation
3. **Medium-term**: Review and fix all remaining hardcoded values
4. **Long-term**: Implement configuration management system

## 🔍 **Files to Monitor**

After fixes, monitor these files for any new hardcoded values:
- All files in `api/` directory
- All files in `backend/` directory  
- All files in `config/` directory
- Main application files (`main.py`, `app.py`, etc.)

This analysis should prevent future issues like FM-013 where hardcoded development values cause production failures.

