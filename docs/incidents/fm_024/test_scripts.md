# FM-024 Test Scripts Documentation

## Available Test Scripts

### 1. `test_staging_storage_error.py`
**Purpose**: Replicates the Supabase storage authentication error using staging configuration

**Usage**:
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
source .venv/bin/activate
python test_staging_storage_error.py
```

**Expected Output**: 
- ✅ SUCCESS: Replicated the storage authentication error!
- Error: `{'statusCode': 403, 'error': Unauthorized, 'message': signature verification failed}`

### 2. `test_storage_auth_error.py`
**Purpose**: Tests local Supabase storage authentication (should work)

**Usage**:
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
source .venv/bin/activate
python test_storage_auth_error.py
```

**Expected Output**:
- ✅ Supabase connection successful
- ✅ Signed URL generated successfully

### 3. `test_upload_with_auth.py`
**Purpose**: Tests full upload flow with JWT authentication

**Usage**:
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
source .venv/bin/activate
python test_upload_with_auth.py
```

**Expected Output**:
- Authentication error (expected due to JWT validation complexity)

### 4. `test_upload_failure.py`
**Purpose**: Basic upload endpoint test

**Usage**:
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
source .venv/bin/activate
python test_upload_failure.py
```

**Expected Output**:
- Authentication error (expected)

## Test Script Locations

All test scripts are located in the project root:
- `/Users/aq_home/1Projects/accessa/insurance_navigator/test_*.py`

## Environment Setup

### Prerequisites
1. Local Supabase running: `supabase start`
2. Python virtual environment activated: `source .venv/bin/activate`
3. API server running: `python main.py` (in background)

### Environment Variables
The test scripts use the following environment variables:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for authentication

## Test Results Interpretation

### Success Indicators
- ✅ Storage authentication works locally
- ❌ Storage authentication fails with staging config
- ✅ Database operations work in both environments

### Failure Patterns
- `signature verification failed` - Storage authentication issue
- `Authentication service error` - JWT validation issue
- `address already in use` - Port conflict (restart API server)

## Debugging Tips

1. **Check Supabase Status**:
   ```bash
   supabase status
   ```

2. **Check API Health**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check Environment Variables**:
   ```bash
   cat .env.development | grep SUPABASE
   cat .env.staging | grep SUPABASE
   ```

4. **View API Logs**:
   - Check terminal where `python main.py` is running
   - Look for error messages and stack traces

## Creating New Test Scripts

When creating new test scripts for FM-024:

1. **Use descriptive names**: `test_fm024_*.py`
2. **Include proper error handling**: Catch and display specific errors
3. **Add success/failure indicators**: Clear output showing test results
4. **Document expected behavior**: What should happen vs what actually happens
5. **Test both environments**: Local (working) vs Staging (failing)
