# FM-027 – Executor Agent Prompt (Next Experiments)

## System Role
You are an execution-focused coding agent. Your job is to run discriminating experiments to falsify or support the top hypotheses with minimal changes and maximum information gain.

## Context (Auto-summarized)

### Signal & Scope
- **Error**: "Document file is not accessible for processing. Please try uploading again."
- **Service**: Upload Pipeline Worker (staging)
- **Status**: Critical StorageManager bug fixed (commit 33c0384), path mismatch investigation ongoing
- **Environment**: Staging Supabase (dfgzeastcxnoqshgyotp.supabase.co)

### Minimal Repro
- **Script**: `test_storage_manager_debug.py`
- **Environment**: Python 3.11, Supabase staging
- **Status**: ✅ Reproduces consistently

### Top Hypotheses
1. **H3: File Path Mismatch** (Priority 1) - Generated paths differ from actual stored paths
2. **H2: File Upload Process** (Priority 2) - Upload uses different path generation than job creation  
3. **H3: Historical Changes** (Priority 3) - Path generation logic changed since file upload

### Key Diffs
- **Critical Fix**: StorageManager URL construction bug (commit 33c0384)
- **Remaining Issue**: Generated path `a5363e8d_5e4390c2.pdf` vs actual `b8cfa47a_5e4390c2.pdf`

### "Spelling Mode" Definition
Not applicable - No spelling mode functionality found in codebase.

### Links & Artifacts
- **Investigation Doc**: `docs/incidents/fm_027/INV-20251001.md`
- **Repro Scripts**: `test_*.py` files in project root
- **Storage Data**: `storage_files_list_20250930_200936.json`
- **Commits**: `33c0384` (critical fix), `e42fcea` (race condition fixes)

## Tasks (Strict Order)

### 1. Validate Minimal Repro Harness
**Objective**: Ensure reproduction script works on your runner
**Procedure**:
```bash
cd /Users/aq_home/1Projects/accessa/insurance_navigator
export SUPABASE_URL="***REMOVED***"
export ANON_KEY="***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE2ODA0ODMsImV4cCI6MjA2NzI1NjQ4M30.wV0kgqo20D1EghH47bO-4MoXpksiyQ_bvANaZlzScyM"
export SUPABASE_SERVICE_ROLE_KEY="***REMOVED***.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRmZ3plYXN0Y3hub3FzaGd5b3RwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTY4MDQ4MywiZXhwIjoyMDY3MjU2NDgzfQ.yYQWEJkDtvFXg-F2Xe4mh9Xj_0QCp6gnXkDI6lEhDT8"
python test_storage_manager_debug.py
```
**Expected**: File access should work (StorageManager fix applied)
**Output**: Raw logs showing successful file access

### 2. Execute Experiment E1: Path Mismatch Investigation
**Objective**: Compare generated paths with actual stored file paths
**Hypothesis**: Generated paths create different filenames than what's actually stored
**Procedure**:
```bash
# Run path generation test
python test_complete_flow_simulation.py

# Check actual stored files
python test_list_storage_files.py

# Compare results
python -c "
import json
with open('storage_files_list_20250930_200936.json') as f:
    actual = json.load(f)
print('Actual files:', [f['name'] for f in actual['files'] if f.get('name')])
"
```
**Expected if true**: Generated path differs from actual stored path
**Expected if false**: Generated path matches actual stored path
**Output**: Comparison table showing path differences

### 3. Execute Experiment E2: File Upload Process Analysis
**Objective**: Trace file upload process and compare with job creation path generation
**Hypothesis**: Upload process uses different path generation than job creation
**Procedure**:
```bash
# Trace upload process
grep -r "generate_storage_path" api/upload_pipeline/
grep -r "raw_path" api/upload_pipeline/

# Check upload endpoints
grep -A 10 -B 5 "upload.*file" api/upload_pipeline/endpoints/upload.py

# Analyze path construction
python -c "
from api.upload_pipeline.utils.upload_pipeline_utils import generate_storage_path
import hashlib
from datetime import datetime

# Test with same inputs as actual file
user_id = '74a635ac-4bfe-4b6e-87d2-c0f54a366fbe'
document_id = '2f064818-4568-5ca2-ad05-e26484d8f1c4'
filename = 'test_document.pdf'

path = generate_storage_path(user_id, document_id, filename)
print('Generated path:', path)

# Check if this matches actual file
actual_path = 'files/user/74a635ac-4bfe-4b6e-87d2-c0f54a366fbe/raw/b8cfa47a_5e4390c2.pdf'
print('Actual path:', actual_path)
print('Match:', path == actual_path)
"
```
**Expected if true**: Upload process uses different path generation
**Expected if false**: Upload and job creation use same path generation
**Output**: Analysis of path generation differences

### 4. Execute Experiment E3: Historical Path Generation Changes
**Objective**: Determine if path generation logic changed since file was uploaded
**Hypothesis**: Path generation logic changed since file was uploaded
**Procedure**:
```bash
# Git bisect on generate_storage_path function
git log --oneline --follow api/upload_pipeline/utils/upload_pipeline_utils.py

# Check when file was uploaded vs when path generation changed
git log --since="2025-09-25" --until="2025-10-01" --oneline api/upload_pipeline/utils/upload_pipeline_utils.py

# Test path generation with different timestamps
python -c "
from api.upload_pipeline.utils.upload_pipeline_utils import generate_storage_path
import hashlib
from datetime import datetime

# Test with different timestamps
user_id = '74a635ac-4bfe-4b6e-87d2-c0f54a366fbe'
document_id = '2f064818-4568-5ca2-ad05-e26484d8f1c4'
filename = 'test_document.pdf'

# Current timestamp
path1 = generate_storage_path(user_id, document_id, filename)
print('Current timestamp path:', path1)

# Simulate old timestamp (if possible)
# Note: This may require modifying the function temporarily
"
```
**Expected if true**: Path generation produces different results with different timestamps
**Expected if false**: Path generation is deterministic regardless of timestamp
**Output**: Analysis of path generation changes over time

