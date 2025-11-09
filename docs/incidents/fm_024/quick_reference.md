# FM-024 Quick Reference Guide

## Issue Summary
**Problem**: Supabase storage authentication failing with "signature verification failed" error  
**Impact**: File uploads cannot complete, though database operations work  
**Status**: Investigation required  

## Key Error
```
storage3.exceptions.StorageApiError: {'statusCode': 403, 'error': Unauthorized, 'message': signature verification failed}
```

## Quick Commands

### Start Local Environment
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
source .venv/bin/activate
supabase start
python main.py &
```

### Run Tests
```bash
# Test local storage (should work)
python test_storage_auth_error.py

# Test staging storage (should fail)
python test_staging_storage_error.py

# Test full upload flow
python test_upload_with_auth.py
```

### Check Status
```bash
# API health
curl http://localhost:8000/health

# Supabase status
supabase status
```

## Configuration Files
- **Staging**: `.env.staging`
- **Development**: `.env.development`
- **Test Scripts**: `test_*.py` (in project root)

## Investigation Areas
1. **Service Role Key Permissions** - Does key have storage access?
2. **Storage Service Status** - Is storage enabled for project?
3. **Bucket Configuration** - Does "raw" bucket exist and have proper policies?
4. **Environment Differences** - Staging vs Development config differences

## Next Steps
1. Run investigation commands
2. Identify root cause
3. Implement fix locally
4. Test thoroughly
5. Deploy to staging
6. Validate fix

## Files to Check
- `api/upload_pipeline/endpoints/upload.py:519` - `_generate_signed_url` function
- `.env.staging` - Staging environment variables
- Supabase project dashboard - Storage configuration
