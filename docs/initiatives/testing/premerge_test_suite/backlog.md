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

### FM-042: API Dockerfile Validation and Pre-Merge Testing

**Status**: ⏳ PENDING  
**Priority**: HIGH  
**Created**: 2025-01-10  
**Related Issue**: [FM-042](../incidents/fm_042/FRACAS_FM_042_DOCKERFILE_OPTIMIZATION_INVESTIGATION.md) - Dockerfile Optimization Investigation

#### Problem Statement

API Dockerfile changes can break deployments if not properly validated. The API Dockerfile needs comprehensive pre-merge validation and should be verified to work equivalently to docker-compose.yml configurations. Note: Worker Dockerfile did not require changes in FM-042.

#### Solution Implemented

- Fixed Dockerfile warnings (FROM/AS casing, undefined variables)
- Created comprehensive test script: `scripts/test_dockerfile_fm042.sh`
- Validated Dockerfile builds, dependencies, and application startup
- Added `--no-cache` option for fresh build testing

#### Validation Tests Required

**Test Suite Name**: `validate_dockerfile_configurations`

**Test Location**: `scripts/test_dockerfile_*.sh` (to be created/expanded)

**Test Components**:

1. **API Dockerfile Pre-Merge Validation** (`scripts/test_dockerfile_fm042.sh` - ✅ IMPLEMENTED)
   - ✅ Docker build succeeds (with and without cache)
   - ✅ Image size is reasonable
   - ✅ Dependencies install correctly (pydantic 2.9.0)
   - ✅ Container starts and uvicorn runs
   - ✅ Application initialization begins
   - ✅ Required directories present
   - ✅ No conflicting flags (PIP_NO_CACHE_DIR, --no-cache-dir, --force-reinstall)
   - ✅ Cache mounts work properly
   - ✅ Environment variables configured correctly
   - ✅ Handles expected database connection failures gracefully
   
   **Pre-Merge Integration**:
   - Should run automatically before merge to `main` branch
   - Should run on any changes to `Dockerfile` or `requirements-api.txt`
   - Can be run manually: `./scripts/test_dockerfile_fm042.sh [--no-cache]`
   - Exit code 0 = pass, non-zero = fail

2. **Dockerfile ↔ docker-compose.yml Equivalence Test** (`scripts/test_dockerfile_compose_equivalence.sh` - to be created)
   - Extract build configuration from docker-compose.yml
   - Extract build configuration from Dockerfile
   - Compare base images (should match)
   - Compare environment variables (should be compatible)
   - Compare exposed ports (should match)
   - Compare health check configurations (should be equivalent)
   - Compare CMD/command (should be equivalent)
   - Verify both can build successfully
   - Verify both produce runnable containers

**Test Design Principles** (Agnostic to Changes):

1. **Configuration Extraction**: Parse Dockerfile and docker-compose.yml programmatically
   - Use Dockerfile parsing libraries or regex patterns
   - Extract docker-compose.yml service definitions
   - Compare semantic meaning, not exact strings

2. **Flexible Matching**:
   - Allow environment variable differences (compose may override)
   - Allow minor version differences in base images
   - Focus on functional equivalence, not exact match

3. **Change Detection**:
   - Track which aspects differ and why
   - Report differences clearly
   - Fail only on breaking changes (not cosmetic)

4. **Test Structure**:
   ```bash
   # Extract Dockerfile config
   dockerfile_base=$(extract_base_image Dockerfile)
   dockerfile_cmd=$(extract_cmd Dockerfile)
   dockerfile_env=$(extract_env_vars Dockerfile)
   
   # Extract docker-compose.yml config
   compose_base=$(extract_build_image docker-compose.yml api)
   compose_cmd=$(extract_command docker-compose.yml api)
   compose_env=$(extract_environment docker-compose.yml api)
   
   # Compare (with tolerance for expected differences)
   assert_equivalent "$dockerfile_base" "$compose_base"
   assert_equivalent "$dockerfile_cmd" "$compose_cmd"
   assert_env_compatible "$dockerfile_env" "$compose_env"
   ```

**Expected Behavior**:
- All Dockerfile builds succeed
- All containers start correctly
- Dockerfile and docker-compose.yml configurations are functionally equivalent
- Tests pass even when non-breaking changes are made to either file

**Failure Criteria**:
- Dockerfile build fails
- Container fails to start
- Critical configuration mismatch between Dockerfile and docker-compose.yml
- Missing required directories or files
- Conflicting flags present

**Integration Points**:
- **Pre-Merge**: Run `./scripts/test_dockerfile_fm042.sh` before merge to `main` branch
- **CI/CD Pipeline**: Integrate into GitHub Actions or similar
- **Pre-Deployment**: Include in deployment checklist
- **Trigger Conditions**: Run on changes to `Dockerfile`, `requirements-api.txt`, or `constraints.txt`

**Implementation Notes**:
- ✅ API Dockerfile test script implemented: `scripts/test_dockerfile_fm042.sh`
- ⏳ Need to create: `scripts/test_dockerfile_compose_equivalence.sh`
- Consider using `docker inspect` to extract actual runtime configuration
- Use `docker-compose config` to parse compose file programmatically
- Make tests idempotent and parallelizable
- Note: Worker Dockerfile validation can be added later if needed (not required for FM-042)

**Related Documentation**:
- [FM-042 FRACAS Report](../incidents/fm_042/FRACAS_FM_042_DOCKERFILE_OPTIMIZATION_INVESTIGATION.md)
- [FM-042 Test Fixes](../incidents/fm_042/fm_042_test_fixes.md)
- [Dockerfile Best Practices](../incidents/fm_042/DOCKERFILE_BEST_PRACTICES.md)
- [Test Script](../scripts/test_dockerfile_fm042.sh)

**Future Enhancements**:
- Add Dockerfile linting (hadolint integration)
- Add security scanning (trivy, snyk)
- Add build time tracking and regression detection
- Add image size regression detection
- Add dependency vulnerability scanning

---

## Additional Backlog Items

_Add other validation tests, improvements, or tasks here as needed._

