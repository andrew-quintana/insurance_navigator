@docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/upload_pipeline_testing_spec.md

ROLE: Execute Phase 3.

OBJECTIVE
- Deploy API + worker to cloud and prove end-to-end parity with Phase 2 on production Supabase.

PRIOR WORK
- @docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/phase2/reports/PHASE2_WEBHOOK_COMPLETION_REPORT.md
- @docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/phase2/reports/PHASE2_TO_PHASE3_HANDOFF.md
- @docs/initiatives/system/upload_refactor/003/deployment/workflow_testing/upload_pipeline/phase2/reports/PHASE2_COMPLETE_SUMMARY.md

ENVIRONMENT
- API + worker: cloud deployments
- Database: production Supabase
- Storage: production blob storage (test bucket/container)

STEPS
1) Deploy artifacts; surface URLs/versions.
2) Run both PDFs through the cloud endpoints.
3) Validate all artifacts + DB rows; compare to Phase 2.

SUCCESS CRITERIA (Ship/No-Ship)
- Both PDFs present in blob storage and parsed/chunked files exist.
- Embeddings generated via OpenAI model.
- Document metadata + chunk + vector rows created.
- Behavior matches local runs (within acceptable variance).

REPORT BACK
- Public/console endpoints, build IDs.
- Evidence links/IDs, row counts, timings.
- Any cloud-only issues + remediation.