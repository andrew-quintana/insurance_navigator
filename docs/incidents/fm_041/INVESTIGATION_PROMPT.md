# FM-041: Render Deployment Failure Investigation Prompt

## Problem Statement

Render deployment `dep-d480hsngi27c7398f2sg` failed with status `update_failed` for commit `6116eb8` ("Local development environment management refactor and organization"). The Docker build completed successfully (image built and pushed), but the deployment update phase failed.

**Service**: `api-service-production` (srv-d0v2nqvdiees73cejf0g)  
**Commit**: `6116eb8549f6706a522f0adef9f15f1b36a20f3a`  
**Deployment Date**: 2025-11-09T03:22:28Z  
**Status**: `update_failed` (build succeeded)

## Investigation Objective

Identify root cause of deployment update failure and implement fix. Follow the concise 3-step methodology to efficiently debug and resolve.

## Step 1: Understand the Failure

### 1.1 Get Deployment Details and Logs

**Actions**:
1. Get failed deployment details:
   ```bash
   mcp_render_get_deploy serviceId=srv-d0v2nqvdiees73cejf0g deployId=dep-d480hsngi27c7398f2sg
   ```

2. Get build logs (verify build actually succeeded):
   ```bash
   mcp_render_list_logs resource=['srv-d0v2nqvdiees73cejf0g'] startTime=2025-11-09T03:20:00Z endTime=2025-11-09T03:30:00Z type=['build'] limit=100
   ```

3. Get runtime logs around deployment time (look for errors):
   ```bash
   mcp_render_list_logs resource=['srv-d0v2nqvdiees73cejf0g'] startTime=2025-11-09T03:20:00Z endTime=2025-11-09T03:30:00Z type=['app'] limit=100
   ```

4. Extract error messages, exceptions, or failure patterns from logs

**Expected Output**: 
- Clear understanding of when/where failure occurred
- Error messages or patterns identified
- Build vs runtime failure distinction

### 1.2 Compare with Last Successful Deployment

**Actions**:
1. List recent deployments to find last successful one:
   ```bash
   mcp_render_list_deploys serviceId=srv-d0v2nqvdiees73cejf0g limit=10
   ```

2. Compare:
   - Commit SHA and message
   - Deployment configuration
   - Any differences in logs

**Expected Output**: 
- Last successful deployment identified
- Key differences noted

## Step 2: Identify Root Cause

### 2.1 Analyze Commit 6116eb8 Changes

**Actions**:
1. Review what changed in commit 6116eb8:
   ```bash
   git show 6116eb8 --stat
   git show 6116eb8 --name-status
   ```

2. Focus on critical areas:
   - **Files moved**: Check if Dockerfile COPY paths need updating
   - **Files deleted**: Check if critical files were removed
   - **Dockerfile changes**: Review any Dockerfile modifications
   - **Service entry point**: Check if main.py or startup script moved
   - **Config directory**: Check if config/ directory was moved

3. Check Dockerfile for broken paths:
   ```bash
   git show 6116eb8:Dockerfile
   git show HEAD:Dockerfile
   git diff 6116eb8 HEAD -- Dockerfile
   ```

**Expected Output**: 
- List of files moved/deleted/changed
- Potential broken references identified

### 2.2 Verify Critical Paths

**Actions**:
1. **Check Dockerfile COPY commands**:
   - Verify all source paths in COPY commands exist
   - Check if moved files broke COPY paths
   - Example: If `config/` moved, verify `COPY config/ ./config/` still works

2. **Verify service entry point**:
   ```bash
   git show HEAD:main.py | head -20
   ls -la main.py
   ```
   - Check if main.py exists at expected location
   - Verify startup command references correct file

3. **Check imports after file moves**:
   ```bash
   grep -r "from config" . --include="*.py" | head -10
   grep -r "import config" . --include="*.py" | head -10
   ```
   - Verify config imports work
   - Check if import paths need updating

4. **Verify config directory**:
   ```bash
   ls -la config/
   git show 6116eb8 --name-status -- config/
   ```
   - Check if config directory exists
   - Verify config files are present

**Expected Output**: 
- Specific broken paths or references identified
- Root cause hypothesis formed

### 2.3 Test Hypothesis

**Actions**:
1. Based on findings, test the most likely hypothesis:
   - If files moved: Check if Dockerfile paths match new locations
   - If imports broken: Verify import statements reference correct paths
   - If config missing: Check if config files exist in expected location

2. Verify hypothesis with evidence:
   - Show specific broken path
   - Show what should be fixed
   - Confirm this matches the error pattern

**Expected Output**: 
- Root cause confirmed with evidence
- Specific fix required identified

## Step 3: Fix and Verify

### 3.1 Implement Fix

**Actions**:
1. Based on root cause, implement fix:
   - **If Dockerfile paths broken**: Update COPY commands to match new file locations
   - **If imports broken**: Update import paths to match new file structure
   - **If config missing**: Restore config files or update paths
   - **If entry point wrong**: Update startup command or file location

2. Verify fix addresses root cause:
   - Check all affected files
   - Verify paths are correct
   - Test imports if possible

**Expected Output**: 
- Fix implemented
- Files updated with correct paths/references

### 3.2 Verify Fix

**Actions**:
1. Test locally if possible:
   ```bash
   docker build -t test-build .
   # If build succeeds, check if files are in correct locations
   ```

2. Commit and push fix:
   ```bash
   git add .
   git commit -S -m "fix: resolve Render deployment update failure (FM-041) - [brief description]"
   git push origin investigation/fm-041-render-deployment-failures
   ```

3. Monitor deployment:
   - Watch Render deployment status
   - Check build logs
   - Check runtime logs
   - Verify deployment succeeds

**Expected Output**: 
- Fix committed and pushed
- Deployment succeeds
- Service running correctly

## Documentation

After resolution, update:
- `FRACAS_FM_041_RENDER_DEPLOYMENT_FAILURES.md` with root cause and fix
- Add prevention measure if applicable

## Key Questions to Answer

1. **What exactly failed?** (build vs runtime, specific error)
2. **What changed in commit 6116eb8?** (files moved, deleted, modified)
3. **What broke?** (Dockerfile paths, imports, config, entry point)
4. **How to fix?** (update paths, restore files, fix imports)
5. **How to prevent?** (validation, documentation, checks)

## Success Criteria

- [ ] Failure point clearly identified
- [ ] Root cause identified with evidence
- [ ] Fix implemented
- [ ] Deployment succeeds
- [ ] FRACAS report updated

---

**Time Estimate**: 50-70 minutes  
**Priority**: P0 - Critical  
**Status**: Ready for execution

