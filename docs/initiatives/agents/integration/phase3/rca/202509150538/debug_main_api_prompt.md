# Debug Prompt — Main API Service Startup

## Context
You are tasked with debugging and fixing the main API service startup failure in the Insurance Navigator project. The service fails to start due to a Supabase client initialization error with the `proxy` parameter.

## Current Status
- **Frontend**: ✅ Running on port 3000
- **Upload Pipeline API**: ✅ Running on port 8001 (with database SSL issues but functional)
- **Local Supabase**: ✅ Running on port 54321
- **Main API Service**: ❌ Failing to start on port 8000

## Error Details
```
TypeError: __init__() got an unexpected keyword argument 'proxy'
```

**Full Error Traceback:**
```
File "/Users/aq_home/1Projects/accessa/insurance_navigator/config/database.py", line 140, in get_supabase_client
    client = create_client(
File "/Users/aq_home/opt/anaconda3/lib/python3.9/site-packages/supabase/_sync/client.py", line 338, in create_client
    return SyncClient.create(
File "/Users/aq_home/opt/anaconda3/lib/python3.9/site-packages/supabase/_sync/client.py", line 101, in create
    client = cls(supabase_url, supabase_key, options)
File "/Users/aq_home/opt/anaconda3/lib/python3.9/site-packages/supabase/_sync/client.py", line 79, in __init__
    self.auth = self._init_supabase_auth_client(
File "/Users/aq_home/opt/anaconda3/lib/python3.9/site-packages/supabase/_sync/client.py", line 248, in _init_supabase_auth_client
    return SyncSupabaseAuthClient(
File "/Users/aq_home/opt/anaconda3/lib/python3.9/site-packages/supabase/_sync/auth_client.py", line 47, in __init__
    super().__init__(
File "/Users/aq_home/opt/anaconda3/lib/python3.9/site-packages/gotrue/_sync/gotrue_client.py", line 108, in __init__
    SyncGoTrueBaseAPI.__init__(
File "/Users/aq_home/opt/anaconda3/lib/python3.9/site-packages/gotrue/_sync/gotrue_base_api.py", line 28, in __init__
    self._http_client = http_client or SyncClient(
TypeError: __init__() got an unexpected keyword argument 'proxy'
```

## Environment Configuration
The following environment variables are set and working for other services:
```bash
export SUPABASE_URL=http://127.0.0.1:54321
export SUPABASE_ANON_KEY=${SUPABASE_JWT_TOKEN}
export SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_JWT_TOKEN}
export SUPABASE_STORAGE_URL=http://127.0.0.1:54321
export DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
export ENVIRONMENT=development
```

## Key Files to Investigate
1. **`config/database.py`** - Supabase client initialization
2. **`main.py`** - Main API service startup
3. **`requirements.txt`** or **`pyproject.toml`** - Dependency versions
4. **`api/upload_pipeline/main.py`** - Working API for comparison

## Investigation Steps

### Step 1: Dependency Analysis
1. Check current Supabase client version:
   ```bash
   pip show supabase
   pip show gotrue
   pip show httpx
   ```

2. Compare with working upload pipeline API dependencies

3. Check for version conflicts in the environment

### Step 2: Code Analysis
1. Examine `config/database.py` lines around 140:
   ```python
   client = create_client(
       supabase_url,
       supabase_key
   )
   ```

2. Check if any custom options are being passed to `create_client()`

3. Look for any proxy configuration in the codebase

### Step 3: Environment Testing
1. Test Supabase client creation in isolation:
   ```python
   from supabase import create_client
   client = create_client(
       "http://127.0.0.1:54321",
       "${SUPABASE_JWT_TOKEN}"
   )
   ```

2. Check if the error occurs with minimal client creation

### Step 4: Solution Implementation
Based on findings, implement one of these solutions:

**Option A: Version Downgrade**
- Downgrade Supabase client to compatible version
- Update requirements.txt

**Option B: Code Fix**
- Modify client initialization to avoid proxy parameter
- Add proper error handling

**Option C: Environment Fix**
- Remove proxy configuration from environment
- Fix environment variable setup

## Success Criteria
- [ ] Main API service starts successfully on port 8000
- [ ] Health check endpoint responds: `GET http://localhost:8000/health`
- [ ] Registration endpoint works: `POST http://localhost:8000/register`
- [ ] No regression in upload pipeline API (port 8001)
- [ ] Frontend can successfully register users

## Testing Commands
```bash
# Start the main API service
cd /Users/aq_home/1Projects/accessa/insurance_navigator
export SUPABASE_URL=http://127.0.0.1:54321
export SUPABASE_ANON_KEY=${SUPABASE_JWT_TOKEN}
export SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_JWT_TOKEN}
export SUPABASE_STORAGE_URL=http://127.0.0.1:54321
export DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres
export ENVIRONMENT=development
python main.py

# Test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/register -H "Content-Type: application/json" -d '{"email":"test@example.com","password":"test123"}'
```

## Expected Outcome
The main API service should start successfully and provide:
- User registration endpoint (`/register`)
- Authentication endpoints (`/auth/login`)
- Health check endpoint (`/health`)
- Status endpoint (`/api/v1/status`)

This will enable the frontend to successfully register users and complete the end-to-end testing workflow.

## Notes
- The upload pipeline API works correctly, so the issue is specific to the main API service
- Local Supabase instance is running and accessible
- Frontend is ready and waiting for the main API service
- Focus on the Supabase client initialization error as the root cause
