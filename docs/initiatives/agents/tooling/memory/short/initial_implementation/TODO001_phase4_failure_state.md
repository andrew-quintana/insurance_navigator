# TODO001_phase_4_failure_state.md — Phase 4 Current Failure State & Handoff

## Summary

Phase 4 (Integration & Production Readiness) stalled during local E2E execution due to environment/runtime issues. Unit coverage for agent, worker (logic), and DB service passed. Local Supabase DB was provisioned and migrations applied non-destructively, but the API failed to come up reliably due to environment constraints; the worker reported async client misuse.

## Environment

- OS: darwin 24.6.0
- Python: anaconda base 3.9 (uvicorn also available under Homebrew Python 3.11)
- Supabase CLI: 2.30.4
- Local Supabase: running via `supabase start`
  - API URL: http://127.0.0.1:54321
  - DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
  - Keys available via `supabase status -o json`
- Env for app (target):
  - `SUPABASE_URL=http://127.0.0.1:54321`
  - `SUPABASE_KEY=<service_role_key from supabase status>`
  - `USE_MOCK_LLM=true`

## What Worked

- Migrations (non-destructive):
  - `chat_metadata` and `chat_context_queue` created after creating a minimal `public.conversations` table (TEXT id)
  - Applied with: `psql "$DATABASE_URL" -f supabase/migrations/20250807000000_add_chat_memory_tables.sql`
- Unit tests:
  - `tests/agents/test_memory_summarizer_agent.py`: PASS
  - `tests/workers/test_memory_processor.py`: PASS
  - `tests/db/test_memory_service.py`: PASS
- Minimal seeding:
  - Inserted `public.conversations` row with id `chat-1`

## What Blocked Us

1) API server startup
   - Initially failed on `ModuleNotFoundError: psycopg2`. Added guarded import in `main.py` (optional psycopg2) but subsequent startup encountered a Python 3.9 typing issue in `utils/cors_config.py` (usage of `str | None`). Fixed to `Optional[str]`.
   - Despite fixes, API health check remained unreachable (curl returned 000). Logs repeatedly showed the earlier psycopg2 error from a different uvicorn path (brew Python 3.11) indicating multiple Python environments and inconsistent interpreters running uvicorn.
   - Recommendation: pin to a single interpreter/venv, install requirements, and run `python -m uvicorn main:app` from that environment.

2) Worker runtime error
   - When running `USE_MOCK_LLM=true python -m scripts.workers.memory_processor`, logs showed:
     - `ERROR: Unexpected error querying pending queue: object APIResponse[...] can't be used in 'await' expression`
   - Cause: `db/services/memory_service.py` uses async/await with the Supabase Python client which is synchronous. Awaiting `.execute()` results in this error under local run.
   - Fix direction: Remove `async` from MemoryService methods or run supabase queries in threadpool; alternatively, use an async DB client or HTTP calls.

## Concrete Errors & Logs

- API
  - `ModuleNotFoundError: No module named 'psycopg2'` (resolved via guard but persisted under brew Python path)
  - `TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'` in `utils/cors_config.py` (fixed by using `Optional[str]`)
  - Health endpoint unreachable (`curl` HTTP code 000).

- Worker
  - `object APIResponse[...] can't be used in 'await' expression` while calling Supabase `.execute()`

## Repro Steps

1) Start local Supabase: `supabase start`
2) Export:
   - `export SUPABASE_URL=http://127.0.0.1:54321`
   - `export SUPABASE_KEY=<service_role_key>`
3) Apply migrations:
   - Create minimal tables for local run if needed:
     - `public.users` (uuid id), `public.audit_logs`, `public.conversations (id text)`
   - `psql "$DATABASE_URL" -f supabase/migrations/20250807000000_add_chat_memory_tables.sql`
4) Seed conversation id:
   - `insert into public.conversations (id, user_id, metadata) values ('chat-1', gen_random_uuid(), '{}'::jsonb) on conflict (id) do nothing;`
5) Try API:
   - From consistent venv: `python -m uvicorn main:app --host 127.0.0.1 --port 8000 --log-level info`
   - If health still unreachable, check logs and ensure psycopg2 import is guarded (already applied) and CORS typing fix present (already applied).
6) Try worker:
   - `USE_MOCK_LLM=true python -m scripts.workers.memory_processor`
   - Expect the async supabase `.execute()` await issue until service refactor.

## Suggested Next Actions

- Environment hygiene:
  - Create a dedicated venv (Python 3.11 preferred), install all requirements, ensure uvicorn and libraries load from that venv.
  - Run `python -m uvicorn main:app` from that venv only.
- MemoryService refactor (priority):
  - Remove `async`/`await` usage from Supabase client calls or wrap in `anyio.to_thread.run_sync`.
  - Apply same adjustment in worker call sites.
- After refactor:
  - Re-run E2E: register/login → create conversation → POST memory/update → worker → GET memory.
  - Capture observed outputs and update Phase 4 docs accordingly.

## Ownership Handoff

- Primary files:
  - `db/services/memory_service.py` (async misuse → convert to sync or threadpool)
  - `scripts/workers/memory_processor.py` (depends on above)
  - `main.py` (psycopg2 guard already applied)
  - `utils/cors_config.py` (typing fixed)
- Local DB state:
  - `chat_metadata`, `chat_context_queue`, and `conversations` exist locally
- Credentials:
  - Use Supabase CLI `status -o json` to fetch keys on your machine

## Notes

- Avoid destructive DB resets (follow non-destructive migration application).
- Keep `USE_MOCK_LLM=true` for cost-free local validation.