# @TODO001_phase3_decisions.md — Phase 3 Design Decisions

- **Agent Pattern**: Implemented `MemorySummarizerAgent` inheriting `BaseAgent` to reuse prompt-formatting and Pydantic validation patterns.
- **Model Choice**: Default `claude-3-haiku-20240307` via Anthropic SDK if `ANTHROPIC_API_KEY` is available; mock mode otherwise to keep tests fast and free.
- **Token Counting**: Used `utils.performance_metrics.estimate_tokens` heuristic to avoid adding heavy tokenizer dependencies.
- **Size Limit Behavior**: When token count exceeds `MEMORY_TOKEN_LIMIT`, we still persist fields but replace `general_summary` with a "start a new chat" guidance string to satisfy RFC size management.
- **Queue Processing**: Simple loop with short idle sleep and FIFO processing via `created_at` ASC from service. Retry by incrementing `retry_count` and leaving status as `pending_summarization`.
- **Error Handling**: Anthropic output parsed as JSON; on failure, treated as string summary and validated by schema to avoid crashes.
- **Observability**: Logging integrated at worker level; hooks available to attach metrics later.

## Alternatives Considered

- **Exact Tokenizer (e.g., tiktoken)**: Skipped for MVP simplicity; heuristic sufficient. Can be swapped later.
- **Dedicated Worker Queue**: Deferred in favor of sequential processor to match RFC MVP.
- **Persisting `trigger_source`**: Deferred to Phase 4+ per notes in Phase 2 handoff.