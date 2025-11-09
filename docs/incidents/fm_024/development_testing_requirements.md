# FM-024 Development Testing Requirements

## MANDATORY Local Testing Before Staging Deployment

### Overview
All fixes for FM-024 must be thoroughly tested in the local development environment before any code is committed or deployed to staging. This ensures that storage authentication issues are resolved without breaking the working development environment.

---

## Local Development Environment Setup

### 1. Prerequisites
```bash
# Navigate to project directory
cd /Users/aq_home/1Projects/accessa/insurance_navigator

# Activate virtual environment
source .venv/bin/activate

# Verify Python version
python --version  # Should be 3.11.x
```

### 2. Start Local Supabase
```bash
# Start Supabase local development environment
supabase start

# Verify Supabase is running
supabase status
```

**Expected Output**:
```
         API URL: http://127.0.0.1:54321
     GraphQL URL: http://127.0.0.1:54321/graphql/v1
  S3 Storage URL: http://127.0.0.1:54321/storage/v1/s3
    Database URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
      Studio URL: http://127.0.0.1:54323
```

### 3. Start API Server
```bash
# Start the API server in background
python main.py &

# Verify API is running
curl http://localhost:8000/health
```

**Expected Output**:
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "storage_service": {"status": "healthy"}
  }
}
```

---

## Testing Protocol

### Phase 1: Baseline Testing
**Purpose**: Verify current state before making changes

```bash
# 1. Test local storage authentication (should work)
python test_storage_auth_error.py

# 2. Test staging storage authentication (should fail)
python test_staging_storage_error.py

# 3. Test full upload flow (may fail due to auth complexity)
python test_upload_with_auth.py
```

**Success Criteria**:
- ✅ Local storage test passes
- ❌ Staging storage test fails (expected)
- ⚠️ Upload flow test may fail (acceptable)

### Phase 2: Fix Implementation
**Purpose**: Implement the identified fix

1. **Make code changes** based on investigation findings
2. **Test changes locally** using the same test scripts
3. **Verify no regression** in local functionality

### Phase 3: Validation Testing
**Purpose**: Ensure fix works and doesn't break existing functionality

```bash
# 1. Re-run all baseline tests
python test_storage_auth_error.py
python test_staging_storage_error.py
python test_upload_with_auth.py

# 2. Test specific fix functionality
# (Create additional test scripts as needed)

# 3. Test edge cases and error conditions
```

**Success Criteria**:
- ✅ All local tests pass
- ✅ Staging simulation works (if applicable)
- ✅ No new errors introduced
- ✅ Existing functionality preserved

---

## Test Script Development

### Creating New Test Scripts
When developing fixes, create test scripts following this pattern:

```python
#!/usr/bin/env python3
"""
Test script for FM-024 fix validation
"""
import asyncio
import httpx
from supabase import create_client

async def test_fix():
    """Test the implemented fix"""
    print("🧪 Testing FM-024 Fix")
    
    # Test configuration
    supabase_url = "http://127.0.0.1:54321"  # Local
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
    
    try:
        # Test the fix
        supabase = create_client(supabase_url, supabase_key)
        response = supabase.storage.from_("raw").create_signed_upload_url("test-file.pdf")
        
        if response.get('signedURL'):
            print("✅ Fix successful!")
            return True
        else:
            print("❌ Fix failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_fix())
```

### Test Script Naming Convention
- `test_fm024_*.py` - FM-024 specific tests
- `test_fix_*.py` - Fix validation tests
- `test_regression_*.py` - Regression tests

---

## Deployment Process

### 1. Pre-Deployment Checklist
- [ ] All local tests pass
- [ ] Code changes reviewed
- [ ] No linting errors
- [ ] Documentation updated
- [ ] Test scripts created/updated

### 2. Git Workflow
```bash
# 1. Create feature branch
git checkout -b fix/fm024-storage-authentication

# 2. Make changes and test locally
# ... implement fix ...
# ... run tests ...

# 3. Commit changes
git add .
git commit -m "fix: resolve Supabase storage authentication issue

- Fix service role key permissions
- Update storage configuration
- Add storage authentication tests

Fixes FM-024"

# 4. Push to remote
git push origin fix/fm024-storage-authentication

# 5. Create pull request to staging branch
```

### 3. Staging Deployment
```bash
# 1. Merge PR to staging branch
# 2. Deploy to staging environment
# 3. Run staging validation tests
# 4. Monitor logs for errors
```

---

## Monitoring and Validation

### 1. Local Monitoring
```bash
# Monitor API logs
tail -f logs/api.log

# Monitor Supabase logs
supabase logs

# Check system resources
htop
```

### 2. Staging Validation
```bash
# Test staging endpoint
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"filename":"test.pdf","bytes_len":1024,"mime":"application/pdf","sha256":"'$(echo -n "test" | sha256sum | cut -d' ' -f1)'","ocr":false}' \
     "https://insurance-navigator-staging-api.onrender.com/api/upload-pipeline/upload"
```

### 3. Success Indicators
- ✅ No 500 errors in logs
- ✅ Signed URLs generated successfully
- ✅ File uploads complete
- ✅ Database operations continue working

---

## Rollback Plan

### If Fix Fails in Staging
1. **Immediate**: Revert to previous working version
2. **Investigation**: Analyze why fix didn't work
3. **Local Testing**: Re-test fix in local environment
4. **Re-deployment**: Apply corrected fix

### Rollback Commands
```bash
# Revert to previous commit
git revert HEAD

# Force push to staging (if necessary)
git push origin staging --force

# Restart staging services
# (Use Render dashboard or CLI)
```

---

## Documentation Requirements

### 1. Update Investigation Notes
- Document what was found
- Record the implemented solution
- Note any side effects or considerations

### 2. Update Test Scripts
- Add new test scripts to `/docs/incidents/fm_024/test_scripts.md`
- Document expected behavior
- Include troubleshooting tips

### 3. Update Configuration Docs
- Update environment configuration documentation
- Record any new environment variables
- Document configuration changes

---

## Success Criteria

### Local Testing Complete When:
- [ ] All test scripts pass locally
- [ ] No regression in existing functionality
- [ ] New functionality works as expected
- [ ] Error handling works correctly
- [ ] Performance is acceptable

### Staging Deployment Complete When:
- [ ] Staging tests pass
- [ ] No errors in staging logs
- [ ] Upload functionality works end-to-end
- [ ] Monitoring shows healthy status
- [ ] Documentation is updated

---

**Remember**: Local testing is MANDATORY. No code should be committed or deployed to staging without thorough local validation.
