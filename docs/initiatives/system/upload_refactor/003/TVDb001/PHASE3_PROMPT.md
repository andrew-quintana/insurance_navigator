# Phase 3 Execution Prompt: LlamaParse Real Integration

## Session Setup
Run `/clear` to start fresh, then execute this phase.

## Required Reading
**IMPORTANT**: Read these documents completely before starting implementation:

1. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001_phase1_handoff.md` - Phase 1 infrastructure
2. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001_phase2_handoff.md` - Phase 2 upload flow
3. `@docs/initiatives/system/upload_refactor/003/TVDb001/RFCTVDb001.md` - LlamaParse integration requirements (section 1)
4. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001.md` - Phase 3 section for detailed tasks
5. `@backend/shared/external/llamaparse.py` - Existing mock implementation for reference

## Phase Objectives
Implement real LlamaParse API integration with comprehensive security and cost controls:
- Real LlamaParse API client with authentication and rate limiting
- Secure webhook callback handling with HMAC signature verification
- Cost tracking integration with daily budget enforcement
- Service router integration for seamless real/mock switching

## Key Implementation Requirements
- Integrate with service router and cost tracker from Phase 1
- Implement secure webhook handling with signature verification  
- Add comprehensive error handling for API failures and timeouts
- Maintain compatibility with existing 003 webhook processing

## Success Criteria
- Real LlamaParse integration processes documents successfully in local environment
- Webhook callbacks are received and verified correctly
- Rate limiting and cost controls prevent API abuse and budget overruns
- Service router seamlessly switches between real and mock LlamaParse services

## Expected Deliverables
Follow the Phase 3 checklist in TODOTVDb001.md exactly. Create these outputs:
- `TODOTVDb001_phase3_notes.md` - Implementation details and decisions
- `TODOTVDb001_phase3_decisions.md` - Technical decisions and rationale
- `TODOTVDb001_phase3_handoff.md` - Requirements for Phase 4
- `TODOTVDb001_phase3_testing_summary.md` - Test results and coverage

## Implementation Approach
Use the detailed task breakdown in TODOTVDb001.md Phase 3 section. Focus on creating a production-ready LlamaParse client that integrates seamlessly with the existing infrastructure while adding real service capabilities.

Start by reviewing Phase 1-2 outputs, then follow the Phase 3 checklist systematically.