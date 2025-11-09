# Migration Workflow Documentation

## Current Status
- ✅ Local migrations synced with production
- ✅ Future-proof workflow established
- ✅ Backup system in place

## How to Add New Migrations

### Option 1: Use the Workflow Script (Recommended)
```bash
./scripts/migration_workflow.sh
```

### Option 2: Manual Process
1. **Create migration file:**
   ```bash
   supabase migration new your_migration_name
   ```

2. **Edit the migration file:**
   ```bash
   # Edit supabase/migrations/TIMESTAMP_your_migration_name.sql
   ```

3. **Test locally:**
   ```bash
   supabase db reset
   ```

4. **Commit and push:**
   ```bash
   git add supabase/migrations/
   git commit -m "Add migration: your_migration_name"
   git push
   ```

5. **Deploy to production:**
   ```bash
   supabase db push
   ```

## Best Practices

### ✅ DO:
- Always test migrations locally first
- Use descriptive migration names
- Include rollback instructions in comments
- Commit migrations immediately after testing
- Use transactions for complex migrations

### ❌ DON'T:
- Edit existing migration files
- Skip local testing
- Deploy untested migrations
- Mix schema and data changes in one migration

## Troubleshooting

### Migration Drift Issues
If you get "migration history does not match" errors:

1. **Check what's different:**
   ```bash
   supabase db pull --dry-run
   ```

2. **Repair specific migrations:**
   ```bash
   supabase migration repair --status reverted MIGRATION_ID
   ```

3. **Full sync (nuclear option):**
   ```bash
   supabase db pull
   ```

### Storage Bucket Issues
If you get column errors with storage.buckets:

1. **Check current schema:**
   ```sql
   \d storage.buckets
   ```

2. **Use conditional logic:**
   ```sql
   DO $$
   BEGIN
       IF EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_schema = 'storage' 
                  AND table_name = 'buckets' 
                  AND column_name = 'public') THEN
           -- Use old schema
       ELSE
           -- Use new schema
       END IF;
   END $$;
   ```

## Emergency Procedures

### Rollback Migration
```bash
supabase migration repair --status reverted MIGRATION_ID
```

### Reset Everything
```bash
supabase db reset
```

### Backup Before Changes
```bash
supabase db dump > backup_$(date +%Y%m%d_%H%M%S).sql
```
