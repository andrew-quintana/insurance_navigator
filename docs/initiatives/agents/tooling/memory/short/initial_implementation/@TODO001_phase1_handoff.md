# @TODO001_phase1_handoff.md — Phase 1 Handoff

## Database Connection Details

- Uses existing Supabase client factory from `config/database.py` (`get_supabase_client`).
- Ensure `.env` has `SUPABASE_URL` and `SUPABASE_KEY` loaded via dotenv.

## Available CRUD Functions (MemoryService)

File: `db/services/memory_service.py`
- `get_memory(chat_id: str) -> dict`
- `upsert_memory(chat_id: str, user_confirmed: dict, llm_inferred: dict, general_summary: str, token_count: int) -> dict`
- `enqueue_context(chat_id: str, snippet: str, status_value: str = 'pending_summarization') -> dict`
- `update_queue_status(queue_id: str, status_value: str, error_message: str | None = None, retry_increment: int = 0) -> bool`
- `get_pending_queue(limit: int = 50) -> list[dict]`

Factory:
- `get_memory_service() -> MemoryService`

## Migrations

- Apply: `supabase db push` or run deployment script `scripts/deployment/apply-production-schema.sh`.
- File added: `supabase/migrations/20250807000000_add_chat_memory_tables.sql`.

## Test Setup Instructions

- Run unit tests (Phase 1 scope): `pytest -m unit tests/db/test_memory_service.py -q`.
- Tests use mocks; no live DB required for Phase 1.
- Optional local schema smoke test (non-destructive):
  - Ensure project is linked: `supabase link` (one-time)
  - Apply migrations: `supabase db push`
  - Verify via helper script (creates backup, push, dry-run verify): `bash scripts/deployment/apply-production-schema.sh`
  - Alternatively, verify tables exist (example):
    - `psql "$DATABASE_URL" -c "select to_regclass('public.chat_metadata');"`
    - `psql "$DATABASE_URL" -c "select to_regclass('public.chat_context_queue');"`

## Open Items / Next Phase Inputs

- Confirm final FK target if `conversations` table changes. Adjust migration accordingly.
- Decide token count calculation approach in Phase 3 when MCP summaries are generated.

