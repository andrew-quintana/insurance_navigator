# Production Environment Setup Prompt

## Overview
This prompt outlines the steps to set up the production environment for the Insurance Navigator system, focusing on environment configuration and database implementation.

## Prerequisites
- Supabase CLI installed
- Access to production Supabase project
- Production environment credentials

## 1. Environment Configuration

### Create Production Environment File
Create `.env.production` with the following structure:

```env
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://[YOUR_PROJECT_ID].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[YOUR_ANON_KEY]
SUPABASE_SERVICE_ROLE_KEY=[YOUR_SERVICE_ROLE_KEY]
SUPABASE_DB_URL=postgresql://postgres:[DB_PASSWORD]@db.[YOUR_PROJECT_ID].supabase.co:5432/postgres

# FastAPI Backend Configuration
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_WORKERS=4
FASTAPI_LOG_LEVEL=info

# Security Configuration
JWT_SECRET=[GENERATE_SECURE_SECRET]
ENCRYPTION_KEY=[GENERATE_SECURE_KEY]

# Storage Configuration
STORAGE_BUCKET_NAME=documents
MAX_FILE_SIZE=10485760  # 10MB in bytes

# Document Processing Configuration
LLAMAPARSE_API_KEY=[YOUR_LLAMAPARSE_KEY]
OPENAI_API_KEY=[YOUR_OPENAI_KEY]

# Monitoring and Logging
LOG_LEVEL=info
SENTRY_DSN=[YOUR_SENTRY_DSN]
```

### Link Production Project
```bash
# Link to production Supabase project
supabase link --project-ref [YOUR_PROJECT_REF]

# Switch to production branch
git checkout production
```

## 2. Database Implementation

### Apply Schema Migration
```bash
# Apply the migration to production
supabase db push

# Verify schema application
supabase db diff --linked
```

### Schema Verification Queries
```sql
-- Verify users table
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users';

-- Verify documents table
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'documents';

-- Verify RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
AND tablename IN ('users', 'documents');

-- Verify storage bucket
SELECT id, name, public, file_size_limit, allowed_mime_types
FROM storage.buckets
WHERE id = 'documents';
```

### Security Verification
```sql
-- Verify RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('users', 'documents');

-- Test anonymous access
SET request.jwt.claim.role = 'anon';
-- Should succeed (signup allowed)
INSERT INTO users (email, name) VALUES ('test@example.com', 'Test User');
-- Should fail (no document access)
SELECT * FROM documents;

-- Test authenticated access
SET request.jwt.claim.role = 'authenticated';
SET request.jwt.claim.sub = '[TEST_USER_ID]';
-- Should only see own records
SELECT * FROM users WHERE id = '[TEST_USER_ID]';
SELECT * FROM documents WHERE user_id = '[TEST_USER_ID]';
```

## 3. Post-Implementation Verification

### Backend Health Check
```bash
# Test FastAPI endpoints
curl -i https://[YOUR_API_DOMAIN]/health
curl -i https://[YOUR_API_DOMAIN]/api/v1/status
```

### Storage Verification
```typescript
// Test storage access (from frontend)
const { data, error } = await supabase.storage
  .from('documents')
  .upload('test.pdf', testFile);

console.log('Upload response:', { data, error });
```

## 4. Rollback Plan

### Database Rollback
```sql
-- Create backup before changes
CREATE TABLE users_backup AS SELECT * FROM users;
CREATE TABLE documents_backup AS SELECT * FROM documents;

-- Rollback command if needed
DROP TABLE documents;
DROP TABLE users;
ALTER TABLE users_backup RENAME TO users;
ALTER TABLE documents_backup RENAME TO documents;
```

### Environment Rollback
```bash
# Keep backup of current env
cp .env.production .env.production.backup

# Restore from backup if needed
mv .env.production.backup .env.production
```

## Success Criteria

### Database
- [ ] Schema matches development environment
- [ ] All tables have RLS enabled
- [ ] All policies are correctly applied
- [ ] Storage bucket is configured correctly
- [ ] Indexes are created and optimal

### Security
- [ ] No unauthorized access possible
- [ ] Service role access works correctly
- [ ] User isolation is enforced
- [ ] All sensitive data is protected

### Performance
- [ ] Query execution plans are optimal
- [ ] Indexes are being used correctly
- [ ] No full table scans on common queries

## Monitoring Setup

### Database Monitoring
```sql
-- Create monitoring view
CREATE VIEW vw_table_stats AS
SELECT
    schemaname,
    relname,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname = 'public';

-- Create performance logging
CREATE TABLE IF NOT EXISTS performance_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    query_id TEXT,
    execution_time INTERVAL,
    rows_affected INTEGER,
    query_plan JSONB
);
```

### Alert Setup
```sql
-- Create alert function for long-running queries
CREATE OR REPLACE FUNCTION alert_long_running_queries()
RETURNS trigger AS $$
BEGIN
    IF NEW.execution_time > interval '30 seconds' THEN
        -- Insert alert logic here
        INSERT INTO alert_logs (alert_type, message)
        VALUES ('long_query', format('Query %s took %s', NEW.query_id, NEW.execution_time));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER tr_alert_long_queries
AFTER INSERT ON performance_logs
FOR EACH ROW
EXECUTE FUNCTION alert_long_running_queries();
```

## Notes
1. Always test changes in staging before applying to production
2. Keep detailed logs of all production changes
3. Monitor performance metrics after changes
4. Have support team ready during migration
5. Schedule maintenance window for implementation
6. Prepare customer communication if needed

## Future Considerations
1. Implement HIPAA compliance features
2. Set up automated backups
3. Configure disaster recovery
4. Implement performance monitoring
5. Set up automated testing in production environment 