### 5. Run Delta Debugging (if needed)
**Objective**: Minimize the failing case if experiments don't discriminate
**Procedure**:
```bash
# If path mismatch persists, minimize the case
python -c "
# Test with minimal inputs to isolate the issue
from api.upload_pipeline.utils.upload_pipeline_utils import generate_storage_path

# Test with minimal inputs
test_cases = [
    ('user1', 'doc1', 'file.pdf'),
    ('74a635ac-4bfe-4b6e-87d2-c0f54a366fbe', 'doc1', 'file.pdf'),
    ('74a635ac-4bfe-4b6e-87d2-c0f54a366fbe', '2f064818-4568-5ca2-ad05-e26484d8f1c4', 'file.pdf'),
    ('74a635ac-4bfe-4b6e-87d2-c0f54a366fbe', '2f064818-4568-5ca2-ad05-e26484d8f1c4', 'test_document.pdf'),
]

for user_id, doc_id, filename in test_cases:
    path = generate_storage_path(user_id, doc_id, filename)
    print(f'{user_id}, {doc_id}, {filename} -> {path}')
"
```
**Output**: Minimized test case showing the exact conditions causing path mismatch

### 6. Add Temporary Tracepoints
**Objective**: Add structured logging to track path generation and file access
**Procedure**:
```python
# Add to generate_storage_path function
def generate_storage_path(user_id: str, document_id: str, filename: str) -> str:
    timestamp = datetime.utcnow().isoformat()
    timestamp_hash = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    ext = filename.split('.')[-1] if '.' in filename else 'pdf'
    path = f"files/user/{user_id}/raw/{timestamp_hash}_{hashlib.md5(document_id.encode()).hexdigest()[:8]}.{ext}"
    
    # ADD TRACEPOINT
    print(f"TRACEPOINT: generate_storage_path({user_id}, {document_id}, {filename}) -> {path}")
    print(f"TRACEPOINT: timestamp={timestamp}, timestamp_hash={timestamp_hash}")
    
    return path
```

### 7. Update Hypotheses Ledger
**Objective**: Update hypothesis statuses based on experimental results
**Format**:
```markdown
| Hypothesis | Test(s) | Observed | Verdict | Links |
|------------|---------|----------|---------|-------|
| H3: Path Mismatch | E1 | [results] | [supported/refuted/inconclusive] | [links] |
| H2: Upload Process | E2 | [results] | [supported/refuted/inconclusive] | [links] |
| H3: Historical Changes | E3 | [results] | [supported/refuted/inconclusive] | [links] |
```

### 8. Create Micro-Fix PR (if causal commit emerges)
**Objective**: If single causal commit/config emerges, create targeted fix
**Procedure**:
- Create minimal fix addressing the root cause
- Add tests to prevent regression
- Include rollback plan
- Document blast radius

## Constraints & Safety

### Safety Rules
- **No production writes**: Use staging environment only
- **PII/PHI redaction**: Ensure no sensitive data in logs
- **Timebox**: Complete within 2 hours
- **Artifact preservation**: Save all outputs under `artifacts/fm_027/20251001_0330/`

### Rollback Plan
- **StorageManager fix**: Already deployed and working
- **Path generation changes**: Revert any modifications to `generate_storage_path`
- **Test modifications**: Revert any temporary changes to test files

## Reporting Format

### Executive Note (≤200 words)
[Provide concise summary of findings and next actions]

### Artifacts List
- `artifacts/fm_027/20251001_0330/repro_validation.log` - Repro harness validation
- `artifacts/fm_027/20251001_0330/experiment_e1_results.json` - Path mismatch analysis
- `artifacts/fm_027/20251001_0330/experiment_e2_results.json` - Upload process analysis
- `artifacts/fm_027/20251001_0330/experiment_e3_results.json` - Historical changes analysis
- `artifacts/fm_027/20251001_0330/hypotheses_ledger.md` - Updated hypothesis statuses

### Hypothesis Results Table
| Hypothesis | Test(s) | Observed | Verdict | Links |
|------------|---------|----------|---------|-------|
| H3: Path Mismatch | E1 | [results] | [supported/refuted/inconclusive] | [links] |
| H2: Upload Process | E2 | [results] | [supported/refuted/inconclusive] | [links] |
| H3: Historical Changes | E3 | [results] | [supported/refuted/inconclusive] | [links] |

### Recommendations
- **Fix**: [Specific fix if root cause identified]
- **Guard**: [Preventive measures to avoid regression]
- **Monitor**: [Observability improvements needed]
- **Risk Notes**: [Any risks associated with recommendations]

## Success Criteria

### Must Achieve
- ✅ At least one hypothesis decisively supported or refuted
- ✅ Repro harness validated and working
- ✅ Clear next action identified (fix PR or next experiments)

### Stop Conditions / Escalation
- **Repro becomes non-deterministic**: After 3 consecutive runs → escalate with captured traces
- **Data corruption detected**: Halt immediately and notify owners
- **Security risk identified**: Halt immediately and notify owners

---

**Time Budget**: 2 hours  
**Priority**: P1 - Core functionality partially restored, secondary issues remain  
**Next Action**: Execute experiments to identify path mismatch root cause
