# Migration Fixes Needed: user_document_vectors → document_vectors

## Critical Issue Identified
The database currently has `user_document_vectors` table, but several files are expecting `document_vectors`. Based on migration V2.0.0, the table should be renamed to `document_vectors`.

## Files Requiring Updates Before Migration

### 1. **CRITICAL - Regulatory Processing Scripts**
These files are actively inserting data and WILL FAIL:

**scripts/bulk_regulatory_processor.py**
- Line 4: Comment refers to "user_document_vectors table"
- Line 258: `INSERT INTO user_document_vectors (...)` 
- **Status**: Currently using old table name ❌

**db/services/encryption_aware_embedding_service.py**
- Line 200: `INSERT INTO user_document_vectors`
- Line 211: `INSERT INTO user_document_vectors`
- Line 362: Comment about "user_document_vectors table schema"
- **Status**: Using old table name ❌

**db/services/embedding_service.py**
- Line 160: `INSERT INTO user_document_vectors`
- Line 281: `FROM user_document_vectors`
- Line 368: `SELECT COUNT(*) FROM user_document_vectors`
- Line 379: `SELECT vector_dims(content_embedding) FROM user_document_vectors`
- **Status**: Using old table name ❌

**main.py** (Core application)
- Line 1447: `INSERT INTO user_document_vectors`
- Line 1561: `FROM user_document_vectors`
- **Status**: Using old table name ❌

### 2. **Test Files - Need Updates**
**test_complete_pipeline.py**
- Line 306: `FROM user_document_vectors`

**scripts/test_pre_migration.py**
- Multiple references to 'user_document_vectors'

**test_regulatory_search.py**
- Line 34: `SELECT COUNT(*) FROM document_vectors` ✅ (This one is correct)

### 3. **Migration Files - Mixed References**
**db/migrations/015_add_regulatory_vectors_support.sql** ✅
- Correctly uses `document_vectors`

**db/migrations/015_add_regulatory_vectors_support_insurance_navigator_fixed.sql** ❌
- Uses `user_document_vectors` (incorrect for target schema)

**db/migrations/016_fix_user_id_nullable.sql** ❌
- Uses `user_document_vectors`

### 4. **Edge Functions**
**db/supabase/functions/vector-processor/index.ts**
- Line 42: `vectorTable: 'user_document_vectors'` ❌
- Line 29: `vectorTable: 'document_vectors'` ✅ (Inconsistent!)

## Resolution Strategy

### Option A: Update All Code to Use document_vectors (RECOMMENDED)
1. Run the V2.0.0 migration to rename the table
2. Update all code references to use `document_vectors`
3. Use the correct migration file (015_add_regulatory_vectors_support.sql)

### Option B: Keep user_document_vectors Name
1. Revert some migration files to use `user_document_vectors`
2. Update the few files using `document_vectors` to use old name

## Recommended Action Plan

1. **FIRST**: Run table rename migration:
   ```sql
   ALTER TABLE user_document_vectors RENAME TO document_vectors;
   ```

2. **THEN**: Update these critical files:
   - `scripts/bulk_regulatory_processor.py`
   - `db/services/encryption_aware_embedding_service.py` 
   - `db/services/embedding_service.py`
   - `main.py`
   - `db/supabase/functions/vector-processor/index.ts`

3. **FINALLY**: Run the regulatory vectors migration using the correct file:
   - `db/migrations/015_add_regulatory_vectors_support.sql` (uses document_vectors ✅)

## Status: 🚨 BLOCKING ISSUE
The regulatory processing system will fail until this table naming inconsistency is resolved. 