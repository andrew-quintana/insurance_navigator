# FM-042: Testing Plan

**Date**: 2025-01-10  
**Status**: 📋 READY FOR TESTING

## Testing Objectives

Validate that FM-042 corrective actions work correctly:
1. ✅ Conflicting flags removed
2. ✅ Cache mounts work properly
3. ✅ Dependencies install correctly (pydantic 2.9.0)
4. ✅ Application starts successfully
5. ✅ Only necessary directories copied
6. ✅ All endpoints accessible

## Test Environment

- **Local Docker**: Test build and run locally
- **Staging** (optional): Test on staging environment
- **Production**: Deploy after successful local tests

## Test Suite

### Automated Tests

Run the automated test script:

```bash
./scripts/test_dockerfile_fm042.sh
```

This script tests:
1. ✅ Docker build succeeds
2. ✅ Image size is reasonable
3. ✅ Pydantic 2.9.0 installed correctly
4. ✅ Cache directory exists
5. ✅ Container starts successfully
6. ✅ Health check endpoint works
7. ✅ All required directories present
8. ✅ main.py exists
9. ✅ Conflicting flags removed from Dockerfile
10. ✅ Application logs are clean

### Manual Tests

#### 1. Build Test

```bash
# Build the image
docker build -t insurance-navigator-fm042-test .

# Check build time (should be faster on subsequent builds)
time docker build -t insurance-navigator-fm042-test .
```

**Expected Results**:
- ✅ Build succeeds without errors
- ✅ Subsequent builds are 20-40% faster (cache working)
- ✅ No warnings about conflicting flags

#### 2. Dependency Verification

```bash
# Check pydantic version
docker run --rm insurance-navigator-fm042-test \
  python -c "import pydantic; print(pydantic.__version__)"

# Should output: 2.9.0
```

**Expected Results**:
- ✅ Pydantic version is exactly 2.9.0
- ✅ No import errors

#### 3. Application Startup Test

```bash
# Start container
docker run -d \
  --name fm042-test \
  -p 8001:8000 \
  -e PORT=8000 \
  insurance-navigator-fm042-test

# Wait for startup
sleep 5

# Check logs
docker logs fm042-test

# Test health endpoint
curl http://localhost:8001/health
```

**Expected Results**:
- ✅ Container starts without errors
- ✅ Health endpoint returns 200 OK
- ✅ No import errors in logs
- ✅ Application initializes successfully

#### 4. Chat Endpoint Test

```bash
# Test chat endpoint (requires authentication)
curl -X POST http://localhost:8001/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "message": "test message",
    "conversation_id": "test_conv"
  }'
```

**Expected Results**:
- ✅ Endpoint responds (may need valid auth token)
- ✅ No 500 errors
- ✅ Application processes request

#### 5. Directory Structure Verification

```bash
# Check that only necessary directories are copied
docker run --rm insurance-navigator-fm042-test \
  ls -la /app

# Should see:
# - main.py
# - api/
# - config/
# - core/
# - db/
# - utils/
# - agents/
# - backend/
# - Should NOT see: docs/, tests/, ui/, etc.
```

**Expected Results**:
- ✅ Only required directories present
- ✅ No unnecessary files (docs, tests, etc.)
- ✅ main.py in root

#### 6. Cache Effectiveness Test

```bash
# First build (no cache)
time docker build --no-cache -t insurance-navigator-fm042-test . > /tmp/build1.log

# Second build (with cache)
time docker build -t insurance-navigator-fm042-test . > /tmp/build2.log

# Compare build times
echo "First build:"
grep "real" /tmp/build1.log
echo "Second build:"
grep "real" /tmp/build2.log
```

**Expected Results**:
- ✅ Second build is 20-40% faster
- ✅ Cache is being used (check logs for "Using cache")
- ✅ Dependencies layer is cached

## Validation Checklist

### Pre-Deployment

- [ ] ✅ Docker build succeeds locally
- [ ] ✅ All automated tests pass
- [ ] ✅ Pydantic 2.9.0 verified
- [ ] ✅ Health endpoint works
- [ ] ✅ No conflicting flags in Dockerfile
- [ ] ✅ Only necessary directories copied
- [ ] ✅ Application starts successfully
- [ ] ✅ Build time improved (cache working)

### Post-Deployment (Render)

- [ ] ✅ Build succeeds on Render
- [ ] ✅ Application starts successfully
- [ ] ✅ Health endpoint accessible
- [ ] ✅ Chat endpoint works
- [ ] ✅ No errors in logs
- [ ] ✅ Build time improved vs previous

## Troubleshooting

### Build Fails

1. Check build logs: `/tmp/docker_build.log`
2. Verify Dockerfile syntax: `docker build --dry-run .` (if supported)
3. Check for missing files/directories
4. Verify constraints.txt exists

### Application Won't Start

1. Check container logs: `docker logs <container-name>`
2. Verify environment variables
3. Check import errors
4. Verify all required directories copied

### Dependencies Wrong Version

1. Verify constraints.txt has correct versions
2. Check pip install command in Dockerfile
3. Verify cache isn't causing issues
4. Try `--no-cache` build flag

### Cache Not Working

1. Verify cache mount syntax in Dockerfile
2. Check that conflicting flags are removed
3. Verify PIP_NO_CACHE_DIR is not set
4. Check Docker build cache settings

## Success Criteria

### Must Have

- ✅ Build succeeds
- ✅ Pydantic 2.9.0 installed
- ✅ Application starts
- ✅ Health endpoint works
- ✅ No conflicting flags

### Should Have

- ✅ Build time improved by 20%+
- ✅ Cache effectiveness > 50%
- ✅ Chat endpoint accessible
- ✅ Only necessary files copied

### Nice to Have

- ✅ Build time improved by 40%+
- ✅ Cache effectiveness > 70%
- ✅ Zero build failures
- ✅ All endpoints working

## Test Execution

### Quick Test (5 minutes)

```bash
# Run automated test script
./scripts/test_dockerfile_fm042.sh
```

### Full Test (15-20 minutes)

1. Run automated test script
2. Manual build time comparison
3. Cache effectiveness test
4. Full application startup test
5. Endpoint testing

### Production Validation (After Deployment)

1. Monitor first 5-10 builds on Render
2. Check build times vs previous
3. Verify application health
4. Monitor error rates
5. Check cache effectiveness metrics

## Rollback Plan

If tests fail:

1. **Immediate**: Revert Dockerfile changes
   ```bash
   git checkout HEAD -- Dockerfile
   ```

2. **Alternative**: Restore previous working version
   ```bash
   git show <previous-commit>:Dockerfile > Dockerfile
   ```

3. **Last Resort**: Manual fix of specific issues

## Next Steps After Testing

1. ✅ All tests pass → Create PR
2. ⏳ PR review → Address feedback
3. ⏳ Merge to main → Deploy to Render
4. ⏳ Monitor deployment → Verify success
5. ⏳ Document results → Update FRACAS

---

**Test Plan Date**: 2025-01-10  
**Status**: 📋 READY FOR EXECUTION

