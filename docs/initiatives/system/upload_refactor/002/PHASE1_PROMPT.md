# Phase 1 Execution Prompt: Infrastructure & Buffer Tables

## Context
You are implementing Phase 1 of the 002 Worker Refactor iteration. This phase establishes the foundation for the unified BaseWorker architecture with buffer-driven pipeline orchestration.

## Documentation References
Please review these documents before starting implementation:
- `@docs/initiatives/system/upload_refactor/002/CONTEXT002.md` - Core architecture and data model
- `@docs/initiatives/system/upload_refactor/002/TODO002.md` - Detailed implementation checklist (Phase 1 section)
- `@docs/initiatives/system/upload_refactor/002/RFC002.md` - Technical design specifications
- `@docs/initiatives/system/upload_refactor/002/PRD002.md` - Product requirements and acceptance criteria

## Primary Objective
Implement the foundational infrastructure for the BaseWorker architecture including:
1. Enhanced database schema with buffer tables
2. Directory restructuring for better separation of concerns  
3. Shared utilities for deterministic operations
4. Buffer management foundation

## Key Implementation Requirements

### Database Schema Updates
- Update `upload_jobs` table with new status values and enhanced progress tracking
- Create `document_chunk_buffer` table for chunk staging with deterministic IDs
- Create `document_vector_buffer` table for embedding staging with integrity verification
- Add efficient indexes for worker polling and progress queries

### Directory Restructuring
- Reorganize codebase into `backend/api/`, `backend/workers/`, `backend/shared/`
- Move existing worker code to new structure while preserving functionality
- Create shared utility modules for database, storage, and external service clients

### Deterministic Operations
- Implement UUIDv5 generation with namespace `6c8a1e6e-1f0b-4aa8-9f0a-1a7c2e6f2b42`
- Create chunk ID generation using format: `{document_id}:{chunker_name}:{chunker_version}:{chunk_ord}`
- Build content hashing utilities for chunk and vector integrity verification

### Buffer Management
- Implement idempotent buffer write operations with `ON CONFLICT DO NOTHING`
- Create buffer cleanup and archival processes
- Develop progress tracking utilities with atomic updates

## Expected Outputs
Document your work in these files:
- `@TODO002_phase1_notes.md` - Implementation details and decisions
- `@TODO002_phase1_decisions.md` - Architectural choices and rationale
- `@TODO002_phase1_handoff.md` - API implementation requirements for Phase 2
- `@TODO002_phase1_testing_summary.md` - Test results and validation

## Success Criteria
- All database schema changes deployed successfully
- Directory structure reorganized with proper import updates
- Deterministic operations validated for consistency
- Buffer operations tested for idempotency
- Comprehensive test coverage for all new utilities

## Implementation Notes
- Focus on idempotency and crash recovery throughout
- Use the detailed checklist in TODO002.md as your implementation guide
- Ensure all operations are atomic and can handle concurrent access
- Document any deviations from the original design with clear rationale

Start by reading the referenced documentation thoroughly, then proceed with the implementation following the detailed checklist in the TODO document.