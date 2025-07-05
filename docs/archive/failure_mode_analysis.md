# Database Schema Migration Failure Mode Analysis

## Executive Summary

The recent upload failures represent a systematic pattern of **Database Schema-Application Code Synchronization Failures** that can be proactively detected and prevented.

## Failure Mode Categories

### 1. **Schema-Code Synchronization Failures** ⚠️ **HIGH RISK**

**Pattern**: Database schema changes without corresponding application code updates

**Recent Examples**:
- Missing `file_path` column (NOT NULL constraint violation)
- Missing `storage_backend`, `bucket_name` columns 
- Dropped `processing_jobs` table while triggers still referenced it

**Root Causes**:
- Migration scripts drop/modify tables without updating application code
- Database triggers reference tables that no longer exist
- Column constraints (NOT NULL) added without default values
- Branch divergence between schema migrations and code changes

### 2. **Database Trigger Dependency Failures** ⚠️ **MEDIUM RISK**

**Pattern**: Database triggers/functions reference objects that don't exist

**Recent Example**:
- `trigger_document_processing()` calls functions that INSERT into `processing_jobs`
- Table was dropped in V2.0.0 but triggers remained active
- Silent failures until runtime

### 3. **Migration Ordering & Dependency Issues** ⚠️ **MEDIUM RISK**

**Pattern**: Migrations applied out of order or with missing dependencies

**Potential Issues**:
- Foreign key constraints fail if referenced tables don't exist yet
- Functions reference columns before they're created
- Index creation on non-existent columns

### 4. **Environment Configuration Drift** ⚠️ **LOW-MEDIUM RISK**

**Pattern**: Production vs Development environment differences

**Potential Issues**:
- Different database schemas between environments
- Missing environment variables in production
- Different database versions or extensions

## Proactive Investigation Framework

### Phase 1: Database Schema Validation 🔍

```sql
-- 1. Check for missing tables referenced by functions
SELECT DISTINCT 
    r.routine_name,
    r.routine_definition
FROM information_schema.routines r
WHERE r.routine_definition ~ 'INSERT INTO|UPDATE|DELETE FROM|SELECT.*FROM'
  AND r.routine_type = 'FUNCTION'
  AND NOT EXISTS (
    SELECT 1 FROM information_schema.tables t 
    WHERE r.routine_definition ILIKE '%' || t.table_name || '%'
  );

-- 2. Check for triggers on non-existent tables
SELECT 
    t.trigger_name,
    t.event_object_table,
    t.action_statement
FROM information_schema.triggers t
WHERE NOT EXISTS (
    SELECT 1 FROM information_schema.tables tb 
    WHERE tb.table_name = t.event_object_table
);

-- 3. Check for foreign key constraints to missing tables
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu 
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND NOT EXISTS (
    SELECT 1 FROM information_schema.tables t 
    WHERE t.table_name = ccu.table_name
  );
```

### Phase 2: Application Code Validation 🔍

```python
# Scan for database table/column references in code
import re
import os
from pathlib import Path

def scan_sql_references():
    """Scan application code for SQL table/column references"""
    sql_patterns = [
        r'INSERT INTO\s+(\w+)',
        r'UPDATE\s+(\w+)\s+SET',
        r'DELETE FROM\s+(\w+)',
        r'FROM\s+(\w+)',
        r'JOIN\s+(\w+)',
    ]
    
    table_refs = set()
    
    for py_file in Path('.').rglob('*.py'):
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for pattern in sql_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                table_refs.update(matches)
    
    return table_refs

def validate_column_references():
    """Check for column references in INSERT/UPDATE statements"""
    column_issues = []
    
    for py_file in Path('.').rglob('*.py'):
        with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Find INSERT statements
            insert_matches = re.findall(
                r'INSERT INTO\s+(\w+)\s*\([^)]+\)\s*VALUES',
                content, re.IGNORECASE | re.DOTALL
            )
            
            # Check if they reference expected columns
            for match in insert_matches:
                if 'file_path' in content and match == 'documents':
                    # Validate that file_path is included
                    pass
    
    return column_issues
```

### Phase 3: Migration Dependency Graph 🔍

