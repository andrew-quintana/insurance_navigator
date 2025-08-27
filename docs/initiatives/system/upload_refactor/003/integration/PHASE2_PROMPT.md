# Phase 2: Development Environment Testing - Cursor Agent Prompt

## Objective  
Test integrated system with real LlamaParse and OpenAI APIs in development environment. Execute cyclical debug→fix→real API test approach until all tests pass with actual external services.

## Required Reading
**Read these documents and Phase 1 deliverables:**
- `docs/initiatives/system/upload_refactor/003/integration/PRD001.md` - Product requirements and success criteria
- `docs/initiatives/system/upload_refactor/003/integration/RFC001.md` - Technical architecture sections 4.1-4.3
- `docs/initiatives/system/upload_refactor/003/integration/TODO001.md` - Phase 2 tasks (P2.1-P2.6)
- `TODO001_phase1_handoff.md` - Phase 1 deliverables and any issues to address

## Key Implementation Tasks
1. **Real API Configuration**: Replace mock services with real LlamaParse and OpenAI APIs
2. **Environment Validation**: Ensure development environment handles real API responses and timing
3. **Performance Testing**: Validate response times with actual external service latency
4. **Error Handling**: Test integration resilience with real API failures and rate limits
5. **Quality Validation**: Confirm agent conversation quality using real processed embeddings

## Success Criteria
- All Phase 1 functionality works with real APIs
- Performance targets maintained: <90s upload-to-queryable, <3s agent responses  
- >95% integration test pass rate with real services
- Agent responses maintain >95% accuracy referencing processed documents

## Documentation to Create
After completing Phase 2, create these files:
- `TODO001_phase2_notes.md` - Real API integration implementation summary
- `TODO001_phase2_decisions.md` - Technical decisions and API-specific configurations
- `TODO001_phase2_testing_summary.md` - Real API testing results and performance validation
- `TODO001_phase2_handoff.md` - Phase deliverables and Phase 3 requirements

## Technical Focus
- Real LlamaParse API integration for document processing
- Real OpenAI API integration for embeddings and agent conversations
- Performance impact assessment of real vs mock services
- Error handling and retry mechanisms for external API failures
- Rate limiting and API key management

Build on Phase 1 foundation. Address any technical debt identified in Phase 1 handoff documentation.