# TODO001: Admin Regulatory Document Management MVP Implementation

## Document Context
- **Version**: TODO001.md (MVP Scope)
- **Created**: 2025-01-25
- **References**: 
  - PRD001_admin_regulatory_documents.md (requirements)
  - RFC001_admin_regulatory_documents.md (technical design)
- **Project**: Insurance Navigator Platform - Admin Document Management MVP
- **Implementation Approach**: Minimal viable implementation for core regulatory document functionality

## MVP Scope Definition

**Core MVP Requirements:**
- Admin can upload regulatory documents (basic functionality only)
- Documents processed through existing pipeline with document_type differentiation
- Users can access regulatory documents (read-only)
- Basic search functionality to find regulatory documents
- Essential security (admin role check, basic RLS policies)

**MVP Success Criteria:**
- [x] Admin upload works with document_type = 'regulatory_document'
- [x] Existing user upload pipeline unaffected
- [x] Users can search and view regulatory documents
- [x] Basic admin/user permission separation functional

**RFC Technical Approach (MVP Focused):**
- Minimal database extension: document_type enum only
- Upload-handler enhancement for role check and document_type setting
- Basic RLS policies for document access
- Reuse existing search functionality with document_type filtering

## MVP Implementation Constraints

**Timeline:** 1-2 weeks for MVP core functionality
**Resource Availability:** Single developer, existing Supabase infrastructure
**Technical Limitations:** Must not break existing functionality, minimal UI changes
**MVP Focus:** Core upload/access functionality only, advanced features deferred

## MVP Validation Requirements

**Essential Acceptance Criteria:**
- [x] Admin can upload documents with regulatory_document type
- [x] Documents processed through existing pipeline unchanged
- [x] Users can view regulatory documents (basic access)
- [x] Basic admin/user permission separation works
- [x] Existing user uploads continue functioning normally

---

# MVP Implementation Plan (2 Phases)

## Phase 1: Core Backend Implementation (Database + API)

### Prerequisites
- Files to read:
  - `@supabase/migrations/20250708000000_init_db_tables.sql` (current schema)
  - `@supabase/functions/upload-handler/index.ts` (current upload implementation)
- Previous phase outputs: None (first phase)
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session. You are implementing MVP Phase 1 - core backend functionality for regulatory documents.

**MVP Goal**: Enable basic admin upload of regulatory documents and user access with minimal changes.

**Current State**: 
- Existing documents table stores user uploads
- Upload-handler processes user documents through pipeline
- Basic JWT authentication exists

**Phase 1 MVP Scope**:
- Add document_type enum to database (minimal extension)
- Enhance upload-handler for admin role check and document_type
- Add basic RLS policy for regulatory document access
- Test core upload/access functionality

### Tasks

#### Minimal Database Extension
1. [x] Create migration: `20250125000000_add_document_type_mvp.sql`
2. [x] Add document_type enum: `('user_document', 'regulatory_document')`
3. [x] Add single column to documents table: `document_type` (default 'user_document')
4. [x] Add basic index on document_type
5. [x] Migrate existing documents to 'user_document' type

#### Basic Upload Handler Enhancement
1. [x] Modify `/supabase/functions/upload-handler/index.ts`:
   - Add simple admin role check from JWT user_metadata
   - Parse documentType from form data 
   - Set document_type field when creating document record
   - Maintain full backward compatibility for user uploads
2. [x] Test admin upload sets regulatory_document type
3. [x] Test user upload continues as user_document type

#### Essential RLS Policy
1. [x] Update existing RLS policies to handle document_type
2. [x] Add policy: users can read regulatory_documents
3. [x] Add policy: admins can insert regulatory_documents
4. [x] Test basic access control works

### Expected Outputs
- [x] Save implementation notes to: `@TODO001_phase1_notes.md`
- [x] Document database migration decisions in: `@TODO001_phase1_decisions.md`  
- [x] List any issues/blockers for Phase 2 in: `@TODO001_phase1_handoff.md`

### Progress Checklist

#### Setup
- [x] Review current database schema and existing migrations
- [x] Review current upload-handler implementation
- [x] Review existing RLS policies

#### MVP Database Changes
- [x] Create migration file for document_type enum
- [x] Add document_type column to documents table
- [x] Create index on document_type field
- [x] Write data migration for existing documents
- [x] Test migration in development environment

