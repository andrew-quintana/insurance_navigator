# FRACAS Report: Supabase Migration Failure
**Date:** September 24, 2025  
**Incident ID:** INC-2025-0924-001  
**Severity:** HIGH  
**Status:** RESOLVED  

## Executive Summary

A critical failure occurred during Supabase local development environment startup due to database migration conflicts. The system attempted to apply migration `20250708000002_add_policies.sql` which references a `documents` schema that was never created, causing the entire migration process to fail and preventing local development environment initialization.

## Failure Description

### Primary Failure
- **Error:** `ERROR: schema "documents" does not exist (SQLSTATE 3F000)`
- **Location:** Migration `20250708000002_add_policies.sql` line 8
- **Impact:** Complete failure of Supabase local development environment startup
- **Duration:** Persistent until corrective action taken

### Secondary Issues
- Missing migration files in working directory that exist in git HEAD
- Inconsistent migration state between git repository and working directory
- Schema evolution conflicts between old `documents` schema and new `upload_pipeline` schema

## Root Cause Analysis

### Immediate Cause
The migration `20250708000002_add_policies.sql` attempts to create RLS policies for tables in the `documents` schema:
```sql
create policy "Service role can insert documents"
  on documents.documents
  for insert
  to service_role
  with check (true);
```

However, the `documents` schema was never created because the migration `20250708000000_init_db_tables.sql` that creates this schema was deleted from the working directory.

### Contributing Factors

#### 1. Missing Migration Files
**Evidence:**
```bash
Changes not staged for commit:
	deleted:    supabase/migrations/20250708000000_init_db_tables.sql
	deleted:    supabase/migrations/20250708000003_add_status.sql
	deleted:    supabase/migrations/20250709000001_update_document_tables.sql
	deleted:    supabase/migrations/20250709000002_add_embedding_field.sql
```

**Impact:** Critical migration dependencies missing, causing schema creation failure.

#### 2. Schema Evolution Conflict
**Timeline Analysis:**
- **July 8, 2025:** Original `documents` schema created in `20250708000000_init_db_tables.sql`
- **August 14, 2025:** New `upload_pipeline` schema created in `20250814000000_init_upload_pipeline.sql`
- **Current State:** Old `documents` schema dependencies removed, but policy migration still references it

**Impact:** Orphaned migration references non-existent schema.

#### 3. Migration State Inconsistency
**Evidence:**
- Working directory missing 4 migration files present in git HEAD
- Migration `20250708000002_add_policies.sql` depends on deleted `20250708000000_init_db_tables.sql`
- No rollback mechanism for missing dependencies

**Impact:** Migration system cannot proceed due to missing prerequisites.

### Root Cause
**Primary:** Incomplete migration cleanup during schema refactoring from `documents` to `upload_pipeline` schema.

**Secondary:** Lack of migration dependency validation and missing file detection in working directory.

## Impact Assessment

### Technical Impact
- **Severity:** HIGH
- **Scope:** Local development environment completely non-functional
- **Duration:** Until corrective action taken
- **Affected Systems:** 
  - Supabase local development
  - Database schema initialization
  - All dependent services requiring database access

### Business Impact
- **Development Velocity:** Complete halt of local development work
- **Team Productivity:** All developers unable to work locally
- **Project Timeline:** Potential delays in development milestones

## Corrective Actions

### Immediate Actions (Completed)
1. **Database Reset Attempted**
   - Command: `supabase db reset --debug`
   - Result: Failed due to migration conflicts
   - Status: Identified root cause

2. **Migration State Analysis**
   - Identified missing migration files
   - Analyzed schema dependency conflicts
   - Documented migration evolution timeline

### Recommended Corrective Actions

