# MVP RAG System - Phase 1 Architectural Decisions

## Technology Choices
- Used Python 3.11+ with asyncpg for direct PostgreSQL/pgvector access (for performance and control)
- Avoided ORM/abstraction layers for retrieval path to minimize latency
- Used dataclasses for config and chunk structures for clarity and type safety

## Patterns
- Property-based lazy initialization for agent integration (compatible with BaseAgent)
- User-scoped access enforced at query level for multi-tenant security
- Token budget enforced in Python for flexibility

## Trade-offs
- Chose direct SQL/asyncpg over Supabase Python client for retrieval speed and fine-grained control
- MVP does not include plugin/expander architecture (kept for future phases)
- No analytics/logging plugins in MVP (to be added in later phases)

## Rationale
- Simplicity and performance prioritized for baseline
- All design choices made to enable rapid future extension and experimentation 

## Testing Decisions
- Included both unit tests (with DB mocking) and a real integration test with live Supabase/Postgres data.
- Rationale: Ensures the MVP baseline is validated both in isolation and in a real environment, increasing confidence in correctness and readiness for future experiments. 