# Phase 3: Multi-User Data Integrity - LLM Implementation Prompt

## Context
You are implementing Phase 3 of the Agent Integration Infrastructure Refactor initiative. This phase focuses on implementing user-scoped duplicate detection to allow legitimate multi-user uploads of the same documents while maintaining data integrity.

## Reference Documents
- **Primary Specification**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/spec_refactor.md` - Review "Data Integrity" sections in Current State and Target State
- **Technical Design**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/rfc.md` - Reference "3. Multi-User Data Integrity" section for database schema updates and implementation approach
- **Implementation Tasks**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/todo.md` - Follow "Phase 3: Multi-User Data Integrity" section for database schema and logic updates

## Key Implementation Areas
Refer to the RFC document section "3. Multi-User Data Integrity" for:
- Database query updates to include user_id in duplicate detection
- Composite index creation for performance optimization
- User isolation implementation in all document operations

## Success Criteria
Implement all acceptance criteria listed in the spec_refactor.md document related to:
- Duplicate upload checks correctly scoping by user_id
- Multiple users able to upload the same document legitimately
- Maintained data integrity across all user operations

## Constraints
- Follow database schema migration considerations outlined in spec_refactor.md risks section
- Ensure user isolation as specified in rfc.md security considerations
- Complete all Phase 3 tasks listed in todo.md before proceeding to Phase 4