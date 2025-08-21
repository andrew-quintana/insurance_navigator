# Phase 4 Execution Prompt: OpenAI Real Integration

## Session Setup
Run `/clear` to start fresh, then execute this phase.

## Required Reading
**IMPORTANT**: Read these documents completely before starting implementation:

1. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001_phase1_handoff.md` - Service router infrastructure
2. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001_phase2_handoff.md` - Upload flow mock validation
2.5. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001_phase2.5_handoff.md` - Upload flow integrated validation
3. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001_phase3_handoff.md` - LlamaParse mock integration
3.5. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001_phase3.5_handoff.md` - LlamaParse api integration
4. `@docs/initiatives/system/upload_refactor/003/TVDb001/RFCTVDb001.md` - OpenAI integration requirements (section 2)
5. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001.md` - Phase 4 section for detailed tasks
6. `@backend/shared/external/openai_client.py` - Existing mock implementation for reference

## Phase Objectives
Implement real OpenAI API integration with batch optimization and cost efficiency:
- Real OpenAI API client with text-embedding-3-small model integration
- Intelligent batch processing for cost optimization and API efficiency
- Token counting and cost calculation accuracy with budget enforcement
- Vector quality validation and consistency checking

## Key Implementation Requirements
- Integrate with service router and cost tracker from Phase 1
- Implement efficient batch processing with optimal token usage
- Add comprehensive vector quality validation (dimension 1536)
- Ensure seamless integration with existing chunking pipeline from 003

## Success Criteria
- Real OpenAI integration generates embeddings with correct dimensions and quality
- Batch processing optimizes cost while maintaining processing efficiency
- Token counting and cost tracking provide accurate usage monitoring
- Service router seamlessly switches between real and mock OpenAI services

## Expected Deliverables
Follow the Phase 4 checklist in TODOTVDb001.md exactly. Create these outputs:
- `TODOTVDb001_phase4_notes.md` - Implementation details and decisions
- `TODOTVDb001_phase4_decisions.md` - Technical decisions and rationale
- `TODOTVDb001_phase4_handoff.md` - Requirements for Phase 5
- `TODOTVDb001_phase4_testing_summary.md` - Test results and coverage

## Implementation Approach
Use the detailed task breakdown in TODOTVDb001.md Phase 4 section. Focus on creating a cost-efficient OpenAI client that maximizes batch processing while maintaining vector quality and integrating seamlessly with existing infrastructure.

Start by reviewing Phase 1-3 outputs, then follow the Phase 4 checklist systematically.