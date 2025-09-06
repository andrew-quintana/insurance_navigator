@InitialSpec

ROLE: You are executing Phase 1 of the Upload Pipeline MVP test.

OBJECTIVE
- Verify API service + worker run locally/dev and process both test PDFs end-to-end against known-good local/dev Supabase.

ENVIRONMENT
- API + worker: local/dev
- Database: local/dev Supabase (known working)
- Test docs: 
  - Small: "Simulated Insurance Document.pdf"
  - Large: "Scan Classic HMO.pdf"

STEPS
1) Start API + worker locally/dev with current config.
2) Upload both PDFs; wait for pipeline completion.
3) Collect artifacts: blob objects, parsed/chunked files, embeddings.
4) Verify DB rows for document metadata, chunk rows, and vector embeddings.

SUCCESS CRITERIA
- Both PDFs complete all stages (queue → parse → chunk → embed).
- Blob storage and DB contain expected artifacts/rows.
- No unrecoverable “upload failed”; retries/checkpoints exercised if needed.

REPORT BACK
- Post a markdown summary:
  - Versions/commit SHAs, env variables used.
  - Timestamps + durations.
  - Paths/IDs of blob objects.
  - Counts of metadata/chunks/embeddings created.
  - Logs (last 200 lines) for API + worker.
  - Any deviations + proposed fixes.