# FM-027 – Executor Agent Prompt (Auth/Env Investigation)

## System Role
You execute high-information experiments to confirm/refute auth/env hypotheses. Minimize changes, maximize signal, never expose secrets.

## Context (Bulleted, 10–15 pts)

### Symptom & Affected Paths
- **Symptom**: Upload Pipeline Worker returns 400 Bad Request on storage access via `StorageManager.blob_exists()`
- **Affected Path**: `backend/shared/storage/storage_manager.py` → Supabase Storage API
- **Timing**: Persistent since 2025-10-01 17:30+ (after endpoint fix deployment)
- **Environment**: Staging worker service `srv-d37dlmvfte5s73b6uq0g` on Render

### Auth Topology Summary
- **Upload Flow**: User JWT → Presigned URL (Service Role) → Storage Upload
- **Worker Fetch**: Service Role Key → Direct API Call → Storage Download
- **Token Provenance**: Service role key used for both upload and fetch operations
- **Storage Policies**: RLS policies allow service role access to `files` bucket

### Environment Precedence & Suspected Collisions
- **Primary Key**: `SUPABASE_SERVICE_ROLE_KEY` (environment variable)
- **Fallback Key**: `SERVICE_ROLE_KEY` (environment variable)
- **Worker Config**: `WorkerConfig.from_environment()` loads with precedence
- **Suspected Issue**: Environment variable loading differences between test and worker contexts

### Links & Resources
- **Investigation Doc**: `docs/incidents/fm_027/investigations/INV-AUTH-20251001.md`
- **Repro Script**: `test_auth_matrix.py` (create if needed)
- **Worker Logs**: Render service `srv-d37dlmvfte5s73b6uq0g`
- **Storage Dashboard**: Supabase project `dfgzeastcxnoqshgyotp`
- **Environment Config**: `config/environment_loader.py`

## Ordered Tasks

### 1. Validate Minimal Repro Harness on Runner
**Objective**: Confirm the auth matrix test works in staging environment
**Method**: 
- Create `test_auth_matrix.py` script
- Run against staging Supabase instance
- Test both old and new endpoint formats
- Verify service role key authentication

**Expected Output**: Raw logs showing status codes for different authentication contexts
**Time Estimate**: 15 minutes

### 2. Capture Worker's Runtime Token Claims & Environment Values
**Objective**: Log actual authentication method and environment variables used by worker
**Method**:
- Add temporary logging to `backend/workers/enhanced_base_worker.py`
- Log environment variable names and presence (not values)
- Log authentication method used by StorageManager
- Deploy to staging worker service

**Expected Output**: Worker logs showing actual environment variables and auth method
**Time Estimate**: 20 minutes

### 3. Run Experiments E1-E6 (from investigation doc)
**Objective**: Execute discriminating experiments to test hypotheses

#### E1: Decode and Log Worker's Actual Token Claims
- Add JWT claim logging (header only, no secrets)
- Verify worker uses service role key, not JWT
- Compare with expected authentication method

#### E2: Generate Presigned URL with Worker's Identity
- Use worker's service role key to generate presigned URL
- Test presigned URL generation with worker's identity
- Verify parity between local and worker contexts

#### E3: Swap Environment Precedence
- Force explicit key usage in worker
- Disable fallback chains
- Set explicit environment variables

#### E4: Toggle Storage Policies
- Create canary bucket with different policies
- Test worker access with different policy configurations
- Isolate policy vs authentication issues

#### E5: Introduce Deterministic Time Check
- Add timestamp logging to worker requests
- Check for clock skew issues
- Verify no time-related authentication problems

#### E6: Run ddmin on Environment Set
- Remove environment variables one by one
- Find decisive environment variable
- Identify critical configuration

**Expected Output**: Sanitized logs and test results for each experiment
**Time Estimate**: 45 minutes

### 4. Produce Micro-Fix PR (if mismatch emerges)
**Objective**: Create targeted fix for identified authentication issue
**Method**:
- If environment variable issue: Fix precedence order
- If authentication method issue: Align worker auth with expected method
- If policy issue: Update storage policies
- Add CI policy test to prevent regression

**Expected Output**: Draft PR with minimal changes and test coverage
**Time Estimate**: 30 minutes

### 5. Update Hypotheses Ledger Verdicts
**Objective**: Document findings and evidence for each hypothesis
**Method**:
- Update `INV-AUTH-20251001.md` with test results
- Mark hypotheses as confirmed/refuted
- Add evidence and confidence levels
- Document any new hypotheses discovered

