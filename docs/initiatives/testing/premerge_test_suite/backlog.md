# Project Backlog

This document tracks validation tests, improvements, and tasks that should be added to the pre-merge test suite and other development workflows.

---

### FM-040: Vercel Deployment Configuration Validation

**Status**: ⏳ PENDING  
**Priority**: HIGH  
**Created**: 2025-11-09  
**Related Issue**: [FM-040](../incidents/fm_040/README.md) - Vercel Deployment Failures

#### Problem Statement

Vercel deployments were failing with "Cannot find module 'tailwindcss'" errors because Vercel was building from the repository root instead of the `ui/` subdirectory where the Next.js application and dependencies are located.

#### Solution Implemented

- Added root-level `vercel.json` with `rootDirectory: "ui"` configuration
- Ensures Vercel always builds from the correct directory
- Version-controlled configuration prevents future configuration drift

#### Validation Test Required

Add a pre-merge validation test to ensure Vercel build configuration is correct:

**Test Name**: `validate_vercel_build_configuration`

**Test Location**: `docs/incidents/fm_040/validate_fix.sh` (already created)

**Test Steps**:
1. Verify root-level `vercel.json` exists with `rootDirectory: "ui"`
2. Verify `tailwindcss` is present in `ui/package.json`
3. Verify `tailwindcss` can be resolved from `ui/` directory
4. Verify all Tailwind configuration files exist:
   - `ui/tailwind.config.js`
   - `ui/postcss.config.js`
   - `ui/app/globals.css`
   - `ui/app/layout.tsx`
5. Verify `globals.css` contains Tailwind directives (`@tailwind base`, `@tailwind components`, `@tailwind utilities`)
6. Verify `postcss.config.js` includes tailwindcss plugin
7. Verify build can succeed from `ui/` directory (test with `npx next build`)

**Expected Behavior**:
- All validation checks pass
- Build succeeds when run from `ui/` directory
- No "Cannot find module 'tailwindcss'" errors

**Failure Criteria**:
- Root-level `vercel.json` missing or incorrect
- `tailwindcss` not found in `ui/package.json`
- Configuration files missing or incorrect
- Build fails when run from `ui/` directory

**Integration Points**:
- Should run before merge to `main` branch
- Should run as part of CI/CD pipeline
- Should be included in pre-deployment checklist

**Implementation Notes**:
- Validation script already exists: `docs/incidents/fm_040/validate_fix.sh`
- Script can be integrated into CI/CD pipeline
- Can be run manually: `./docs/incidents/fm_040/validate_fix.sh`
- Should be added to pre-merge hooks or CI pipeline

**Related Documentation**:
- [FM-040 FRACAS Report](../incidents/fm_040/FRACAS_FM_040_VERCEL_DEPLOYMENT_FAILURES.md)
- [Phase 6 Implementation](../incidents/fm_040/phase6_solution_implementation.md)
- [Validation Script](../incidents/fm_040/validate_fix.sh)

---

## Additional Backlog Items

_Add other validation tests, improvements, or tasks here as needed._

