# Phase 3: Multi-User Data Integrity - LLM Implementation Prompt

## Context
You are implementing Phase 3 of the Agent Integration Infrastructure Refactor initiative. This phase focuses on implementing document row duplication system to allow multiple users to upload the same document content while maintaining separate user-scoped document entries and preserving existing processing data.

## Reference Documents
- **Primary Specification**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/scoping/spec_refactor.md` - Review "Data Integrity" sections in Current State and Target State
- **Technical Design**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/scoping/rfc.md` - Reference "3. Multi-User Data Integrity" section for document row duplication implementation
- **Implementation Tasks**: `@docs/initiatives/agents/integration/phase3/bulk_refactor/scoping/todo.md` - Follow "Phase 3: Document Row Duplication System" section for implementation tasks

## Key Implementation Areas
Refer to the RFC document section "3. Multi-User Data Integrity" for:
- Document row duplication logic when same content is uploaded by different users
- Content hash-based duplicate detection and document copying
- Preservation of document_chunks relationships through proper document_id references
- RAG functionality maintenance through normalized table relationships

## Success Criteria
Implement all acceptance criteria listed in the spec_refactor.md document related to:
- Document row duplication creating separate user-scoped document entries
- Multiple users able to upload same content with their own document rows
- RAG functionality preserved through proper document-chunk relationships
- Existing processing data preserved when duplicating documents

## Constraints
- Follow database schema migration considerations outlined in spec_refactor.md risks section
- Ensure user isolation as specified in rfc.md security considerations
- Complete all Phase 3 tasks listed in todo.md before proceeding to Phase 4