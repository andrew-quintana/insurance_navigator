# @TODO001_phase3_handoff.md — Phase 3 Handoff

## Components

- Agent: `agents/tooling/mcp/memory/summarizer_agent.py`
  - Class: `MemorySummarizerAgent`
  - Schema: `agents/tooling/mcp/memory/types.py` (`MemorySummary`)
- Worker: `scripts/workers/memory_processor.py`
  - Entry: `python -m scripts.workers.memory_processor`

## Environment

- `ANTHROPIC_API_KEY` (optional; mock mode when missing)
- `ANTHROPIC_MODEL` (default `claude-3-haiku-20240307`)
- `USE_MOCK_LLM` (default `true`)
- `MEMORY_TOKEN_LIMIT` (default `8000`)
- `MEMORY_PROCESSOR_IDLE_SLEEP` (default `2.0` seconds)

## Usage

- Start worker locally:
  - `USE_MOCK_LLM=true python -m scripts.workers.memory_processor`
- Workflow:
  1. API `POST /api/v1/memory/update` enqueues context
  2. Worker polls `chat_context_queue` for `pending_summarization`
  3. Summarizer merges prior memory + new snippet
  4. Worker upserts `chat_metadata` and marks queue `complete`

## Testing

- Unit tests (no external services required):
  - `pytest -m unit tests/agents/test_memory_summarizer_agent.py -q`
  - `pytest -m unit tests/workers/test_memory_processor.py -q`

## Notes

- Exceeded size: when tokens > `MEMORY_TOKEN_LIMIT`, `general_summary` is replaced with a start-new-chat guidance string and persisted; status set to `complete`.
- Observability: Logging included; add metrics later if needed.