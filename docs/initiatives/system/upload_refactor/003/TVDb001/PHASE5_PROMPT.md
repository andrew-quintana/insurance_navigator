# Phase 5 Execution Prompt: Enhanced BaseWorker Integration

## Session Setup
Run `/clear` to start fresh, then execute this phase.

## Required Reading
**IMPORTANT**: Read these documents completely before starting implementation:

1. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001_phase1-4_handoff.md` - All previous phase outputs
2. `@docs/initiatives/system/upload_refactor/003/TODO003_phase3_notes.md` - Original BaseWorker reference
3. `@docs/initiatives/system/upload_refactor/003/TVDb001/RFCTVDb001.md` - BaseWorker enhancement requirements (section 5)
4. `@docs/initiatives/system/upload_refactor/003/TVDb001/TODOTVDb001.md` - Phase 5 section for detailed tasks
5. `@backend/workers/base_worker.py` - Existing 003 BaseWorker implementation

## Phase Objectives
Integrate real service clients with existing BaseWorker for seamless processing:
- Service router integration for dynamic service selection during processing
- Enhanced error handling for real service failures with fallback mechanisms
- Cost limit and service unavailability handling with proper job management
- Comprehensive monitoring and logging for real service operations

## Key Implementation Requirements
- Integrate all previous phases (service router, upload flow, LlamaParse, OpenAI)
- Maintain compatibility with existing 003 BaseWorker architecture
- Implement robust error handling for cost limits and service unavailability
- Add correlation ID tracking throughout the entire processing pipeline

## Success Criteria
- Enhanced BaseWorker processes jobs with both real and mock services seamlessly
- Error handling gracefully manages cost limits and service outages
- Service switching occurs without interrupting job processing
- Monitoring provides comprehensive visibility into real service operations

## Expected Deliverables
Follow the Phase 5 checklist in TODOTVDb001.md exactly. Create these outputs:
- `TODOTVDb001_phase5_notes.md` - Implementation details and decisions
- `TODOTVDb001_phase5_decisions.md` - Technical decisions and rationale
- `TODOTVDb001_phase5_handoff.md` - Requirements for Phase 6
- `TODOTVDb001_phase5_testing_summary.md` - Test results and coverage

## Implementation Approach
Use the detailed task breakdown in TODOTVDb001.md Phase 5 section. Focus on creating a robust integration that brings together all previous phases into a cohesive processing system that maintains 003's reliability while adding real service capabilities.

Start by reviewing all previous phase outputs, then follow the Phase 5 checklist systematically.