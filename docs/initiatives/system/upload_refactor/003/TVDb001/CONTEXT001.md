CONTEXT.md – Real API Integration Testing & Debugging Guide

Request Type: Testing & Debugging
Purpose: Guide for implementing, validating, and debugging the real API integrations in the document processing pipeline.
Project Relationship: This is a successor project to the Upload Refactor 003. It uses the learnings and architecture from 003 but represents a new effort focused specifically on validating real service integrations in a local development environment. Documentation for 003 can be found under @docs/initiatives/system/upload_refactor/003

⸻

Overview

This document serves two purposes:
	1.	Implementation Guide – It provides clear, scoped guidance for integrating LlamaParse, OpenAI, and the local chunking service into the existing local pipeline for real-world validation and debugging.
	2.	Context Reference – It acts as the canonical context for any agents, coders, or systems working on this testing effort. It assumes 003 Upload Refactor is completed and stable, and will reference its behavior as a correctness baseline.

⸻

What This Testing Effort Is (and Isn’t)

This is:
	•	A scoped validation of replacing mock services with real APIs
	•	A local-only test suite using Dockerized infrastructure
	•	An implementation and debugging workflow for each API call
	•	A chance to verify webhook delivery, chunking correctness, and embedding behavior
	•	The groundwork for production pipeline readiness

This is NOT:
	•	A production deployment or rollout
	•	A request to modify the database schema or state machine
	•	A feature expansion or architecture change
	•	An observability or agent-trigger integration request

⸻

Implementation Goals (Cross-check with 003)

Use this section to double-check the functional requirements established in 003, now applied to real services:

| Stage             | 003 Mock Behavior                         | Real Service Target Behavior                          |
|------------------|--------------------------------------------|--------------------------------------------------------|
| Upload Triggering | Triggers webhook via mock                 | Triggers webhook from actual LlamaParse callback       |
| Parsing           | Returns markdown from test fixture        | Returns real markdown from LlamaParse API              |
| Chunking          | Chunked text based on mock markdown       | Real parsing output chunked with metadata retained     |
| Embedding         | Embeds mock vectors from fixture          | Real OpenAI vectors generated in batches               |
| Vector Storage    | Stores vectors in buffer table            | Same behavior, verified for correctness and limits     |
| Finalization      | Transitions document to ‘complete’ state  | Same, with all transitions logged and monitored        |


Milestones & Phase Plan

Each service follows a 2-step milestone: test setup and test execution/debugging.

| Phase                  | Milestone Type           | Description                                   |
|------------------------|--------------------------|-----------------------------------------------|
| Phase 1A               | Setup                    | Upload initialization, signed URL flow        |
| Phase 1B               | Debug                    | Verify upload triggers pipeline correctly     |
| Phase 2A               | Setup                    | LlamaParse integration                        |
| Phase 2B               | Debug                    | Validate real markdown extraction             |
| Phase 3A               | Setup                    | Chunking from real parsed content             |
| Phase 3B               | Debug                    | Confirm chunking logic with real input        |
| Phase 4A               | Setup                    | OpenAI real embedding integration             |
| Phase 4B               | Debug                    | Validate real embeddings and vector storage   |
| Phase 5A               | Setup                    | Full pipeline from upload → embed             |
| Phase 5B               | Debug                    | Test fallback behavior, recovery, rate limits |
| Phase 6A               | Setup                    | Render/Vercel integration prep (placeholder)  |
| Phase 6B               | Debug                    | Future phase - not implemented now            |
| Phase 7                | Documentation            | Technical debt log and next-phase setup       |

Integration Points

| Service        | Integration Notes |
|----------------|------------------|
| LlamaParse     | Use real API and webhooks, verify Markdown output, simulate 429 |
| Chunking       | Ensure content is passed post-parsing, verify chunk density and structure |
| OpenAI         | Use `text-embedding-3-small`, batch inputs, log token counts |
| Supabase       | Maintain current schema and buffer logic, validate vector insertions |

Each behavior must be tested for:
	•	Correct flow from one stage to the next
	•	Error handling consistent with 003 fallback logic
	•	Output format matches production schema expectations
	•	Performance tolerances acceptable for development

⸻

Environment Assumptions
	•	Dockerized local dev environment with Supabase and FastAPI worker
	•	All .env values are configured with real API keys
	•	Logs are accessible locally; no external logging/observability yet
	•	Rate-limiting constraints respected by all integrations

⸻

Real API Integration Steps
	1.	Replace Mock Endpoints
	•	LlamaParse: Use real API endpoint and handle real webhook delivery
	•	OpenAI: Replace mock embedding with real batch-encoded calls
	2.	Implement Fallback & Debugging
	•	Ensure retry logic exists and handles 429s or timeouts
	•	Log all failures locally with correlation IDs
	3.	Test and Validate in Phases
	•	Parse → Chunk → Embed → Finalize
	•	Validate each step independently and end-to-end
	4.	Compare Against 003 Behavior
	•	Validate output of real services against mock expectations
	•	Identify any changes needed to account for real-world response quirks

⸻

Testing Checklist
	•	Upload simulated via client server and interacts with components correctly per 003
	•	LlamaParse call triggers webhook per 003
	•	Markdown is chunked into valid units with metadata
	•	Embeddings are generated with correct batching
	•	Vectors are inserted into vectors table with correct document linkage
	•	State machine transitions from parsed to embedded to complete
	•	Errors are logged with retry attempts and timestamps
	•	Local dashboard/logs reflects pipeline activity accurately

⸻

Constraints
	•	Single-user testing only
	•	No concurrent document processing
	•	No modifications to Supabase schema
	•	Vercel or Render orchestration in this initiative only in ways that a coding agent can test and debug autonomously

⸻

Success Criteria
	•	All real service integrations behave identically or better than mocks
	•	No manual intervention required for pipeline to complete
	•	Failures handled gracefully and retryable
	•	Local monitoring reflects real API activity
	•	Output artifacts (markdown, chunks, vectors) are valid and consistent

⸻

Open Questions
	•	Should failed webhook calls be retried automatically or manually?
    automatically with a proper retry strategy
	•	What is the best way to monitor OpenAI rate limit usage locally?
    limit the amount of requests per a specific window of time
	•	Should vector sizes be validated against mock embedding sizes?
    no vector sizes should be a typical length of 1536 for text-embedding-3-small
	•	How do we log correlation IDs across all steps for post-mortem debugging?
    reference 003 for how unique ids are created as sha256 or uuids depending on the stage and table

⸻

Notes for Future Phases
	•	Keep mock services available for local fallback
	•	Consider adding agent validation or auto-debug triggers later
	•	Use this phase to gather usage and failure patterns before production logic

⸻

Reminder: This testing context is scoped, controlled, and focused on validating real-world external service behavior in isolation. It should not be used to trigger upstream or downstream system changes without explicit coordination.