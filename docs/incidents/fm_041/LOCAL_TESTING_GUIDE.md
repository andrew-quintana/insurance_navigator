# Local Testing Guide for FM-041 Fix

This guide explains how to test dependency compatibility locally to catch similar errors before deployment.

## Problem

The FM-041 deployment failure was caused by a dependency version mismatch that only appeared at runtime:
- `supabase_auth` requires `pydantic>=2.6.0` (for `with_config` decorator)
- Project was pinned to `pydantic==2.5.0`
- Error only appeared when application tried to start in Docker container

## Testing Solutions

### Option 1: Docker-Based Test (Recommended)

This test builds the Docker image and tests imports in the same environment as Render deployment:

```bash
./scripts/test_docker_imports.sh
```

**What it does:**
1. Builds the Docker image using the same Dockerfile as production
2. Runs import tests inside the Docker container
3. Verifies pydantic version and `with_config` availability
4. Tests supabase and critical application imports

**Advantages:**
- Tests in the exact same environment as deployment
- Catches dependency version mismatches
- Catches import errors before deployment
- No need to install dependencies locally

**When to use:**
- Before every deployment
- After updating dependency versions
- After major refactors that might affect imports

### Option 2: Dependency Compatibility Script

For quick checks without Docker:

```bash
python3 scripts/test_dependency_compatibility.py
```

**Note:** This requires dependencies to be installed locally (in virtual environment).

**What it does:**
1. Checks pydantic version and `with_config` availability
2. Tests supabase imports
3. Tests critical application imports

**When to use:**
- Quick checks during development
- When you have a local virtual environment set up

### Option 3: Quick Dependency Check (No Docker)

For quick checks when Docker isn't available:

```bash
python3 scripts/test_dependency_compatibility.py
```

**Note**: Requires dependencies to be installed locally. For production-like testing, use Option 1 (Docker-based test).

## Pre-Deployment Checklist

Before deploying to Render, run:

1. **Docker Import Test** (catches FM-041 type errors - REQUIRED):
   ```bash
   ./scripts/test_docker_imports.sh
   ```
   
   This is the primary test that validates dependencies in the same environment as Render.

2. **Verify dependency versions**:
   ```bash
   grep -E "pydantic|supabase" requirements-api.txt constraints.txt
   ```

3. **Check for version conflicts**:
   ```bash
   # In Docker container, check installed versions
   docker run --rm insurance-navigator-test:latest pip list | grep -E "pydantic|supabase"
   ```

## Integration with CI/CD

### GitHub Actions (Future)

Add to `.github/workflows/pre-deployment-check.yml`:

```yaml
name: Pre-Deployment Checks

on:
  pull_request:
    branches: [main]

jobs:
  test-imports:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Docker Imports
        run: ./scripts/test_docker_imports.sh
```

### Pre-commit Hook (Optional)

Add to `.git/hooks/pre-push`:

```bash
#!/bin/bash
# Test imports before pushing
if ! ./scripts/test_docker_imports.sh; then
    echo "Import tests failed! Fix errors before pushing."
    exit 1
fi
```

## Common Issues and Solutions

### Issue: "No module named 'pydantic'"
**Solution:** Install dependencies or use Docker-based test

### Issue: "cannot import name 'with_config'"
**Solution:** Update pydantic to >=2.6.0 in requirements-api.txt and constraints.txt

### Issue: "ImportError: No module named 'supabase'"
**Solution:** Ensure supabase is in requirements-api.txt

### Issue: Docker build fails
**Solution:** Check Dockerfile syntax and ensure all COPY paths exist

## Testing After Dependency Updates

When updating dependencies:

1. **Update requirements files**
2. **Run Docker import test:**
   ```bash
   ./scripts/test_docker_imports.sh
   ```
3. **If test passes, proceed with deployment**
4. **If test fails, fix dependency versions and repeat**

## Example: Testing FM-041 Fix

After updating pydantic versions:

```bash
# 1. Test the fix
./scripts/test_docker_imports.sh

# Expected output:
# ✓ Pydantic version: 2.9.0
# ✓ with_config is available
# ✓ Supabase imports successful
# ✓ Critical application imports successful
# ✓ All import tests passed!
```

## Monitoring

After deployment, monitor Render logs for:
- Successful application startup
- No import errors in runtime logs
- Health check endpoints responding

## Related Files

- `scripts/test_docker_imports.sh` - Docker-based import test
- `scripts/test_dependency_compatibility.py` - Python-based compatibility test
- `scripts/test_deployment_readiness.sh` - Full deployment readiness check
- `requirements-api.txt` - API service dependencies
- `constraints.txt` - Dependency version constraints

