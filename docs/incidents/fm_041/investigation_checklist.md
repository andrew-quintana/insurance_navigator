# FM-041 Investigation Checklist

## Pre-Investigation Setup
- [x] Create investigation directory structure
- [x] Create FRACAS report template
- [x] Document initial failure information
- [ ] Review the investigation prompts thoroughly
- [ ] Gather all relevant tools and access credentials
- [ ] Access Render Dashboard for service (srv-d0v2nqvdiees73cejf0g)

## Phase 1: FRACAS Documentation Setup ✅ COMPLETE
- [x] Create `docs/incidents/fm_041/` directory
- [x] Create `docs/incidents/fm_041/prompts/` subdirectory
- [x] Create `README.md` with failure mode overview
- [x] Create main FRACAS report: `FRACAS_FM_041_RENDER_DEPLOYMENT_FAILURES.md`
- [x] Create investigation checklist: `investigation_checklist.md`
- [x] Create all 7 phase prompt files
- [x] Document initial failure information

## Phase 2: Render Deployment Analysis ⏳ PENDING

### Deployment History Investigation
- [ ] Use Render MCP to list all deployments since Nov 8, 2025
  ```bash
  mcp_render_list_deploys serviceId=srv-d0v2nqvdiees73cejf0g limit=20
  ```
- [ ] Identify all failed deployments (update_failed status)
- [ ] Extract error messages from deployment logs
- [ ] Map failures to git commits
- [ ] Create timeline of failures
- [ ] Update FRACAS report with findings

### Latest Failed Deployment Analysis
- [ ] Review full deployment details for `dep-d480hsngi27c7398f2sg`
  ```bash
  mcp_render_get_deploy serviceId=srv-d0v2nqvdiees73cejf0g deployId=dep-d480hsngi27c7398f2sg
  ```
- [ ] Review build logs (type=build)
- [ ] Review runtime logs (type=app) around deployment time
- [ ] Identify exact failure point
- [ ] Check for error messages in logs
- [ ] Document error details in FRACAS report

### Successful Deployment Comparison
- [ ] Find last successful deployment before failure
- [ ] Compare deployment configurations
- [ ] Identify differences between successful and failed deployments
- [ ] Check for configuration changes
- [ ] Document comparison in FRACAS report

### Phase 2 Deliverables
- [ ] Complete deployment timeline
- [ ] Error pattern categorization
- [ ] Root cause identification
- [ ] Detailed analysis document: `phase2_deployment_analysis.md`

## Phase 3: Dependency & Configuration Analysis ⏳ PENDING

### Dockerfile and Build Configuration
- [ ] Review Dockerfile for changes in commit 6116eb8
- [ ] Check for missing files or broken COPY commands
- [ ] Verify build context and paths
- [ ] Check for environment variable requirements
- [ ] Document findings

### Environment Variables
- [ ] Review environment variable configuration
- [ ] Check for missing required variables
- [ ] Verify variable values are correct
- [ ] Check for variable name changes
- [ ] Document any issues

### Service Configuration
- [ ] Review Render service configuration
- [ ] Check startup command
- [ ] Verify health check configuration
- [ ] Check resource allocation
- [ ] Document configuration status

### Phase 3 Deliverables
- [ ] Complete dependency and configuration status report
- [ ] Dockerfile analysis
- [ ] Environment variable verification
- [ ] Configuration file analysis
- [ ] Detailed analysis document: `phase3_dependency_analysis.md`

## Phase 4: Codebase Changes Analysis ⏳ PENDING

### Commit 6116eb8 Review
- [ ] Analyze what files were changed in commit 6116eb8
  ```bash
  git show 6116eb8 --stat
  git show 6116eb8 --name-only
  ```
- [ ] Check if any critical files were moved or deleted
- [ ] Verify if Dockerfile or build configs were affected
- [ ] Check if service entry points changed
- [ ] Document file change impact

### File Structure Changes
- [ ] Check for moved directories
- [ ] Verify file paths in Dockerfile
- [ ] Check for broken imports or references
- [ ] Verify service startup scripts exist
- [ ] Document structure changes

### Phase 4 Deliverables
- [ ] Complete commit 6116eb8 impact analysis
- [ ] File structure change analysis
- [ ] Import/reference verification
- [ ] Build script analysis
- [ ] Detailed analysis document: `phase4_codebase_analysis.md`

## Phase 5: Root Cause Synthesis ⏳ PENDING

### Findings Synthesis
- [ ] Review all evidence gathered from Phases 2-4
- [ ] Identify patterns and correlations
- [ ] Create comprehensive failure timeline
- [ ] Document all hypotheses

