# FRACAS FM-022 Investigation Prompt

## Investigation Context
**Incident**: Upload 500 Authentication Error  
**Environment**: Staging  
**Priority**: P1 - High  
**Date**: 2025-09-27  

## Current Status
- ✅ **Error Confirmed**: Upload endpoint returns 500 "Authentication service error"
- ✅ **Environment Verified**: Staging API is healthy and responsive
- ✅ **Pattern Identified**: Same error pattern as FM-017 (JWT authentication failure)
- 🔄 **Root Cause**: Suspected JWT secret mismatch between main API and upload pipeline

## Investigation Tasks

### 1. JWT Configuration Analysis
**Objective**: Compare JWT secrets between main API and upload pipeline

**Commands to Run**:
```bash
# Check main API JWT configuration
grep -r "JWT_SECRET" backend/ | head -10
grep -r "jwt_secret" backend/ | head -10

# Check upload pipeline JWT configuration
grep -r "JWT_SECRET" api/upload_pipeline/ | head -10
grep -r "jwt_secret" api/upload_pipeline/ | head -10

# Check environment variables
cat .env.staging | grep -E "(JWT|jwt)" | head -5
```

**Expected Outcome**: Identify JWT secret configuration differences

### 2. Upload Pipeline Auth Analysis
**Objective**: Examine upload pipeline authentication implementation

**Files to Check**:
- `api/upload_pipeline/auth.py` - Authentication service
- `api/upload_pipeline/config.py` - Configuration management
- `api/upload_pipeline/main.py` - Application setup

**Key Questions**:
- How does the upload pipeline validate JWT tokens?
- What JWT secret is it using?
- Is it reading from environment variables or hardcoded?

### 3. Main API JWT Analysis
**Objective**: Understand how main API generates JWT tokens

**Files to Check**:
- `backend/shared/auth/` - Authentication services
- `db/services/` - User authentication services
- Configuration files for JWT secret

**Key Questions**:
- What JWT secret does the main API use?
- How are JWT tokens generated?
- Are environment variables properly configured?

### 4. Environment Configuration Verification
**Objective**: Verify staging environment has correct JWT configuration

**Commands to Run**:
```bash
# Check staging environment variables
cat .env.staging | grep -E "(SUPABASE|JWT|AUTH)" | head -10

# Check if JWT_SECRET_KEY is set
echo "JWT_SECRET_KEY: ${JWT_SECRET_KEY:-NOT_SET}"

# Check upload pipeline environment loading
python3 -c "
from api.upload_pipeline.config import get_config
config = get_config()
print('Upload pipeline config loaded successfully')
print('Environment:', config.environment)
"
```

### 5. JWT Token Validation Test
**Objective**: Test JWT token validation in upload pipeline

**Commands to Run**:
```bash
# Test with valid JWT token from main API
# First, get a valid token from main API login
curl -X POST https://insurance-navigator-staging-api.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}' \
  -v

# Then test upload with the token
curl -X POST https://insurance-navigator-staging-api.onrender.com/api/upload-pipeline/upload \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <valid_token>" \
  -d '{"filename":"test.pdf","bytes_len":1000,"mime":"application/pdf","sha256":"a"*64,"ocr":false}' \
  -v
```

## Expected Findings

### Root Cause Identified
The upload pipeline is not loading environment variables from `.env.staging` file, causing the Supabase authentication service to fail when trying to access `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_ANON_KEY`.

### Required Fix
Update the upload pipeline to load environment variables on startup:

```python
# In api/upload_pipeline/main.py or config.py
import os
from dotenv import load_dotenv

# Load environment variables based on environment
environment = os.getenv('ENVIRONMENT', 'production')
env_file = f'.env.{environment}'
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ Loaded environment variables from {env_file}")
else:
    print(f"⚠️ Environment file {env_file} not found")
```

## Success Criteria
- [ ] JWT secret mismatch identified
- [ ] Configuration difference documented
- [ ] Fix implemented and tested
- [ ] Upload functionality restored
- [ ] Prevention measures documented

## Investigation Notes
- This appears to be a continuation of FM-017 issues
- Staging environment has different configuration than production
- Upload-test endpoint works, indicating the issue is authentication-specific
- Main API health check shows all services are healthy

## Next Steps After Investigation
1. **If JWT secret mismatch confirmed**: Update upload pipeline configuration
2. **If different issue found**: Document new root cause and solution
3. **If configuration issue**: Fix environment variable setup
4. **If code issue**: Update authentication implementation

## Files to Monitor
- `api/upload_pipeline/auth.py` - Authentication service
- `api/upload_pipeline/config.py` - Configuration management
- `.env.staging` - Staging environment variables
- `backend/shared/auth/` - Main API authentication

## Related Documentation
- FM-017: Upload Pipeline JWT Authentication Failure
- FM-014: API Upload Authentication Failure
- Authentication migration documentation
