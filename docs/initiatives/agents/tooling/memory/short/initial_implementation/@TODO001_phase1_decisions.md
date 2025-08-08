# @TODO001_phase1_decisions.md — Phase 1 Design Decisions

- Foreign Key Target:
  - **Chosen:** `conversations(id)` TEXT
  - **Reason:** Existing services (`ConversationService`) and docs indicate chat sessions are stored in `conversations` with TEXT ids. Ensures compatibility.
  - **RFC Note:** RFC proposed `chats(id)` UUID; we aligned to repo reality.

- Indexing Strategy:
  - `chat_metadata(chat_id)`, `chat_metadata(last_updated)` for fast lookups and freshness tracking.
  - `chat_context_queue(status, created_at)`, `chat_context_queue(chat_id)` for efficient queue pulls and chat-scoped queries.

- Error Handling:
  - Service methods raise FastAPI `HTTPException` for invalid inputs and DB errors, matching existing patterns.
  - Fallback implemented when `.upsert()` method is unavailable in client version (insert→update pattern).

- Testing Approach:
  - Unit tests mock Supabase client chains to isolate logic.
  - Defaults returned for missing memory to simplify consumer logic.

