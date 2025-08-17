# Phase 3 Execution Prompt: BaseWorker Implementation

## Context
You are implementing Phase 3 of the 002 Worker Refactor iteration. This phase implements the unified BaseWorker class that orchestrates all processing stages through a state machine, replacing the specialized worker architecture.

## Documentation References
Please review these documents before starting implementation:
- `@docs/initiatives/system/upload_refactor/002/CONTEXT002.md` - BaseWorker orchestration pattern and state machine
- `@docs/initiatives/system/upload_refactor/002/TODO002.md` - Detailed implementation checklist (Phase 3 section)
- `@docs/initiatives/system/upload_refactor/002/RFC002.md` - Technical design for worker architecture
- `@TODO002_phase2_notes.md` - Phase 2 webhook implementation details
- `@TODO002_phase2_decisions.md` - Previous security and API decisions
- `@TODO002_phase2_handoff.md` - BaseWorker requirements from Phase 2

## Primary Objective
Implement the unified BaseWorker class with state machine processing including:
1. Core BaseWorker framework with job polling and state machine routing
2. Parse validation stage with content normalization and duplicate detection
3. Chunking stage with deterministic chunk generation and buffer persistence
4. Micro-batch embedding stage with OpenAI integration and rate limiting
5. External service integration with comprehensive error handling

## Key Implementation Requirements

### BaseWorker Core Framework
- Implement BaseWorker class with state machine processing logic
- Create efficient job polling mechanism with `FOR UPDATE SKIP LOCKED`
- Add stage-specific processing methods with atomic transitions
- Implement comprehensive error handling, retry scheduling, and dead letter processing

### Parse Validation Stage
- Validate parsed content and compute normalized SHA256 hashes
- Handle duplicate detection and canonical path assignment
- Implement atomic status transition from `parsed` to `parse_validated`
- Add detailed logging and error reporting with correlation IDs

### Chunking Stage Processing
- Generate deterministic chunks with UUIDv5 identifiers using canonical strings
- Write chunks to `document_chunk_buffer` with idempotent `ON CONFLICT DO NOTHING` operations
- Update job status to `chunks_stored` after successful buffer writes
- Validate chunk counts and content integrity against expected values

### Micro-Batch Embedding Stage
- Implement OpenAI API client with rate limiting and comprehensive retry logic
- Process embeddings in micro-batches (up to 256 vectors) with immediate buffer persistence
- Update progress counters atomically per batch in `upload_jobs.progress`
- Handle embedding failures and partial completion scenarios with resume capability

### External Service Integration
- Integrate token bucket rate limiting for OpenAI API calls
- Implement circuit breaker patterns for external service failures
- Add exponential backoff retry logic with maximum retry limits
- Create cost tracking and monitoring for external API usage

## Expected Outputs
Document your work in these files:
- `@TODO002_phase3_notes.md` - BaseWorker implementation details and processing patterns
- `@TODO002_phase3_decisions.md` - Processing architecture decisions and trade-offs
- `@TODO002_phase3_handoff.md` - Integration testing requirements and validation criteria for Phase 4
- `@TODO002_phase3_testing_summary.md` - Performance testing results and optimization findings

## Success Criteria
- BaseWorker processes all job stages from `parsed` through `complete` status
- Micro-batch embedding processes large documents efficiently within memory limits
- All operations are idempotent and can resume from any failure point
- Rate limiting and circuit breaker patterns handle external service failures gracefully
- Performance tests demonstrate linear scaling with additional worker instances

## Implementation Notes
- Follow the exact state machine transitions defined in CONTEXT002.md
- Implement the BaseWorker processing loop pattern from the documentation
- Use deterministic UUIDv5 generation with the specified namespace
- Ensure all buffer operations are atomic and tied to status updates
- Use the detailed checklist in TODO002.md Phase 3 section as your implementation guide
- Focus on memory efficiency for large document processing
- Document any performance optimizations or design decisions

Start by reading all referenced documentation and previous phase outputs, then implement the BaseWorker following the state machine pattern and processing requirements.