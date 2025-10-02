# Migration Archive

This directory contains migration files that have been archived for various reasons:

## Archived Files

### Backup Files (.backup)
- `20250925200000_phase1_remove_public_users_table.sql.backup` - Backup of phase1 migration
- `20251001000000_add_storage_buckets_rls_policies.sql.backup` - Backup of storage buckets RLS policies
- `20251001000001_add_storage_buckets_rls_policies_simple.sql.backup` - Backup of simplified storage policies
- `20251001133101_add_staging_storage_rls_policies.sql.backup` - Backup of staging storage RLS policies
- `20251001133102_storage_policies_only.sql.backup` - Backup of storage policies only migration

### Problematic Migrations
- `20251001133103_bucket_policies_only.sql` - Failed due to dependency on previous migration
- `20251001133104_storage_policies_only_fixed.sql` - Alternative implementation that wasn't needed

## Archive Reasons

1. **Backup Files**: These are `.backup` files created during development/testing
2. **Failed Migrations**: These migrations failed during deployment due to:
   - Policy already exists errors
   - Dependency issues
   - Alternative implementations that weren't needed

## Notes

- All essential functionality from these migrations has been incorporated into the successfully applied migrations
- The archived files are preserved for reference and potential future use
- No data loss occurred - all critical database changes were applied through other migration files
