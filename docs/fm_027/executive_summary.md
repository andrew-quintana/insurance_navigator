# FM-027 Executive Summary

## Issue Status: ROOT CAUSE IDENTIFIED ✅

**Error**: "Document file is not accessible for processing. Please try uploading again."
**Service**: Upload Pipeline Worker (staging)
**Root Cause**: Non-deterministic path generation in `generate_storage_path()` function

## Key Findings

### 1. Path Mismatch Confirmed (H3 - SUPPORTED)
- **Generated paths**: `6ff1b1c1_5e4390c2.pdf`, `b8cfa47a_5e4390c2.pdf`, `96379752_5e4390c2.pdf`
- **Actual stored file**: `28f176cc_5e4390c2.pdf`
- **Pattern**: All paths have different timestamp hashes but same document hash (`5e4390c2`)

### 2. Upload Process Analysis (H2 - REFUTED)
- Both upload process and job creation use the same `generate_storage_path()` function
- No difference in path generation between processes
- Issue affects both processes equally

### 3. Historical Changes Analysis (H3 - SUPPORTED)
- Path generation uses `datetime.utcnow().isoformat()` which changes every call
- No recent changes to the function in git history
- Non-deterministic behavior is by design, not due to changes

## Root Cause Analysis

The `generate_storage_path()` function in `api/upload_pipeline/utils/upload_pipeline_utils.py` creates non-deterministic paths:

```python
def generate_storage_path(user_id: str, document_id: str, filename: str) -> str:
    timestamp = datetime.utcnow().isoformat()  # ← NON-DETERMINISTIC
    timestamp_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"files/user/{user_id}/raw/{timestamp_hash}_{hashlib.md5(document_id.encode()).hexdigest()[:8]}.{ext}"
```

**Problem**: Every call generates a different path for the same document, causing:
1. Job creation generates path A
2. File upload stores file at path B (generated later)
3. Worker tries to access path A, but file is at path B
4. File not found error

## Recommended Solution

Replace timestamp-based hashing with deterministic content-based hashing:

```python
def generate_storage_path(user_id: str, document_id: str, filename: str) -> str:
    # Use document_id hash for deterministic path
    doc_hash = hashlib.md5(document_id.encode()).hexdigest()[:8]
    ext = filename.split('.')[-1] if '.' in filename else 'pdf'
    return f"files/user/{user_id}/raw/{doc_hash}.{ext}"
```

## Implementation Plan

1. **Immediate Fix**: Update `generate_storage_path()` to use deterministic hashing
2. **Migration**: Handle existing files with timestamp-based paths
3. **Testing**: Add regression tests to prevent future issues
4. **Documentation**: Update path generation documentation

## Risk Assessment

- **Blast Radius**: High - affects all file uploads and processing
- **Data Loss Risk**: Low - files exist, just at different paths
- **Rollback Plan**: Revert to timestamp-based hashing if issues arise
- **Testing Required**: Full integration testing of upload pipeline

## Next Actions

1. Create PR with deterministic path generation fix
2. Implement migration strategy for existing files
3. Add comprehensive tests
4. Deploy to staging for validation
5. Deploy to production after staging validation

## Success Criteria

- ✅ Root cause identified and confirmed
- ✅ All hypotheses tested and resolved
- ✅ Clear fix identified and documented
- ✅ Implementation plan created
- ✅ Risk assessment completed