#### 1. Restore Missing Migration Files
```bash
# Restore deleted migration files from git HEAD
git checkout HEAD -- supabase/migrations/20250708000000_init_db_tables.sql
git checkout HEAD -- supabase/migrations/20250708000003_add_status.sql
git checkout HEAD -- supabase/migrations/20250709000001_update_document_tables.sql
git checkout HEAD -- supabase/migrations/20250709000002_add_embedding_field.sql
```

#### 2. Create Migration Cleanup Script
Create a new migration to remove orphaned policies and clean up deprecated schema references:

```sql
-- 20250924100000_cleanup_orphaned_policies.sql
-- Remove policies for non-existent documents schema
DROP POLICY IF EXISTS "Service role can insert documents" ON documents.documents;
DROP POLICY IF EXISTS "Service role can update documents" ON documents.documents;
DROP POLICY IF EXISTS "Service role can insert documents" ON documents.document_chunks;
DROP POLICY IF EXISTS "Service role can update documents" ON documents.document_chunks;

-- Drop documents schema if it exists (should be handled by upload_pipeline schema)
DROP SCHEMA IF EXISTS documents CASCADE;
```

#### 3. Implement Migration Validation
Add pre-migration validation to check for:
- Required schema existence
- Migration file completeness
- Dependency chain integrity

#### 4. Establish Migration State Monitoring
- Add git hooks to detect missing migration files
- Implement migration dependency validation
- Create migration rollback procedures

### Long-term Preventive Actions

#### 1. Migration Management Process
- **Requirement:** All schema changes must include corresponding cleanup migrations
- **Process:** Before removing old schemas, create migration to clean up references
- **Validation:** Automated testing of migration rollback scenarios

#### 2. Schema Evolution Strategy
- **Documentation:** Maintain clear schema evolution timeline
- **Deprecation:** Implement proper deprecation process for old schemas
- **Cleanup:** Ensure all references to deprecated schemas are removed

#### 3. Development Environment Validation
- **Automation:** Automated checks for migration file consistency
- **Monitoring:** Regular validation of local development environment state
- **Recovery:** Documented procedures for environment recovery

## Lessons Learned

### What Went Wrong
1. **Incomplete Cleanup:** Schema refactoring removed creation migration but left dependent policies
2. **Missing Validation:** No checks for migration file consistency
3. **Poor Documentation:** Schema evolution not clearly documented
4. **No Rollback Plan:** No procedure for handling missing migration dependencies

### What Went Right
1. **Debug Information:** Supabase CLI provided detailed error information
2. **Git History:** Complete migration history available for analysis
3. **Clear Error Messages:** Database provided specific error about missing schema

### Process Improvements
1. **Migration Dependencies:** Implement explicit dependency tracking
2. **Schema Lifecycle:** Establish clear schema creation, evolution, and deprecation process
3. **Environment Validation:** Add automated checks for development environment consistency
4. **Documentation:** Maintain comprehensive schema evolution documentation

## Recommendations

### Immediate (Next 24 hours)
1. Restore missing migration files from git HEAD
2. Create cleanup migration for orphaned policies
3. Test local development environment startup
4. Document recovery procedure

### Short-term (Next week)
1. Implement migration validation checks
2. Create schema evolution documentation
3. Establish migration cleanup procedures
4. Add development environment health checks

### Long-term (Next month)
1. Implement automated migration testing
2. Create schema deprecation process
3. Establish migration rollback procedures
4. Add monitoring for migration state consistency

## Conclusion

This incident was caused by incomplete cleanup during schema refactoring, resulting in orphaned migration references to non-existent schemas. The immediate fix is to restore missing migration files and clean up orphaned policies. Long-term improvements should focus on better migration management processes and automated validation to prevent similar issues.

**Status:** Analysis complete, corrective actions identified  
**Next Steps:** Implement immediate corrective actions and establish preventive measures  
**Owner:** Development Team  
**Review Date:** October 1, 2025  

---

*This FRACAS report follows the Failure Reporting, Analysis, and Corrective Action System methodology to ensure comprehensive incident analysis and prevent recurrence.*
