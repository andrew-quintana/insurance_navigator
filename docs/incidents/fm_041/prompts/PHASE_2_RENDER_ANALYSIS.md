# FM-041 Phase 2: Render Deployment Analysis

**Status**: ⏳ PENDING  
**Date**: 2025-11-09  
**Phase**: 2 of 7

## Phase Objective

Analyze all Render deployments since commit 6116eb8 to identify failure patterns, extract error messages, and create a comprehensive timeline of deployment failures.

## Context

The latest deployment (`dep-d480hsngi27c7398f2sg`) failed with status `update_failed` even though the build succeeded. This phase will investigate the deployment history to understand when failures started and identify patterns.

## Reference Documents

- Main FRACAS Report: `docs/incidents/fm_041/FRACAS_FM_041_RENDER_DEPLOYMENT_FAILURES.md`
- Investigation Checklist: `docs/incidents/fm_041/investigation_checklist.md`

## Key Information

- **Service ID**: `srv-d0v2nqvdiees73cejf0g` (api-service-production)
- **Starting Commit**: `6116eb8` (Nov 8, 2025)
- **Latest Failed Deployment**: `dep-d480hsngi27c7398f2sg`

## Tasks

### 1. Deployment History Analysis
**Objective**: Get complete deployment history since commit 6116eb8

**Actions**:
1. Use Render MCP to list all deployments since Nov 8, 2025
   ```bash
   mcp_render_list_deploys serviceId=srv-d0v2nqvdiees73cejf0g limit=20
   ```
2. Filter deployments by status (update_failed, live, deactivated, canceled)
3. Extract commit SHAs and messages for each deployment
4. Map deployments to git commits
5. Create timeline showing deployment states over time

**Expected Output**: Complete list of deployments with states and commit mappings

### 2. Failed Deployment Analysis
**Objective**: Analyze all failed deployments to identify error patterns

**Actions**:
1. Identify all deployments with `update_failed` status
2. For each failed deployment:
   - Get deployment details using `mcp_render_get_deploy`
   - Get build logs using `mcp_render_list_logs` with `type=['build']`
   - Get runtime logs using `mcp_render_list_logs` with `type=['app']`
   - Extract error messages
   - Identify failure point in deployment process
3. Categorize errors:
   - Build errors (shouldn't occur if build succeeded)
   - Runtime errors
   - Configuration errors
   - Health check failures
   - Other errors
4. Create error pattern analysis

**Expected Output**: Categorized list of all deployment failures with error messages

### 3. Latest Failed Deployment Deep Dive
**Objective**: Detailed analysis of the most recent failure

**Actions**:
1. Get full deployment details for `dep-d480hsngi27c7398f2sg`
   ```bash
   mcp_render_get_deploy serviceId=srv-d0v2nqvdiees73cejf0g deployId=dep-d480hsngi27c7398f2sg
   ```
2. Get build logs around deployment time:
   ```bash
   mcp_render_list_logs resource=['srv-d0v2nqvdiees73cejf0g'] startTime=2025-11-09T03:20:00Z endTime=2025-11-09T03:30:00Z type=['build'] limit=100
   ```
3. Get runtime logs around deployment time:
   ```bash
   mcp_render_list_logs resource=['srv-d0v2nqvdiees73cejf0g'] startTime=2025-11-09T03:20:00Z endTime=2025-11-09T03:30:00Z type=['app'] limit=100
   ```
4. Analyze deployment process:
   - Build phase (Docker build)
   - Image push phase
   - Deployment update phase
   - Service startup phase
   - Health check phase
5. Check for error messages in logs
6. Document exact failure sequence

**Expected Output**: Detailed failure analysis with exact error location

### 4. Successful Deployment Comparison
**Objective**: Compare failed deployments with successful ones

**Actions**:
1. Find last successful deployment before failure
2. Get deployment details for successful deployment
3. Compare:
   - Build configuration
   - Environment variables (if accessible)
   - Service configuration
   - Commit changes
4. Identify differences between successful and failed deployments
5. Document what changed

**Expected Output**: Comparison report showing differences

## Deliverables

1. **Deployment Timeline**: Timeline showing all deployments since 6116eb8 with states
2. **Failure Analysis**: List of all failed deployments with error messages
3. **Error Patterns**: Categorized error patterns and frequencies
4. **Latest Failure Details**: Complete analysis of dep-d480hsngi27c7398f2sg
5. **Comparison Report**: Differences between successful and failed deployments
6. **Updated FRACAS Report**: Add findings to main FRACAS report

## Success Criteria

- [ ] All deployments since 6116eb8 identified and categorized
- [ ] All failed deployments analyzed with error messages extracted
- [ ] Latest failure fully documented with log analysis
- [ ] Successful deployment identified and compared
- [ ] FRACAS report updated with Phase 2 findings
- [ ] Investigation checklist updated with Phase 2 completion

## Tools Required

- Render MCP (list_deploys, get_deploy, list_logs)
- GitHub MCP (for commit information if needed)
- File reading (for configuration comparison)

## Next Phase

After completing this phase, proceed to **Phase 3: Dependency & Configuration Analysis** using `prompts/PHASE_3_DEPENDENCY_ANALYSIS.md`

---

**Investigation Notes**: Document any patterns or observations during this phase in the FRACAS report.

