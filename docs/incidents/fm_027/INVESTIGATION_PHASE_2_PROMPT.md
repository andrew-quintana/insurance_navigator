# FM-027 Phase 2 Investigation Prompt

## Investigation Context
**Incident ID**: FM-027  
**Phase**: 2 - Render Environment Deep Dive  
**Previous Phase**: Root cause identified as environment-specific issue on Render  
**Status**: Ready for execution  

## Problem Statement
The Upload Pipeline Worker is experiencing 400 Bad Request errors when accessing Supabase Storage via `StorageManager.blob_exists()` on Render, while identical code and environment variables work perfectly in the local environment.

## Previous Findings Summary
- ✅ **StorageManager Code**: Correctly configured with both required headers (`apikey` + `Authorization`)
- ✅ **Local Environment**: All operations return Status 200, working perfectly
- ❌ **Render Environment**: 400 Bad Request errors, FM-027 logs not appearing
- ✅ **Authentication Requirements**: Confirmed Supabase requires both headers

## Investigation Objectives

### Primary Goal
Identify the specific differences between local and Render environments that cause the 400 Bad Request errors, despite using identical environment variables and code.

### Secondary Goals
1. Determine why FM-027 StorageManager logs are not appearing on Render
2. Identify the exact point of failure in the Render environment
3. Provide a concrete fix for the Render-specific issue

## Investigation Scope

### Environment Comparison Focus
**Local Environment (Working)**:
- Python 3.9.12 on macOS
- httpx 0.25.2
- Environment variables loaded from `.env.staging`
- All StorageManager operations return Status 200

**Render Environment (Failing)**:
- Docker container on Render
- Environment variables loaded from Render environment
- StorageManager operations return 400 Bad Request
- FM-027 logs not appearing

### Key Questions to Answer
1. **Environment Variables**: Are the environment variables actually identical on Render?
2. **Python Environment**: Are there differences in Python version, httpx version, or other dependencies?
3. **Network Configuration**: Are there network-level differences affecting the requests?
4. **Docker Environment**: Are there container-specific issues affecting HTTP requests?
5. **Logging Configuration**: Why aren't the FM-027 logs appearing on Render?
6. **Request Headers**: Are the headers being sent correctly from Render?
7. **SSL/TLS**: Are there certificate or SSL issues on Render?
8. **DNS Resolution**: Are there DNS resolution differences?

## Investigation Tasks

### Task 1: Environment Variable Audit
**Objective**: Verify environment variables are identical between local and Render
**Actions**:
1. Check Render environment variables via Render dashboard
2. Compare with local `.env.staging` file
3. Verify environment variable loading in worker code
4. Test environment variable resolution in Render logs

### Task 2: Python Environment Analysis
**Objective**: Identify Python environment differences
**Actions**:
1. Check Python version on Render vs local
2. Verify httpx version and other dependencies
3. Check for any missing or different packages
4. Verify Python path and module loading

### Task 3: Network and HTTP Analysis
**Objective**: Identify network-level differences
**Actions**:
1. Test HTTP requests from Render to Supabase
2. Check for proxy or firewall issues
3. Verify SSL/TLS configuration
4. Test DNS resolution from Render
5. Check for rate limiting or IP blocking

### Task 4: Docker Environment Investigation
**Objective**: Identify container-specific issues
**Actions**:
1. Check Docker container configuration
2. Verify network settings in container
3. Check for container resource limits
4. Verify file system permissions

### Task 5: Logging and Debugging
**Objective**: Understand why FM-027 logs aren't appearing
**Actions**:
1. Check logging configuration on Render
2. Verify log levels and filters
3. Test basic logging functionality
4. Check for log truncation or filtering

### Task 6: Request Header Analysis
**Objective**: Verify headers are being sent correctly
**Actions**:
1. Add detailed request logging to StorageManager
2. Capture actual headers being sent from Render
3. Compare with local environment headers
4. Test with different header combinations

## Investigation Tools and Scripts

### Required Scripts to Create
1. **`render_environment_audit.py`** - Comprehensive Render environment analysis
2. **`render_http_debug.py`** - HTTP request debugging from Render
3. **`render_logging_test.py`** - Logging configuration test
4. **`render_network_test.py`** - Network connectivity and DNS tests

