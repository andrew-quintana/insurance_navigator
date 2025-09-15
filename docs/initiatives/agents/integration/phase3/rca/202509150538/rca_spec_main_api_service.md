# RCA Spec — Main API Service Startup Failure

## Summary
Root Cause Analysis specification for the main API service startup failure due to Supabase client initialization issues with the `proxy` parameter error.

## Problem Statement
The main API service (`main.py`) fails to start with the following error:
```
TypeError: __init__() got an unexpected keyword argument 'proxy'
```

This occurs during Supabase client initialization in the database configuration module, preventing the entire API service from starting.

## Scope
- **In Scope**: 
  - Supabase client initialization in `config/database.py`
  - Main API service startup process
  - Environment variable configuration
  - Dependency version compatibility
- **Out of Scope**: 
  - Upload pipeline API (working correctly)
  - Frontend application (working correctly)
  - Local Supabase instance (working correctly)

## Root Cause Analysis Areas

### 1. Dependency Version Analysis
- **Supabase Python client version**: Check current version and compatibility
- **GoTrue client version**: Identify version causing `proxy` parameter issue
- **HTTP client dependencies**: Check httpx/requests version conflicts
- **Python version compatibility**: Verify Python 3.9 compatibility

### 2. Configuration Analysis
- **Environment variables**: Verify all required Supabase environment variables are set
- **Client initialization options**: Check if custom options are being passed incorrectly
- **Proxy configuration**: Identify where `proxy` parameter is being passed

### 3. Code Path Analysis
- **`config/database.py`**: Analyze `get_supabase_client()` function
- **Client creation flow**: Trace through `create_client()` call chain
- **Error propagation**: Understand how the error bubbles up through retry logic

### 4. Integration Analysis
- **Database pool initialization**: Check if database pool setup affects Supabase client
- **Service startup sequence**: Verify order of service initialization
- **Retry mechanism**: Analyze tenacity retry configuration

## Evidence Collection Requirements

### Code Evidence
- [ ] Current Supabase client version in `requirements.txt` or `pyproject.toml`
- [ ] Exact error traceback with line numbers
- [ ] Environment variable values at runtime
- [ ] Client initialization code in `config/database.py`

### Environment Evidence
- [ ] Python version and environment details
- [ ] Installed package versions (`pip list` output)
- [ ] Local Supabase instance status and configuration
- [ ] Network connectivity to Supabase instance

### Configuration Evidence
- [ ] Environment variable configuration
- [ ] Supabase client options being passed
- [ ] Database connection string format
- [ ] CORS and proxy settings

## Analysis Methodology

### Phase 1: Dependency Investigation
1. Check current Supabase client version
2. Identify minimum compatible versions
3. Check for version conflicts with other packages
4. Verify Python 3.9 compatibility matrix

### Phase 2: Code Analysis
1. Review `config/database.py` client creation logic
2. Check for hardcoded or dynamic options being passed
3. Analyze error propagation through retry mechanism
4. Verify environment variable usage

### Phase 3: Environment Analysis
1. Test Supabase client creation in isolation
2. Verify local Supabase instance accessibility
3. Check network configuration and proxy settings
4. Validate environment variable values

### Phase 4: Solution Validation
1. Test proposed fixes in isolation
2. Verify service startup with fixes
3. Validate all endpoints work correctly
4. Ensure no regression in other services

## Success Criteria
- [ ] Main API service starts successfully without errors
- [ ] All health check endpoints respond correctly
- [ ] Registration endpoint works as expected
- [ ] No regression in upload pipeline API
- [ ] Clean service separation (main API on 8000, upload pipeline on 8001)

## Deliverables
- [ ] RCA report with root cause identification
- [ ] Proposed solution with implementation steps
- [ ] Updated dependency versions if needed
- [ ] Configuration fixes if required
- [ ] Validation test results

## Risks & Constraints
- **Compatibility**: Must maintain compatibility with existing upload pipeline API
- **Environment**: Must work with local Supabase instance configuration
- **Dependencies**: Changes must not break other services
- **Timeline**: Service needs to be operational for frontend testing

## Context Budget
- Max: 15k tokens
- Focus: 60% code analysis, 30% dependency investigation, 10% environment setup
- Priority: Supabase client initialization error resolution