#### Upload Handler Enhancement
- [x] Add admin role detection from JWT user_metadata
- [x] Add documentType parsing from form data
- [x] Update document creation to include document_type
- [x] Test admin upload creates regulatory_document
- [x] Test user upload continues as user_document
- [x] Verify existing processing pipeline unaffected

#### Basic RLS Policies
- [x] Update existing policies to handle document_type
- [x] Add policy for users to read regulatory documents
- [x] Add policy for admins to insert regulatory documents
- [x] Test policy enforcement with test users

#### MVP Validation
- [x] Test complete admin upload flow
- [x] Test user access to regulatory documents
- [x] Verify existing user functionality unchanged
- [x] Confirm processing pipeline works for both document types

#### Documentation
- [x] Save `@TODO001_phase1_notes.md`
- [x] Save `@TODO001_phase1_handoff.md`

---

## Phase 2: Minimal Frontend Access (MVP UI)

### Prerequisites
- Files to read:
  - `@TODO001_phase1_notes.md` (backend implementation results)
  - `@TODO001_phase1_handoff.md` (backend integration details)
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session continuing MVP Phase 2 - minimal UI for regulatory document access.

**Previous Phase Results**: Backend completed with document_type support, admin upload capability, and basic RLS policies.

**MVP Phase 2 Goal**: Complete backend and validation tasks. All UI-related tasks are deferred and tracked in `regulatory_ui_update.md` in this directory.

**Scope**:
- No UI changes in this phase. All UI enhancements are deferred.
- Focus on backend validation, integration testing, and documentation.

### Tasks

#### Backend Validation & Documentation
1. [x] Review Phase 1 backend implementation and integration points
2. [x] Validate that admin upload and user access work via API (no UI changes)
3. [x] Confirm RLS policies and document_type logic function as intended
4. [x] Document any issues, blockers, or integration notes for UI phase
5. [x] Save implementation notes to: `@TODO001_phase2_notes.md`
6. [x] Create MVP completion summary in: `@TODO001_phase2_completion.md`

#### Deferred UI Tasks
- [ ] All UI-related tasks (admin upload UI, user access UI, indicators, etc.) are now tracked in `regulatory_ui_update.md` in this directory.

### Progress Checklist

#### Setup
- [x] Review Phase 1 backend implementation
- [x] Review integration points and API endpoints

#### Backend Validation
- [x] Validate admin upload via API (no UI)
- [x] Validate user access to regulatory documents via API (no UI)
- [x] Confirm RLS and document_type logic
- [x] Document any issues/blockers for UI phase

#### Documentation
- [x] Save `@TODO001_phase2_notes.md`
- [x] Save `@TODO001_phase2_completion.md`

---

# MVP Completion Checklist

## Phase 1: Core Backend Implementation
- [x] Document type enum created (user_document, regulatory_document)
- [x] Documents table extended with document_type column
- [x] Basic index on document_type implemented
- [x] Upload-handler enhanced for admin role check and document_type
- [x] Basic RLS policies for regulatory document access
- [x] Data migration completed for existing documents
- [x] Phase 1 documentation saved

## Phase 2: Backend Validation (UI Deferred)
- [x] Backend validation of admin upload and user access completed (API only)
- [x] RLS/document_type logic confirmed
- [x] Issues/blockers for UI phase documented
- [x] Phase 2 documentation saved

## Deferred: UI Enhancements
- [ ] All UI tasks moved to `regulatory_ui_update.md` in this directory

## MVP Sign-off

### Essential Requirements Met
- [x] Admin can upload documents with regulatory_document type (API)
- [x] Documents processed through existing pipeline unchanged
- [x] Users can access regulatory documents (API)
- [x] Basic admin/user permission separation works
- [x] Existing user uploads continue functioning normally

### MVP Validation
- [x] Test complete admin upload flow (API)
- [x] Test user access to regulatory documents (API)
- [x] Verify existing user functionality unchanged
- [x] Confirm processing pipeline works for both document types
- [x] Basic error handling functional

### MVP Success Criteria
- [x] Admin upload works with document_type = 'regulatory_document' (API)
- [x] Existing user upload pipeline unaffected
- [x] Users can access regulatory documents (API)
- [x] Basic admin/user permission separation functional

**MVP Status**: [x] Core regulatory document backend functionality implemented and ready for UI integration

---

*All UI-related tasks for regulatory document management are now deferred and tracked in `regulatory_ui_update.md` in this directory. This file will be updated when UI work resumes.*