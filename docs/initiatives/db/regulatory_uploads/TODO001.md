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
- Admin upload works with document_type = 'regulatory_document'
- Existing user upload pipeline unaffected
- Users can search and view regulatory documents
- Basic admin/user permission separation functional

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
- Admin can upload documents with regulatory_document type
- Documents processed through existing pipeline unchanged
- Users can view regulatory documents (basic access)
- Basic admin/user permission separation works
- Existing user uploads continue functioning normally

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
1. Create migration: `20250125000000_add_document_type_mvp.sql`
2. Add document_type enum: `('user_document', 'regulatory_document')`
3. Add single column to documents table: `document_type` (default 'user_document')
4. Add basic index on document_type
5. Migrate existing documents to 'user_document' type

#### Basic Upload Handler Enhancement
1. Modify `/supabase/functions/upload-handler/index.ts`:
   - Add simple admin role check from JWT user_metadata
   - Parse documentType from form data 
   - Set document_type field when creating document record
   - Maintain full backward compatibility for user uploads
2. Test admin upload sets regulatory_document type
3. Test user upload continues as user_document type

#### Essential RLS Policy
1. Update existing RLS policies to handle document_type
2. Add policy: users can read regulatory_documents
3. Add policy: admins can insert regulatory_documents
4. Test basic access control works

### Expected Outputs
- Save implementation notes to: `@TODO001_phase1_notes.md`
- Document database migration decisions in: `@TODO001_phase1_decisions.md`  
- List any issues/blockers for Phase 2 in: `@TODO001_phase1_handoff.md`

### Progress Checklist

#### Setup
- [ ] Review current database schema and existing migrations
- [ ] Review current upload-handler implementation
- [ ] Review existing RLS policies

#### MVP Database Changes
- [ ] Create migration file for document_type enum
- [ ] Add document_type column to documents table
- [ ] Create index on document_type field
- [ ] Write data migration for existing documents
- [ ] Test migration in development environment

#### Upload Handler Enhancement
- [ ] Add admin role detection from JWT user_metadata
- [ ] Add documentType parsing from form data
- [ ] Update document creation to include document_type
- [ ] Test admin upload creates regulatory_document
- [ ] Test user upload continues as user_document
- [ ] Verify existing processing pipeline unaffected

#### Basic RLS Policies
- [ ] Update existing policies to handle document_type
- [ ] Add policy for users to read regulatory documents
- [ ] Add policy for admins to insert regulatory documents
- [ ] Test policy enforcement with test users

#### MVP Validation
- [ ] Test complete admin upload flow
- [ ] Test user access to regulatory documents
- [ ] Verify existing user functionality unchanged
- [ ] Confirm processing pipeline works for both document types

#### Documentation
- [ ] Save `@TODO001_phase1_notes.md`
- [ ] Save `@TODO001_phase1_handoff.md`

---

## Phase 2: Minimal Frontend Access (MVP UI)

### Prerequisites
- Files to read:
  - Current user interface files for document upload/search
  - `@TODO001_phase1_notes.md` (backend implementation results)
- Previous phase outputs: 
  - `@TODO001_phase1_handoff.md` (backend integration details)
- Session setup: Run `/clear` to start fresh

### Context for Claude
**IMPORTANT**: This is a new session continuing MVP Phase 2 - minimal UI for regulatory document access.

**Previous Phase Results**: Backend completed with document_type support, admin upload capability, and basic RLS policies.

**MVP Phase 2 Goal**: Add minimal UI changes to enable regulatory document functionality.

**Scope**:
- Add simple admin upload option (reuse existing upload UI)
- Add basic regulatory document access for users
- Minimal UI changes - leverage existing components
- Focus on functionality over polish

### Tasks

#### Minimal Admin Upload Enhancement
1. Find existing upload interface/component
2. Add simple document type selection for admin users:
   - Check if user has admin role
   - Show documentType field if admin (regulatory_document option)
   - Pass documentType in form data to upload-handler
3. Test admin can upload regulatory documents
4. Ensure regular users see no changes

#### Basic User Access to Regulatory Documents
1. Find existing document search/list interface
2. Add regulatory documents to search results for users:
   - Include regulatory_document type in search queries
   - Display document type indicator in results
   - Enable viewing regulatory documents (read-only)
3. Test users can find and view regulatory documents
4. Ensure regulatory documents are clearly identified

#### MVP Integration Testing
1. Test complete admin workflow: login → upload regulatory doc → verify processing
2. Test complete user workflow: login → search → find regulatory doc → view
3. Verify existing user document functionality unchanged
4. Test error handling and edge cases

### Expected Outputs
- Save implementation notes to: `@TODO001_phase2_notes.md`
- Create MVP completion summary in: `@TODO001_phase2_completion.md`

### Progress Checklist

#### Setup
- [ ] Review Phase 1 backend implementation
- [ ] Locate existing upload and search UI components
- [ ] Understand current user interface patterns

#### Admin Upload UI
- [ ] Find current upload interface/component
- [ ] Add admin role detection in frontend
- [ ] Add document type selection for admin users
- [ ] Update form submission to include documentType
- [ ] Test admin upload functionality
- [ ] Verify regular users see no UI changes

#### User Access UI
- [ ] Find current document search/list interface
- [ ] Include regulatory documents in search queries
- [ ] Add document type indicators in search results
- [ ] Enable viewing regulatory documents (read-only)
- [ ] Test user search and access functionality

#### MVP Testing & Validation
- [ ] Test end-to-end admin workflow
- [ ] Test end-to-end user workflow
- [ ] Verify existing functionality unchanged
- [ ] Test basic error scenarios
- [ ] Confirm MVP requirements met

#### Documentation
- [ ] Save `@TODO001_phase2_notes.md`
- [ ] Save `@TODO001_phase2_completion.md`

---

# MVP Completion Checklist

## Phase 1: Core Backend Implementation
- [ ] Document type enum created (user_document, regulatory_document)
- [ ] Documents table extended with document_type column
- [ ] Basic index on document_type implemented
- [ ] Upload-handler enhanced for admin role check and document_type
- [ ] Basic RLS policies for regulatory document access
- [ ] Data migration completed for existing documents
- [ ] Phase 1 documentation saved

## Phase 2: Minimal Frontend Access
- [ ] Admin upload option added to existing UI
- [ ] User access to regulatory documents implemented
- [ ] Document type indicators in search results
- [ ] Basic regulatory document viewing (read-only)
- [ ] MVP integration testing completed
- [ ] Phase 2 documentation saved

## MVP Sign-off

### Essential Requirements Met
- [ ] Admin can upload documents with regulatory_document type
- [ ] Documents processed through existing pipeline unchanged
- [ ] Users can view regulatory documents (basic access)
- [ ] Basic admin/user permission separation works
- [ ] Existing user uploads continue functioning normally

### MVP Validation
- [ ] Test complete admin upload flow
- [ ] Test user access to regulatory documents  
- [ ] Verify existing user functionality unchanged
- [ ] Confirm processing pipeline works for both document types
- [ ] Basic error handling functional

### MVP Success Criteria
- [ ] Admin upload works with document_type = 'regulatory_document'
- [ ] Existing user upload pipeline unaffected
- [ ] Users can search and view regulatory documents
- [ ] Basic admin/user permission separation functional

**MVP Status**: [ ] Core regulatory document functionality implemented and ready for use

---

*This MVP TODO provides focused implementation for essential regulatory document functionality, enabling the base system required for further development.*