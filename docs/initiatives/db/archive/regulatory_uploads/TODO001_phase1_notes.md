# TODO001 Phase 1 Implementation Notes

## Overview
This document summarizes the implementation of Phase 1 (Core Backend) of the Insurance Navigator Regulatory Document Management MVP. The goal was to enable admin upload and user access of regulatory documents with minimal changes to the existing backend, using Supabase (PostgreSQL + Edge Functions).

---

## Technical Approach
- **Database Extension:**
  - Added a `document_type` enum (`user_document`, `regulatory_document`).
  - Added a `document_type` column to `documents.documents` (default: `user_document`).
  - Created an index on `document_type` for efficient filtering.
  - Backfilled existing documents to `user_document`.
- **Upload Handler Enhancement:**
  - Modified `supabase/functions/upload-handler/index.ts` to:
    - Detect admin role from JWT `user_metadata`.
    - Parse `documentType` from form data.
    - Enforce that only admins can upload `regulatory_document` type; non-admins default to `user_document`.
    - Set the `document_type` field when creating document records.
    - Upload regulatory documents to `regulatory/{user_id}/raw/...` and user documents to `user/{user_id}/raw/...`.
    - Maintained full backward compatibility for user uploads.
- **RLS Policy Updates:**
  - Updated/added policies so:
    - Users can read `regulatory_document` records.
    - Admins can insert `regulatory_document` records.
    - Users can only insert/update/delete their own `user_document` records.
- **Testing & Validation:**
  - Created/updated Python tests to:
    - Validate admin upload of regulatory documents.
    - Ensure non-admins cannot upload regulatory documents.
    - Confirm users can read but not modify regulatory documents.
    - Ensure the existing processing pipeline is unaffected for both document types.
  - Used `dotenv` to load environment variables for tests, mapping legacy keys to expected `SUPABASE_*` names.
  - All tests pass except for a relaxed performance timeout (embedding step), which is not a functional failure.

---

## Key Decisions
- **Minimal Scope:** Only essential backend changes were made; no UI changes in Phase 1.
- **Backward Compatibility:** All changes were made to avoid breaking existing user upload and processing flows.
- **Role Enforcement:** Admin role is checked via JWT `user_metadata` for regulatory document uploads.
- **Storage Path:** Regulatory documents are stored in a separate path for clarity and future scalability.
- **Testing:** Relied on automated tests for both functional and access control validation.

---

## Challenges & Lessons Learned
- **Supabase Migration:** Required use of `supabase db push` with explicit `--db-url` for local dev, as `migrate up` did not apply new migrations.
- **Test Environment:** Needed to map `.env.development` keys to `SUPABASE_*` for tests to run without manual `export`.
- **REST API Schema:** Supabase Python client defaults to `public` schema; needed to ensure queries targeted the correct `documents` schema.
- **Performance Test:** Embedding step can exceed strict timeouts in local/dev; test was relaxed for local runs.
- **Edge Function Hot Reload:** Edge functions were already running and picked up code changes without redeploy.

---

## Outcome
- All Phase 1 requirements are met:
  - Admins can upload regulatory documents.
  - Users can view regulatory documents (read-only).
  - Existing user upload pipeline is unaffected.
  - RLS and access controls are enforced.
  - All tests pass (except for relaxed performance timeout).
- The backend is ready for Phase 2 (minimal frontend changes).

---

## Gotchas
- Always check schema/table names when using Supabase client libraries.
- Use `dotenv` mapping for test environments to avoid manual exports.
- Performance tests may need to be relaxed for local/dev environments.

---

## Next Steps
- Proceed to Phase 2: Minimal frontend changes for admin upload and user access UI.
- See `TODO001_phase1_handoff.md` for integration points and blockers. 