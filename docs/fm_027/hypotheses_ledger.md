# FM-027 Hypotheses Ledger

## Executive Summary
**Root Cause Identified**: The `generate_storage_path()` function uses non-deterministic timestamp-based hashing, causing generated paths to never match stored file paths. This is a fundamental design flaw, not a bug.

## Hypothesis Results

| Hypothesis | Test(s) | Observed | Verdict | Links |
|------------|---------|----------|---------|-------|
| H3: Path Mismatch | E1 | Generated paths differ from actual stored paths | **SUPPORTED** | [E1 Results](experiment_e1_results.json) |
| H2: Upload Process | E2 | Both upload and job creation use same path generation | **REFUTED** | [E2 Results](experiment_e2_results.json) |
| H3: Historical Changes | E3 | Path generation is fundamentally non-deterministic | **SUPPORTED** | [E3 Results](experiment_e3_results.json) |

## Detailed Analysis

### H3: Path Mismatch (SUPPORTED)
- **Evidence**: Generated path `6ff1b1c1_5e4390c2.pdf` vs actual stored `28f176cc_5e4390c2.pdf`
- **Root Cause**: Timestamp-based hashing creates different paths for same document
- **Impact**: Files are never found because paths are generated at different times

### H2: Upload Process (REFUTED)
- **Evidence**: Both upload process and job creation use `generate_storage_path()` function
- **Conclusion**: No difference in path generation between processes
- **Impact**: The issue affects both processes equally

### H3: Historical Changes (SUPPORTED)
- **Evidence**: Path generation uses `datetime.utcnow().isoformat()` which changes every call
- **Git History**: No changes to `generate_storage_path()` function in recent commits
- **Conclusion**: The non-deterministic behavior is by design, not due to changes

## Root Cause Summary
The `generate_storage_path()` function in `api/upload_pipeline/utils/upload_pipeline_utils.py` uses:
```python
timestamp = datetime.utcnow().isoformat()
timestamp_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
```

This creates a different path every time it's called, even for the same document. The worker tries to access files using paths generated at job creation time, but the actual files are stored with paths generated at upload time.

## Recommended Fix
Replace timestamp-based hashing with deterministic content-based hashing:
```python
def generate_storage_path(user_id: str, document_id: str, filename: str) -> str:
    # Use document_id hash for deterministic path
    doc_hash = hashlib.md5(document_id.encode()).hexdigest()[:8]
    ext = filename.split('.')[-1] if '.' in filename else 'pdf'
    return f"files/user/{user_id}/raw/{doc_hash}.{ext}"
```

## Next Steps
1. Implement deterministic path generation
2. Add migration strategy for existing files
3. Add regression tests to prevent future issues
4. Update documentation to reflect deterministic behavior