```python
def analyze_migration_dependencies():
    """Create dependency graph of migrations"""
    migrations = []
    
    for sql_file in Path('db/migrations').glob('*.sql'):
        with open(sql_file, 'r') as f:
            content = f.read()
            
            # Extract table creations, drops, references
            creates = re.findall(r'CREATE TABLE\s+(\w+)', content, re.IGNORECASE)
            drops = re.findall(r'DROP TABLE\s+(?:IF EXISTS\s+)?(\w+)', content, re.IGNORECASE)
            references = re.findall(r'REFERENCES\s+(\w+)', content, re.IGNORECASE)
            
            migrations.append({
                'file': sql_file.name,
                'creates': creates,
                'drops': drops,
                'references': references
            })
    
    # Validate dependencies
    for migration in migrations:
        for ref_table in migration['references']:
            # Check if referenced table is created before this migration
            # or if it's dropped after this migration
            pass
    
    return migrations
```

### Phase 4: Automated Health Checks 🤖

```python
async def database_health_check():
    """Comprehensive database health validation"""
    issues = []
    
    # 1. Schema-Code Synchronization
    app_tables = scan_sql_references()
    db_tables = await get_database_tables()
    
    missing_tables = app_tables - db_tables
    if missing_tables:
        issues.append(f"Tables referenced in code but missing in DB: {missing_tables}")
    
    # 2. Trigger Validation
    broken_triggers = await check_broken_triggers()
    if broken_triggers:
        issues.append(f"Broken triggers found: {broken_triggers}")
    
    # 3. Foreign Key Validation
    broken_fks = await check_foreign_keys()
    if broken_fks:
        issues.append(f"Broken foreign keys: {broken_fks}")
    
    # 4. Function Validation
    broken_functions = await check_broken_functions()
    if broken_functions:
        issues.append(f"Broken functions: {broken_functions}")
    
    return issues
```

## Proactive Prevention Strategies

### 1. **Pre-Migration Validation** ✅

```bash
# Run before applying any migration
python scripts/validate_migration.py db/migrations/V2.0.X__new_migration.sql
```

**Checks**:
- Referenced tables exist
- Column constraints have defaults or are nullable
- Foreign keys point to existing tables
- Functions don't reference dropped tables

### 2. **Post-Migration Validation** ✅

```bash
# Run after applying migration
python scripts/post_migration_check.py
```

**Checks**:
- All application-referenced tables exist
- All triggers function correctly
- All foreign keys are valid
- Sample operations work (INSERT/UPDATE/DELETE)

### 3. **Continuous Integration Checks** ✅

```yaml
# .github/workflows/schema_validation.yml
- name: Database Schema Validation
  run: |
    python scripts/validate_schema_sync.py
    python scripts/check_migration_dependencies.py
    python scripts/simulate_critical_operations.py
```

### 4. **Production Monitoring** 📊

```python
# Add to application startup
async def startup_schema_validation():
    """Run critical schema checks on startup"""
    critical_tables = ['users', 'documents', 'processing_jobs', 'conversations']
    
    for table in critical_tables:
        if not await table_exists(table):
            logger.critical(f"CRITICAL: Required table '{table}' missing!")
            raise RuntimeError(f"Database schema incomplete: {table} missing")
```

## Implementation Priority

### 🔥 **Immediate (This Week)**
1. Create database validation script (`scripts/validate_database_schema.py`)
2. Add startup schema validation to main.py
3. Create migration validation script

### 📅 **Short Term (Next Sprint)**
1. Implement automated health checks in CI/CD
2. Create schema-code synchronization tests
3. Add migration dependency validation

### 🎯 **Long Term (Next Month)**
1. Automated schema drift detection
2. Cross-environment schema comparison
3. Migration rollback validation

## Recommended Investigation Scripts

Would you like me to create any of these specific validation scripts to proactively catch these issues?

1. **`scripts/validate_database_schema.py`** - Comprehensive schema validation
2. **`scripts/check_migration_dependencies.py`** - Migration dependency analysis  
3. **`scripts/simulate_critical_operations.py`** - Test critical operations
4. **`scripts/schema_drift_detector.py`** - Compare schemas across environments

This framework will help catch these systematic failures before they reach production. 