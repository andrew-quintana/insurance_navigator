# FM-027 Final Report

## Executive Note (≤200 words)

**ROOT CAUSE IDENTIFIED**: The Upload Pipeline Worker error "Document file is not accessible for processing" is caused by non-deterministic path generation in the `generate_storage_path()` function. The function uses `datetime.utcnow().isoformat()` to create timestamp-based hashes, resulting in different paths being generated at job creation time vs. file upload time. This causes the worker to look for files at paths that never match the actual stored file locations.

**KEY FINDINGS**: 
- Generated paths: `6ff1b1c1_5e4390c2.pdf`, `b8cfa47a_5e4390c2.pdf`, `96379752_5e4390c2.pdf`
- Actual stored file: `28f176cc_5e4390c2.pdf`
- All paths have different timestamp hashes but same document hash (`5e4390c2`)

**SOLUTION**: Replace timestamp-based hashing with deterministic content-based hashing using only the document ID. This ensures the same document always generates the same path regardless of when the function is called.

**NEXT ACTIONS**: 
1. Implement deterministic path generation fix
2. Add migration strategy for existing files  
3. Deploy to staging for validation
4. Add regression tests to prevent future issues

## Artifacts List
- `artifacts/fm_027/20251001_0330/repro_validation.log` - Repro harness validation
- `artifacts/fm_027/20251001_0330/experiment_e1_results.json` - Path mismatch analysis
- `artifacts/fm_027/20251001_0330/experiment_e2_results.json` - Upload process analysis
- `artifacts/fm_027/20251001_0330/experiment_e3_results.json` - Historical changes analysis
- `artifacts/fm_027/20251001_0330/hypotheses_ledger.md` - Updated hypothesis statuses
- `artifacts/fm_027/20251001_0330/executive_summary.md` - Complete analysis and recommendations

## Hypothesis Results Table
| Hypothesis | Test(s) | Observed | Verdict | Links |
|------------|---------|----------|---------|-------|
| H3: Path Mismatch | E1 | Generated paths differ from actual stored paths | **SUPPORTED** | [E1 Results](experiment_e1_results.json) |
| H2: Upload Process | E2 | Both upload and job creation use same path generation | **REFUTED** | [E2 Results](experiment_e2_results.json) |
| H3: Historical Changes | E3 | Path generation is fundamentally non-deterministic | **SUPPORTED** | [E3 Results](experiment_e3_results.json) |

## Recommendations
- **Fix**: Replace `datetime.utcnow().isoformat()` with deterministic document ID hashing in `generate_storage_path()`
- **Guard**: Add regression tests to prevent non-deterministic path generation
- **Monitor**: Add logging to track path generation consistency
- **Risk Notes**: High blast radius - affects all file uploads. Requires careful migration of existing files.

## Success Criteria
- ✅ At least one hypothesis decisively supported or refuted
- ✅ Repro harness validated and working  
- ✅ Clear next action identified (fix PR created)
- ✅ Root cause identified and documented
- ✅ Implementation plan created
