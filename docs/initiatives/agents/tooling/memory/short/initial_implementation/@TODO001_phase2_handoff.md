# @TODO001_phase2_handoff.md — Phase 2 Handoff

## API Endpoints

- POST `/api/v1/memory/update`
  - Body: `{ "chat_id": "string", "context_snippet": "string", "trigger_source": "manual|api|test" }`
  - Response 201: `{ "queue_id": "uuid", "status": "pending_summarization", "estimated_completion": "<ISO8601>Z" }`
  - Headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

- GET `/api/v1/memory/{chat_id}`
  - Response 200: `{ "chat_id": "string", "user_confirmed": {}, "llm_inferred": {}, "general_summary": "", "last_updated": "<ISO8601>|null" }`
  - Headers: `X-RateLimit-*` as above

## Authentication

- Uses `Depends(get_current_user)` from `main.py` for both endpoints
- Requires `Authorization: Bearer <token>`

## Rate Limiting

- In-memory per-user sliding window limiter: default 100 req/min
- Config: `API_RATE_LIMIT_PER_MIN` env var (string integer)
- 429 returned when exceeded

## Dependencies

- `db/services/memory_service.py`
  - `get_memory_service()`
  - `MemoryService.enqueue_context(chat_id, snippet, status_value)`
  - `MemoryService.get_memory(chat_id)`
- `db/services/conversation_service.py`
  - `get_conversation_service()`
  - `ConversationService.get_conversation(chat_id)` (TEXT id)

## Testing Notes

- Start server: `uvicorn main:app --reload`
- Manual test:
  - Create/identify a valid conversation id in `conversations`
  - POST update, then GET memory
- Integration: expand `tests/integration/test_api_endpoints.py` with authenticated calls to the new endpoints

## Open Items for Phase 3

- Persist `trigger_source` in queue schema for observability
- Replace in-memory limiter with shared store for multi-replica deployments
- Add API reference section and examples to central docs