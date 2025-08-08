# Phase 1 Prompt: Database Foundation & Core Infrastructure

You are implementing **Phase 1** of the Short-Term Chat Memory MVP. This phase focuses on creating the database foundation for a standalone memory system that stores chat summaries without any workflow integrations.

## Project Context

**Goal**: Create database schema and basic CRUD operations for chat memory storage
**Scope**: Standalone system with manual API triggers (no workflow automation)
**Architecture**: PostgreSQL/Supabase backend with two core tables
**Memory Structure**: Three fields per chat (user_confirmed, llm_inferred, general_summary)

## Required Reading

Before starting, read these files for complete context:
- `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/tooling/memory/short/initial_implementation/RFC001.md` (database schema specifications)
- `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/tooling/memory/short/initial_implementation/PRD001.md` (requirements)
- `/Users/aq_home/1Projects/accessa/insurance_navigator/docs/initiatives/agents/tooling/memory/short/initial_implementation/TODO001.md` (complete implementation plan)

## Database Requirements

From RFC001.md, implement these two core tables:

### chat_metadata table
- Stores canonical memory summaries per chat
- Fields: chat_id (UUID PK), user_confirmed (JSONB), llm_inferred (JSONB), general_summary (TEXT), token_count (INTEGER), timestamps
- Foreign key relationship to existing chats table
- Optimized indexes for performance

### chat_context_queue table  
- Write-ahead log for reliable memory updates
- Fields: id (UUID PK), chat_id (FK), new_context_snippet (TEXT), status (VARCHAR), processing timestamps, retry fields, error_message
- Status tracking: 'pending_summarization', 'complete'
- Indexes for queue processing efficiency

## Implementation Tasks

### 1. Environment Setup
- Identify existing database migration system in the codebase
- Review current Supabase configuration and connection patterns
- Locate existing table schemas for reference patterns
- Set up development database environment

### 2. Database Schema Creation
- Create migration scripts for both tables following RFC specifications
- Add proper foreign key constraints and relationships
- Implement optimized indexes for query performance
- Include rollback procedures for safe deployment

### 3. CRUD Operations Implementation
- **Memory retrieval**: Query chat_metadata by chat_id with graceful handling of missing data
- **Memory upsert**: Update existing memory or insert new record with validation
- **Queue operations**: Insert entries, update status, query pending entries with retry logic
- **Error handling**: Connection management and comprehensive error handling

### 4. Testing Infrastructure
- Set up unit test framework for database operations
- Create test data fixtures for various memory scenarios
- Add performance testing for concurrent operations (1000+ memory records)
- Implement database rollback/cleanup for test isolation

### 5. Development Utilities
- Create monitoring queries for queue status and depth
- Add data validation functions for memory field types  
- Implement cleanup procedures for completed queue entries
- Create backup/restore procedures for development

## Expected Outputs

Save your work in these files:
- `@TODO001_phase1_notes.md`: Implementation details, CRUD specifications, performance results, setup instructions
- `@TODO001_phase1_decisions.md`: Database design choices, indexing strategy, error handling approach, testing decisions
- `@TODO001_phase1_handoff.md`: Database connection details, available CRUD functions and interfaces, test setup instructions, any unresolved issues

## Success Criteria

- Both database tables created with proper schema and indexes
- All CRUD operations implemented with comprehensive error handling  
- Unit tests passing for memory operations with various scenarios
- Performance tests validate concurrent operations and query speed
- Complete documentation saved for Phase 2 handoff

## Development Notes

- Follow existing codebase patterns for database operations and migrations
- Use the exact schema specifications from RFC001.md without modifications
- Ensure all foreign key relationships are properly configured
- Test with realistic data volumes (1000+ memory records) to validate performance
- Document any architectural decisions or trade-offs made during implementation

Begin by reading the required files, then proceed with environment setup and schema implementation.