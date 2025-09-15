# Phase 4: RAG Performance & Observability - LLM Implementation Prompt

## Context
You are implementing Phase 4 of the Agent Integration Infrastructure Refactor initiative. This phase focuses on optimizing RAG similarity thresholds and implementing enhanced observability with histogram logging. **Note: RAG performance speed is non-critical for this initiative.**

## Reference Documents
- **Primary Specification**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/scoping/spec_refactor.md` - Review "RAG Configuration" and "Observability" sections in Current State and Target State
- **Technical Design**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/scoping/rfc.md` - Reference "4. RAG Performance Optimization" and "5. Enhanced Observability" sections for implementation details
- **Implementation Tasks**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/scoping/todo.md` - Follow "Phase 4: RAG Performance & Observability" section for threshold and logging implementation

## Key Implementation Areas
Refer to the RFC document sections "4. RAG Performance Optimization" and "5. Enhanced Observability" for:
- Similarity threshold configuration update to 0.3
- Configurable per-user/context threshold management
- Similarity histogram logging implementation with UUIDs
- Performance monitoring and traceability systems

## Success Criteria
Implement all acceptance criteria listed in the spec_refactor.md document related to:
- RAG similarity threshold set to 0.3 across all configurations
- INFO logs including cosine similarity histograms with clear UUID traceability
- RAG functionality remaining stable (performance speed is non-critical)

## Constraints
- Performance speed optimization is explicitly non-critical for this phase
- Focus on observability and threshold tuning rather than speed improvements
- Complete all Phase 4 tasks listed in todo.md before proceeding to Phase 5