**Expected Output**: Updated investigation document with verdicts
**Time Estimate**: 15 minutes

### 6. Propose Next Experiments (if inconclusive)
**Objective**: Identify next highest-yield experiments if root cause not found
**Method**:
- Analyze remaining hypotheses
- Identify highest-confidence next steps
- Propose 2 most promising experiments
- Estimate time and resources needed

**Expected Output**: List of next experiments with rationale
**Time Estimate**: 10 minutes

## Constraints & Safety

### No Production Writes
- **Scope**: Staging/canary only
- **Verification**: All changes must be deployed to staging first
- **Rollback**: Maintain ability to revert changes immediately

### Never Print Secrets
- **JWT Tokens**: Log claims only (iss/aud/sub/exp), never full tokens
- **API Keys**: Log presence and length only, never actual values
- **Database URLs**: Log host and port only, never credentials

### Timebox to 2 Hours
- **Total Budget**: 2 hours maximum
- **Priority**: Focus on highest-yield experiments first
- **Escalation**: If time exceeded, document findings and escalate

### Prefer Isolating Tests
- **Identity vs Policy**: Test authentication method separately from storage policies
- **Environment vs Code**: Test environment variables separately from code changes
- **Local vs Worker**: Compare local test results with worker results

## Reporting Format

### Executive Note (150 words)
- **Summary**: Brief description of findings
- **Root Cause**: Identified cause of 400 Bad Request errors
- **Fix Applied**: Solution implemented (if any)
- **Status**: Current state of investigation

### Hypothesis Results Table
| Hypothesis | Test(s) | Observed | Verdict | Artifacts |
|------------|---------|----------|---------|-----------|
| H1: JWT aud/iss mismatch | E1, E2 | [Results] | [Confirmed/Refuted] | [Links] |
| H2: Presigned URL context | E2, E3 | [Results] | [Confirmed/Refuted] | [Links] |
| H3: Environment precedence | E3, E6 | [Results] | [Confirmed/Refuted] | [Links] |
| H4: JWT secret mismatch | E1, E5 | [Results] | [Confirmed/Refuted] | [Links] |
| H5: Clock skew/expiry | E5 | [Results] | [Confirmed/Refuted] | [Links] |
| H6: Bucket policy mismatch | E4 | [Results] | [Confirmed/Refuted] | [Links] |

### Proposed Fix & Risk
- **Fix Description**: Detailed explanation of solution
- **Implementation**: Code changes and configuration updates
- **Testing**: Verification steps and test coverage
- **Risks**: Potential side effects and mitigation strategies
- **Rollback Plan**: Steps to revert if issues arise

## Success Criteria

### Clear Identity & Environment Precedence Determination
- **Identity**: Confirmed authentication method used by worker
- **Environment**: Verified environment variable loading and precedence
- **Mismatch**: Identified specific cause of 400 Bad Request errors

### Validated Fix PR or Minimized Failing Case
- **Fix PR**: Working solution with test coverage
- **Minimized Case**: Isolated failing scenario for further investigation
- **Next Steps**: Clear path forward for resolution

## Stop/Escalate Conditions

### Halt and Page Owners
- **Token Verification Fails**: If JWT secret mismatch confirmed
- **Environment Corruption**: If environment variables are corrupted or missing
- **Security Issue**: If authentication bypass or security vulnerability discovered

### Capture and Escalate
- **Presigned URL Expiry**: If URLs intermittently expire due to clock skew
- **Policy Changes**: If storage policies changed unexpectedly
- **Service Outage**: If Supabase storage service is down or degraded

## Deliverables

### Required Artifacts
- **Test Scripts**: `test_auth_matrix.py` and any other test files
- **Worker Logs**: Sanitized logs from staging worker service
- **Environment Audit**: List of environment variables and their sources
- **Fix PR**: Draft pull request with solution (if applicable)

### Documentation Updates
- **Investigation Doc**: Updated `INV-AUTH-20251001.md` with findings
- **Hypotheses Ledger**: Updated verdicts and evidence
- **Next Steps**: Clear path forward for resolution

### Communication
- **Status Update**: Brief summary of findings and next steps
- **Escalation**: If critical issues discovered that require immediate attention
- **Handoff**: If investigation needs to be passed to another team member

---

**Remember**: Focus on high-information experiments that isolate the root cause. Minimize changes, maximize signal, never expose secrets. The goal is to identify why the worker gets 400 Bad Request when direct tests return 200 OK with the same configuration.

