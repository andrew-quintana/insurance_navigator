@docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/upload_pipeline_testing_spec.md

ROLE: Execute Phase 2.

OBJECTIVE
- Run local API + worker against the **production** Supabase to validate schema/config parity with local.

ENVIRONMENT
- API + worker: local
- Database: production Supabase

GUARDS
- Read/write to a dedicated test schema/namespace or test org/project.
- Prefix all inserted rows with RUN_ID for cleanup.

STEPS
1) Point services to production Supabase (test schema), migrate if required.
    - rework the production Supabase schema to match the Supabase instance used in phase 1 so that they match in functionality
2) Re-run both PDFs; collect artifacts.
3) Compare behavior vs Phase 1 (counts, latencies, error types).

SUCCESS CRITERIA
- Identical functional results to Phase 1 (artifact presence + row counts).
- No schema mismatches; migrations applied cleanly.
- Network/auth flows succeed.

REPORT BACK
- Diff table vs Phase 1 (✓/✗ per check).
- Any parity gaps + minimal fix plan.