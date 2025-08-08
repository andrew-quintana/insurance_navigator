# @TODO001_phase2_notes.md — Phase 2 Implementation Notes

## What Was Implemented

- Added two API endpoints in `main.py`:
  - `POST /api/v1/memory/update` — validates input, checks chat existence via `ConversationService`, sanitizes `context_snippet`, enqueues with `MemoryService.enqueue_context`, returns `queue_id`, status, and 2s estimated completion.
  - `GET /api/v1/memory/{chat_id}` — validates chat existence, retrieves memory via `MemoryService.get_memory`, returns three fields and `last_updated`.
- Implemented lightweight per-user rate limiting (100 req/min default) with headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. Configurable via `API_RATE_LIMIT_PER_MIN` env var.
- Added input sanitization helper for `context_snippet` (strips control chars, trims, caps at 8k chars).
- Reused existing authentication pattern `Depends(get_current_user)`.
- Validated chat existence using `ConversationService.get_conversation(chat_id)`; IDs are TEXT.

## Files Touched

- `main.py` — imports `MemoryService`, adds `RateLimiter`, sanitization, validation helpers, and two endpoints.

## Response Contracts

- Update (201):
```json
{ "queue_id": "uuid", "status": "pending_summarization", "estimated_completion": "<ISO8601>Z" }
```
- Retrieve (200):
```json
{ "chat_id": "string", "user_confirmed": {}, "llm_inferred": {}, "general_summary": "", "last_updated": null }
```

## Security & Validation

- Auth required for both endpoints using existing token validation.
- Rate limiting enforced per user.
- `trigger_source` accepted but advisory; validated by regex `(manual|api|test)`.
- `context_snippet` sanitized and length-limited.

## Open Items

- Consider persisting `trigger_source` to `chat_context_queue` for observability.
- Replace in-memory limiter with Redis for multi-replica deployments.
- Add API docs section in central API reference.

