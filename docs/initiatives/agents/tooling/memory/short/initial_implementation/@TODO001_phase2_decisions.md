# @TODO001_phase2_decisions.md — Phase 2 Design Decisions

- Auth Pattern: Reused `Depends(get_current_user)` from `main.py` to ensure consistency with existing endpoints.
- Rate Limiting: Implemented simple in-memory sliding-window limiter (100 req/min default) to meet RFC requirement quickly. Exposed standard headers. Trade-off: not multi-replica safe; to be replaced with Redis in production scale.
- Chat ID Validation: Used `ConversationService.get_conversation(chat_id)`; repo uses TEXT ids for `conversations(id)`. RFC’s UUID `chats(id)` was not used to stay aligned with repo reality.
- Input Sanitization: Stripped control characters, trimmed, and capped `context_snippet` at 8k chars to reduce risk of injection and large payloads.
- Trigger Source: Validated via regex but not persisted in queue schema (not in Phase 1). Will consider adding a column in future migration for observability.
- Response Shape: Followed RFC exactly for both endpoints; added rate limit headers for client ergonomics.
- Error Handling: Used existing ErrorHandler middleware and consistent HTTPException usage with 422/404/429 semantics.

## Alternatives Considered

- External Limiter (Redis/SlowAPI): Deferred to keep MVP light; added env-configurable limit and headers to ease migration later.
- UUID Validation for chat_id: Not applied because `conversations.id` is TEXT; validating format would cause false negatives.
- Persisting trigger_source: Requires schema change; postponed to Phase 3/4.