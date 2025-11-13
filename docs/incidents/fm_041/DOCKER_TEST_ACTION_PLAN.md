# FM-041 Docker Test Action Plan

## Current Situation

### Disk Space Status
- **Before cleanup**: 94% full (906Mi available)
- **After cleanup**: 70% full (6.0Gi available) ✅
- **Freed**: ~5GB

### Existing Docker Images (from user screenshot)
1. **insurance_navigator-api**:latest
   - Size: 4.4 GB
   - Age: 1 month ago
   - **Likely has OLD pydantic 2.5.0** (before FM-041 fix)

2. **insurance_navigator-worker**:latest
   - Size: 1.4 GB
   - Age: 1 month ago
   - **Likely has OLD pydantic 2.5.0** (before FM-041 fix)

3. **public.ecr.aws/supabase/edge-runtime**
   - Size: 973.32 MB
   - Age: 29 days ago
   - External dependency (not our image)

### Dockerfile Status
- ✅ **Rolled back** to original working version (commit 0a0cc86b)
- ✅ **Pydantic fix included**: pydantic==2.9.0, pydantic-core==2.23.2
- ✅ **Dockerfile syntax**: Valid (only minor casing warning)

## Test Plan

### Step 1: Test Existing Image
```bash
# Check if existing image has the fix
docker run --rm insurance_navigator-api:latest python3 -c "
import pydantic
print(f'Pydantic: {pydantic.__version__}')
print('with_config available:', hasattr(pydantic, 'with_config'))
"
```

**Expected Result**: 
- If pydantic 2.5.0 → **NEEDS REBUILD** (old version, FM-041 not fixed)
- If pydantic 2.9.0 → **CAN USE EXISTING** (fix already applied)

### Step 2: If Rebuild Needed
```bash
# Build with current Dockerfile (has fix)
docker build -t insurance-navigator-test:latest -f Dockerfile .

# Test the fix
docker run --rm insurance-navigator-test:latest python3 -c "
import pydantic
assert hasattr(pydantic, 'with_config'), 'FM-041 NOT FIXED'
print('✓ FM-041 fix verified')
"
```

### Step 3: Verify Critical Imports
```bash
docker run --rm insurance-navigator-test:latest python3 -c "
from config.environment_loader import load_environment
from config.database import get_supabase_client
from db.services.auth_adapter import auth_adapter
print('✓ All critical imports work')
"
```

## Action Plan

### Scenario A: Existing Image Has Old Pydantic (Most Likely)
1. **Rebuild image** with current Dockerfile (has pydantic 2.9.0 fix)
2. **Test imports** to verify FM-041 fix
3. **Tag as latest** if tests pass
4. **Document** that rebuild was necessary

### Scenario B: Existing Image Has New Pydantic (Unlikely)
1. **Test existing image** to confirm fix
2. **Use existing image** for deployment
3. **No rebuild needed**

### Scenario C: Build Fails
1. **Check disk space** (should be fine now at 70%)
2. **Check Docker daemon** status
3. **Review build logs** for specific errors
4. **Fix issues** and retry

## Key Findings So Far

1. ✅ **Dockerfile rolled back** - using original working version
2. ✅ **Pydantic fix included** - requirements have pydantic 2.9.0
3. ✅ **Disk space cleared** - 6GB available now
4. ⚠️ **Existing images are 1 month old** - likely need rebuild
5. ✅ **Dockerfile syntax valid** - only minor casing warning

## Next Steps

1. **Test existing image** to check pydantic version
2. **Rebuild if needed** with current Dockerfile
3. **Verify FM-041 fix** works in new image
4. **Update documentation** with test results

## Commands Reference

```bash
# Check existing images
docker images | grep insurance

# Test existing image
docker run --rm insurance_navigator-api:latest python3 -c "import pydantic; print(pydantic.__version__)"

# Rebuild if needed
docker build -t insurance-navigator-test:latest -f Dockerfile .

# Test new image
docker run --rm insurance-navigator-test:latest python3 -c "import pydantic; assert hasattr(pydantic, 'with_config'); print('✓ Fix verified')"

# Clean up old images (after testing)
docker rmi insurance_navigator-api:latest insurance_navigator-worker:latest
```

