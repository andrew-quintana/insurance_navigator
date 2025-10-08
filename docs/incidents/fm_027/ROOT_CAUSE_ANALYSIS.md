# FM-027 Root Cause Analysis: The Real Issue

## Executive Summary

**Status**: ✅ **ROOT CAUSE IDENTIFIED** - Path format mismatch between database and new code
**Issue**: Existing database records use old timestamp-based paths, but new code generates deterministic paths
**Impact**: Workers can't access files because they look for files using new paths, but files are stored with old paths

## The Real Problem

### 1. Path Format Mismatch
- **Database records**: Use old format `a61afcc6_36d295c4.pdf` (timestamp_hash + document_hash)
- **New code generates**: New format `36d295c4.pdf` (just document_hash)
- **Worker uses**: Path from job data (old format) but might be regenerating paths somewhere

### 2. Timeline Analysis
1. **Old uploads**: Used timestamp-based path generation → stored in database as `a61afcc6_36d295c4.pdf`
2. **Our fix deployed**: New uploads use deterministic path generation → stored as `36d295c4.pdf`
3. **Worker processes job**: Uses path from job data (old format) but file might not exist at that path
4. **LlamaParse fails**: Can't access file because of path mismatch

### 3. Evidence
**Staging Database Analysis**:
- Document ID: `d37eadde-2ea1-5a66-91d9-1d5474b6ba23`
- Database path: `files/user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/a61afcc6_36d295c4.pdf`
- Generated path: `files/user/be18f14d-4815-422f-8ebd-bfa044c33953/raw/36d295c4.pdf`
- **Result**: ❌ **MISMATCH CONFIRMED**

## Technical Analysis

### Path Generation Evolution
```python
# OLD (Non-deterministic) - Used for existing data
def generate_storage_path_old(user_id, document_id, filename):
    timestamp = datetime.utcnow().isoformat()
    timestamp_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    doc_hash = hashlib.md5(document_id.encode()).hexdigest()[:8]
    return f"files/user/{user_id}/raw/{timestamp_hash}_{doc_hash}.{ext}"

# NEW (Deterministic) - Our fix
def generate_storage_path(user_id, document_id, filename):
    doc_hash = hashlib.md5(document_id.encode()).hexdigest()[:8]
    return f"files/user/{user_id}/raw/{doc_hash}.{ext}"
```

### Worker Flow Analysis
1. **Job Creation**: Uses `generate_storage_path()` → stores path in job data
2. **File Upload**: Uploads file to the generated path
3. **Worker Processing**: Uses path from job data to access file
4. **LlamaParse**: Tries to access file using the path from job data

### The Issue
- **New jobs**: Work correctly (use new deterministic paths)
- **Existing jobs**: Still have old paths in database, but files might be stored with different paths
- **Worker**: Uses path from job data, but file might not exist at that exact path

## Solutions

### Option A: Database Migration (Recommended)
Update existing database records to use new path format:
```sql
UPDATE upload_pipeline.documents 
SET raw_path = REPLACE(raw_path, 
    SUBSTRING(raw_path FROM 'raw/[^_]+_([^.]+)\.'), 
    'raw/\1.')
WHERE raw_path LIKE '%_%.pdf';
```

### Option B: Worker Path Resolution
Modify worker to try both old and new path formats:
```python
# Try new format first
file_exists = await self.storage.blob_exists(new_path)
if not file_exists:
    # Fallback to old format
    file_exists = await self.storage.blob_exists(old_path)
```

### Option C: File Migration
Move existing files from old paths to new paths:
```python
# Move file from old path to new path
await storage.move_file(old_path, new_path)
```

## Recommended Action

**Immediate Fix**: Implement Option B (Worker Path Resolution) to handle both formats
**Long-term**: Implement Option A (Database Migration) to standardize on new format

## Testing Strategy

1. **Test existing data**: Verify worker can access files with old path format
2. **Test new data**: Verify worker can access files with new path format
3. **Test mixed scenario**: Verify worker handles both formats correctly
4. **Deploy with monitoring**: Watch for any remaining path mismatch errors

## Success Criteria

- [x] Root cause identified and documented
- [ ] Worker can access files with old path format
- [ ] Worker can access files with new path format
- [ ] No more "Document file is not accessible" errors
- [ ] System handles both path formats gracefully

**Status**: 🔧 **READY FOR IMPLEMENTATION**