### Hypothesis Evaluation
- [ ] **Hypothesis 1**: [Description] - Evaluate with evidence
- [ ] **Hypothesis 2**: [Description] - Evaluate with evidence
- [ ] **Hypothesis 3**: [Description] - Evaluate with evidence
- [ ] Rank hypotheses by likelihood

### Root Cause Identification
- [ ] Select most likely root cause based on evidence
- [ ] Document supporting evidence
- [ ] Identify contributing factors
- [ ] Update FRACAS report with root cause analysis

### Phase 5 Deliverables
- [ ] Evidence summary
- [ ] Hypothesis evaluation
- [ ] Root cause statement
- [ ] Impact assessment
- [ ] Updated FRACAS report
- [ ] Detailed analysis document: `phase5_root_cause_synthesis.md`

## Phase 6: Solution Implementation ⏳ PENDING

### Fix Implementation
- [ ] Implement fix based on root cause
- [ ] Verify fix addresses root cause
- [ ] Test locally if possible
- [ ] Update configuration files
- [ ] Document changes

### Deployment and Verification
- [ ] Commit fixes to repository
- [ ] Push to remote repository
- [ ] Monitor Render deployment
- [ ] Verify deployment succeeds
- [ ] Update FRACAS report with solution details

### Phase 6 Deliverables
- [ ] Fix implemented
- [ ] Changes committed and pushed
- [ ] Deployment verified
- [ ] FRACAS report updated
- [ ] Implementation document: `phase6_solution_implementation.md`

## Phase 7: Prevention Measures ⏳ PENDING

### Build Validation
- [ ] Ensure all required files are present
- [ ] Add pre-deploy checks
- [ ] Verify deployment succeeds before merge
- [ ] Document validation process

### Documentation Updates
- [ ] Update deployment documentation
- [ ] Document required files and configurations
- [ ] Add troubleshooting guide for similar issues
- [ ] Update FRACAS report with prevention measures

### CI/CD Improvements
- [ ] Add deployment checks in CI pipeline
- [ ] Verify configurations before deployment
- [ ] Add automated validation
- [ ] Document CI/CD improvements

### Finalize FRACAS Documentation
- [ ] Complete all sections of FRACAS report
- [ ] Mark investigation as resolved
- [ ] Update README.md with resolution status
- [ ] Create summary for future reference

---

## Investigation Tools and Commands

### Render MCP Commands
```bash
# List deployments
mcp_render_list_deploys serviceId=srv-d0v2nqvdiees73cejf0g limit=20

# Get deployment details
mcp_render_get_deploy serviceId=srv-d0v2nqvdiees73cejf0g deployId=dep-d480hsngi27c7398f2sg

# Get logs
mcp_render_list_logs resource=['srv-d0v2nqvdiees73cejf0g'] startTime=2025-11-09T03:20:00Z endTime=2025-11-09T03:30:00Z type=['build'] limit=100
mcp_render_list_logs resource=['srv-d0v2nqvdiees73cejf0g'] startTime=2025-11-09T03:20:00Z endTime=2025-11-09T03:30:00Z type=['app'] limit=100
```

### Git Commands
```bash
# Show commit 6116eb8 changes
git show 6116eb8 --stat
git show 6116eb8 --name-only

# Check Dockerfile changes
git log --oneline --since="2025-11-08" -- Dockerfile
git diff 6116eb8 HEAD -- Dockerfile

# Check configuration files
git show HEAD:Dockerfile
git show HEAD:main.py
```

### Local Testing Commands
```bash
# Check Dockerfile
cat Dockerfile

# Test Docker build locally
docker build -t test-build .

# Check service configuration
cat render.yaml  # if exists
```

---

## Progress Tracking

**Investigation Started**: 2025-11-09  
**Phase 1 Completed**: 2025-11-09 ✅  
**Phase 2 Completed**: [TBD]
**Phase 3 Completed**: [TBD]
**Phase 4 Completed**: [TBD]
**Phase 5 Completed**: [TBD]
**Phase 6 Completed**: [TBD]
**Phase 7 Completed**: [TBD]

**Investigation Completed**: [TBD]  
**Resolution Deployed**: [TBD]  
**Monitoring Active**: [TBD]

---

## Notes and Observations

### Key Findings
- [ ] Finding 1: [Description]
- [ ] Finding 2: [Description]
- [ ] Finding 3: [Description]

### Critical Issues Identified
- [ ] Issue 1: [Description]
- [ ] Issue 2: [Description]
- [ ] Issue 3: [Description]

### Recommendations
- [ ] Recommendation 1: [Description]
- [ ] Recommendation 2: [Description]
- [ ] Recommendation 3: [Description]

---

**Investigator**: [TBD]  
**Reviewer**: [TBD]  
**Approval**: [TBD]  
**Date**: 2025-11-09

