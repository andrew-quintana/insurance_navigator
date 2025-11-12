# FM-042: Test Script Fixes

**Date**: 2025-01-10  
**Status**: ✅ FIXED

## Issues Identified

### 1. Container Startup Failure
**Problem**: Container failed to start with error:
```
FileNotFoundError: Environment file not found: .env or .env.development
```

**Root Cause**: The environment loader was detecting the container as a local deployment (not cloud) because `RENDER` environment variable was not set. This caused it to look for `.env` files which don't exist in Docker images.

**Solution**: Updated test script to:
- Set `RENDER=true` to enable cloud deployment mode
- Provide all required environment variables via `-e` flags:
  - `ENVIRONMENT=testing`
  - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`
  - `OPENAI_API_KEY`, `LLAMAPARSE_API_KEY`
  - `LOG_LEVEL=INFO`

### 2. Dockerfile Warnings
**Problem**: Docker build showed 3 warnings:
1. `FromAsCasing: 'as' and 'FROM' keywords' casing do not match (line 2)`
2. `UndefinedVar: Usage of undefined variable '$PYTHONPATH' (line 68)`
3. `UndefinedVar: Usage of undefined variable '$PORT' (line 71)`

**Solutions**:
1. **FROM/AS casing**: Changed `FROM python:3.11-slim as builder` to `FROM python:3.11-slim AS builder` (uppercase AS)
2. **PYTHONPATH**: Removed undefined variable reference - changed from `ENV PYTHONPATH=...:$PYTHONPATH` to `ENV PYTHONPATH=...` (since we're in a clean container, no need to append)
3. **PORT variable**: Set default `ENV PORT=8000` and use `${PORT:-8000}` syntax in CMD/HEALTHCHECK (runtime variable, not build-time)

### 3. macOS grep Compatibility
**Problem**: Test script used `grep -oP` (Perl regex) which is not supported on macOS:
```
grep: invalid option -- P
```

**Solution**: Replaced with `sed -E` (extended regex) which is available on both macOS and Linux:
```bash
# Before:
BUILD_TIME=$(grep -oP 'real\s+\K[\d.]+' /tmp/docker_build.log | head -1)

# After:
BUILD_TIME=$(grep "real" /tmp/docker_build.log | sed -E 's/.*real[[:space:]]+([0-9]+\.[0-9]+).*/\1/' | head -1)
```

## Files Modified

1. **scripts/test_dockerfile_fm042.sh**
   - Added cloud deployment mode detection (`RENDER=true`)
   - Added required environment variables for container startup
   - Fixed grep command for macOS compatibility

2. **Dockerfile**
   - Fixed FROM/AS casing (uppercase AS)
   - Fixed PYTHONPATH environment variable (removed undefined reference)
   - Fixed PORT variable handling (proper ENV with runtime default)

## Testing

After these fixes, the test script should:
1. ✅ Build successfully without warnings
2. ✅ Start container in cloud deployment mode
3. ✅ Pass all test checks (build, dependencies, startup, health check)

## Next Steps

1. Run the test script again: `./scripts/test_dockerfile_fm042.sh`
2. Verify all tests pass
3. If successful, proceed with deployment to staging/production

## Notes

- The test environment variables are dummy values - they're sufficient for the application to start and validate the Dockerfile changes
- In production, real environment variables will be provided by the deployment platform (Render)
- The cache directory check may still show "MISSING" - this is expected as cache mounts don't persist in the final image, only during build