### Required Logging Enhancements
1. **Enhanced StorageManager Logging** - Add more detailed request/response logging
2. **Environment Variable Logging** - Log all environment variables on startup
3. **HTTP Client Logging** - Log httpx client configuration and requests
4. **Error Context Logging** - Add more context to error messages

## Expected Deliverables

### 1. Investigation Report
- Detailed comparison of local vs Render environments
- Specific differences identified
- Root cause analysis of the 400 errors
- Explanation of missing FM-027 logs

### 2. Fix Implementation
- Concrete solution for the Render environment issue
- Code changes required
- Configuration changes needed
- Verification steps

### 3. Prevention Measures
- Recommendations to prevent similar issues
- Monitoring improvements
- Documentation updates

## Success Criteria

### Primary Success
- ✅ Identify the exact cause of 400 Bad Request errors on Render
- ✅ Fix the issue so worker processes jobs successfully
- ✅ FM-027 logs appear in Render worker logs

### Secondary Success
- ✅ Understand why local and Render environments behave differently
- ✅ Implement monitoring to detect similar issues
- ✅ Document the solution for future reference

## Investigation Constraints

### Technical Constraints
- Cannot modify Render environment variables directly
- Must work within Render's Docker container limitations
- Cannot access Render internal network configuration

### Time Constraints
- Investigation should be completed within 2-3 hours
- Focus on high-impact, low-effort solutions first
- Prioritize fixes that can be deployed immediately

### Security Constraints
- Never expose sensitive environment variables in logs
- Use secure methods for testing authentication
- Follow security best practices for debugging

## Investigation Methodology

### Phase 1: Data Collection
1. Deploy enhanced logging to Render worker
2. Run comprehensive environment audit
3. Capture detailed request/response data
4. Compare with local environment data

### Phase 2: Analysis
1. Identify specific differences between environments
2. Analyze request/response patterns
3. Determine root cause of 400 errors
4. Understand logging configuration issues

### Phase 3: Solution
1. Implement fix for identified issue
2. Deploy and test solution
3. Verify FM-027 logs appear
4. Confirm worker processes jobs successfully

### Phase 4: Documentation
1. Document the root cause and solution
2. Update incident report
3. Create prevention measures
4. Update troubleshooting documentation

## Files to Reference

### Previous Investigation Files
- `docs/incidents/fm_027/INVESTIGATION_FINDINGS.md`
- `docs/incidents/fm_027/FINAL_INCIDENT_REPORT.md`
- `test_worker_storage_debug.py` - Local environment test
- `test_render_environment.py` - Render environment test

### Key Code Files
- `backend/shared/storage/storage_manager.py` - StorageManager implementation
- `backend/workers/enhanced_base_worker.py` - Worker implementation
- `backend/shared/config/worker_config.py` - Configuration loading

## Investigation Prompt for Next Chat

```
You are investigating FM-027 Phase 2, focusing on Render environment differences that cause 400 Bad Request errors in the Upload Pipeline Worker.

CONTEXT:
- StorageManager works perfectly in local environment (Status 200)
- Same code and environment variables fail on Render (400 Bad Request)
- FM-027 logs are not appearing in Render worker logs
- Root cause is environment-specific to Render

YOUR MISSION:
1. Deploy enhanced logging to Render worker
2. Run comprehensive environment audit comparing local vs Render
3. Identify the specific differences causing the 400 errors
4. Fix the issue so worker processes jobs successfully
5. Document the solution

START WITH:
1. Check current Render worker status and logs
2. Deploy enhanced debugging to StorageManager
3. Run environment comparison tests
4. Analyze the differences and implement fix

FOCUS ON:
- Environment variable differences
- Python/httpx version differences  
- Network/SSL configuration differences
- Docker container issues
- Logging configuration problems

DELIVERABLES:
- Root cause analysis of Render-specific issue
- Working fix for the 400 errors
- FM-027 logs appearing in Render
- Updated incident documentation

Use the investigation files in docs/incidents/fm_027/ as reference.
```

## Investigation Status
**Ready for Execution** - All context and objectives clearly defined for next phase investigation.

