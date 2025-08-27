# Phase 1: Mock Integration Setup & Testing - Cursor Agent Prompt

## Objective
Establish integration between 003 upload infrastructure and agent systems using mock services. Follow cyclical debug→fix→mock test approach until end-to-end mock testing passes.

## Required Reading
**Read these documents first to understand the complete requirements:**
- `docs/initiatives/system/upload_refactor/003/integration/PRD001.md` - Product requirements and success criteria
- `docs/initiatives/system/upload_refactor/003/integration/RFC001.md` - Technical architecture and implementation approach  
- `docs/initiatives/system/upload_refactor/003/integration/TODO001.md` - Phase 1 detailed tasks (P1.1-P1.7)

## Key Implementation Tasks
1. **Integrated Environment Setup**: Configure Docker environment with mock LlamaParse and OpenAI services
2. **Agent RAG Integration**: Configure agent system to query `upload_pipeline` vectors directly via pgvector
3. **End-to-End Flow**: Implement document upload → processing → agent conversation using mock services
4. **Cyclical Testing**: Debug→fix→test cycle until all integration tests pass
5. **Performance Validation**: Ensure <90 second upload-to-queryable and <3 second agent responses

## Success Criteria
- Complete upload→agent conversation flow works with mock services
- Agent responses accurately reference processed document content >95%
- Integration tests pass >95% reliably
- Performance targets met consistently

## Documentation to Create
After completing Phase 1, create these files:
- `TODO001_phase1_notes.md` - Implementation summary and key activities
- `TODO001_phase1_decisions.md` - Technical decisions made and rationale  
- `TODO001_phase1_testing_summary.md` - Testing results and validation outcomes
- `TODO001_phase1_handoff.md` - Phase deliverables and Phase 2 requirements

## Technical Focus
- Direct vector access via `upload_pipeline.document_chunks` table
- pgvector semantic search queries (see RFC001.md section 3.2.2)
- Mock service coordination for consistent behavior
- User-scoped access control validation

Prioritize getting the integration working over optimization. Use cyclical development approach throughout.