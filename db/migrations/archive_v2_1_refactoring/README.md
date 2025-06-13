# V2.1.x Migration Archive

This folder contains the historical migration files from the database refactoring effort that resulted in the consolidated V0.2.0 schema.

## Archived Files

### Migration Sequence (Historical)

1. **V2.0.0__mvp_schema_refactor.sql** - Initial refactoring attempt
2. **V2.0.1__rollback_if_needed.sql** - Rollback procedures 
3. **V2.0.2__migrate_data.sql** - Data migration logic
4. **V2.0.3__cleanup_old_tables.sql** - Table cleanup
5. **V2.0.4__final_polish.sql** - Final optimizations

### Supabase-Specific Migrations

1. **V2.1.0__supabase_migration.sql** - Initial Supabase adaptation
2. **V2.1.1__supabase_migration_fixed.sql** - Schema fixes for Supabase
3. **V2.1.2__supabase_migration_final.sql** - Complete data migration
4. **V2.1.3__supabase_cleanup.sql** - Table cleanup for Supabase
5. **V2.1.4__restore_cron_triggers.sql** - Processing infrastructure restoration

## Why These Were Archived

The V2.1.x series was a successful refactoring effort that:

- Reduced database complexity from 27+ tables to 13 tables
- Implemented JSONB policy storage for hybrid search
- Created processing pipeline with cron jobs and triggers
- Achieved 100% data preservation during migration
- Improved performance significantly

However, for future deployments, the **V0.2.0 consolidated migration** is preferred because it:

- Represents the final optimized schema in a single file
- Includes all lessons learned from the V2.1.x series
- Provides cleaner installation for new environments
- Has comprehensive documentation and validation

## Reference Value

These archived files are valuable for:

- Understanding the migration evolution process
- Debugging issues by comparing with working V2.1.x implementations
- Learning about complex database refactoring approaches
- Historical reference for the refactoring methodology

## Current Recommendation

**For new installations**: Use `V0.2.0__consolidated_mvp_schema.sql`

**For existing V2.1.x systems**: Continue using current schema or carefully migrate to V0.2.0 with proper backups

## Related Documentation

- `docs/database/refactoring/REFACTORING_IMPLEMENTATION_SUMMARY.md` - Complete refactoring process
- `docs/database/refactoring/DATABASE_REFACTORING_COMPLETE.md` - Final implementation details  
- `docs/database/refactoring/SUPABASE_MIGRATION_COMPLETE.md` - Supabase-specific implementation
- `docs/database/refactoring/V0.2.0_MIGRATION_GUIDE.md` - New consolidated migration guide 