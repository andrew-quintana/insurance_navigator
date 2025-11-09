# FM-024 Environment Configuration Analysis

## Environment Comparison

### Staging Environment (Failing)
**File**: `.env.staging`
```bash
SUPABASE_URL=https://your-staging-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTY4MDQ4MywiZXhwIjoyMDY3MjU2NDgzfQ.placeholder
```

### Development Environment (Working)
**File**: `.env.development`
```bash
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
```

## Key Differences

| Aspect | Staging | Development |
|--------|---------|-------------|
| **URL Type** | HTTPS (Cloud) | HTTP (Local) |
| **Domain** | `your-staging-project.supabase.co` | `127.0.0.1:54321` |
| **Key Type** | Production JWT | Demo JWT |
| **Key Expiry** | 2067-12-31 | 1983-12-31 (Demo) |
| **Project Ref** | `your-staging-project` | `supabase-demo` |

## JWT Token Analysis

### Staging Service Role Key
```json
{
  "iss": "supabase",
  "ref": "your-staging-project",
  "role": "service_role",
  "iat": 1751680483,
  "exp": 2067256483
}
```

### Development Service Role Key
```json
{
  "iss": "supabase-demo",
  "role": "service_role",
  "exp": 1983812996
}
```

## Storage Configuration Investigation

### 1. Check Storage Service Status
```bash
# Test staging storage
curl -H "apikey: $STAGING_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $STAGING_SERVICE_ROLE_KEY" \
     "https://your-staging-project.supabase.co/storage/v1/bucket"

# Test local storage
curl -H "apikey: $DEV_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $DEV_SERVICE_ROLE_KEY" \
     "http://127.0.0.1:54321/storage/v1/bucket"
```

### 2. Check Raw Bucket Existence
```bash
# Check staging raw bucket
curl -H "apikey: $STAGING_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $STAGING_SERVICE_ROLE_KEY" \
     "https://your-staging-project.supabase.co/storage/v1/bucket/raw"

# Check local raw bucket
curl -H "apikey: $DEV_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $DEV_SERVICE_ROLE_KEY" \
     "http://127.0.0.1:54321/storage/v1/bucket/raw"
```

### 3. Test Signed URL Generation
```bash
# Test staging signed URL
curl -X POST \
     -H "apikey: $STAGING_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $STAGING_SERVICE_ROLE_KEY" \
     -H "Content-Type: application/json" \
     -d '{"expiresIn": 3600}' \
     "https://your-staging-project.supabase.co/storage/v1/object/upload/sign/raw/test-file.pdf"

# Test local signed URL
curl -X POST \
     -H "apikey: $DEV_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $DEV_SERVICE_ROLE_KEY" \
     -H "Content-Type: application/json" \
     -d '{"expiresIn": 3600}' \
     "http://127.0.0.1:54321/storage/v1/object/upload/sign/raw/test-file.pdf"
```

## Potential Issues

### 1. Service Role Key Permissions
- **Issue**: Key may not have storage permissions
- **Check**: Verify key has `storage.objects.create` and `storage.objects.upload` permissions
- **Solution**: Update key permissions in Supabase dashboard

### 2. Storage Service Not Enabled
- **Issue**: Storage service may not be enabled for the project
- **Check**: Verify storage is enabled in project settings
- **Solution**: Enable storage service in Supabase dashboard

### 3. Bucket Configuration
- **Issue**: "raw" bucket may not exist or be misconfigured
- **Check**: Verify bucket exists and has proper policies
- **Solution**: Create bucket or fix policies

### 4. RLS Policies
- **Issue**: Row Level Security may be blocking service role access
- **Check**: Verify RLS policies allow service role access
- **Solution**: Update RLS policies for storage

### 5. Project Configuration Mismatch
- **Issue**: Staging project may have different configuration than expected
- **Check**: Compare project settings with development
- **Solution**: Align configurations or update code

## Investigation Commands

### Check Project Status
```bash
# Get project info
curl -H "apikey: $STAGING_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $STAGING_SERVICE_ROLE_KEY" \
     "https://your-staging-project.supabase.co/rest/v1/"
```

### Check Storage Buckets
```bash
# List all buckets
curl -H "apikey: $STAGING_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $STAGING_SERVICE_ROLE_KEY" \
     "https://your-staging-project.supabase.co/storage/v1/bucket"
```

### Check Storage Policies
```bash
# Check storage policies (if accessible)
curl -H "apikey: $STAGING_SERVICE_ROLE_KEY" \
     -H "Authorization: Bearer $STAGING_SERVICE_ROLE_KEY" \
     "https://your-staging-project.supabase.co/rest/v1/storage_policies"
```

## Next Steps

1. **Run investigation commands** to gather current status
2. **Compare results** between staging and development
3. **Identify specific failure point** in storage configuration
4. **Implement fix** based on findings
5. **Test locally** before deploying to staging
6. **Validate fix** in staging environment
