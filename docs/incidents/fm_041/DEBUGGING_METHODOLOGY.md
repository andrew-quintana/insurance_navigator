# FM-041: Concise Debugging Methodology

## Overview

Streamlined 3-step approach to debug and resolve Render deployment failures when build succeeds but deployment update fails.

## Methodology

### Step 1: Understand the Failure (15-20 min)
**Goal**: Get clear picture of what failed and when

1. **Get deployment details and logs**
   - Use Render MCP to get failed deployment details
   - Extract build logs (type=build) - verify build actually succeeded
   - Extract runtime logs (type=app) around deployment time
   - Look for error messages, exceptions, or failure patterns

2. **Compare with last successful deployment**
   - Find last successful deployment
   - Compare commit, configuration, and logs
   - Identify what changed between success and failure

**Output**: Clear understanding of failure point and error messages

### Step 2: Identify Root Cause (20-30 min)
**Goal**: Find what changed that caused the failure

1. **Analyze commit changes**
   - Review commit 6116eb8 changes: `git show 6116eb8 --stat`
   - Focus on:
     - Files moved/deleted (check Dockerfile COPY paths)
     - Service entry point changes (main.py location)
     - Import path changes (config/ directory)
     - Dockerfile modifications

2. **Verify critical paths**
   - Check Dockerfile COPY commands match actual file locations
   - Verify service entry point exists and is correct
   - Check imports resolve correctly after file moves
   - Verify environment variables are set

3. **Test hypothesis**
   - If files moved: verify Dockerfile paths updated
   - If imports broken: verify import paths updated
   - If config missing: verify config files present

**Output**: Root cause identified with evidence

### Step 3: Fix and Verify (15-20 min)
**Goal**: Implement fix and confirm it works

1. **Implement fix**
   - Update Dockerfile paths if files moved
   - Fix import paths if broken
   - Update configuration if needed
   - Fix environment variables if missing

2. **Verify fix**
   - Test locally if possible (docker build)
   - Commit and push fix
   - Monitor deployment
   - Verify deployment succeeds

**Output**: Fix deployed and verified

## Key Tools

- **Render MCP**: `list_deploys`, `get_deploy`, `list_logs`
- **Git**: `show`, `diff`, `log` to analyze changes
- **File system**: Verify file locations and paths

## Common Root Causes

1. **File moves without Dockerfile updates** - COPY commands reference old paths
2. **Broken imports after file moves** - Import paths not updated
3. **Missing config files** - Config directory moved or deleted
4. **Service entry point changed** - main.py moved or startup command wrong
5. **Environment variables missing** - Required vars not set in Render

## Success Criteria

- [ ] Failure point clearly identified
- [ ] Root cause identified with evidence
- [ ] Fix implemented and tested
- [ ] Deployment succeeds
- [ ] Prevention measure documented

---

**Total Time Estimate**: 50-70 minutes  
**Focus**: Get to root cause quickly, fix, verify, document

